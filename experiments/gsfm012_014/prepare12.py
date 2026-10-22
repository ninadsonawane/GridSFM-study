"""Prepare exactly the three prescribed inputs; refuses existing output."""
from pathlib import Path
import json,sys,hashlib,copy,datetime
R=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');E=R/'experiments/gsfm012_014';E.mkdir(exist_ok=True);O=R/'results/comparisons/GSFM-012/20261023-frozen-two-copy';assert not O.exists(),'Refusing to overwrite experiment';O.mkdir(parents=True);sys.path.insert(0,str(R/'scripts/python'));from matpower_case import read_case,construct,components
base=read_case(R/'results/inference/2026-10-21-base-cases/case300.m');cfg=json.loads((R/'configs/network-case300x2.json').read_text());rows=[]
for name,delta in [('S0',0.),('Splus',.05),('Sminus',-.05)]:
 config=copy.deepcopy(cfg);config['load_delta']=delta;c,mp=construct(base,config);assert len(c['bus'])==600 and len(c['gen'])==138 and len(c['branch'])==824;assert len(components(c))==1;assert sum(b[1]==3 for b in c['bus'])==1
 for a in range(2):
  for i,b in enumerate(base['bus']):
   x=c['bus'][a*300+i];want=b[:];want[0]=a*300+i+1;want[6]+=a*max(bb[6] for bb in base['bus']);want[10]+=a*max(bb[10] for bb in base['bus']);want[2]*=1+(1 if a==0 else -1)*delta;want[3]*=1+(1 if a==0 else -1)*delta
   if a and want[1]==3:want[1]=2
   assert x==want
  for i,g in enumerate(base['gen']):assert c['gen'][a*69+i][1:]==g[1:]
  for i,b in enumerate(base['branch']):assert c['branch'][a*411+i][2:]==b[2:]
 assert all(b[5]==0 for b in c['branch'][:822]);assert c['branch'][-1]==c['branch'][-2];assert abs(sum(b[2] for b in c['bus'])-2*sum(b[2] for b in base['bus']))<1e-8
 d=O/name;d.mkdir();(d/'input.json').write_text(json.dumps(c,indent=2)+'\n');(d/'mapping.json').write_text(json.dumps(mp,indent=2)+'\n');rows.append({'id':name,'A_scale':1+delta,'B_scale':1-delta,'input_sha256':hashlib.sha256((d/'input.json').read_bytes()).hexdigest(),'structure_gate':'PASS'})
(O/'scenario-manifest.json').write_text(json.dumps({'experiment':12,'started_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inclusive_cap_minutes':90,'scenarios':rows,'source_commit':'96888bc4ecd792022f54ada495aad90f45d989dc','config':cfg,'settings':'frozen shipped defaults; exact FP64 independent physics; CPU sequential batch1; AC3000iter120s one flat retry only on failure; DC PIPS200 as11B'},indent=2)+'\n');print(O)
