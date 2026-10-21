"""Sequential post-fit phases with explicit elapsed times; never runs training."""
from common import *
def main():
    results=[]
    for phase in ['lock','fresh_data','evaluate','report','verify']:
      deadline();start=time.perf_counter();utc=datetime.datetime.now(datetime.timezone.utc).isoformat();path=RUN/f'{phase}.log'
      if path.exists():raise RuntimeError('Preserve existing phase log: '+str(path))
      with path.open('w') as out:process=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name(phase+'.py'))],stdout=out,stderr=subprocess.STDOUT)
      results.append(dict(phase=phase,start_utc=utc,end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=time.perf_counter()-start,returncode=process.returncode,log=str(path)));save(RUN/'phase-timings.json',results);log('PHASE_FINISHED',**results[-1])
      if process.returncode:raise RuntimeError('Phase failed; retained logs: '+phase)
if __name__=='__main__':main()
