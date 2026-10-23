"""Postprocessing only; never solve or infer. Re-export original IDs after label fix."""
from electrical import *
O=pathlib.Path(sys.argv[1]);summary=[];bus=[];branch=[];area=[]
for item in read(O/'scenario-manifest.json')['scenarios']:
 name=item['id'];D=O/name;c=read(D/'input.json');ref=read(D/'ac-native.json') if (D/'ac-native.json').exists() else None;case=[]
 for method,file in [('AC-OPF','ac-native.json' if (D/'ac-native.json').exists() else 'ac-failed-iterate.json'),('DC-OPF','dc-native.json'),('microsoft-v1.1','microsoft-v1.1-native.json'),('newer-base-v2','newer-base-v2-native.json')]:
  if not(D/file).exists():continue
  s=read(D/file);sm,bu,br,ar=score(c,s,method,ref);sm.update(scenario=name,reference_valid=ref is not None,solver_status=('VERIFIED_LOCAL_REFERENCE' if ref is not None else 'FAILED_UNKNOWN') if method=='AC-OPF' else ('CONVERGED' if method=='DC-OPF' else 'NATIVE_RETURNED'));summary.append(sm);case.append(sm)
  assert {x['bus_id'] for x in bu}=={int(b[0]) for b in c['bus']}
  for j,row in enumerate(br):assert [row['from_bus'],row['to_bus']]==list(map(int,c['branch'][j][:2]))
  for rr in [bu,br,ar]:
   for z in rr:z['scenario']=name
  bus+=bu;branch+=br;area+=ar
 save(D/'summary.json',case)
save(O/'method-summary.json',summary);csvsave(O/'bus-metrics.csv',bus);csvsave(O/'branch-flows.csv',branch);csvsave(O/'area-exchange.csv',area);print('REEXPORTED VERIFIED INPUT IDS; no scientific calls')
