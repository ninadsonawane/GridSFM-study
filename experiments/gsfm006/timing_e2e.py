# Fully repeated preprocessing+model+completion, no parallel computation.
import time
PROCESS_START=time.perf_counter()
from common import *

def main():
 assert read(RUN/'execution.json')['status']=='COMPLETE'
 original=read(PREV/'data/manifest.json')['ordinary'];f=read(RUN/'training-summary.json');rows=[];cold={};cold['imports_seconds']=time.perf_counter()-PROCESS_START
 for label in ['frozen','selected']:
  t=time.perf_counter();m=make_model()
  if label=='selected':m.load_state_dict(torch.load(f['selected']['checkpoint'],weights_only=False,map_location='cpu')['model_state'],strict=True)
  cold[label+'_load_seconds']=time.perf_counter()-t
  for repeat in [-1,0,1,2]:
   for rec in original[:1] if repeat==-1 else original:
    guard();start=time.perf_counter();it=Item(rec);prep=time.perf_counter()-start;t=time.perf_counter()
    with torch.no_grad():raw=physical(m(it.batch()))
    model_s=time.perf_counter()-t;t=time.perf_counter();_,d=completion(it,raw);comp_s=time.perf_counter()-t;total=time.perf_counter()-start
    rows.append(dict(method=label,repeat=repeat,scenario_id=it.key,preprocessing_seconds=prep,model_seconds=model_s,completion_seconds=comp_s,total_seconds=total,converged=d['converged'],preprocessing_note='input/reference JSON loading, schema conversion and fresh graph preparation incl disk topology-cache lookup; labels never fed to model'))
   log('E2E_REPEAT_COMPLETE',method=label,repeat=repeat)
 save(RUN/'timing-e2e.json',rows);save(RUN/'cold-start.json',cold)
if __name__=='__main__':main()
