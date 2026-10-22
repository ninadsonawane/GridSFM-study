import pathlib,json,subprocess,time,traceback,hashlib,os,platform
R=pathlib.Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');O=pathlib.Path(os.environ.get('GSFM011C1_OUTPUT',str(R/'results/comparisons/GSFM-011C-1/20261022-loading-only')));E=R/'experiments/gsfm011c1';py=str(R.parent/'GridSFM/model/.venv/bin/python');env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',XDG_CACHE_HOME='/private/tmp/gsfm011c1-20261022/cache');statuses=[]
assert not (O/'run-status.json').exists(),'Refusing to repeat completed attempts; set GSFM011C1_OUTPUT to a fresh directory'
(O/'environment.json').write_text(json.dumps({'platform':platform.platform(),'machine':platform.machine(),'processor':platform.processor(),'python':py,'hardware':subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),'memory_bytes':subprocess.check_output(['sysctl','-n','hw.memsize'],text=True).strip(),'env':{k:env[k] for k in ['PYTHONDONTWRITEBYTECODE','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']},'scientific_calls':{'AC':6,'DC':6,'Microsoft_v1.1':6,'newer_v2':6},'base_1_00':'reused; no new call'},indent=2)+'\n')
for item in json.loads((O/'frozen-protocol.json').read_text())['inputs']:
 d=O/item['id']
 for method,script,args,cap in [('AC','run_ac.py',[str(d)],120),('DC','run_dc.py',[str(d)],30),('Microsoft_v1.1','run_model.py',['microsoft-v1.1',str(d)],90),('newer_v2','run_model.py',['newer-base-v2',str(d)],90)]:
  command=[py,'-B',str(E/script)]+args;t=time.perf_counter();s={'case':item['id'],'method':method,'command':command,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'timeout_seconds':cap};print('START',item['id'],method,flush=True)
  try:
   p=subprocess.run(command,capture_output=True,text=True,timeout=cap,env=env);(d/(method+'-worker.log')).write_text(p.stdout+'\nSTDERR\n'+p.stderr);s.update(returncode=p.returncode,status='RETURNED' if p.returncode==0 else 'FAILED_UNKNOWN')
  except subprocess.TimeoutExpired as x:
   (d/(method+'-worker.log')).write_text(str(x.stdout)+'\n'+str(x.stderr));s.update(status='TIMEOUT_UNKNOWN')
  s['elapsed_seconds']=time.perf_counter()-t;statuses.append(s);(O/'run-status.json').write_text(json.dumps(statuses,indent=2)+'\n');print('DONE',item['id'],method,s['status'],round(s['elapsed_seconds'],2),flush=True)
 # All returned states remain saved even if the AC reference verification fails.
 if (d/'ac-result.json').exists() and all((d/(m+'-native.json')).exists() for m in ['dc','microsoft-v1.1','newer-base-v2']):
  p=subprocess.run([py,'-B',str(E/'evaluate_saved.py'),str(d)],capture_output=True,text=True,env=env);(d/'evaluation.log').write_text(p.stdout+'\nSTDERR\n'+p.stderr);print('EVALUATE',item['id'],p.returncode,flush=True)
print('SIX CASES FINISHED',flush=True)
