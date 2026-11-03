"""Frozen independent P/Q benchmark; run phases in objective order."""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='4', MKL_NUM_THREADS='1')
import copy, datetime, hashlib, json, pathlib, subprocess, sys
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[2]
OLD=pathlib.Path(r'C:\Users\Ninad\Documents\Codex\2026-10-26\don-t-wait-for-max-anything\work')
RT=OLD/'runtime'
EXP=ROOT/'experiments/loading'
sys.path.insert(0,str(ROOT/'scripts/python'))
from matpower_case import read_case, construct, validate, components
from gridsfm_convert import convert
from electrical import terms, matrices, dc_matrices, excess, csvsave
from solver_checks import writecase,checkparsed

def read(p): return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(x,indent=2,allow_nan=False,default=lambda v:v.item() if isinstance(v,np.generic) else v.tolist())+'\n',encoding='utf-8')
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
TOL={'balance_MW_MVAr':1e-3,'generation_MW_MVAr':1e-3,'voltage_pu':1e-4,'thermal_MVA':1e-3,'angle_deg':1e-3,'equation_crosscheck_MVA':1e-6}
REL=[('microsoft-v1.1','microsoft','gridsfm_open_v1.1.pt'),('newer-base-v2','newer','gridsfm_open_v2.pt')]

def constraint(v,tol):
 v=np.asarray(v,float)
 if len(v)==0:return None
 return {'eligible_count':len(v),'violating_count':int(sum(v>tol)),'maximum':float(v.max()),'mean_all':float(v.mean()),'mean_violating':float(v[v>tol].mean()) if any(v>tol) else 0.0}
def err(v):
 v=np.asarray(v,float);return {'MAE':float(np.mean(abs(v))),'RMSE':float(np.sqrt(np.mean(v*v))),'count':len(v)}
def dist(v):
 v=abs(np.asarray(v,float));return {'max_abs':float(max(v)),'mean_abs':float(v.mean()),'p95_abs':float(np.percentile(v,95,method='linear')),'violating_bus_count':int(sum(v>TOL['balance_MW_MVAr'])),'bus_count':len(v)}

def evaluate(c,s,method,ref=None):
 dc=method=='DC-OPF';ids,b,e,f,t=matrices(c);g=np.array(c['gen']);on=g[:,7]>0;active=e[:,10]>0;pg=np.array(s['pg_mw']);va=np.array(s['va_deg'])
 assert len(pg)==len(g) and len(va)==len(b) and np.isfinite(pg).all() and np.isfinite(va).all()
 pex=np.where(on,excess(pg,g[:,9],g[:,8]),abs(pg));cons={'Pg_MW':constraint(pex,1e-3)}
 angle=va[f]-va[t];lo=e[:,11];hi=e[:,12]
 # MATPOWER: (0,0) disables angle bounds; +/-360 denotes unbounded side.
 ac=active&~((lo==0)&(hi==0))&((lo>-360)|(hi<360))
 aex=np.maximum(np.maximum(np.where(lo>-360,lo-angle,0),np.where(hi<360,angle-hi,0)),0)
 cons['branch_angle_deg']=constraint(aex[ac],1e-3)
 rated=active&(e[:,5]>0)
 if dc:
  B,F,pb,pf,_=dc_matrices(c);net=np.zeros(len(b));np.add.at(net,[ids[int(x)] for x in g[:,0]],np.where(on,pg,0))
  rp=net-b[:,2]-b[:,4]-c['baseMVA']*(B@np.deg2rad(va)+pb)
  sf=c['baseMVA']*(F@np.deg2rad(va)+pf);st=-sf;rq=None
  assert np.max(abs(sf-np.array(s['pf_mw'])))<1e-6
  assert np.max(abs(st-np.array(s['pt_mw'])))<1e-6
  cons.update(Qg_MVAr=None,voltage_pu=None,branch_thermal_MVA=None,branch_active_MW=constraint(np.maximum(np.maximum(abs(sf),abs(st))[rated]-e[rated,5],0),1e-3))
 else:
  for key,n in [('qg_mvar',len(g)),('vm',len(b))]:assert len(s[key])==n and np.isfinite(s[key]).all()
  qg=np.array(s['qg_mvar']);vm=np.array(s['vm']);tr=terms(c,s);rp=tr['r'].real;rq=tr['r'].imag;sf=tr['sf'];st=tr['st']
  cons.update(Qg_MVAr=constraint(np.where(on,excess(qg,g[:,4],g[:,3]),abs(qg)),1e-3),voltage_pu=constraint(excess(vm,b[:,12],b[:,11]),1e-4),branch_thermal_MVA=constraint(np.maximum(np.maximum(abs(sf),abs(st))[rated]-e[rated,5],0),1e-3),branch_active_MW=None)
 passed=bool(max(abs(rp))<=1e-3 and (dc or max(abs(rq))<=1e-3) and all(x is None or x['violating_count']==0 for x in cons.values()))
 accuracy={k:None for k in ['Pg_MW','Qg_MVAr','V_pu','aligned_angle_deg']}
 if ref is not None:
  slack=np.flatnonzero(b[:,1]==3)[0];ar=np.array(ref['va_deg']);d=(va-va[slack])-(ar-ar[slack]);d=(d+180)%360-180
  accuracy.update(Pg_MW=err((pg-ref['pg_mw'])[on]),aligned_angle_deg=err(d))
  if not dc:accuracy.update(Qg_MVAr=err((qg-ref['qg_mvar'])[on]),V_pu=err(vm-ref['vm']))
 out={'method':method,'P_balance_MW':dist(rp),'Q_balance_MVAr':None if dc else dist(rq),'constraints':cons,'accuracy':accuracy,'AC_joint_pass':None if dc else passed,'DC_own_constraints_pass':passed if dc else None,'reference_valid':ref is not None}
 bus=[{'bus_id':int(c['bus'][i][0]),'PD_MW':float(b[i,2]),'QD_MVAr':float(b[i,3]),'P_residual_MW':float(rp[i]),'Q_residual_MVAr':None if dc else float(rq[i]),'V_pu':None if dc else float(s['vm'][i]),'angle_deg':float(va[i])} for i in range(len(b))]
 branch=[{'branch_row':i+1,'from_bus':int(c['branch'][i][0]),'to_bus':int(c['branch'][i][1]),'online':bool(active[i]),'Pf_MW':float(np.real(sf[i])),'Pt_MW':float(np.real(st[i])),'Qf_MVAr':None if dc else float(np.imag(sf[i])),'Qt_MVAr':None if dc else float(np.imag(st[i])),'Sf_MVA':None if dc else float(abs(sf[i])),'St_MVA':None if dc else float(abs(st[i])),'RATE_A':float(e[i,5]) if rated[i] else None} for i in range(len(e))]
 gen=[{'generator_row':i+1,'bus_id':int(g[i,0]),'online':bool(on[i]),'Pg_MW':float(pg[i]),'Qg_MVAr':None if dc else float(s['qg_mvar'][i]),'Pmin':g[i,9],'Pmax':g[i,8],'Qmin':g[i,4],'Qmax':g[i,3]} for i in range(len(g))]
 return out,bus,gen,branch

def init():
 assert not (ROOT/'manifest.json').exists(),'Refuse replacing frozen manifest'
 base=read_case(ROOT/'sources/case300.m');assert sha(ROOT/'sources/case300.m')=='69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5'
 two,mapping=construct(base,read(ROOT/'sources/network-case300x2.json'));save(ROOT/'cases/two-copy-mapping.json',mapping)
 cases={'case300':base,'case300x2':two,'case500goc':read_case(ROOT/'sources/pglib_opf_case500_goc.m')}
 manifest={'frozen_UTC':now(),'research_question':'How do GridSFM state accuracy and physical feasibility change under independent P/Q loading changes?','source_study_revision':subprocess.check_output(['git','-C',str(OLD/'GridSFM-study'),'rev-parse','HEAD'],text=True).strip(),'tolerances':TOL,'cases':{},'models':{},'source_files':{p.name:sha(p) for p in (ROOT/'sources').iterdir() if p.is_file()},'runtime_paths':{'python':sys.executable,'source_root':str(RT),'julia':str(OLD/'julia/julia-1.11.9/bin/julia.exe'),'julia_project':str(OLD/'GridSFM-study/experiments/gsfm020/julia')},'AC_options':{'solver':'PowerModels ACP / Ipopt','tol':1e-9,'constr_viol_tol':1e-10,'acceptable_tol':1e-9,'bound_relax_factor':0,'max_iter':3000,'seconds_per_attempt':120,'starts':['default','flat'],'acceptance':'solver local success and independent common evaluator pass'},'DC_options':{'solver':'PYPOWER PIPS 200','max_iterations':150,'feastol':1e-10,'gradtol':1e-9,'comptol':1e-9},'averaging':{'state':'online generators, all active buses; equally weighted; angle referenced to original REF bus and wrapped to [-180,180)','balance':'all buses, prescribed demands, NumPy linear p95','equipment':'one violation per item with positive maximum bound excess; count exceeds tolerance; mean_all includes zeros; mean_violating separately; branch thermal maximum over both ends','feasibility':'all applicable original constraints; denominator includes every attempted scenario; separately report returned states and reference acceptance','DC':'Q, V, apparent thermal and joint AC feasibility N/A; own linear constraints separately'}}
 from model_worker import PINS
 for rel,src,ck in REL:
  assert sha(RT/'checkpoints'/ck)==PINS[rel][1]
  manifest['models'][rel]={'source_commit':PINS[rel][0],'checkpoint_sha256':sha(RT/'checkpoints'/ck),'checkpoint_path':str(RT/'checkpoints'/ck),'source_path':str(RT/'sources'/src),'clip_mode':'shipped clamp','leaky_alpha':0,'dtype':'float32','device':'CPU','seed':0,'torch_threads':4,'external_postprocessing':'none','training_exposure':'PENDING separate source audit; no ID/OOD claim'}
 for name,c in cases.items():
  validate(c);assert len(components(c))==1; obj=convert(c);assert 'solution' not in obj
  p=ROOT/'cases'/name/'base.json';save(p,c)
  manifest['cases'][name]={'file':str(p.relative_to(ROOT)),'sha256':sha(p),'bus_count':len(c['bus']),'gen_count':len(c['gen']),'branch_count':len(c['branch']),'online_rated_branches':sum(e[10]>0 and e[5]>0 for e in c['branch']),'baseMVA':c['baseMVA'],'PD_total_MW':sum(b[2] for b in c['bus']),'QD_total_MVAr':sum(b[3] for b in c['bus']),'mapping':obj['metadata']}
  d=ROOT/'results'/f'{name}-base';save(d/'input.json',c)
 manifest['code_sha256']={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*.py')};manifest['solver_server_sha256']=sha(EXP/'solver_server.jl')
 save(ROOT/'manifest.json',manifest);print('FROZEN',[(k,v['bus_count'],v['gen_count'],v['branch_count']) for k,v in manifest['cases'].items()],flush=True)

class ACServer:
 def __init__(self):
  env=os.environ.copy();env['JULIA_DEPOT_PATH']=str(OLD/'julia/depot');env['JULIA_NUM_THREADS']='1'
  self.log=(ROOT/'results/ac-server-stderr.log').open('a',encoding='utf-8')
  self.p=subprocess.Popen([str(OLD/'julia/julia-1.11.9/bin/julia.exe'),'--startup-file=no','--history-file=no','--compiled-modules=existing','--project='+str(OLD/'GridSFM-study/experiments/gsfm020/julia'),str(EXP/'solver_server.jl')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,env=env)
  while True:
   line=self.p.stdout.readline()
   if not line:raise RuntimeError('Julia server exited before ready')
   try:r=json.loads(line)
   except ValueError:continue
   if r.get('ready'):save(ROOT/'results/ac-runtime.json',r);break
 def close(self):
  if self.p.poll() is None:self.p.stdin.write('{"quit":true}\n');self.p.stdin.flush();self.p.wait(timeout=30)
  self.log.close()
 def run(self,d):
  if (d/'ac-status.json').exists():return read(d/'ac-native.json') if (d/'ac-native.json').exists() else None
  c=read(d/'input.json');writecase(c,d/'case.m');attempts=[];accepted=None
  for i,mode in enumerate(['default','flat']):
   rawpath=d/f'ac-attempt{i}.json';req={'run_id':d.name+'-'+str(i),'method':mode,'matpower_file':str(d/'case.m'),'log_path':str(d/f'ac-attempt{i}.log'),'result_path':str(rawpath),'load_scale':1.,'remaining_seconds':120.,'capture_internal_iterate':False};save(d/f'ac-request{i}.json',req)
   self.p.stdin.write(json.dumps(req)+'\n');self.p.stdin.flush()
   while True:
    line=self.p.stdout.readline()
    if not line:raise RuntimeError('AC server exited')
    try:answer=json.loads(line);break
    except ValueError:continue
   item={'initialization':mode,'response':answer}
   if rawpath.exists():
    raw=read(rawpath);checkparsed(c,raw);s=raw.get('solution',{})
    if 'bus' in s and 'gen' in s:
     point={'vm':[s['bus'][str(int(b[0]))]['vm'] for b in c['bus']],'va_deg':[float(np.rad2deg(s['bus'][str(int(b[0]))]['va'])) for b in c['bus']],'pg_mw':[s['gen'][str(j+1)]['pg']*c['baseMVA'] if g[7]>0 else 0 for j,g in enumerate(c['gen'])],'qg_mvar':[s['gen'][str(j+1)]['qg']*c['baseMVA'] if g[7]>0 else 0 for j,g in enumerate(c['gen'])]}
     save(d/f'ac-attempt{i}-state.json',point);m,*_=evaluate(c,point,'AC-OPF');item.update(solver_status=raw['termination_status'],independent_evaluation=m)
     if raw['termination_status'] in ['LOCALLY_SOLVED','OPTIMAL','ALMOST_LOCALLY_SOLVED'] and m['AC_joint_pass']:accepted=point;save(d/'ac-native.json',point)
   attempts.append(item)
   if accepted is not None:break
  save(d/'ac-status.json',{'attempts':attempts,'reference_valid':accepted is not None,'status':'CHECKED_LOCAL_OPTIMUM' if accepted is not None else 'UNKNOWN'})
  print('AC',d.name,'CHECKED' if accepted else 'UNKNOWN',flush=True);return accepted

def score_dir(d):
 c=read(d/'input.json');ref=read(d/'ac-native.json') if (d/'ac-native.json').exists() else None;out=[]
 for method,fn in [('AC-OPF','ac-native.json'),('DC-OPF','dc-native.json')]+[(r,r+'-native.json') for r,_,_ in REL]:
  if not (d/fn).exists():out.append({'method':method,'scenario':d.name,'status':'UNKNOWN_OR_NOT_RUN','reference_valid':ref is not None});continue
  s=read(d/fn);m,bu,ge,br=evaluate(c,s,method,ref);m.update(scenario=d.name,status='RETURNED');out.append(m)
  csvsave(d/(method+'-bus.csv'),bu);csvsave(d/(method+'-generator.csv'),ge);csvsave(d/(method+'-branch.csv'),br)
 save(d/'metrics.json',out);return out

def validate_evaluator():
 checks=[]
 for name in ['case300','case300x2','case500goc']:
  d=ROOT/'results'/f'{name}-base';c=read(d/'input.json');s=read(d/'ac-native.json');m,*_=evaluate(c,s,'AC-OPF',s);assert m['AC_joint_pass'];assert all(v['MAE']==0 and v['RMSE']==0 for v in m['accuracy'].values())
  i=next(j for j,g in enumerate(c['gen']) if g[7]>0);bid=int(c['gen'][i][0]);bi=next(j for j,b in enumerate(c['bus']) if b[0]==bid)
  before=terms(c,s)['r'];z=copy.deepcopy(s);z['pg_mw'][i]+=10.;z['qg_mvar'][i]+=7.;after=terms(c,z)['r'];expected=np.zeros(len(c['bus']),complex);expected[bi]=10+7j;assert max(abs(after-before-expected))<1e-7
  z=copy.deepcopy(s);z['pg_mw'][i]=c['gen'][i][8]+5.;mm,*_=evaluate(c,z,'AC-OPF');assert abs(mm['constraints']['Pg_MW']['maximum']-5)<1e-7
  z=copy.deepcopy(s);z['vm'][0]=c['bus'][0][11]+.01;mm,*_=evaluate(c,z,'AC-OPF');assert mm['constraints']['voltage_pu']['violating_count']>=1
  # Angle error must be invariant to uniform global reference shift.
  z=copy.deepcopy(s);z['va_deg']=[v+35 for v in z['va_deg']];mm,*_=evaluate(c,z,'AC-OPF',s);assert mm['accuracy']['aligned_angle_deg']['RMSE']<1e-10
  tr=terms(c,s);j=int(np.argmax(np.maximum(abs(tr['sf']),abs(tr['st']))));cc=copy.deepcopy(c);peak=float(max(abs(tr['sf'][j]),abs(tr['st'][j])));cc['branch'][j][5]=peak-1.;mm,*_=evaluate(cc,s,'AC-OPF');assert abs(mm['constraints']['branch_thermal_MVA']['maximum']-1)<1e-5
  checks.append({'network':name,'baseline_checked':True,'generation_perturbation_MW_MVAr':[10,7],'Pg_bound_excess_MW':5,'voltage_bound_detection':True,'global_angle_shift_invariance':True,'both_end_thermal_excess_MVA':1,'independent_branch_stamp_Ybus_agreement':True})
 save(ROOT/'evaluator-validation.json',{'status':'PASS','checks':checks,'completed_UTC':now(),'code_sha256':sha(__file__)})
 print('EVALUATOR VALIDATED',flush=True)

if __name__=='__main__':
 action=sys.argv[1]
 if action=='init':init()
 elif action=='baseline-ac':
  srv=ACServer()
  try:
   for name in ['case300','case300x2','case500goc']:srv.run(ROOT/'results'/f'{name}-base')
  finally:srv.close()
  validate_evaluator()
 elif action=='score':
  for d in (ROOT/'results').iterdir():
   if d.is_dir() and (d/'input.json').exists():score_dir(d)
