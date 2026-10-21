from common import *
import subprocess,selectors

def main():
 assert read(RUN/'execution.json')['status']=='COMPLETE'
 its=items('ordinary');out=RUN/'conventional';out.mkdir(exist_ok=True);err=(out/'stderr.log').open('w');t=time.perf_counter()
 proc=subprocess.Popen(['/Users/ninadsonawane/julia/bin/julia','--startup-file=no','--project='+str(ROOT.parent/'GridSFM/power_grid/US/topology_solver_pipeline'),str(Path(__file__).with_name('solver_server.jl'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
 def receive():
  sel=selectors.DefaultSelector();sel.register(proc.stdout,selectors.EVENT_READ)
  if not sel.select(45):proc.kill();raise TimeoutError('conventional solver response45s')
  line=proc.stdout.readline();sel.close();return json.loads(line)
 ready=receive();ready['process_ready_seconds']=time.perf_counter()-t;save(out/'startup.json',ready);rows=[]
 for repeat in [-1,0,1,2]:
  for it in its[:1] if repeat==-1 else its:
   guard();name=f'{repeat}-{it.key}';rp=out/f'{name}-result.json';req=dict(input_path=str(it.path/'candidate.m'),result_path=str(rp),log_path=str(out/f'{name}.log'));t=time.perf_counter();proc.stdin.write(json.dumps(req)+'\n');proc.stdin.flush();r=receive();r.update(repeat=repeat,scenario_id=it.key,request_seconds=time.perf_counter()-t)
   if rp.exists():
    raw=read(rp);sol=raw['solution'];s=dict(vm=[sol['bus'][str(int(b[0]))]['vm'] for b in it.c['bus']],va_deg=[math.degrees(sol['bus'][str(int(b[0]))]['va']) for b in it.c['bus']],pg_mw=[100*sol['gen'][str(i+1)]['pg'] for i in range(69)],qg_mvar=[100*sol['gen'][str(i+1)]['qg'] for i in range(69)])
    r['metrics']=score(it,s);save(out/f'{name}-prediction.json',s)
   rows.append(r)
  log('CONVENTIONAL_TIMING_REPEAT',repeat=repeat,n=len(rows))
 proc.stdin.write('{"quit":true}\n');proc.stdin.flush();proc.wait(timeout=10);err.close();save(out/'timing.json',rows)
if __name__=='__main__':
 try:main()
 except Exception:(RUN/'conventional-failure.txt').write_text(traceback.format_exc());raise
