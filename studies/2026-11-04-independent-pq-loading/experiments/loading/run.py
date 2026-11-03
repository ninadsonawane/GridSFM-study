"""Phase runner. Preserve failures; never silently replace states."""
import argparse,time,traceback
from study import *

def run_process(cmd,log,env=None,timeout=1800):
 with log.open('w',encoding='utf-8') as f:
  p=subprocess.run([str(x) for x in cmd],stdout=f,stderr=subprocess.STDOUT,env=env,timeout=timeout)
 assert p.returncode==0,('worker failed',str(log),p.returncode)

def methods(dirs,phase):
 assert read(ROOT/'evaluator-validation.json')['status']=='PASS'
 env=os.environ.copy();env['STUDY_CACHE_ROOT']=str(ROOT.parents[1]/'work/cache');env['PYTHONHASHSEED']='0'
 for rel,src,ck in REL:
  p=ROOT/'results'/f'{phase}-{rel}-plan.json';save(p,{'source':str(RT/'sources'/src),'checkpoint':str(RT/'checkpoints'/ck),'cache':str(ROOT.parents[1]/'work/cache'/phase/rel),'folders':[str(d) for d in dirs]})
  print('MODEL START',phase,rel,len(dirs),flush=True)
  run_process([sys.executable,'-B',EXP/'model_batch.py',p,rel],ROOT/'results'/f'{phase}-{rel}.log',env)
  print('MODEL COMPLETE',phase,rel,flush=True)
 for d in dirs:
  if not (d/'dc-status.json').exists():run_process([sys.executable,'-B',EXP/'run_dc.py',d],d/'dc-worker.log',env,180)
  score_dir(d)
  print('DC AND SCORE',d.name,flush=True)

def freeze():
 assert not (ROOT/'scenario-plan.json').exists()
 assert all((ROOT/'results'/f'{n}-base/metrics.json').exists() for n in ['case300','case300x2','case500goc'])
 items=[]
 def add(net,group,p,q,baseline=1.,historical=None):
  id=f'{net}-{group}-p{p:.4f}-q{q:.4f}';c=read(ROOT/'cases'/net/'base.json')
  for b in c['bus']:b[2]*=p;b[3]*=q
  d=ROOT/'results'/id;save(d/'input.json',c)
  item={'id':id,'network':net,'group':group,'absolute_P_factor':p,'absolute_Q_factor':q,'relative_baseline':baseline,'relative_P_factor':p/baseline,'relative_Q_factor':q/baseline,'input_sha256':sha(d/'input.json'),'historical_control':historical}
  save(d/'scenario.json',item);items.append(item)
 for net in ['case300','case300x2','case500goc']:
  for group in ['P','Q','PQ']:
   for factor in [1.01,1.02,1.05,1.10]:add(net,group,factor if group!='Q' else 1.,factor if group!='P' else 1.)
 # Original case-3 controls and nearby refinement, all at original limits.
 for x in [.92,.93,.9301,.9303,.935,.94,.945,.95]:add('case300','case3-PQ',x,x,.93,'GSFM-020 global '+str(x))
 for group in ['P','Q']:
  for x in [.935,.94,.95]:add('case300','case3-'+group,x if group=='P' else .93,x if group=='Q' else .93,.93,'GSFM-020 isolated '+group)
 # Sensitivity phase is last: 0.5% step supports a second step-size check.
 for net in ['case300','case300x2','case500goc']:
  for group in ['P','Q']:add(net,'sensitivity-'+group,1.005 if group=='P' else 1.,1.005 if group=='Q' else 1.)
 save(ROOT/'scenario-plan.json',{'frozen_UTC':now(),'main_factors':[1.,1.01,1.02,1.05,1.10],'baseline_ids':[n+'-base' for n in ['case300','case300x2','case500goc']],'scenarios':items,'case3_definition':'Absolute factors refer to original MATPOWER case300; adjusted baseline is both components at 0.93. No equipment changes. Case3 label resolved from matching original 93-94 percent studies.','sensitivity_definition':'Forward finite differences at 1.00 with h=0.01 and h=0.005; also adjacent 1.01 to 1.02. Voltage, Pg, Qg; compare signed changes and magnitude, separate baseline offsets.'})
 print('SCENARIOS FROZEN',len(items),'plus 3 unique baselines',flush=True)

def phase(name):
 if name=='baseline':
  dirs=[ROOT/'results'/f'{n}-base' for n in ['case300','case300x2','case500goc']];methods(dirs,name)
 else:
  plan=read(ROOT/'scenario-plan.json');selected=[s for s in plan['scenarios'] if (s['group'].startswith('sensitivity-'))==(name=='sensitivity')]
  if name=='sensitivity':assert (ROOT/'loading-analysis.json').exists(),'Analyze main loading before final sensitivity phase'
  dirs=[ROOT/'results'/s['id'] for s in selected]
  # Immutable model input conversion is label-free regardless of solve order.
  methods(dirs,name)
  server=ACServer()
  try:
   for d in dirs:server.run(d);score_dir(d)
  finally:server.close()
 save(ROOT/'results'/f'{name}-complete.json',{'phase':name,'completed_UTC':now(),'scenario_count':len(dirs),'code_sha256':{str(p.relative_to(ROOT)):sha(p) for p in EXP.glob('*.py')}})

if __name__=='__main__':
 action=sys.argv[1]
 if action=='freeze':freeze()
 else:phase(action)
