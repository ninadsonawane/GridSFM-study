from adapter import *
import argparse, datetime, platform, subprocess, traceback
from torch_geometric.data import HeteroData
from gridsfm.checkpoint import load_model
from electrical import csvsave

METHODS=[('frozen-official','V2-frozen+official-PF',False),('frozen-exact','V2-frozen+official-PF-exact-matrix',True)]
ADAPTED=[('adapted-official','V2-adapted+official-PF',False),('adapted-exact','V2-adapted+official-PF-exact-matrix',True)]

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def scenarios():
    plan=read(PRIOR/'scenario-plan.json')
    return [{'id':s,'network':s.removesuffix('-base'),'group':'baseline','absolute_P_factor':1.,'absolute_Q_factor':1.} for s in plan['baseline_ids']]+plan['scenarios']

def freeze():
    target=ROOT/'manifests/execution.json'
    assert not target.exists(),'Manifest already frozen'
    assert read(ROOT/'validation/adapter-gates.json')['original_matrix_known_control_gates_pass']
    specs=scenarios();assert len(specs)==59 and len({r['id'] for r in specs})==59
    inventory=read(PRIOR/'artifact-sha256.json')
    for spec in specs:
        sid=spec['id']; path=PRIOR/'results'/sid/'input.json'
        expected=spec.get('input_sha256',inventory[f'results/{sid}/input.json'])
        assert sha(path)==expected
        spec['input_sha256']=expected
        spec['reused_v2_state_sha256']=sha(path.parent/'newer-base-v2-native.json')
        spec['reused_prepared_graph_sha256']=sha(path.parent/'newer-base-v2-prepared-used.pt')
    source_hashes=read(ROOT/'manifests/reuse-audit.json')['source_files']
    for rel,expected in source_hashes.items():assert sha(SOURCE/rel)==expected,rel
    import scipy,torch_geometric
    adapted=read(ROOT/'manifests/adapted-checkpoint.json')
    assert sha(adapted['local_path'])==adapted['sha256']
    record={'frozen_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_pin':PIN,
            'study_code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
            'code_sha256':{p.name:sha(p) for p in (ROOT/'code').glob('*.py')},
            'official_source_files':source_hashes,'preset':PRESET,'tolerances':read(PRIOR/'manifest.json')['tolerances'],
            'scenarios':specs,'initialization':'cold DC angles plus native predicted full Vm, no reference labels or inter-scenario reuse',
            'frozen_checkpoint':read(PRIOR/'manifest.json')['models']['newer-base-v2'],
            'adapted_checkpoint':adapted,'adapted_clip_mode':'sigmoid; compare to separately retained adapted-native state',
            'environment':{'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'torch':torch.__version__,'torch_geometric':torch_geometric.__version__,'platform':platform.platform(),'threads':4,'seed':0},
            'stage_availability':{'case300':{'frozen_official':True,'adapted_official':False,'reason':'No released compatible case300 adapted checkpoint'},'case300x2':{'frozen_official':True,'adapted_official':False,'reason':'No released compatible constructed-case checkpoint'},'case500goc':{'frozen_official':True,'adapted_official':True,'weights':'author n0100'}},
            'missing_author_component':'evaluate_model/completion.py referenced by train_elastic.py is absent from the 76-file pinned tree; unchanged newton_pf plus disclosed study export adapter is used, not a claim of full paper reproduction'}
    save(target,record);print('FROZEN',len(specs),'inputs',flush=True)

_model=None
def adapted_native(sid):
    global _model
    target=ROOT/'results'/sid/'adapted-native'
    if (target/'status.json').exists():return read(target/'state.json')
    assert sid.startswith('case500goc-')
    manifest=read(ROOT/'manifests/execution.json')
    base=pathlib.Path(manifest['frozen_checkpoint']['checkpoint_path'])
    adapted=pathlib.Path(manifest['adapted_checkpoint']['local_path'])
    if _model is None:
        assert sha(base)==manifest['frozen_checkpoint']['checkpoint_sha256']
        assert sha(adapted)==manifest['adapted_checkpoint']['sha256']
        torch.manual_seed(0)
        _model=load_model(base,device='cpu')
        _model.load_state_dict(torch.load(adapted,weights_only=True,map_location='cpu'),strict=True)
        _model.clip_mode='sigmoid';_model.eval()
    d=PRIOR/'results'/sid
    graph=HeteroData.from_dict(torch.load(d/'newer-base-v2-prepared-used.pt',weights_only=True,map_location='cpu'))
    c=read(d/'input.json');mapping=read(d/'newer-base-v2-input.pyg.json')['metadata']
    target.mkdir(parents=True,exist_ok=True)
    with torch.inference_mode():
        output=_model(graph.clone())
        returned={'bus':output['bus'].pred.detach().cpu(),'generator':output['generator'].pred.detach().cpu()}
    torch.save(returned,target/'returned.pt')
    raw={k:v.double().numpy() for k,v in returned.items()}
    state={'vm':raw['bus'][:,1].tolist(),'va_deg':np.rad2deg(raw['bus'][:,0]).tolist(),'pg_mw':[0.]*len(c['gen']),'qg_mvar':[0.]*len(c['gen'])}
    for j,i in enumerate(mapping['gen_source_rows']):
        state['pg_mw'][i]=float(raw['generator'][j,0]*c['baseMVA']);state['qg_mvar'][i]=float(raw['generator'][j,1]*c['baseMVA'])
    save(target/'state.json',state)
    ref=read(d/'ac-native.json') if (d/'ac-native.json').exists() else None
    metric,bus,gen,branch=evaluate(c,state,'V2-adapted-native',ref)
    metric.update(scenario=sid)
    save(target/'metrics.json',metric)
    for name,rows in [('bus',bus),('generator',gen),('branch',branch)]:csvsave(target/(name+'.csv'),rows)
    save(target/'status.json',{'status':'RETURNED','scenario':sid,'method':'V2-adapted-native','checkpoint_sha256':sha(adapted),'source_commit':PIN,'clip_mode':'sigmoid','prepared_graph_reused_sha256':sha(d/'newer-base-v2-prepared-used.pt'),'native_saved_before_evaluation':True})
    return state

def run(phase):
    manifest=read(ROOT/'manifests/execution.json')
    for name,expected in manifest['code_sha256'].items():assert sha(ROOT/'code'/name)==expected,name
    specs=manifest['scenarios']
    if phase=='baseline':specs=[s for s in specs if s['group']=='baseline']
    elif phase=='main':specs=[s for s in specs if s['group']!='baseline' and 'sensitivity' not in s['group']]
    elif phase=='sensitivity':specs=[s for s in specs if 'sensitivity' in s['group']]
    for spec in specs:
        sid=spec['id'];d=PRIOR/'results'/sid
        assert sha(d/'input.json')==spec['input_sha256']
        controls=read(d/'newer-base-v2-native.json')
        stages=[(folder,method,exact,controls) for folder,method,exact in METHODS]
        if spec['network']=='case500goc':
            adapted=adapted_native(sid)
            stages += [(folder,method,exact,adapted) for folder,method,exact in ADAPTED]
        for folder,method,exact,state in stages:
            destination=ROOT/'results'/sid/folder
            if (destination/'status.json').exists():continue
            try:
                _,status=score_and_save(destination,sid,state,method,exact=exact)
                print(sid,folder,'CONVERGED' if status['converged'] else 'NONCONVERGED',status['iterations'],flush=True)
            except Exception as error:
                destination.mkdir(parents=True,exist_ok=True)
                save(destination/'status.json',{'scenario':sid,'method':method,'status':'ERROR','error':repr(error),'traceback':traceback.format_exc(),'attempted':True,'converged':False,'source_commit':PIN})
                raise
    save(ROOT/'manifests'/(phase+'-complete.json'),{'status':'COMPLETE','scenario_count':len(specs),'ids':[s['id'] for s in specs],'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['freeze','baseline','main','sensitivity']);args=parser.parse_args()
    if args.phase=='freeze':freeze()
    else:run(args.phase)
