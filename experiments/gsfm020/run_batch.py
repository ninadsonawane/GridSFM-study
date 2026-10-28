"""Execute preregistered local batches; retain every attempt and failure."""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
import argparse, datetime as dt, json, pathlib, subprocess, sys, time, traceback
from electrical import *
from prepare import O,save,read,sha
from solver_checks import writecase,checkparsed
E=pathlib.Path(__file__).parent
W=R.parent
RT=W/'runtime'
REL=['microsoft-v1.1','newer-base-v2']
def worker(cmd,log,timeout,input_text=None,env=None):
 start=time.monotonic()
 try:
  p=subprocess.run([str(x) for x in cmd],input=input_text,capture_output=True,text=True,timeout=timeout,env=env)
  log.write_text(p.stdout+'\nSTDERR\n'+p.stderr,encoding='utf-8')
  return {'argv':[str(x) for x in cmd],'returncode':p.returncode,'wall_seconds':time.monotonic()-start}
 except subprocess.TimeoutExpired as x:
  log.write_text(str(x.stdout)+'\n'+str(x.stderr),encoding='utf-8')
  return {'argv':[str(x) for x in cmd],'returncode':None,'status':'TIMEOUT_UNKNOWN','wall_seconds':time.monotonic()-start}
def ac_run(d,c):
 ref=None;last=None;attempts=[];writecase(c,d/'case.m')
 env=os.environ.copy();env['JULIA_DEPOT_PATH']=str(W/'julia/depot');env['JULIA_NUM_THREADS']='1'
 for attempt,init in enumerate(['default','flat']):
  rawpath=d/f'ac-attempt{attempt}.json'
  req={'run_id':'20-'+d.name+'-'+str(attempt),'method':init,'matpower_file':str(d/'case.m'),'log_path':str(d/f'ac-attempt{attempt}.log'),'result_path':str(rawpath),'load_scale':1.,'remaining_seconds':120.,'capture_internal_iterate':False}
  cmd=[W/'julia/julia-1.11.9/bin/julia.exe','--startup-file=no','--history-file=no','--compiled-modules=existing','--project='+str(E/'julia'),E/'solver_server.jl']
  outcome=worker(cmd,d/f'ac-server{attempt}.log',300,json.dumps(req)+'\n'+json.dumps({'quit':True})+'\n',env)
  outcome['method']=init;outcome['request']=req
  if rawpath.exists():
   raw=read(rawpath);checkparsed(c,raw);s=raw.get('solution',{});outcome['solver_status']=raw['termination_status'];outcome['iterations']=raw.get('iterations')
   if all(k in s for k in ['bus','gen']):
    point={'vm':[s['bus'][str(int(b[0]))]['vm'] for b in c['bus']],'va_deg':[float(np.rad2deg(s['bus'][str(int(b[0]))]['va'])) for b in c['bus']],'pg_mw':[(s['gen'][str(j+1)]['pg']*c['baseMVA'] if c['gen'][j][7]>0 else 0.) for j in range(len(c['gen']))],'qg_mvar':[(s['gen'][str(j+1)]['qg']*c['baseMVA'] if c['gen'][j][7]>0 else 0.) for j in range(len(c['gen']))]}
    save(d/f'ac-attempt{attempt}-native.json',point);last=point
    m=evaluate(c,point);terms(c,point);outcome['independent_pass']=m['all_tested_constraints_pass'];outcome['objective']=raw['objective']
    assert abs(cost(c,point['pg_mw'],point['qg_mvar'])-raw['objective'])<1e-4,'Objective mismatch'
    if raw['termination_status'] in ['LOCALLY_SOLVED','OPTIMAL','ALMOST_LOCALLY_SOLVED'] and m['all_tested_constraints_pass']:
     ref=point;save(d/'ac-native.json',ref)
  attempts.append(outcome);save(d/'ac-status.json',{'attempts':attempts,'verified_reference':ref is not None,'feasibility':'verified feasible local optimum' if ref is not None else 'UNKNOWN'})
  if ref is not None:break
 if last is not None and ref is None:save(d/'ac-failed-iterate.json',last)
 return ref,last,attempts
def score_case(d,c,ref,last):
 modes={'AC-OPF':last,'DC-OPF':read(d/'dc-native.json') if (d/'dc-native.json').exists() else None}
 modes.update({rel:read(d/(rel+'-native.json')) for rel in REL})
 summaries=[];busall=[];branchall=[];areaall=[];clampall=[];violations=[]
 for method,s in modes.items():
  if s is None:
   summaries.append({'method':method,'scenario':d.name,'status':'FAILED_UNKNOWN','reference_valid':ref is not None,'approximation':None});continue
  sm,bu,br,ar=score(c,s,method,ref);sm.update(scenario=d.name,reference_valid=ref is not None,status='VERIFIED_LOCAL_REFERENCE' if method=='AC-OPF' and ref is not None else 'FAILED_UNKNOWN' if method=='AC-OPF' else 'NATIVE_RETURNED')
  if method=='DC-OPF':sm['status']=read(d/'dc-status.json')['status']
  for v,k in [('P','P_residual_MW'),('Q','Q_residual_MVAr')]:
   if v=='Q' and method=='DC-OPF':continue
   a=np.array([abs(x[k]) for x in bu]);sm[v+'_worst_bus']=max(bu,key=lambda x:abs(x[k]))['bus_id']
   sm[v+'_severity_band_counts']={label:int(((a>lo)&(a<=hi)).sum()) for label,lo,hi in [('0.001-1',.001,1),('1-10',1,10),('10-100',10,100),('100-1000',100,1000),('over1000',1000,float('inf'))]}
  if method!='DC-OPF':
   sm['total_Qg_MVAr']=sum(s['qg_mvar']);sm['total_Pg_MW']=sum(s['pg_mw'])
   sm['Qg_at_lower_count']=sum(abs(q-g[4])<=1e-3 for q,g in zip(s['qg_mvar'],c['gen']))
   sm['Qg_at_upper_count']=sum(abs(q-g[3])<=1e-3 for q,g in zip(s['qg_mvar'],c['gen']))
   violations.append({'method':method,'independent_full_metrics':evaluate(c,s)})
  if method in REL:
   captures=read(d/(method+'-clamps.json'))['captures']
   for x in captures:
    a=np.asarray(x['input']);z=np.asarray(x['output']);lo=np.asarray(x['lo']);hi=np.asarray(x['hi'])
    assert np.array_equal(np.clip(a,lo,hi),z)
    variable=x['variable'];scale=1 if variable=='V' else c['baseMVA'];tol=1e-4 if variable=='V' else 1e-3
    ids=[int(b[0]) for b in c['bus']] if variable=='V' else [i+1 for i,g in enumerate(c['gen']) if g[7]>0]
    clampall.append({'method':method,'variable':variable,'strict_count':int((a!=z).sum()),'material_count':int((abs(a-z)*scale>tol).sum()),'lower_count':int((a<lo).sum()),'upper_count':int((a>hi).sum()),'max_change':float(max(abs(a-z)*scale)),'strict_locations':[ids[i] for i in range(len(a)) if a[i]!=z[i]],'material_locations':[ids[i] for i in range(len(a)) if abs(a[i]-z[i])*scale>tol]})
  summaries.append(sm)
  for rows,dest in [(bu,busall),(br,branchall),(ar,areaall)]:
   for row in rows:row['scenario']=d.name
   dest.extend(rows)
 save(d/'summary.json',summaries);save(d/'violations.json',violations);save(d/'clipping-summary.json',clampall)
 csvsave(d/'bus-metrics.csv',busall);csvsave(d/'branch-flows.csv',branchall);csvsave(d/'area-exchange.csv',areaall)
 return summaries
def run(planfile):
 plan=read(planfile);batchdir=pathlib.Path(planfile).parent;statuses=[]
 assert not (batchdir/'run-status.json').exists(),'No implicit reruns'
 for required in [RT/'sources/microsoft/model/gridsfm/model.py',RT/'sources/newer/model/gridsfm/model.py',RT/'checkpoints/gridsfm_open_v1.1.pt',RT/'checkpoints/gridsfm_open_v2.pt',W/'julia/julia-1.11.9/bin/julia.exe']:
  assert required.is_file(),('Missing required local runtime file',str(required))
 gate=read(O/'diagnostic-gate.json');assert gate['status']=='PASS'
 assert gate['executed_neural_forwards']<=20
 assert all(g['exact_independent_process_all_returned_equal'] and g['within_process_repeat_and_label_invariance'] for g in gate['gates'])
 for item in plan['scenarios']:
  ledger=read(O/'ledger.json')
  assert dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(ledger['compute_stop_UTC'])
  assert item['id'] not in [x['id'] for x in ledger['attempted']],'Input already attempted'
  assert sum(x['kind']==plan['kind'] for x in ledger['attempted'])<ledger[plan['kind']+'_limit']
  rec={'id':item['id'],'batch':plan['batch'],'kind':plan['kind'],'attempted_UTC':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'ATTEMPTED'}
  ledger['attempted'].append(rec);save(O/'ledger.json',ledger)
  d=O/'cases'/item['id'];c=read(d/'input.json');assert sha(d/'input.json')==item['input_sha256']
  save(d/'code-at-execution.json',{'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'files':{str(p.relative_to(R)):sha(p) for p in sorted(E.rglob('*')) if p.is_file() and p.suffix in ['.py','.jl','.toml','.md','.json'] and '__pycache__' not in p.parts},'clock_UTC':dt.datetime.now(dt.timezone.utc).isoformat()})
  print('START',item['id'],flush=True);status={'scenario':item['id'],'models':{}}
  try:
   # Models see only unsolved input; AC reference is computed after returns are saved.
   for rel,source,ckpt in [('microsoft-v1.1','microsoft','gridsfm_open_v1.1.pt'),('newer-base-v2','newer','gridsfm_open_v2.pt')]:
    cmd=[sys.executable,'-B',E/'model_worker.py','--release',rel,'--source',RT/'sources'/source,'--checkpoint',RT/'checkpoints'/ckpt,'--input',d/'input.json','--out',d]
    result=worker(cmd,d/(rel+'-worker.log'),180);status['models'][rel]=result
    assert result['returncode']==0,('Model gate failed',rel,result)
    assert sha(d/'input.json')==item['input_sha256'],'Frozen input was modified'
    md=read(d/(rel+'-metadata.json'));mp=md['mapping'];assert mp['bus_source_rows']==list(range(len(c['bus'])))
    assert mp['gen_source_rows']==[i for i,g in enumerate(c['gen']) if g[7]>0]
    assert sorted(mp['ac_line_source_rows']+mp['transformer_source_rows'])==[i for i,b in enumerate(c['branch']) if b[10]>0]
   dc=worker([sys.executable,'-B',E/'run_dc.py',d],d/'dc-worker.log',180);status['DC']=dc
   assert dc['returncode']==0,('DC adapter failure',dc)
   ref,last,acstatus=ac_run(d,c);status['AC']=acstatus
   summaries=score_case(d,c,ref,last)
   rec.update(status='COMPLETE',reference_valid=ref is not None,completed_UTC=dt.datetime.now(dt.timezone.utc).isoformat())
   save(d/'run-status.json',status);statuses.append(status);save(batchdir/'run-status.json',statuses)
   print('COMPLETE',item['id'],'AC',ref is not None,[(s['method'],None if s.get('Q') is None else round(s['Q']['max'],3),s.get('AC_joint_feasible')) for s in summaries],flush=True)
  except Exception:
   rec.update(status='STOPPED_CORRECTNESS_GATE',traceback=traceback.format_exc());save(d/'failure.json',rec);raise
  finally:
   latest=read(O/'ledger.json');latest['attempted']=[rec if x['id']==rec['id'] else x for x in latest['attempted']];save(O/'ledger.json',latest)
 save(batchdir/'verification.json',{'status':'COMPLETE','scenarios':len(plan['scenarios']),'plan_sha256':sha(planfile),'completed_UTC':dt.datetime.now(dt.timezone.utc).isoformat()})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('plan',type=pathlib.Path);args=p.parse_args();run(args.plan.resolve())
