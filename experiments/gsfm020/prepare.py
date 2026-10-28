"""Recreate only existing networks and freeze a batch before outcomes."""
import argparse, copy, datetime as dt, hashlib, json, pathlib, subprocess, sys
R=pathlib.Path(__file__).resolve().parents[2]
O=R/'results/comparisons/GSFM-020/20261026-local-operating-conditions'
sys.path.insert(0,str(R/'scripts/python'))
from matpower_case import read_case,construct,validate,components
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
def init():
 assert not O.exists(),'Run already initialized; refuse overwrite'
 O.mkdir(parents=True)
 p=R/'data/source/matpower-8.1/case300.m'
 assert sha(p)=='69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5'
 base=read_case(p);validate(base)
 cfg=read(R/'configs/network-case300x2.json');two,mp=construct(base,cfg)
 for n,c in [('300',base),('600',two)]:
  d=O/'bases'/n;save(d/'input.json',c)
  assert len(components(c))==1
  assert len(c['bus'])==int(n)
 save(O/'bases/600/mapping.json',mp)
 expected300=read(R/'results/comparisons/GSFM-015/20261023-load-location-charging/all-scenarios.json')['scenarios']
 hashes={x['id']:x['input_sha256'] for x in expected300}
 checks={}
 for n in ['300','600']:
  actual=sha(O/'bases'/n/'input.json');checks[n]={'actual':actual,'expected':hashes['G'+n+'-1.00'],'match':actual==hashes['G'+n+'-1.00']}
 assert all(x['match'] for x in checks.values()),checks
 save(O/'reconstructed-input-checks.json',checks)
 prior={p:sha(R/p) for p in subprocess.check_output(['git','ls-files'],cwd=R,text=True).splitlines() if (R/p).is_file()}
 save(O/'prior-tracked-sha256.json',prior)
 save(O/'ledger.json',{'start_UTC':'2026-10-26T16:45:13+00:00','deadline_UTC':'2026-10-26T21:45:13+00:00','compute_stop_UTC':'2026-10-26T21:15:13+00:00','discovery_limit':24,'confirmation_limit':6,'attempted':[],'diagnostic_forward_limit':20,'diagnostic_forwards':[],'baseline_replays':[]})
 save(O/'provenance.json',{'study_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'case_source_sha256':sha(p),'config_sha256':sha(R/'configs/network-case300x2.json'),'protocol_sha256':sha(R/'experiments/gsfm020/protocol.md'),'initialized_UTC':dt.datetime.now(dt.timezone.utc).isoformat(),'local_setup_authorized':True,'no_publication':True})
 print(json.dumps(checks,indent=2))
def build(spec):
 c=copy.deepcopy(read(O/'bases'/str(spec['network'])/'input.json'))
 scale=spec.get('load_scale',1.)
 for i,b in enumerate(c['bus']):
  area=(1 if i<300 else -1) if spec['network']==600 else 0
  b[2]*=scale*spec.get('p_scale',1.)*(1+area*spec.get('area_delta',0.))
  b[3]*=scale*spec.get('q_scale',1.)*(1+area*spec.get('area_delta',0.))
 if 'charging_scale' in spec:
  for e in c['branch']:
   if e[4]>0:e[4]*=spec['charging_scale']
 if 'redistribution' in spec:
  assert spec['network']==300
  sel=read(R/'results/comparisons/GSFM-015/20261023-load-location-charging/local-selection.json')
  groups=[[i for i,b in enumerate(c['bus']) if b[0] in sel[k]] for k in ['weak_bus_ids','strong_bus_ids']]
  for col,k in [(2,'transfer_MW'),(3,'transfer_MVAr')]:
   before=sum(b[col] for b in c['bus'])
   for group,sign in zip(groups,[1,-1]):
    denom=sum(c['bus'][i][col] for i in group)
    old=[c['bus'][i][col] for i in group]
    for i,v in zip(group,old):c['bus'][i][col]+=sign*spec['redistribution']*sel[k]*v/denom
    assert all(c['bus'][i][col]>0 for i in group),'Redistribution crossed a selected positive load through zero'
   assert abs(sum(b[col] for b in c['bus'])-before)<1e-8
 validate(c);assert len(components(c))==1
 assert all(e[5]==0 for e in c['branch'][:411 if spec['network']==300 else 822])
 return c
def batch(path):
 plan=read(path);name=plan['batch'];d=O/'batches'/name
 assert not d.exists(),'Refuse replacing preregistration'
 assert 4<=len(plan['scenarios'])<=6
 assert plan['kind'] in ['discovery','confirmation']
 ledger=read(O/'ledger.json');n=sum(x['kind']==plan['kind'] for x in ledger['attempted'])
 assert n+len(plan['scenarios'])<=ledger[plan['kind']+'_limit']
 assert dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(ledger['compute_stop_UTC'])
 plan['frozen_UTC']=dt.datetime.now(dt.timezone.utc).isoformat()
 for item in plan['scenarios']:
  case=build(item);out=O/'cases'/item['id'];assert not out.exists(),item['id']
  save(out/'input.json',case);item['input_sha256']=sha(out/'input.json')
  original=read(O/'bases'/str(item['network'])/'input.json')
  diff=[{'matrix':k,'row_1based':i+1,'column_1based':j+1,'before':x,'after':y} for k in ['bus','gen','branch','gencost'] for i,(a,b) in enumerate(zip(original[k],case[k])) for j,(x,y) in enumerate(zip(a,b)) if x!=y]
  save(out/'field-differences.json',diff)
 save(d/'plan.json',plan);print('FROZEN',name,len(plan['scenarios']),sha(d/'plan.json'))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['init','batch']);a.add_argument('plan',nargs='?');args=a.parse_args()
 init() if args.action=='init' else batch(args.plan)
