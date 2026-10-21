import json,pathlib,csv,hashlib,datetime,platform,subprocess,importlib.metadata as md,statistics
repo=pathlib.Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');r=repo/'results/pilots/GSFM-007/20261021T195824Z-m5-practical'
read=lambda p:json.loads((r/p).read_text())
def write(p,x):(r/p).write_text(json.dumps(x,indent=2)+'\n')
def flatten(x,prefix=''):
 out={}
 for k,v in x.items():
  key=prefix+k
  if isinstance(v,dict):out.update(flatten(v,key+'.'))
  elif isinstance(v,list):out[key]=json.dumps(v,separators=(',',':'))
  else:out[key]=v
 return out
def table(p,rows):
 rows=[flatten(x) for x in rows];keys=list(dict.fromkeys(k for row in rows for k in row))
 with (r/p).open('w',newline='') as f:
  w=csv.DictWriter(f,keys,lineterminator="\n");w.writeheader();w.writerows(rows)
rows=[x for x in read('online-all.json') if x['repeat']>=0]
table('per-request-metrics.csv',rows);table('stage-summary.csv',read('summary.json'))
fits=read('training-summary.json')
table('fit-status.csv',[{k:v for k,v in x.items() if k!='validation'} for x in fits])
table('selection-audit.csv',[{'network':x['network'],'seed':x['seed'],'update':v['update'],'epoch':v['epoch'],'score':v['score'],'fraction_converged':v['fraction_converged'],'eligible':v['fraction_converged']>=.99,'selected':v['update']==x['selected']['update']} for x in fits for v in x['validation']])
pooled=[]
for net in ['case300','pglib118']:
 for method in sorted({x['method'] for x in rows}):
  z=[x for x in rows if x['network']==net and x['method']==method];ts=sorted(x['total_seconds'] for x in z)
  pooled.append(dict(network=net,method=method,requests=len(z),PF_converged=sum(x['PF_converged'] is True for x in z) if method!='conventional' else None,PF_feasible=sum(bool((x.get('PF_metrics')or{}).get('all_tested_constraints_pass')) for x in z) if method!='conventional' else None,final_feasible=sum(x['feasible_within_deadline'] for x in z),quality=sum(x['quality_pass'] for x in z),fallbacks=sum(x['fallback'] for x in z),median_seconds=statistics.median(ts),p95_seconds=__import__('numpy').percentile(ts,95)))
write('pooled-summary.json',pooled);table('pooled-summary.csv',pooled)
failed=[x for x in rows if not x['feasible_within_deadline']];write('failed-requests.json',failed)
effects=read('factorial-paired-effects.json');agg=[]
for net in ['case300','pglib118']:
 for arm in ['FT_P_ridge_V','ridge_P_FT_V','ridge_P_ridge_V']:
  z=[x for x in effects if x['network']==net and x['controls']==arm]
  agg.append({'network':net,'substitution':arm,'scenario_seed_pairs':len(z),'median_paired_change':{k:statistics.median(x['change_relative_to_FT_P_FT_V'][k] for x in z) for k in z[0]['change_relative_to_FT_P_FT_V']}})
write('factorial-summary.json',agg)
env={'platform':platform.platform(),'machine':platform.machine(),'python':platform.python_version(),'packages':{n:md.version(n) for n in ['torch','numpy','scipy','torch-geometric','PyYAML']},'hardware':subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string','hw.memsize'],text=True).strip(),'threads':{'torch':4,'BLAS':1,'closure_workers':0},'python_executable':__import__('sys').executable,'solver':read('solver-startup.json')}
write('environment.json',env)
print(json.dumps(pooled,indent=2));print('failed',len(failed));print(env)
