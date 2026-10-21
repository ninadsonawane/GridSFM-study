import os,sys,time,json,hashlib,datetime,copy,math,random,traceback
from pathlib import Path
os.environ['XDG_CACHE_HOME']='/private/tmp/gsfm006-20261021T171629Z/cache'
os.environ.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
ROOT=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study'); SRC=Path('/private/tmp/gsfm006-source-20261021'); WORK=Path('/private/tmp/gsfm006-20261021T171629Z'); RUN=WORK/'results';RUN.mkdir(exist_ok=True)
START=datetime.datetime(2026,10,21,17,16,29,tzinfo=datetime.timezone.utc).timestamp()
CKPT=WORK/'gridsfm_open_v2.pt'; OLD=ROOT/'results/pilots/GSFM-004/20261021T104843Z-m5-seed11'; PREV=ROOT/'results/pilots/GSFM-005/20261021T120300Z-m5-seeds11-22-33'
sys.path[:0]=[str(SRC/'model'),str(SRC/'finetune_model/src'),str(ROOT/'scripts/python')]
import numpy as np,torch,psutil
from gridsfm.checkpoint import load_model
from gridsfm.data import batch_data_list,prepare_for_inference,drop_offline_rows
from dataset import load_obj
from closure import extract_case,build_Ssp,dc_init_V,newton_pf,close_batch,ClosurePool
from gridsfm_convert import convert
from physics_metrics import evaluate,cost,wrap_degrees
from store import CaseStore
from masks import bus_masks
import yaml

def read(p):return json.loads(Path(p).read_text())
def save(p,o):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def log(event,**kw):
 row=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),event=event,**kw);print(json.dumps(row,default=str),flush=True)
 with (RUN/'events.jsonl').open('a') as f:f.write(json.dumps(row,default=str)+'\n')
PEAK=0;MINAV=10**20

def guard():
 global PEAK,MINAV
 p=psutil.Process();rss=p.memory_info().rss+sum(c.memory_info().rss for c in p.children(recursive=True) if c.is_running());av=psutil.virtual_memory().available;PEAK=max(PEAK,rss);MINAV=min(MINAV,av)
 if rss>32*2**30 or av<12*2**30 or time.time()>START+3*3600+40*60:raise RuntimeError('Resource/deadline stop')
 return dict(process_tree_RSS_bytes=rss,peak_RSS_bytes=PEAK,minimum_available_bytes=MINAV)
def finite(x,label=''):
 if isinstance(x,torch.Tensor) and x.numel() and not torch.isfinite(x).all():raise FloatingPointError(label)
def seed():random.seed(11);np.random.seed(11);torch.manual_seed(11);torch.set_num_threads(4)
def make_model():
 seed();m=load_model(CKPT,'cpu');blob=torch.load(CKPT,weights_only=True,map_location='cpu');m.load_state_dict(blob['state_dict'],strict=True);m.clip_mode='sigmoid';m.eval()
 # Check values BEFORE upstream zero sanitizers; leave finite behavior identical.
 import gridsfm.model as mm,gridsfm.blocks as bb
 if not getattr(mm,'_gsfm006_guard',False):
  orig=mm._nan_to_zero
  def checked(x,*a,**kw):finite(x,'pre-sanitizer nonfinite');return orig(x,*a,**kw)
  mm._nan_to_zero=checked;bb._nan_to_zero=checked;mm._gsfm006_guard=True
 return m
def append_availability(obj):
 # Current converter emits active-only rows. Explicit new schema status columns.
 for rows in obj['grid']['nodes'].values():
  for row in rows:row.append(1.0)
 for name in ['ac_line','transformer']:
  for row in obj['grid']['edges'][name]['features']:row.append(1.0)
class Item:
 def __init__(self,rec):
  self.rec=rec;self.path=Path(rec['path']);self.c=read(self.path/'input.json');self.ref=read(self.path/'reference.json');t=time.perf_counter();self.obj=convert(self.c);append_availability(self.obj);self.d=load_obj(self.obj);self.kept=drop_offline_rows(self.d);self.d=prepare_for_inference(self.d);self.prep_s=time.perf_counter()-t;self.case=extract_case(self.d)
  assert self.c['baseMVA']==100 and len(self.c['gen'])==self.case.n_gen
  self.key=rec['scenario_id'];self.pg_gt=torch.tensor(np.array(self.ref['pg_mw'])/100,dtype=torch.float64);self.vm_gt=torch.tensor(self.ref['vm'],dtype=torch.float64)
 def batch(self):return batch_data_list([self.d.clone()])
def items(split,old=False):
 man=read((OLD if old else PREV)/'data/manifest.json');return [Item(r) for r in man[split] if r['accepted']]
def physical(out):return dict(vm=out['bus'].pred[:,1].detach().double().tolist(),va_deg=np.rad2deg(out['bus'].pred[:,0].detach().double().numpy()).tolist(),pg_mw=(100*out['generator'].pred[:,0].detach().double()).tolist(),qg_mvar=(100*out['generator'].pred[:,1].detach().double()).tolist())
def score(it,s):
 c=it.c;ref=it.ref;m=evaluate(c,s);sl=next(i for i,b in enumerate(c['bus']) if b[1]==3);rc=cost(c,ref['pg_mw'],ref['qg_mvar'])
 m={k:v for k,v in m.items() if k not in ['pf_mw','qf_mvar','pt_mw','qt_mvar']};m.update(cost_error_percent=100*abs(m['generation_cost_per_hour']-rc)/max(abs(rc),1),voltage_mae_pu=float(np.mean(np.abs(np.array(s['vm'])-ref['vm']))),angle_mae_deg=float(np.mean([abs(wrap_degrees((a-s['va_deg'][sl])-(b-ref['va_deg'][sl]))) for a,b in zip(s['va_deg'],ref['va_deg'])])),pg_mae_mw=float(np.mean(np.abs(np.array(s['pg_mw'])-ref['pg_mw']))),qg_mae_mvar=float(np.mean(np.abs(np.array(s['qg_mvar'])-ref['qg_mvar']))))
 return m

def completion(it,raw,tol=1e-8):
 c=it.case;pg=np.array(raw['pg_mw'])/100;v=np.array(raw['vm']);v0=dc_init_V(c,pg,v);v0[c.ctrl_bus]=v[c.ctrl_bus]*np.exp(1j*np.angle(v0[c.ctrl_bus]));res=newton_pf(c,build_Ssp(c,pg),v0,tol,40,True)
 # The repository releases closure but no completion/export module. Preserve predicted
 # non-slack P; recover slack P and bus-level Q from the closure network, distributing
 # among online co-located units in proportion to capability ranges, with no clipping.
 inj=res.V*np.conj(c.Ybus@res.V);gp=pg.copy();gq=np.zeros(c.n_gen);alloc=[]
 for bus in np.unique(c.gen2bus[c.gen_online]):
  ix=np.where(c.gen_online&(c.gen2bus==bus))[0];qr=c.Qmax[ix]-c.Qmin[ix];frac=qr/qr.sum() if qr.sum()>0 else np.ones(len(ix))/len(ix);qtot=inj[bus].imag+c.Qd[bus];gq[ix]=c.Qmin[ix]+frac*(qtot-c.Qmin[ix].sum())
  if bus in c.ref:
   pr=c.Pmax[ix]-c.Pmin[ix];pf=pr/pr.sum() if pr.sum()>0 else np.ones(len(ix))/len(ix);ptot=inj[bus].real+c.Pd[bus];gp[ix]=c.Pmin[ix]+pf*(ptot-c.Pmin[ix].sum())
  alloc.append(dict(bus_index=int(bus),generator_rows=ix.tolist(),Q_total_pu=float(qtot)))
 s=dict(vm=np.abs(res.V).tolist(),va_deg=np.rad2deg(np.angle(res.V)).tolist(),pg_mw=(gp*100).tolist(),qg_mvar=(gq*100).tolist())
 return s,dict(converged=bool(res.converged),iterations=res.iters,closure_max_residual_pu=res.norm_hist[-1],norm_history=res.norm_hist,Q_limit_switching=False,export_allocation='capability-range affine allocation, no clipping; study export adapter, not released completion module',allocation=alloc)
