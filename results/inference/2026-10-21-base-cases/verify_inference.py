import sys,json,math,hashlib
from pathlib import Path
OUT=Path(__file__).parent
MODEL=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM')
sys.path.insert(0,str(MODEL/'model'))
import torch
from gridsfm import load_model,predict,load_pyg_json,prepare_for_inference
torch.manual_seed(0);torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
model=load_model(MODEL/'model/checkpoints/gridsfm_open_v1.1.pt',device='cpu')
checks={}
for name in ['case300','case300x2']:
    raw=json.loads((OUT/f'{name}-model-output.json').read_text())
    clean=predict(model,OUT/f'{name}.pyg.json')
    labeled=predict(model,OUT/f'{name}-labeled.pyg.json')
    assert all(torch.equal(clean[k],labeled[k]) for k in ['V','theta','Pg','Qg','Pij','Qij','Pji','Qji'])
    assert all(torch.equal(clean[k],torch.tensor(raw[k],dtype=clean[k].dtype)) for k in ['V','theta','Pg','Qg'])
    d=prepare_for_inference(load_pyg_json(OUT/f'{name}.pyg.json'))
    n=d['bus'].x.size(0);m=sum(d['bus',family,'bus'].edge_index.size(1) for family in ['ac_line','transformer'])
    nc=d['cycle'].x.size(0)
    assert nc==m-n+1,(name,nc,m-n+1)
    count=sum(clean['flow_edge_counts']);assert count==m
    checks[name]={'prediction_label_invariance':'bitwise identical',
                  'repeat_determinism':'bitwise identical','cycle_count':nc,
                  'expected_cycle_rank':m-n+1,'physical_branch_output_count':count,
                  'finite_predictions':all(torch.isfinite(clean[k]).all().item() for k in ['V','theta','Pg','Qg'])}
    if name=='case300x2':
        x=json.loads((OUT/f'{name}.pyg.json').read_text());ids=x['metadata']['ac_line_branch_ids']+x['metadata']['transformer_branch_ids']
        assert 'tie:1' in ids and 'tie:2' in ids
        checks[name]['both_physical_tie_ids_preserved']=True
sample=json.loads((MODEL/'model/samples/case500_goc.pyg.json').read_text())
p=json.loads((OUT/'control-case500-model-output.json').read_text())
by=sample['solution']['nodes']['bus'];gy=sample['solution']['nodes']['generator'];gx=sample['grid']['nodes']['generator']
cost=lambda pg:sum(x[8]*v**2+x[9]*v+x[10] for x,v in zip(gx,pg))
cr=cost([x[0] for x in gy]);cp=cost(p['Pg'])
checks['shipped_case500_control']={'voltage_mae_pu':sum(abs(a-b[1]) for a,b in zip(p['V'],by))/len(by),
    'absolute_cost_error_percent':100*abs(cp-cr)/abs(cr),'model_feasibility_probability':p['feas'],
    'scope':'sanity comparison with shipped labels; not an independent electrical feasibility certification'}
hashes={str(p.relative_to(MODEL)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((MODEL/'model/gridsfm').glob('*.py'))}
checks['model_source_sha256']=hashes
(OUT/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps({k:v for k,v in checks.items() if k!='model_source_sha256'},indent=2))
