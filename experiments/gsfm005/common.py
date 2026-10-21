"""GSFM-005 revision2: bounded CPU discovery. Original model source stays unchanged."""
import os,sys,json,hashlib,time,math,random,copy,subprocess,platform
from pathlib import Path
os.environ['OMP_NUM_THREADS']='4';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1';os.environ['VECLIB_MAXIMUM_THREADS']='1';os.environ['PYTHONDONTWRITEBYTECODE']='1'
REPO=Path(os.environ.get('GSFM005_ROOT','/Users/ninadsonawane/workspace/research-dev/GridSFM-study'))
MODEL=REPO.parent/'GridSFM';BASE=REPO/'results/inference/2026-10-21-base-cases'
RUN_ID=os.environ.get('GSFM005_RUN_ID','20261021T120300Z-m5-seeds11-22-33')
RUN=REPO/'results/pilots/GSFM-005'/RUN_ID
import datetime
START=datetime.datetime.fromisoformat(os.environ.get('GSFM005_START_UTC','2026-10-21T12:01:19+00:00')).timestamp()
if RUN_ID!='20261021T120300Z-m5-seeds11-22-33' and 'GSFM005_START_UTC' not in os.environ:raise ValueError('New replay runs require an explicit original start time')
COMPUTE_END=START+4*3600+40*60;HARD_END=START+5*3600
sys.path[:0]=[str(REPO/'scripts/python'),str(MODEL/'model')]
import numpy as np
from physics_metrics import evaluate,branch_flows,cost,wrap_degrees
from gridsfm_convert import convert
def read(p):return json.loads(Path(p).read_text())
def save(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def content_hash(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def deadline():
    if time.time()>=COMPUTE_END:raise TimeoutError('GSFM-005 compute cutoff reached')
def log(event,**kwargs):
    row={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':event,**kwargs}
    with (RUN/'events.jsonl').open('a') as f:f.write(json.dumps(row,allow_nan=False)+'\n')
    print(json.dumps(row),flush=True)
def seed_all(seed=11):
    import torch
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
def physical_state(out):
    return {'vm':out['bus'].pred[:,1].detach().cpu().double().tolist(),
            'va_deg':np.rad2deg(out['bus'].pred[:,0].detach().cpu().double().numpy()).tolist(),
            'pg_mw':(out['generator'].pred[:,0].detach().cpu().double()*100).tolist(),
            'qg_mvar':(out['generator'].pred[:,1].detach().cpu().double()*100).tolist()}
def decode_vector(v):
    return dict(va_deg=np.rad2deg(v[:300]).tolist(),vm=v[300:600].tolist(),pg_mw=(v[600:669]*100).tolist(),qg_mvar=(v[669:738]*100).tolist())
def encode_state(s):return np.r_[np.deg2rad(s['va_deg']),s['vm'],np.array(s['pg_mw'])/100,np.array(s['qg_mvar'])/100]
def score(c,p,ref):
    m=evaluate(c,p);rc=cost(c,ref['pg_mw'],ref['qg_mvar']);slack=next(i for i,b in enumerate(c['bus']) if b[1]==3)
    ang=[abs(wrap_degrees((a-p['va_deg'][slack])-(b-ref['va_deg'][slack]))) for a,b in zip(p['va_deg'],ref['va_deg'])]
    m.update(cost_error_percent=100*abs(m['generation_cost_per_hour']-rc)/max(abs(rc),1),signed_cost_error_percent=100*(m['generation_cost_per_hour']-rc)/max(abs(rc),1),voltage_mae_pu=float(np.mean(np.abs(np.array(p['vm'])-ref['vm']))),angle_mae_deg=float(np.mean(ang)),pg_mae_mw=float(np.mean(np.abs(np.array(p['pg_mw'])-ref['pg_mw']))),qg_mae_mvar=float(np.mean(np.abs(np.array(p['qg_mvar'])-ref['qg_mvar']))))
    return {k:v for k,v in m.items() if k not in ['pf_mw','qf_mvar','pt_mw','qt_mvar']}
def val_score(rows):
    return (float(np.mean([np.log1p(max(r['max_p_residual_mw'],r['max_q_residual_mvar'])) for r in rows])),float(np.median([r['cost_error_percent'] for r in rows])))

OLD=REPO/'results/pilots/GSFM-004/20261021T104843Z-m5-seed11'
