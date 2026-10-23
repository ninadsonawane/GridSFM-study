from pathlib import Path
import json,hashlib,copy,sys,collections,subprocess,datetime
R=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');E=R/'experiments/gsfm015';O=R/'results/comparisons/GSFM-015/20261023-load-location-charging';assert not O.exists();E.mkdir(exist_ok=True);O.mkdir(parents=True)
sys.path[:0]=[str(R/'experiments/gsfm012_014'),str(R/'scripts/python')]
from electrical import matrices,makeYbus
from matpower_case import components
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
B=R/'results/comparisons/GSFM-011B/20261022-original-case300';L=R/'results/comparisons/GSFM-011C-1/20261022-loading-only';T=R/'results/comparisons/GSFM-012/20261023-frozen-two-copy';bases={'300':json.loads((B/'input.json').read_text()),'600':json.loads((T/'S0/input.json').read_text())};allrows=[];newrows=[];old=[]
# Freeze all prior scientific artifacts before execution; unchanged earlier files checked after.
for root in [B,L,R/'results/diagnosis/GSFM-011D',T,R/'results/diagnosis/GSFM-013',R/'results/comparisons/GSFM-014']:
 for p in sorted(root.rglob('*')):
  if p.is_file():old.append({'path':str(p.relative_to(R)),'sha256':sha(p)})
save(O/'prior-artifacts.json',old)
def add(name,c,family,network,source=None,**meta):
 d=O/name;d.mkdir();assert len(components(c))==1;save(d/'input.json',c);row={'id':name,'family':family,'network':network,'input_sha256':sha(d/'input.json'),**meta};allrows.append(row)
 if source:
  original=json.loads((source/'input.json').read_text());assert original==c
  row['reused_from']=str(source.relative_to(R));row['reused_source_hashes']={}
  for file in ['ac-native.json','ac-status.json','dc-native.json','dc-status.json','microsoft-v1.1-native.json','newer-base-v2-native.json']:
   if (source/file).exists():
    target=file.replace('-native.json','-saved-native.json') if file.startswith(('microsoft','newer')) else file
    (d/target).write_bytes((source/file).read_bytes());row['reused_source_hashes'][file]=sha(source/file)
 else:newrows.append(row)
for net,base in bases.items():
 for scale in [.9,1.,1.06]:
  if net=='300':src=B if scale==1 else L/f'load-{scale:.2f}';c=json.loads((src/'input.json').read_text())
  else:
   src=T/'S0' if scale==1 else None;c=copy.deepcopy(base)
   for b,orig in zip(c['bus'],base['bus']):b[2]=orig[2]*scale;b[3]=orig[3]*scale
  add(f'G{net}-{scale:.2f}',c,'global',net,src,load_scale=scale)
# Source-only strong/weak selection: PQ buses with positive Pd,Qd in most common kV stratum.
c=bases['300'];ids,b,e,f,t=matrices(c);Y,*_=makeYbus(c['baseMVA'],b,e);pool=[i for i,z in enumerate(c['bus']) if z[1]==1 and z[2]>0 and z[3]>0];kv=min(collections.Counter(c['bus'][i][9] for i in pool).items(),key=lambda z:(-z[1],z[0]))[0];pool=[i for i in pool if c['bus'][i][9]==kv];rank=sorted(pool,key=lambda i:(abs(Y[i,i]),c['bus'][i][0]));weak=rank[:5];strong=rank[-5:];assert set(weak).isdisjoint(strong)
transfer={j:.2*min(sum(c['bus'][i][j] for i in weak),sum(c['bus'][i][j] for i in strong)) for j in [2,3]};selection={'frozen_before_predictions':True,'rule':'Among PQ buses with positive Pd and Qd in most common kV stratum, take bottom/top5 |Ybus_ii| with original-ID ties. This source admittance proxy is not a full voltage-stability/short-circuit-strength measure.','base_kV':kv,'weak_bus_ids':[c['bus'][i][0] for i in weak],'strong_bus_ids':[c['bus'][i][0] for i in strong],'transfer_MW':transfer[2],'transfer_MVAr':transfer[3]};save(O/'local-selection.json',selection)
for target,recipient,donor in [('weak',weak,strong),('strong',strong,weak)]:
 case=copy.deepcopy(c)
 for j in [2,3]:
  for group,sgn in [(recipient,1),(donor,-1)]:
   denom=sum(c['bus'][i][j] for i in group)
   for i in group:case['bus'][i][j]+=sgn*transfer[j]*c['bus'][i][j]/denom
  assert abs(sum(z[j] for z in case['bus'])-sum(z[j] for z in c['bus']))<1e-8
 add('L300-'+target,case,'local','300',location=target,transfer_MW=transfer[2],transfer_MVAr=transfer[3])
for name in ['Splus','Sminus']:
 src=T/name;c=json.loads((src/'input.json').read_text());add('L600-'+name,c,'local','600',src,location='A1.05/B.95' if name=='Splus' else 'A.95/B1.05')
for net,base in bases.items():
 for load in [.9,1.06]:
  for factor in [.5,0.]:
   case=copy.deepcopy(base)
   for z,orig in zip(case['bus'],base['bus']):z[2]=orig[2]*load;z[3]=orig[3]*load
   changed=[]
   for i,(z,orig) in enumerate(zip(case['branch'],base['branch'])):
    if orig[4]>0:z[4]=orig[4]*factor;changed.append(i+1)
   add(f'C{net}-L{load:.2f}-B{factor:.2f}',case,'charging',net,load_scale=load,positive_charging_factor=factor,changed_branch_rows=changed)
for row in allrows:
 case=json.loads((O/row['id']/'input.json').read_text());base=bases[row['network']]
 for key in ['gen','gencost']:assert case[key]==base[key]
 for x,z in zip(case['bus'],base['bus']):assert all(x[j]==z[j] for j in range(13) if j not in [2,3]);assert all((x[j]==0)==(z[j]==0) and x[j]*z[j]>=0 for j in [2,3])
 for x,z in zip(case['branch'],base['branch']):assert all(x[j]==z[j] for j in range(13) if not(row['family']=='charging' and j==4 and z[j]>0))
 assert all(z[5]==0 for z in case['branch'][:411 if row['network']=='300' else 822]);row['matrix_difference_gate']='PASS'
start=datetime.datetime.now(datetime.timezone.utc).isoformat();save(O/'all-scenarios.json',{'experiment':'15A/B/C','started_UTC':start,'scenarios':allrows,'new_inputs':len(newrows),'reused_solver_inputs':len(allrows)-len(newrows),'local_selection':selection,'parent_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()});save(O/'scenario-manifest.json',{'experiment':15,'started_UTC':start,'scenarios':newrows})
for name in ['electrical.py','run_dc.py','solver_server.jl','rescore_saved.py']:(E/name).write_bytes((R/'experiments/gsfm012_014'/name).read_bytes())
s=(R/'experiments/gsfm012_014/run_model.py').read_text();needle='t=time.perf_counter();raw=predict(m,p);'
instrument='''# Observe the exact values entering each existing clamp; return its unmodified output.
import gridsfm.model as model_module
captured=[];original_clip=model_module._leaky_clip
def observe_clip(value,lo,hi,**kwargs):
 out=original_clip(value,lo,hi,**kwargs)
 captured.append({'input':value.detach().cpu().tolist(),'lo':lo.detach().cpu().tolist(),'hi':hi.detach().cpu().tolist(),'output':out.detach().cpu().tolist()})
 return out
model_module._leaky_clip=observe_clip
'''
s=s.replace(needle,instrument+needle);s+='''\nassert len(captured)==3, len(captured)
for item,key in zip(captured,['Pg','Qg','V']):
 item['variable']=key
 assert torch.isfinite(torch.tensor(item['input'])).all()
 assert item['output']==serial[key]
(OUT/(release+'-clamps.json')).write_text(json.dumps({'captures':captured,'semantics':'Pg/Qg inputs include shipped midpoint offsets; Vm direct head output; theta remains native and was calculated from clipped Pg. No forward modification.'},indent=2)+'\\n')
saved=OUT/(release+'-saved-native.json')
if saved.exists():assert json.loads(saved.read_text())==native,'Instrumented prediction differs from saved native point'
''';(E/'run_model.py').write_text(s)
s=(R/'experiments/gsfm012_014/run_cases.py').read_text().replace("E=pathlib.Path(__file__).parent;","E=pathlib.Path(__file__).parent;");(E/'run_cases.py').write_text(s)
protocol='''# Experiment15 — load level, load location and line charging versus errors and clipping

AUTHORIZED by Ninad23 October2026: append and execute exactly these three focused tests, AC-OPF/DC-OPF/both frozen models. No training, sigmoid override, PF completion or OPF repair. All prior results immutable.

-15A global: case300 and unchanged two-copy case600 at0.90/1.00/1.06 Pd/Qd. Reuse matching solver/native points; repeat neural forward only to capture exact pre/post clamp inputs and require equality with saved outputs.
-15B location: two opposite fixed-total transfers between source-only selected five-bus PQ/positive-load groups in case300; most common kV, bottom/top |Ybus_ii|. Transfer20% of smaller group total separately for P/Q, distributed proportionally, preserving signs. This is an admittance-proxy contrast, not an established weak/strong-grid or causal sensitivity classification. Two-copy area shifts reuse12 Splus/Sminus. No pairing selected from prediction outcomes.
-15C charging: at0.90 and1.06 loading, reduce strictly positive branch total charging b to50%/0 on each network; negative charging, all bus shunts, r/x/taps/phase shifts/statuses/limits/costs unchanged. Both synthetic tie charging values scale too; interior versus tie contributions reported separately. No claim these independent parameter edits represent physical line replacement.

18 unique inputs:12 new solver inputs and6 reused. Two sequential native forwards per input (36 total), seed0 and shipped clip defaults. Existing environments read-only. Inputs, group selection and hashes frozen before outcomes. Solver options/tolerances same12: AC120s/3000iter, at most one deterministic flat retry; DC audited PIPS QP. Numerical failure UNKNOWN; reference errors N/A if no verified local reference. Original equations FP64 with Ybus/branch-sum crosscheck. No invented ratings:300 interior thermal N/A;600 thermal only two600MVA synthetic ties.

Capture existing _leaky_clip inputs/outputs via observer returning the original tensor unchanged. Save Pg/Qg midpoint-adjusted preclip values and direct Vm preclip values; strict counts and physically meaningful clipping counts/magnitudes plus original IDs. Recompute four diagnostics substituting preclip Pg only, Qg only, Vm only, or all three, holding native theta. These are hybrid counterfactual diagnostics; theta depends on clipped Pg through the DC prior, so they are NOT a complete unclipped inference or practical operating points. No extra forwards needed. Compare solver bound activity separately from neural clipping.

Results: per-input method state/flow errors, P/Q residual distributions and worst IDs, Pg/Qg/V/angle/rated-branch excesses, full-feasibility counts; detailed pre/post clip counts/magnitudes and signed residual changes; matched charging/global/location contrasts. Small inspected screen, no generalization/novelty guarantee. Raw artifacts local-only with hashes, compact report/tables in a new GSFM-015 directory. Stop after report.
''';(R/'docs/experiments/GSFM-015.md').write_text(protocol)
print('FROZEN18 / NEW',len(newrows),'SELECTION',selection)
