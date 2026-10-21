from common import *

def label(server,c,net,split,i,factors):
 p=RUN/f'data/{net}/candidates/{split}-{i:03d}';p.mkdir(parents=True,exist_ok=False);save(p/'input.json',c);write_m(c,p/'candidate.m');save(p/'factors.json',factors);rec=dict(scenario_id=f'{split}-{i:03d}',network=net,split=split,path=str(p),accepted=False,input_sha256=sha(p/'input.json'))
 # No model/reference guesses enter the conventional source-data initialization.
 it=types.SimpleNamespace(c=c,path=p,ref=None);r=server.request(it,p/'label-solve',remaining=30);rec.update(status=r.get('termination_status',r.get('status','UNKNOWN')),generation_seconds=r['request_seconds'])
 if r.get('metrics',{}).get('all_tested_constraints_pass'):
  save(p/'reference.json',r['state']);save(p/'reference-metrics.json',r['metrics']);rec['accepted']=True
 save(p/'record.json',rec);return rec

def main():
 assert not (RUN/'prepare-complete.json').exists();assert sha(CKPT)=='9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7';t=time.perf_counter();server=Server();bases=dict(case300=read(ROOT/'results/inference/2026-10-21-base-cases/case300-input.json'),pglib118=read_case(WORK/'pglib_opf_case118_ieee.m'));save(RUN/'source-cases.json',bases)
 man=dict(train=read(OLD/'data/manifest.json')['train'],validation=read(OLD/'data/manifest.json')['validation']);save(RUN/'data/case300/manifest.json',man)
 second={};ts=time.perf_counter()
 for split,target,seednum,cap in [('train',50,7101181,150),('validation',10,7101182,30)]:
  rng=np.random.Generator(np.random.PCG64(seednum));recs=[]
  for i in range(cap):
   guard()
   if sum(r['accepted'] for r in recs)>=target or time.perf_counter()-ts>1200:break
   scale=float(rng.uniform(.9,1.03));j=rng.uniform(.98,1.02,len(bases['pglib118']['bus']));f=scale*j;c=copy.deepcopy(bases['pglib118'])
   for b,fac in zip(c['bus'],f):b[2]*=float(fac);b[3]*=float(fac)
   recs.append(label(server,c,'pglib118',split,i,dict(seed=seednum,global_scale=scale,bus_jitter=j.tolist(),actual_factors=f.tolist())))
  second[split]=recs;save(RUN/'data/pglib118/manifest.json',second);log('LABEL_PROGRESS',network='pglib118',split=split,accepted=sum(r['accepted'] for r in recs),attempts=len(recs))
 assert all(sum(r['accepted'] for r in second[s])>=n for s,n in [('train',50),('validation',10)]),'PGLib118 label budget incomplete'
 save(RUN/'prepare-complete.json',dict(status='PASS',seconds=time.perf_counter()-t,pglib_label_seconds=time.perf_counter()-ts,counts={s:sum(r['accepted'] for r in rs) for s,rs in second.items()}));server.close()
if __name__=='__main__':
 try:main()
 except Exception:(RUN/'prepare-failure.txt').write_text(traceback.format_exc());raise
