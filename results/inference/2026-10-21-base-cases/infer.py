import sys, json, math, time, hashlib, platform, subprocess
from pathlib import Path
ROOT=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study')
MODEL=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM')
sys.path.insert(0,str(ROOT/'scripts/python'))
sys.path.insert(0,str(MODEL/'model'))
import torch, numpy, scipy, torch_geometric, gridsfm
from gridsfm import load_model, predict, load_pyg_json, prepare_for_inference
from physics_metrics import evaluate
OUT=Path(__file__).parent
torch.manual_seed(0)
torch.set_num_threads(4)
torch.use_deterministic_algorithms(True)
ckpt=MODEL/'model/checkpoints/gridsfm_open_v1.1.pt'
meta={'python':sys.version,'platform':platform.platform(),'torch':torch.__version__,
      'numpy':numpy.__version__,'scipy':scipy.__version__,'pyg':torch_geometric.__version__,
      'model_module':gridsfm.__file__,'device':'cpu','threads':torch.get_num_threads(),'seed':0,
      'checkpoint_sha256':hashlib.sha256(ckpt.read_bytes()).hexdigest(),
      'model_commit':subprocess.check_output(['git','-C',str(MODEL),'rev-parse','HEAD'],text=True).strip(),
      'study_commit':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()}
t=time.perf_counter(); model=load_model(ckpt,device='cpu');meta['checkpoint_load_seconds']=time.perf_counter()-t
meta['parameters']=sum(p.numel() for p in model.parameters())
(OUT/'environment.json').write_text(json.dumps(meta,indent=2)+'\n')
# Shipped supported-size control exercises the same checkpoint and installed package.
for name,path in [('control-case500',MODEL/'model/samples/case500_goc.pyg.json'),
                  ('case300',OUT/'case300.pyg.json'),('case300x2',OUT/'case300x2.pyg.json')]:
    t=time.perf_counter(); pred=predict(model,path);elapsed=time.perf_counter()-t
    serial={k:v.tolist() if torch.is_tensor(v) else v for k,v in pred.items()}
    serial['predict_seconds_including_preprocessing']=elapsed
    (OUT/f'{name}-model-output.json').write_text(json.dumps(serial,indent=2,allow_nan=False)+'\n')
    print(name,'inference seconds',elapsed,'feas classifier',pred['feas'],flush=True)
    if name.startswith('control'):continue
    case=json.loads((OUT/f'{name}-input.json').read_text())
    physical={'vm':serial['V'],'va_deg':[math.degrees(v) for v in serial['theta']],
              'pg_mw':[v*case['baseMVA'] for v in serial['Pg']],
              'qg_mvar':[v*case['baseMVA'] for v in serial['Qg']]}
    (OUT/f'{name}-prediction.json').write_text(json.dumps(physical,indent=2)+'\n')
    metrics=evaluate(case,physical)
    metrics['model_feasibility_probability']=pred['feas']
    metrics['predict_seconds_including_preprocessing']=elapsed
    (OUT/f'{name}-prediction-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    print(name,json.dumps({k:v for k,v in metrics.items() if not isinstance(v,list)}),flush=True)
