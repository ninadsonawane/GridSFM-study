from common import *
from gate import residual

def main():
 assert read(RUN/'execution.json')['status']=='COMPLETE'
 train=items('train',True)[:5];audit=[]
 for it in train:
  guard();d=load_obj(it.obj)
  # Restore original decimal precision BEFORE extract_case for a diagnostic only.
  for nt,rows in it.obj['grid']['nodes'].items():d[nt].x=torch.tensor(rows,dtype=torch.float64)
  for fam in ['ac_line','transformer']:d['bus',fam,'bus'].edge_attr=torch.tensor(it.obj['grid']['edges'][fam]['features'],dtype=torch.float64)
  orig_case=it.case;it.case=extract_case(d);s,meta=completion(it,it.ref);audit.append(dict(scenario_id=it.key,purpose='ORACLE DIAGNOSTIC ONLY: isolate native FP32 rounding from released +1e-12 denominator',metrics=score(it,s),completion=meta));it.case=orig_case
 save(RUN/'checks/original-precision-oracle.json',audit)
 # Identical control extraction for ridge and all three historical E seeds, no new fitting.
 ordinary=items('ordinary');methods={'ridge':PREV/'evaluation/ridge-None-baseline-ordinary.json'}
 for seed in [11,22,33]:methods[f'E-{seed}']=PREV/f'evaluation/E-{seed}-selected-ordinary.json'
 for method,p in methods.items():
  old=read(p);assert [r['scenario_id'] for r in old]==[it.key for it in ordinary];rows=[]
  for it,r in zip(ordinary,old):
   t=time.perf_counter();s,d=completion(it,r['prediction']);rows.append(dict(scenario_id=it.key,completed=s,completed_metrics=score(it,s),completion=d,completion_seconds=time.perf_counter()-t,raw_source=str(p),raw_source_sha256=sha(p)))
  save(RUN/f'evaluation/hybrid-{method}-ordinary.json',rows);log('HYBRID_DIAGNOSTIC',method=method,converged=sum(r['completion']['converged'] for r in rows),strict_feasible=sum(r['completed_metrics']['all_tested_constraints_pass'] for r in rows))
if __name__=='__main__':main()
