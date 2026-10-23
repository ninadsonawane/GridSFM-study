"""Freeze distinct mechanism contrasts before outcome inspection; preserve originals."""
from pathlib import Path
import copy,json,hashlib,sys,collections,datetime,subprocess
R=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');E=R/'experiments/gsfm016';O=R/'results/comparisons/GSFM-016/20261024-electrical-mechanisms';assert not O.exists();E.mkdir(exist_ok=True);O.mkdir(parents=True)
sys.path[:0]=[str(R/'scripts/python')]
from matpower_case import components
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
S=R/'results/comparisons/GSFM-015/20261023-load-location-charging';P=R/'results/comparisons/GSFM-014/20261023-rated-variants';base={n:json.loads((S/f'G{n}-1.00/input.json').read_text()) for n in ['300','600']};rows=[];prior=[]
for root in [S,P,R/'results/comparisons/GSFM-012',R/'results/diagnosis/GSFM-013',R/'results/comparisons/GSFM-011B',R/'results/comparisons/GSFM-011C-1',R/'results/diagnosis/GSFM-011D']:
 for p in sorted(root.rglob('*')):
  if p.is_file():prior.append({'path':str(p.relative_to(R)),'sha256':sha(p)})
save(O/'prior-artifacts.json',prior)
# Map inherited source locations without using predictions/reference outcomes.
source=base['300'];load_i=max((i for i,b in enumerate(source['bus']) if b[1]==1 and b[2]>0 and b[3]>0),key=lambda i:(source['bus'][i][2],-source['bus'][i][0]));tap_i=next(i for i,b in enumerate(source['branch']) if b[8] not in [0,1] and b[9]==0);stiff_i=min((i for i,b in enumerate(source['branch']) if b[2]>0 and b[3]>0 and b[8]==b[9]==0),key=lambda i:(abs(complex(*source['branch'][i][2:4])),i));refids={b[0] for b in source['bus'] if b[1]==3};gen_i=max((i for i,g in enumerate(source['gen']) if g[0] not in refids and g[9]==0 and g[4]<=0<=g[3]),key=lambda i:(source['gen'][i][8],-i));pairs=collections.defaultdict(list)
for i,b in enumerate(source['branch']):pairs[tuple(sorted(b[:2]))].append(i)
out_i=next(v[0] for k,v in sorted(pairs.items()) if len(v)>1)
selection={'frozen_source_only':True,'load_bus':source['bus'][load_i][0],'source_gen_row_1based':gen_i+1,'gen_bus':source['gen'][gen_i][0],'source_tap_branch_row_1based':tap_i+1,'source_stiff_branch_row_1based':stiff_i+1,'source_parallel_outage_branch_row_1based':out_i+1,'scope':'Generator/cost/load interventions in600 affect areaA only except explicitly distributed total addition; inherited impedance/transformer/shunt/limit interventions affect both copies; ties changed only in coupling/outage cases.'};save(O/'source-selection.json',selection)
def add(name,net,family,c,changes,baseline=None,**kwargs):
 d=O/name;d.mkdir();save(d/'input.json',c);assert len(components(c))==1;assert sum(b[1]==3 for b in c['bus'])==1
 row={'id':name,'network':net,'family':family,'baseline':baseline or f'G{net}-1.00','changes':changes,'input_sha256':sha(d/'input.json'),**kwargs};rows.append(row)
for net,c0 in base.items():
 copies=1 if net=='300' else 2
 for variable,column in [('P',2),('Q',3)]:
  c=copy.deepcopy(c0)
  for b in c['bus']:b[column]*=1.1
  add(f'{variable}10-{net}',net,variable+'-only',c,f'{variable} demand×1.10, signs/zeros retained; other component unchanged')
 for mode in ['concentrated','distributed']:
  c=copy.deepcopy(c0)
  if mode=='concentrated':c['bus'][load_i][2]+=20.;c['bus'][load_i][3]+=5.
  else:
   for column,delta in [(2,20.),(3,5.)]:
    pool=[i for i,b in enumerate(c0['bus']) if b[column]>0];total=sum(c0['bus'][i][column] for i in pool)
    for i in pool:c['bus'][i][column]+=delta*c0['bus'][i][column]/total
  assert abs(sum(b[2] for b in c['bus'])-sum(b[2] for b in c0['bus'])-20)<1e-8;assert abs(sum(b[3] for b in c['bus'])-sum(b[3] for b in c0['bus'])-5)<1e-8
  add(f'ADD-{mode}-{net}',net,'concentration',c,'Add20MW/5MVAr at source-selected largest-PQ-load bus inA versus proportional positive demands network-wide',paired=f'ADD-{"distributed" if mode=="concentrated" else "concentrated"}-{net}')
 c=copy.deepcopy(c0)
 for b in c['bus']:
  if b[5]>0:b[5]*=.5
 add(f'SHUNT50-{net}',net,'shunt',c,'Positive capacitive bus Bs×0.5; negative Bs and line charging unchanged')
 c=copy.deepcopy(c0)
 for g in c['gen']:
  mid=(g[3]+g[4])/2;width=(g[3]-g[4])*.8;g[3]=mid+width/2;g[4]=mid-width/2
 add(f'QBOX80-{net}',net,'Q-headroom',c,'Qg interval width×0.8 around original midpoint; fixed bounds preserved')
 c=copy.deepcopy(c0);c['gen'][gen_i][7]=0;bid=c['gen'][gen_i][0]
 if not any(g[0]==bid and g[7]>0 for g in c['gen']):next(b for b in c['bus'] if b[0]==bid)[1]=1
 add(f'GENOUT-{net}',net,'generator-outage',c,'Largest nonreference source generator out inA, row/status retained; former PV becomesPQ if no remaining online gen',offline_gen_row_1based=gen_i+1)
 c=copy.deepcopy(c0)
 for k in range(4,len(c['gencost'][gen_i])):c['gencost'][gen_i][k]*=2.
 add(f'COST2-{net}',net,'cost',c,'Cost polynomial coefficients×2 for same source-selected generator inA; capacities/status unchanged')
 c=copy.deepcopy(c0)
 for k in range(copies):c['branch'][tap_i+411*k][8]*=1.02
 add(f'TAP102-{net}',net,'tap',c,'First original off-nominal transformer tap×1.02 in each copy')
 c=copy.deepcopy(c0)
 for k in range(copies):c['branch'][tap_i+411*k][9]+=2.
 add(f'SHIFT2-{net}',net,'phase-shift',c,'Same transformer shift+2degrees in each copy; tap unchanged')
 c=copy.deepcopy(c0)
 for b in c['bus']:
  mid=(b[11]+b[12])/2;width=(b[11]-b[12])*.8;b[11]=mid+width/2;b[12]=mid-width/2
 add(f'VBOX80-{net}',net,'voltage-bounds',c,'Bus voltage interval width×0.8 around original midpoint')
 for variable,col in [('R',2),('X',3)]:
  c=copy.deepcopy(c0)
  for k in range(copies):c['branch'][stiff_i+411*k][col]*=1.1
  add(f'{variable}110-{net}',net,variable+'-impedance',c,'Original231–237 positive '+variable+'×1.10 in each copy; other coefficients unchanged')
 for mode in ['renumber','reorder']:
  c=copy.deepcopy(c0);nb=len(c['bus']);ng=len(c['gen']);ne=len(c['branch']);mapping={'bus_to_base_rows':list(range(nb)),'gen_to_base_rows':list(range(ng)),'branch_to_base_rows':list(range(ne))}
  if mode=='renumber':
   relabel={int(b[0]):100001+(37*i)%nb for i,b in enumerate(c0['bus'])};mapping['relabel_old_to_new']=relabel
   for b in c['bus']:b[0]=relabel[int(b[0])]
   for g in c['gen']:g[0]=relabel[int(g[0])]
   for b in c['branch']:b[0]=relabel[int(b[0])];b[1]=relabel[int(b[1])]
   c['diagnostic_bus_origins']=[{'area':'original' if net=='300' else ('A' if i<300 else 'B'),'original_id':int(b[0]) if net=='300' else int(c0['bus_ids'][i].split(':')[-1])} for i,b in enumerate(c0['bus'])]
  else:
   mapping={k:list(reversed(v)) for k,v in mapping.items()}
   for field in ['bus','gen','branch','gencost']:c[field]=list(reversed(c[field]))
   for field in ['bus_ids','gen_ids','branch_ids']:
    if field in c:c[field]=list(reversed(c[field]))
  add(f'REP-{mode}-{net}',net,'representation',c,'Physically equivalent input: '+mode,representation_mapping=mapping)
# Single source interior parallel outage for300; one synthetic tie outage for600.
c=copy.deepcopy(base['300']);c['branch'][out_i][10]=0;add('LINEOUT-300','300','line-outage',c,'One original parallel branch off; row retained; connectedness verified',branch_row_1based=out_i+1)
c=json.loads((S/'L600-Splus/input.json').read_text());c['branch'][822][10]=0;add('TIEOUT-600','600','line-outage',c,'One of two synthetic parallel ties off; other unchanged; no island',branch_row_1based=823,baseline='L600-Splus')
c=json.loads((S/'L600-Splus/input.json').read_text())
for b in c['branch'][822:]:b[3]*=2.
add('TIEX2-600','600','coupling',c,'Both synthetic tie reactances×2; resistances/charging/ratings unchanged; A1.05/B.95',baseline='L600-Splus')
for net in ['300','600']:
 src=P/f'R{net}-base';c=json.loads((src/'input.json').read_text())
 for b in c['branch']:
  if b[5]>0:b[5]*=.8
 add(f'RATE80-{net}',net,'thermal',c,'Complete published rated PGLib baseline; every positive RATE_A×0.8; RATE_B/C and all other fields unchanged',baseline=f'R{net}-base')
# Every field-level mutation is retained before any outcomes.
for row in rows:
 c=json.loads((O/row['id']/'input.json').read_text());origin=json.loads(((P/row['baseline']/'input.json') if row['family']=='thermal' else (S/row['baseline']/'input.json')).read_text());diff=[]
 for field in ['bus','gen','branch','gencost']:
  assert len(c[field])==len(origin[field])
  for i,(a,b) in enumerate(zip(origin[field],c[field])):
   assert len(a)==len(b)
   for j,(x,y) in enumerate(zip(a,b)):
    if x!=y:diff.append({'matrix':field,'row_1based':i+1,'col_1based':j+1,'before':x,'after':y})
 save(O/row['id']/'field-differences.json',diff);row['field_diff_sha256']=sha(O/row['id']/'field-differences.json')
reuse=[]
for row in json.loads((S/'all-scenarios.json').read_text())['scenarios']:reuse.append({'id':row['id'],'network':row['network'],'family':row['family'],'source':str((S/row['id']).relative_to(R)),'input_sha256':sha(S/row['id']/'input.json')})
for net in ['300','600']:
 src=P/f'R{net}-base';d=O/f'R{net}-base';d.mkdir();(d/'input.json').write_bytes((src/'input.json').read_bytes())
 for rel in ['microsoft-v1.1','newer-base-v2']:(d/(rel+'-saved-native.json')).write_bytes((src/(rel+'-native.json')).read_bytes())
 reuse.append({'id':f'R{net}-base','network':net,'family':'rated-baseline','source':str(src.relative_to(R)),'capture_dir':str(d.relative_to(R)),'input_sha256':sha(src/'input.json')})
assert len(rows)==35,len(rows);assert len(reuse)==20
start=datetime.datetime.now(datetime.timezone.utc).isoformat();save(O/'scenario-manifest.json',{'experiment':16,'started_UTC':start,'parent_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'scenarios':rows,'source_selection':selection,'maximum_new_inputs':35,'inclusive_compute_cap_minutes':75});save(O/'reused-inputs.json',reuse)
for name in ['electrical.py','run_dc.py','solver_server.jl']:(E/name).write_bytes((R/'experiments/gsfm015'/name).read_bytes())
print('35 NEW INPUTS FROZEN;20 REUSED; source',selection)
