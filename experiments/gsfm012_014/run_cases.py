"""Sequential bounded runner for prescribed12 or14 cases, no training/recovery."""
import os,sys,pathlib,subprocess,time,traceback,copy
os.environ.update(PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='4',MKL_NUM_THREADS='1')
from electrical import *
from matpower_case import read_case
E=pathlib.Path(__file__).parent;PY=str(R.parent/'GridSFM/model/.venv/bin/python');JULIA='/Users/ninadsonawane/julia/bin/julia';PROJECT=str(R.parent/'GridSFM/power_grid/US/topology_solver_pipeline');OUT=pathlib.Path(sys.argv[1]);experiment=int(sys.argv[2]);manifest=read(OUT/'scenario-manifest.json');assert not (OUT/'run-status.json').exists(),'Refusing duplicate execution';allstatus=[];summaries=[];busall=[];branchall=[];areaall=[];gates=[]
def worker(cmd,log,timeout):
 start=time.perf_counter()
 try:
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout);log.write_text(p.stdout+'\nSTDERR\n'+p.stderr);return {'argv':cmd,'returncode':p.returncode,'wall_seconds':time.perf_counter()-start}
 except subprocess.TimeoutExpired as x:
  log.write_text(str(x.stdout)+'\n'+str(x.stderr));return {'argv':cmd,'returncode':None,'status':'TIMEOUT_UNKNOWN','wall_seconds':time.perf_counter()-start}
def writecase(c,path):
 lines=['function mpc = input_case',"mpc.version = '2';",f"mpc.baseMVA = {c['baseMVA']};"]
 for k in ['bus','gen','branch','gencost']:lines += [f'mpc.{k} = [']+[' '.join(format(v,'.17g') for v in row)+';' for row in c[k]]+['];']
 path.write_text('\n'.join(lines)+'\n');parsed=read_case(path);assert all(parsed[k]==c[k] for k in ['bus','gen','branch','gencost','baseMVA'])
def checkparsed(c,raw):
 d=raw['parsed_network'];base=c['baseMVA'];load={};shunt={}
 for z in d.get('load',{}).values():load[z['load_bus']]=load.get(z['load_bus'],0)+complex(z['pd'],z['qd'])*base
 for z in d.get('shunt',{}).values():shunt[z['shunt_bus']]=shunt.get(z['shunt_bus'],0)+complex(z['gs'],z['bs'])*base
 for b in c['bus']:
  bid=int(b[0]);x=d['bus'][str(bid)];assert max(abs(x['vmin']-b[12]),abs(x['vmax']-b[11]),abs(load.get(bid,0)-complex(b[2],b[3])),abs(shunt.get(bid,0)-complex(b[4],b[5])))<1e-8
 for j,br in enumerate(c['branch'],1):
  x=d['branch'][str(j)]
  for k,want in [('br_r',br[2]),('br_x',br[3]),('tap',br[8] or 1),('shift',np.deg2rad(br[9])),('angmin',np.deg2rad(br[11])),('angmax',np.deg2rad(br[12])),('rate_a',br[5]/base),('br_status',br[10]),('f_bus',br[0]),('t_bus',br[1])]:assert abs(x.get(k,0)-want)<1e-9,(j,k,x.get(k),want)
  assert abs(x['b_fr']+x['b_to']-br[4])<1e-9
 for j,g in enumerate(c['gen'],1):
  x=d['gen'][str(j)]
  for k,want in [('pmin',g[9]/base),('pmax',g[8]/base),('qmin',g[4]/base),('qmax',g[3]/base),('gen_status',g[7]),('gen_bus',g[0])]:assert abs(x[k]-want)<1e-9
  rawcost=c['gencost'][j-1];n=int(rawcost[3]);expected=[v*base**(n-1-i) for i,v in enumerate(rawcost[4:4+n])];assert np.allclose(x['cost'],expected,rtol=0,atol=1e-7)
for item in manifest['scenarios']:
 name=item['id'];D=OUT/name;c=read(D/'input.json');print('START',experiment,name,flush=True);writecase(c,D/'case.m');ref=None;last=None;attempts=[]
 for attempt,init in enumerate(['default','flat']):
  rawpath=D/f'ac-attempt{attempt}.json';req={'run_id':f'{experiment}-{name}-{attempt}','method':init,'matpower_file':str(D/'case.m'),'log_path':str(D/f'ac-attempt{attempt}.log'),'result_path':str(rawpath),'load_scale':1.,'remaining_seconds':120.,'capture_internal_iterate':False};cmd=[JULIA,'--startup-file=no','--history-file=no','--compiled-modules=existing','--project='+PROJECT,str(E/'solver_server.jl')];start=time.perf_counter()
  try:
   p=subprocess.run(cmd,input=json.dumps(req)+'\n'+json.dumps({'quit':True})+'\n',capture_output=True,text=True,timeout=135);(D/f'ac-server{attempt}.log').write_text(p.stdout+'\nSTDERR\n'+p.stderr);outcome={'returncode':p.returncode,'method':init,'seconds':time.perf_counter()-start,'argv':cmd,'request':req}
  except subprocess.TimeoutExpired as x:outcome={'returncode':None,'status':'TIMEOUT_UNKNOWN','method':init,'seconds':time.perf_counter()-start}
  if rawpath.exists():
   raw=read(rawpath);checkparsed(c,raw);s=raw.get('solution',{});outcome['solver_status']=raw['termination_status'];outcome['iterations']=raw.get('iterations')
   if all(k in s for k in ['bus','gen']):
    point={'vm':[s['bus'][str(int(b[0]))]['vm'] for b in c['bus']],'va_deg':[np.rad2deg(s['bus'][str(int(b[0]))]['va']) for b in c['bus']],'pg_mw':[s['gen'][str(j+1)]['pg']*c['baseMVA'] for j in range(len(c['gen']))],'qg_mvar':[s['gen'][str(j+1)]['qg']*c['baseMVA'] for j in range(len(c['gen']))]};save(D/f'ac-attempt{attempt}-native.json',point);last=point;m=evaluate(c,point);terms(c,point);outcome['independent_pass']=m['all_tested_constraints_pass'];outcome['objective']=raw['objective'];assert abs(cost(c,point['pg_mw'],point['qg_mvar'])-raw['objective'])<1e-4
    if raw['termination_status'] in ['LOCALLY_SOLVED','OPTIMAL','ALMOST_LOCALLY_SOLVED'] and m['all_tested_constraints_pass']:ref=point;save(D/'ac-native.json',ref)
  attempts.append(outcome);save(D/'ac-status.json',{'attempts':attempts,'verified_reference':ref is not None,'feasibility':'verified feasible local optimum' if ref is not None else 'UNKNOWN'})
  if ref is not None:break
 if last is not None and ref is None:save(D/'ac-failed-iterate.json',last)
 dc=worker([PY,'-B',str(E/'run_dc.py'),str(D)],D/'dc-worker.log',120);assert dc['returncode']==0,dc
 if (D/'dc-native.json').exists():check=read(D/'dc-status.json');dc.update(check)
 else:dc['status']='FAILED_UNKNOWN'
 modes={'AC-OPF':last,'DC-OPF':read(D/'dc-native.json') if (D/'dc-native.json').exists() else None}
 auditformat=(experiment==12 and name=='S0') or (experiment==14 and name in ['R300-base','R600-base'])
 modelstatus={}
 for rel in ['microsoft-v1.1','newer-base-v2']:
  args=[PY,'-B',str(E/'run_model.py'),rel,str(D)]+(['--audit-labels'] if auditformat else []);status=worker(args,D/(rel+'-worker.log'),120);modelstatus[rel]=status
  if status['returncode']!=0:save(D/(rel+'-failure.json'),status);raise RuntimeError('Model preprocessing/inference/label gate failed; stop before further cases: '+rel+' '+name)
  md=read(D/(rel+'-metadata.json'));assert md['input_sha256']==sha(D/'input.json');assert md['mapping']['bus_source_rows']==list(range(len(c['bus'])));assert md['mapping']['gen_source_rows']==list(range(len(c['gen'])));assert sorted(md['mapping']['ac_line_source_rows']+md['mapping']['transformer_source_rows'])==list(range(len(c['branch'])));point=read(D/(rel+'-native.json'));assert all(np.isfinite(point[k]).all() for k in ['vm','va_deg','pg_mw','qg_mvar']);modes[rel]=point
  if auditformat:assert read(D/(rel+'-label-invariance.json'))['status']=='PASS'
 case_summaries=[]
 for label,point in modes.items():
  if point is None:continue
  sm,bu,br,ar=score(c,point,label,ref);sm['scenario']=name;sm['reference_valid']=ref is not None;sm['solver_status']=('VERIFIED_LOCAL_REFERENCE' if ref is not None else 'FAILED_UNKNOWN') if label=='AC-OPF' else ('CONVERGED' if label=='DC-OPF' and dc.get('solver_success') else ('FAILED_UNKNOWN' if label=='DC-OPF' else 'NATIVE_RETURNED'));summaries.append(sm);case_summaries.append(sm)
  for z in bu:z['scenario']=name
  for z in br:z['scenario']=name
  for z in ar:z['scenario']=name
  busall+=bu;branchall+=br;areaall+=ar
 save(D/'summary.json',case_summaries);gates.append({'scenario':name,'matrix_roundtrip':True,'solver_parameters_costs_loads_shunts_limits_roundtrip':True,'model_mapping':True,'physics_crosscheck_below_1e_minus6':True,'label_invariance_audited':auditformat,'reference_valid':ref is not None});allstatus.append({'scenario':name,'AC':attempts,'DC':dc,'models':modelstatus});save(OUT/'run-status.json',allstatus);save(OUT/'gates.json',gates);save(OUT/'method-summary.json',summaries);csvsave(OUT/'bus-metrics.csv',busall);csvsave(OUT/'branch-flows.csv',branchall);csvsave(OUT/'area-exchange.csv',areaall);print('COMPLETE',name,'AC_reference',ref is not None,[(x['method'],x['AC_joint_feasible'],round(x['P']['max'],3),None if x['Q'] is None else round(x['Q']['max'],3)) for x in case_summaries],flush=True)
print('EXPERIMENT',experiment,'COMPLETE',flush=True)
