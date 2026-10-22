from electrical import *
import copy,datetime
from matpower_case import read_case,construct
O=R/'results/comparisons/GSFM-014/20261023-rated-variants';assert not (O/'scenario-manifest.json').exists();source=O/'source/pglib_opf_case300_ieee.m';assert sha(source)=='7ecf056d5942135765200ad7ae8791c28f0d35fb1dc888ba2c32dfc950f3c2f5';base=read_case(source);orig=read_case(R/'results/inference/2026-10-21-base-cases/case300.m');cfg=read(R/'configs/network-case300x2.json');diff=[]
for key in ['bus','gen','branch','gencost']:
 assert len(base[key])==len(orig[key])
 for i,(a,b) in enumerate(zip(orig[key],base[key])):
  for j in range(max(len(a),len(b))):
   x=a[j] if j<len(a) else None;y=b[j] if j<len(b) else None
   if x!=y:diff.append({'matrix':key,'row_1based':i+1,'column_1based':j+1,'MATPOWER_original':x,'PGLib_published':y})
csvsave(O/'matpower-versus-pglib.csv',diff);rows=[]
for name in ['R300-base','R600-base','U300-base','U600-base','R300-low','R300-high','R600-A','R600-B']:
 config=copy.deepcopy(cfg);mp=None
 if '600' in name:
  config['load_delta']=.05 if name=='R600-A' else (-.05 if name=='R600-B' else 0.);c,mp=construct(base,config)
 else:
  c=copy.deepcopy(base);scale=.95 if name=='R300-low' else(1.05 if name=='R300-high' else 1.)
  for b,x in zip(c['bus'],base['bus']):b[2]=x[2]*scale;b[3]=x[3]*scale
 if name.startswith('U'):
  paired=read(O/name.replace('U','R',1)/'input.json');c=copy.deepcopy(paired);n=822 if '600' in name else 411;udiff=[]
  for i in range(n):
   for j in [5,6,7]:
    if c['branch'][i][j]!=0:udiff.append({'branch_row_1based':i+1,'column_1based':j+1,'rated_value':c['branch'][i][j],'unlimited_value':0.})
    c['branch'][i][j]=0.
  for key in ['bus','gen','gencost']:assert np.array(c[key],float).tobytes()==np.array(paired[key],float).tobytes()
  for i,(a,b) in enumerate(zip(c['branch'],paired['branch'])):
   for j in range(13):assert (i<n and j in [5,6,7]) or a[j]==b[j]
  csvsave(O/(name+'-field-diff.csv'),udiff)
 d=O/name;d.mkdir();save(d/'input.json',c)
 if mp:save(d/'mapping.json',mp)
 count=sum(b[5]>0 and b[10]>0 for b in c['branch']);expected=(824 if '600' in name else 411) if name.startswith('R') else (2 if '600' in name else 0);assert count==expected
 rows.append({'id':name,'input_sha256':sha(d/'input.json'),'rated_online_branches':count,'fixed_Pg_generators':sum(g[8]==g[9] for g in c['gen']),'source_preserved':True})
save(O/'scenario-manifest.json',{'experiment':14,'started_UTC':read(O/'source-manifest.json')['started_UTC'],'inclusive_cap_minutes':120,'scenarios':rows,'source_manifest':'source-manifest.json','settings':'Two pinned frozen releases, shipped clamps; no widening fixed-P bounds; original FP64 physics; AC3000iter120s one flat retry only; DC PIPS200; matrices immutable after freeze'});print('14 EIGHT INPUTS FROZEN; source differences',len(diff))
