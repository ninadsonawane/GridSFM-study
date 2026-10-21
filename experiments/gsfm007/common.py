import os,sys,time,json,hashlib,datetime,copy,math,random,traceback
from pathlib import Path
os.environ['XDG_CACHE_HOME']=os.environ.get('GSFM007_CACHE','/private/tmp/gsfm007-20261021T195824Z/cache')
os.environ.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
ROOT=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study'); SRC=ROOT/'work/GSFM-006-source-517a075'; WORK=Path(os.environ.get('GSFM007_WORK','/private/tmp/gsfm007-20261021T195824Z')); RUN=Path(os.environ.get('GSFM007_RUN',str(WORK/'results')));RUN.mkdir(exist_ok=True)
START=datetime.datetime.fromisoformat(os.environ.get('GSFM007_START_UTC','2026-10-21T19:58:24+00:00')).timestamp()
CKPT=ROOT/'data/checkpoints/GSFM-006-gridsfm_open_v2.pt'; OLD=ROOT/'results/pilots/GSFM-004/20261021T104843Z-m5-seed11'; PREV=ROOT/'results/pilots/GSFM-005/20261021T120300Z-m5-seeds11-22-33'
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
 if rss>32*2**30 or av<12*2**30 or time.time()>START+4*3600+35*60:raise RuntimeError('Resource/deadline stop')
 return dict(process_tree_RSS_bytes=rss,peak_RSS_bytes=PEAK,minimum_available_bytes=MINAV)
def finite(x,label=''):
 if isinstance(x,torch.Tensor) and x.numel() and not torch.isfinite(x).all():raise FloatingPointError(label)
def seed(s=11):random.seed(s);np.random.seed(s);torch.manual_seed(s);torch.set_num_threads(4)
def make_model(s=11):
 seed(s);m=load_model(CKPT,'cpu');blob=torch.load(CKPT,weights_only=True,map_location='cpu');m.load_state_dict(blob['state_dict'],strict=True);m.clip_mode='sigmoid';m.eval()
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
  self.rec=rec;self.path=Path(rec['path']);self.c=read(self.path/'input.json');self.ref=read(self.path/'reference.json') if (self.path/'reference.json').exists() else None;t=time.perf_counter();self.obj=convert(self.c);append_availability(self.obj);self.d=load_obj(self.obj);self.kept=drop_offline_rows(self.d);self.d=prepare_for_inference(self.d);self.prep_s=time.perf_counter()-t;self.case=extract_case(self.d)
  assert self.c['baseMVA']==100 and len(self.c['gen'])==self.case.n_gen
  self.key=rec['scenario_id'];self.pg_gt=torch.tensor(np.array(self.ref['pg_mw'])/100,dtype=torch.float64) if self.ref else None;self.vm_gt=torch.tensor(self.ref['vm'],dtype=torch.float64) if self.ref else None
 def batch(self):return batch_data_list([self.d.clone()])
def items(split,old=False):
 man=read((OLD if old else PREV)/'data/manifest.json');return [Item(r) for r in man[split] if r['accepted']]
def physical(out):return dict(vm=out['bus'].pred[:,1].detach().double().tolist(),va_deg=np.rad2deg(out['bus'].pred[:,0].detach().double().numpy()).tolist(),pg_mw=(100*out['generator'].pred[:,0].detach().double()).tolist(),qg_mvar=(100*out['generator'].pred[:,1].detach().double()).tolist())
def score(it,s):
 c=it.c;m=evaluate(c,s);m={k:v for k,v in m.items() if k not in ['pf_mw','qf_mvar','pt_mw','qt_mvar']}
 pv=[];qv=[]
 for g,p,q in zip(c['gen'],s['pg_mw'],s['qg_mvar']):
  pv.append(max(g[9]-p,p-g[8],0));qv.append(max(g[4]-q,q-g[3],0))
 m.update(max_Pg_violation_MW=max(pv,default=0),max_Qg_violation_MVAr=max(qv,default=0),Pg_violated_rows=[i+1 for i,v in enumerate(pv) if v>1e-3],Qg_violated_rows=[i+1 for i,v in enumerate(qv) if v>1e-3],worst_Pg_row=int(np.argmax(pv))+1,worst_Qg_row=int(np.argmax(qv))+1)
 ref=it.ref
 if ref:
  sl=next(i for i,b in enumerate(c['bus']) if b[1]==3);rc=cost(c,ref['pg_mw'],ref['qg_mvar']);gap=100*(m['generation_cost_per_hour']-rc)/max(abs(rc),1)
  m.update(cost_error_percent=abs(gap),signed_cost_gap_percent=gap,reference_cost=rc,voltage_mae_pu=float(np.mean(np.abs(np.array(s['vm'])-ref['vm']))),angle_mae_deg=float(np.mean([abs(wrap_degrees((a-s['va_deg'][sl])-(b-ref['va_deg'][sl]))) for a,b in zip(s['va_deg'],ref['va_deg'])])),pg_mae_mw=float(np.mean(np.abs(np.array(s['pg_mw'])-ref['pg_mw']))),qg_mae_mvar=float(np.mean(np.abs(np.array(s['qg_mvar'])-ref['qg_mvar']))))
 else:m.update(cost_error_percent=None,signed_cost_gap_percent=None,reference_cost=None)
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

from physics_metrics import branch_flows
from matpower_case import read_case
import subprocess,selectors,ast,textwrap,types,inspect,collections
from elastic_loss import elastic_loss,curriculum_tol
from loss import control_loss,rmse_control_loss
from optim import build_optimizer,build_scheduler
from closure import flat_init_V

def dataset(net,split):return [Item(r) for r in read(RUN/f'data/{net}/manifest.json')[split] if r.get('accepted',True) and r.get('status') not in ['DUPLICATE','DEGENERATE']]
def write_m(c,p):
 lines=['function mpc = candidate',"mpc.version = '2';",f'mpc.baseMVA = {c["baseMVA"]};']
 for k in ['bus','gen','branch','gencost']:
  lines+=[f'mpc.{k} = [']+[' '.join(format(v,'.17g') for v in row)+';' for row in c[k]]+ ['];']
 Path(p).write_text('\n'.join(lines)+'\n')
def raw_from_solution(c,sol):
 return dict(vm=[sol['bus'][str(int(b[0]))]['vm'] for b in c['bus']],va_deg=[math.degrees(sol['bus'][str(int(b[0]))]['va']) for b in c['bus']],pg_mw=[100*sol['gen'][str(i+1)]['pg'] for i in range(len(c['gen']))],qg_mvar=[100*sol['gen'][str(i+1)]['qg'] for i in range(len(c['gen']))])
class Server:
 def __init__(self):
  self.err=(RUN/'solver-stderr.log').open('a');t=time.perf_counter();self.proc=subprocess.Popen(['/Users/ninadsonawane/julia/bin/julia','--startup-file=no','--project='+str(ROOT.parent/'GridSFM/power_grid/US/topology_solver_pipeline'),str(Path(__file__).with_name('solver_server.jl'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,text=True,bufsize=1);self.startup=self.receive(35);self.startup['process_ready_seconds']=time.perf_counter()-t;save(RUN/'solver-startup.json',self.startup)
 def receive(self,timeout):
  sel=selectors.DefaultSelector();sel.register(self.proc.stdout,selectors.EVENT_READ);ready=sel.select(max(.001,timeout));sel.close()
  if not ready:self.proc.kill();self.proc.wait();raise TimeoutError('solver wall watchdog')
  return json.loads(self.proc.stdout.readline())
 def request(self,it,folder,initial=None,remaining=30,capture=False):
  folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);mp=it.path/'candidate.m'
  if not mp.exists():write_m(it.c,mp)
  req=dict(matpower_file=str(mp),result_path=str(folder/'result.json'),log_path=str(folder/'solver.log'),remaining_seconds=remaining,capture_internal_iterate=capture,method='gridsfm' if initial is not None else 'default',run_id=folder.name,load_scale=1)
  if initial is not None:
   flows=branch_flows(it.c,initial['vm'],initial['va_deg']);init=dict(bus={str(int(b[0])):dict(vm=initial['vm'][i],va=math.radians(initial['va_deg'][i])) for i,b in enumerate(it.c['bus'])},gen={str(i+1):dict(pg=initial['pg_mw'][i]/100,qg=initial['qg_mvar'][i]/100) for i in range(len(it.c['gen']))},branch={str(i+1):dict(pf=flows[0][i].real/100,qf=flows[0][i].imag/100,pt=flows[1][i].real/100,qt=flows[1][i].imag/100) for i in range(len(it.c['branch']))});save(folder/'supplied-start.json',init);req['initialization_file']=str(folder/'supplied-start.json')
  t=time.perf_counter();self.proc.stdin.write(json.dumps(req)+'\n');self.proc.stdin.flush()
  try:r=self.receive(remaining)
  except TimeoutError:return dict(status='WALL_TIMEOUT',request_seconds=time.perf_counter()-t,remaining_seconds=remaining)
  r['request_seconds']=time.perf_counter()-t
  if (folder/'result.json').exists():
   raw=read(folder/'result.json');r['state']=raw_from_solution(it.c,raw['solution']);r['metrics']=score(it,r['state']);r['iterations']=raw.get('iterations');r['result_path']=str(folder/'result.json')
  save(folder/'response.json',r);return r
 def close(self):
  if self.proc.poll() is None:self.proc.stdin.write('{"quit":true}\n');self.proc.stdin.flush();self.proc.wait(timeout=10)
  self.err.close()

def recipe(net,train):
 cfg=yaml.safe_load((SRC/'finetune_model/config/case500_goc_finetune.yaml').read_text());cfg['runtime']['device']='cpu';cfg['train'].update(batch=1,lr_horizon=400);cfg['closure']['workers']=0;cfg['eval'].update(batch=1,test_batch=1)
 cfg['study']=dict(network=net,updates=1500,fit_cap_seconds=1500,seed_order=[11,22,33],selection='mean native elastic loss +32*mean control loss; >=.99 validation convergence; earliest exact tie',CPU_batch_accommodation='train/eval batch1, serial closure; no pooling top-k across cases',fixed_outputs='include fixed-P online generators and all voltage regulators')
 cfg['resolved_topk']=dict(pg=max(1,round(.0435*len(train[0].c['gen']))),v=max(1,round(.0254*len(train[0].case.ctrl_bus))))
 cfg['resolved_cost_scale']=1/max(np.mean([np.sum(abs(it.case.cp1)*it.case.Pmax+it.case.cp2*it.case.Pmax**2) for it in train]),1e-9)
 return cfg
class Store:
 def __init__(self,its):self.its={it.key:it for it in its}
 def batch(self,keys):
  assert len(keys)==1;it=self.its[keys[0]];data=it.batch();n=it.case.n_gen;b=it.case.n_bus
  return dict(data=data,pg_gt=it.pg_gt,vm_gt=it.vm_gt,av=torch.tensor(it.case.gen_online),vctrl=torch.tensor(np.isin(np.arange(b),it.case.ctrl_bus)),gen_seg=torch.zeros(n,dtype=torch.long),bus_seg=torch.zeros(b,dtype=torch.long),nseg=1)

def official_forward(model,its,cfg,pool,warm):
 # Execute the actual source-defined nested function, avoiding a duplicated objective.
 source=(SRC/'finetune_model/src/train_elastic.py').read_text();tree=ast.parse(source);outer=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_elastic');fn=next(n for n in outer.body if isinstance(n,ast.FunctionDef) and n.name=='closed_forward');code=ast.Module(body=[fn],type_ignores=[]);ast.fix_missing_locations(code);store=Store(its)
 def cases_for(keys):return [store.its[k].case for k in keys]
 ns=dict(globals(),store=store,cases_for=cases_for,model=model,WARM_START=True,COLD_INIT='dc',warm=warm,pool=pool,L=cfg['loss'],CL=cfg['closure'],D={'topk_pg':cfg['resolved_topk']['pg'],'topk_v':cfg['resolved_topk']['v']},MERIT_LOG=False,CTRL_FORM='maxaligned',cost_scale=cfg['resolved_cost_scale'],wm=170.)
 exec(compile(code,'<pinned train_elastic.closed_forward>','exec'),ns);return ns['closed_forward'],hashlib.sha256(ast.unparse(fn).encode()).hexdigest()
def val_epoch(model,fn,its):
 model.eval();rows=[]
 with torch.no_grad():
  for it in its:
   _,d=fn([it.key],tol=1e-8,wc=0.,train_mode=False);rows.append(d)
 return dict(score=float(np.mean([r['loss']+32*r['control_term'] for r in rows])),fraction_converged=float(np.mean([r['frac_converged'] for r in rows])),rows=rows)

from store import predict
