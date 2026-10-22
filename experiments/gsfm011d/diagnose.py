"""11D: deterministic diagnosis of SAVED states only. No model or solver import/call."""
import pathlib,sys,json,hashlib,csv,itertools,math,datetime,subprocess,platform
import numpy as np
from pypower.makeYbus import makeYbus
R=pathlib.Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');B=R/'results/comparisons/GSFM-011B/20261022-original-case300';C=R/'results/comparisons/GSFM-011C-1/20261022-loading-only';O=R/'results/diagnosis/GSFM-011D/20261022-saved-states';O.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(R/'scripts/python'))
from physics_metrics import branch_flows,evaluate,wrap_degrees
from matpower_case import read_case
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,x):(O/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def writecsv(name,rows):
 if not rows:return
 with (O/name).open('w',newline='') as f:
  w=csv.DictWriter(f,list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
source=R/'results/inference/2026-10-21-base-cases/case300.m';original=read_case(source);assert sha(source)=='69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5';assert len(original['bus'])==300 and len(original['gen'])==69 and len(original['branch'])==411
scales=[.8,.9,.95,1.,1.03,1.06,1.1];releases=['microsoft-v1.1','newer-base-v2'];method={'microsoft-v1.1':'Microsoft v1.1','newer-base-v2':'Newer v2'};dirs={v:B if v==1 else C/f'load-{v:.2f}' for v in scales};cases={v:read(d/'input.json') for v,d in dirs.items()};ids={int(b[0]):i for i,b in enumerate(original['bus'])};busids=list(ids);gindex=np.array([ids[int(g[0])] for g in original['gen']]);online=np.array([g[7]>0 for g in original['gen']]);branches=np.array(original['branch']);f=np.array([ids[int(b[0])] for b in branches]);t=np.array([ids[int(b[1])] for b in branches]);adj={i:[] for i in range(300)}
for j,(ff,tt) in enumerate(zip(f,t)):adj[ff].append((j,'from'));adj[tt].append((j,'to'))
# Gate: immutable saved artifacts, unchanged cases, sources/checkpoints/defaults.
checks={};input_hashes={};sourcepins={}
for directory in [B,C]:
 inv=read(directory/'artifact-inventory.json');bad=[n for n,v in inv.items() if sha(directory/n)!=v['sha256']];assert not bad,(directory,bad);checks[str(directory/'artifact-inventory.json')]={'sha256':sha(directory/'artifact-inventory.json'),'files_verified':len(inv)}
for release in releases:
 md=read(B/(release+'-metadata.json'));cp=pathlib.Path(md['checkpoint_path']);assert sha(cp)==md['checkpoint_sha256'];src=pathlib.Path('/private/tmp/gsfm011b-20261022/microsoft-source') if release=='microsoft-v1.1' else R/'work/GSFM-006-source-517a075';assert sha(src/'model/gridsfm/model.py')==md['source_model_sha256'];sourcepins[release]={k:md[k] for k in ['source_commit','source_model_sha256','checkpoint_path','checkpoint_sha256','clip_mode','leaky_alpha']}
assert sourcepins[releases[0]]['clip_mode']=='leaky_clip' and sourcepins[releases[1]]['clip_mode']=='clamp'
assert all(p['leaky_alpha']==0 for p in sourcepins.values())
net={};states={};refs={};physics={};gate=[]
def terms(c,s):
 bus=np.array(c['bus']);base=c['baseMVA'];V=np.array(s['vm'])*np.exp(1j*np.deg2rad(s['va_deg']));gen=np.zeros(300,complex);np.add.at(gen,gindex[online],np.array(s['pg_mw'])[online]+1j*np.array(s['qg_mvar'])[online]);demand=bus[:,2]+1j*bus[:,3];shunt=(bus[:,4]-1j*bus[:,5])*np.abs(V)**2;sf,st=branch_flows(c,s['vm'],s['va_deg']);sf=np.array(sf);st=np.array(st);out=np.zeros(300,complex);np.add.at(out,f,sf);np.add.at(out,t,st);res=gen-demand-out-shunt;Y,Yf,Yt=net[id(c)];yr=gen-demand-base*V*np.conj(Y@V)
 err=max(float(abs(res-yr).max()),float(abs(sf-base*V[f]*np.conj(Yf@V)).max()),float(abs(st-base*V[t]*np.conj(Yt@V)).max()));assert err<1e-7,err
 return {'generation':gen,'demand':demand,'branch_out':out,'shunt_consumption':shunt,'residual':res,'sf':sf,'st':st,'V':V,'crosscheck_error':err}
for scale in scales:
 c=cases[scale];assert c['baseMVA']==100
 for key in ['branch','gen','gencost']:assert c[key]==original[key]
 for b,x in zip(c['bus'],original['bus']):assert b[2]==x[2]*scale and b[3]==x[3]*scale and b[:2]+b[4:]==x[:2]+x[4:]
 bb=np.array(c['bus'],float);ee=np.array(c['branch'],float);bb[:,0]=np.arange(300);ee[:,0]=f;ee[:,1]=t;net[id(c)]=makeYbus(c['baseMVA'],bb,ee);d=dirs[scale];input_hashes[str(scale)]={'input':sha(d/'input.json'),'native':{}}
 if scale!=1.1:
  ref=read(d/'ac-native.json');assert read(d/'ac-result.json')['termination_status']=='LOCALLY_SOLVED';assert evaluate(c,ref)['all_tested_constraints_pass'];refs[scale]=ref;physics[(scale,'AC-reference')]=terms(c,ref);input_hashes[str(scale)]['AC_reference']=sha(d/'ac-native.json');refdiff=0.
  with (d/'bus-diagnostics.csv').open() as fh:
   for row in csv.DictReader(fh):
    if row['method']=='AC-OPF':
     value=physics[(scale,'AC-reference')]['residual'][ids[int(row['original_bus_id'])]];refdiff=max(refdiff,abs(value.real-float(row['P_imbalance_MW'])),abs(value.imag-float(row['Q_imbalance_MVAr'])))
  assert refdiff<1e-7
  gate.append({'scale':scale,'state':'AC-reference','max_crosscheck_error_MW_MVAr':physics[(scale,'AC-reference')]['crosscheck_error'],'saved_residual_max_difference':refdiff})
 else:assert read(d/'verification.json')['AC_reference_independently_feasible'] is False
 saved={x['method']:x for x in read(d/'physical-validity.json')};savedbus={}
 with (d/'bus-diagnostics.csv').open() as h:
  for row in csv.DictReader(h):savedbus[(row['method'],int(row['original_bus_id']))]=(float(row['P_imbalance_MW']),float(row['Q_imbalance_MVAr']) if row['Q_imbalance_MVAr'] else None)
 for release in releases:
  md=read(d/(release+'-metadata.json'));assert all(md[k]==sourcepins[release][k] for k in sourcepins[release]);assert md['input_sha256']==sha(d/'input.json');assert not md['additional_PF_or_OPF'] and md['native_saved_before_evaluation'] and not md['model_input_has_solution'];assert md['mapping']['bus_external_ids']==busids and md['mapping']['gen_source_rows']==list(range(69));maps=md['mapping'];rowmaps=maps['ac_line_source_rows']+maps['transformer_source_rows'];assert sorted(rowmaps)==list(range(411))
  state=read(d/(release+'-native.json'));raw=read(d/(release+'-returned.json'));assert np.array_equal(state['vm'],raw['V']);assert np.allclose(state['va_deg'],np.rad2deg(raw['theta']),atol=1e-12,rtol=0);assert np.allclose(state['pg_mw'],np.array(raw['Pg'])*100,atol=1e-12,rtol=0);assert np.allclose(state['qg_mvar'],np.array(raw['Qg'])*100,atol=1e-12,rtol=0)
  assert all(np.isfinite(state[k]).all() for k in ['vm','va_deg','pg_mw','qg_mvar']);states[(scale,release)]=state;tr=terms(c,state);physics[(scale,release)]=tr;r=tr['residual'];prior=saved[method[release]];diff=max(abs(float(abs(r.real).max())-prior['max_P_imbalance_MW']),abs(float(abs(r.imag).max())-prior['max_Q_imbalance_MVAr']))
  for i,bid in enumerate(busids):
   pp,qq=savedbus[(method[release],bid)];diff=max(diff,abs(r[i].real-pp),abs(r[i].imag-qq))
  assert diff<1e-7,diff;input_hashes[str(scale)]['native'][release]=sha(d/(release+'-native.json'));gate.append({'scale':scale,'state':release,'max_crosscheck_error_MW_MVAr':tr['crosscheck_error'],'saved_residual_max_difference':diff})
save('verification.json',{'status':'PASS','gate_completed_before_interpretation':True,'date_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'study_execution_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'saved_artifact_inventories':checks,'source_checkpoints_settings':sourcepins,'input_native_hashes':input_hashes,'crosschecks':gate,'max_crosscheck_error':max(x['max_crosscheck_error_MW_MVAr'] for x in gate),'max_saved_residual_difference':max(x['saved_residual_max_difference'] for x in gate),'units':'Vm pu, angle degrees converted once to radians in phasors, Pg/Qg MW/MVAr (native per-unit API multiplied by100); r MW+jMVAr','orientation':'Original from/to preserved; from-side complex tap exp(+j shift), Yft=-y/conj(tap), Ytf=-y/tap; branch charging at both ends; bus shunt (Gs-jBs)*Vm² once','branch_identity':'Original 1-based row numbers, including both parallel row pairs; not keyed only by bus pair','scope':'14 saved native model states +6 valid saved references. AC1.10 values never loaded as reference. No inference/solver/training/new scenarios/network modification.','forbidden_operation_count':0})
print('VERIFICATION PASS',len(gate),'states; exact Ybus/branch signs/units/mappings consistent',flush=True)
# Interpretation starts only after the gate above passes.
def metrics(r):
 return {'P_max_MW':float(abs(r.real).max()),'P_mean_abs_MW':float(abs(r.real).mean()),'P_total_abs_MW':float(abs(r.real).sum()),'P_signed_sum_MW':float(r.real.sum()),'Q_max_MVAr':float(abs(r.imag).max()),'Q_mean_abs_MVAr':float(abs(r.imag).mean()),'Q_total_abs_MVAr':float(abs(r.imag).sum()),'Q_signed_sum_MVAr':float(r.imag.sum())}
base_rows=[];focus={};concentr=[];combos=[];comparators=[];profiles=[];tracks=[];branch_rows=[];oracle_bus=[];rankrows=[]
def profile(i):
 b=original['bus'][i];ng=sum(1 for j in range(69) if online[j] and gindex[j]==i);return {'bus_id':busids[i],'bus_type':int(b[1]),'online_generator_count':ng,'Pd_MW':b[2],'Qd_MVAr':b[3],'Gs_MW_at_1pu':b[4],'Bs_MVAr_at_1pu':b[5],'base_kV':b[9],'incident_branch_rows':len(adj[i]),'unique_neighbors':len({int(branches[j][1] if side=='from' else branches[j][0]) for j,side in adj[i]}),'zero_injection_bus':bool(ng==0 and b[2]==0 and b[3]==0 and b[4]==0 and b[5]==0),'zero_demand_bus':bool(b[2]==0 and b[3]==0)}
prof=[profile(i) for i in range(300)]
def sorted_top(v,n):return sorted(range(300),key=lambda i:(-abs(v[i]),busids[i]))[:n]
# Per-release focus union fixed from unchanged base: named3 + top5P + top5Q.
# Low-error = lowest75/300 by max(abs(P),abs(Q)), ties by original ID.
# Match categorical type, generator-presence and structural-zero flag lexicographically;
# then minimize normalized demand/kV/degree distance; no post-selection adjustments.
for release in releases:
 tr=physics[(1.,release)];r=tr['residual'];topP=sorted_top(r.real,5);topQ=sorted_top(r.imag,5);targets=sorted({ids[238],ids[231],ids[137],*topP,*topQ},key=lambda i:busids[i]);focus[release]={'top5P':[busids[i] for i in topP],'top5Q':[busids[i] for i in topQ],'targets':[busids[i] for i in targets]};score=np.maximum(abs(r.real),abs(r.imag));low=sorted(range(300),key=lambda i:(score[i],busids[i]))[:75];pool=[i for i in low if i not in targets];assert pool
 for i in targets:
  a=prof[i]
  def match(j):
   b=prof[j];cat=(a['bus_type']!=b['bus_type'],(a['online_generator_count']>0)!=(b['online_generator_count']>0),a['zero_injection_bus']!=b['zero_injection_bus']);dist=abs(a['Pd_MW']-b['Pd_MW'])/max(1,abs(a['Pd_MW']))+abs(a['Qd_MVAr']-b['Qd_MVAr'])/max(1,abs(a['Qd_MVAr']))+abs(a['base_kV']-b['base_kV'])/max(1,abs(a['base_kV']))+abs(a['incident_branch_rows']-b['incident_branch_rows'])/max(1,a['incident_branch_rows'])+abs(a['unique_neighbors']-b['unique_neighbors'])/max(1,a['unique_neighbors']);return (*cat,dist,busids[j])
  j=min(pool,key=match);b=prof[j];m=match(j);poor=any(m[:3]) or a['base_kV']!=b['base_kV'] or m[3]>1;comparators.append({'release':release,'target_bus':busids[i],'comparator_bus':busids[j],'target_profile':a,'comparator_profile':b,'comparator_base_max_abs_P_Q':float(score[j]),'low_error_rule':'Lowest75 of300 by max(|rP|,|rQ|), original-ID tie-break, exclude focus targets','categorical_mismatches':list(map(bool,m[:3])),'normalized_continuous_distance':m[3],'poor_match':bool(poor),'matching_note':'Independent nearest match; reuse allowed. Poor if any category mismatch, unequal kV, or summed normalized distance>1. Demand has original signs, not magnitude-only matching.'})
 for comp,vals in [('P',r.real),('Q',r.imag)]:
  order=sorted_top(vals,300);total=float(abs(vals).sum());row={'release':release,'component':comp,'total_absolute_imbalance':total}
  for n in [1,5,10]:row[f'top{n}_fraction']=float(abs(vals[order[:n]]).sum()/total);row[f'outside_top{n}_absolute']=float(abs(vals[order[n:]]).sum());row[f'top{n}_bus_ids']=[busids[i] for i in order[:n]]
  concentr.append(row)
  for rank,i in enumerate(order,1):rankrows.append({'release':release,'component':comp,'rank':rank,'bus_id':busids[i],'signed_imbalance':float(vals[i]),'absolute_imbalance':float(abs(vals[i]))})
# Keep both releases' base-case focus/comparators fixed over all saved loads.
fixed={release:sorted(set(focus[release]['targets']+[x['comparator_bus'] for x in comparators if x['release']==release])) for release in releases}
for release in releases:
 for scale in scales:
  c=cases[scale];s=states[(scale,release)];tr=physics[(scale,release)];reftr=physics.get((scale,'AC-reference'));ref=refs.get(scale)
  for i in range(300):
   b=prof[i];row={'loading':scale,'release':release,'bus_id':busids[i],'area':int(c['bus'][i][6]),'bus_type':b['bus_type'],'generator_present':b['online_generator_count']>0,'zero_injection_bus':b['zero_injection_bus'],'zero_demand_bus':b['zero_demand_bus'],'base_kV':b['base_kV'],'reference_available':ref is not None,'Vm_pred_pu':s['vm'][i],'Vm_ref_pu':None if ref is None else ref['vm'][i],'angle_pred_deg':s['va_deg'][i],'angle_ref_deg':None if ref is None else ref['va_deg'][i],'reference_aligned_angle_error_deg':None if ref is None else wrap_degrees((s['va_deg'][i]-s['va_deg'][next(k for k,b in enumerate(c['bus']) if b[1]==3)])-(ref['va_deg'][i]-ref['va_deg'][next(k for k,b in enumerate(c['bus']) if b[1]==3)]))}
   for name in ['generation','demand','branch_out','shunt_consumption','residual']:
    for comp,access in [('P','real'),('Q','imag')]:
     val=float(getattr(tr[name][i],access));rv=None if reftr is None else float(getattr(reftr[name][i],access));row[name+'_'+comp+'_pred']=val;row[name+'_'+comp+'_ref']=rv;row[name+'_'+comp+'_delta']=None if rv is None else val-rv
   if scale==1.:base_rows.append(row)
   if busids[i] in fixed[release]:tracks.append(row)
  for bid in fixed[release]:
   i=ids[bid]
   for j,side in adj[i]:
    ff,tt=f[j],t[j];br=c['branch'][j];pred_diff=s['va_deg'][ff]-s['va_deg'][tt];ref_diff=None if ref is None else ref['va_deg'][ff]-ref['va_deg'][tt];sout=tr['sf'][j] if side=='from' else tr['st'][j];sref=None if reftr is None else (reftr['sf'][j] if side=='from' else reftr['st'][j]);row={'loading':scale,'release':release,'focus_bus':bid,'branch_row_1based':j+1,'bus_endpoint':side,'from_bus':int(br[0]),'to_bus':int(br[1]),'r_pu':br[2],'x_pu':br[3],'bc_total_pu':br[4],'tap_original':br[8],'tap_effective':br[8] or 1.,'shift_deg':br[9],'status':br[10],'from_Gs':c['bus'][ff][4],'from_Bs':c['bus'][ff][5],'to_Gs':c['bus'][tt][4],'to_Bs':c['bus'][tt][5],'Vm_from_pred':s['vm'][ff],'Vm_to_pred':s['vm'][tt],'Vm_from_ref':None if ref is None else ref['vm'][ff],'Vm_to_ref':None if ref is None else ref['vm'][tt],'angle_difference_pred_deg':pred_diff,'angle_difference_ref_deg':ref_diff,'angle_difference_error_deg':None if ref is None else wrap_degrees(pred_diff-ref_diff),'out_P_pred_MW':float(sout.real),'out_Q_pred_MVAr':float(sout.imag),'out_P_ref_MW':None if sref is None else float(sref.real),'out_Q_ref_MVAr':None if sref is None else float(sref.imag),'out_P_delta_MW':None if sref is None else float((sout-sref).real),'out_Q_delta_MVAr':None if sref is None else float((sout-sref).imag),'Pf_pred_MW':float(tr['sf'][j].real),'Qf_pred_MVAr':float(tr['sf'][j].imag),'Pt_pred_MW':float(tr['st'][j].real),'Qt_pred_MVAr':float(tr['st'][j].imag),'Pf_ref_MW':None if reftr is None else float(reftr['sf'][j].real),'Qf_ref_MVAr':None if reftr is None else float(reftr['sf'][j].imag),'Pt_ref_MW':None if reftr is None else float(reftr['st'][j].real),'Qt_ref_MVAr':None if reftr is None else float(reftr['st'][j].imag)};branch_rows.append(row)
  # All8 complete-network oracle block substitutions, only with a valid reference.
  # Angles are aligned to a common original reference to remove arbitrary gauge.
  if ref is not None:
   slack=next(i for i,b in enumerate(c['bus']) if b[1]==3);predang=np.array(s['va_deg'])-s['va_deg'][slack];refang=np.array(ref['va_deg'])-ref['va_deg'][slack]
   for g,v,a in itertools.product([0,1],repeat=3):
    h={'pg_mw':ref['pg_mw'] if g else s['pg_mw'],'qg_mvar':ref['qg_mvar'] if g else s['qg_mvar'],'vm':ref['vm'] if v else s['vm'],'va_deg':refang.tolist() if a else predang.tolist()};ht=terms(c,h);r=ht['residual'];m=metrics(r);combos.append({'loading':scale,'release':release,'blocks_reference_G_V_A':f'{g}{v}{a}','reference_G':bool(g),'reference_Vm':bool(v),'reference_angle':bool(a),**m})
    for bid in fixed[release]:
     i=ids[bid];oracle_bus.append({'loading':scale,'release':release,'bus_id':bid,'blocks_reference_G_V_A':f'{g}{v}{a}','signed_P_imbalance_MW':float(r[i].real),'signed_Q_imbalance_MVAr':float(r[i].imag)})
 # Signed base error closure against near-zero reference; demand error exactly0.
 for row in [r for r in base_rows if r['release']==release]:
  for comp in ['P','Q']:
   assert abs(row['residual_'+comp+'_delta']-(row['generation_'+comp+'_delta']-row['demand_'+comp+'_delta']-row['branch_out_'+comp+'_delta']-row['shunt_consumption_'+comp+'_delta']))<1e-8
save('base-focus.json',focus);save('comparators.json',comparators);save('concentration.json',concentr);save('oracle-combinations.json',combos);writecsv('base-bus-terms.csv',base_rows);writecsv('fixed-bus-loading-terms.csv',tracks);writecsv('incident-branches.csv',branch_rows);writecsv('oracle-fixed-buses.csv',oracle_bus);writecsv('base-ranked-residuals.csv',rankrows);writecsv('oracle-combinations.csv',combos)
# Compact base tables: named + worst focus + matching low-error buses.
selected=[r for r in base_rows if r['bus_id'] in fixed[r['release']]];save('base-selected-terms.json',selected)
# Which branch changes explain newer v2's90→95 residual jump? Exact signed budget.
transition=[];transition_br=[]
for release in releases:
 for bid in fixed[release]:
  x=next(r for r in tracks if r['release']==release and r['bus_id']==bid and r['loading']==.9);y=next(r for r in tracks if r['release']==release and r['bus_id']==bid and r['loading']==.95);d={'release':release,'bus_id':bid}
  for name in ['generation','demand','branch_out','shunt_consumption','residual']:
   for comp in ['P','Q']:d['change_'+name+'_'+comp]=y[name+'_'+comp+'_pred']-x[name+'_'+comp+'_pred']
  transition.append(d)
  b9={r['branch_row_1based']:r for r in branch_rows if r['release']==release and r['focus_bus']==bid and r['loading']==.9};b95={r['branch_row_1based']:r for r in branch_rows if r['release']==release and r['focus_bus']==bid and r['loading']==.95}
  for j,r9 in b9.items():
   r95=b95[j];transition_br.append({'release':release,'focus_bus':bid,'branch_row_1based':j,'from_bus':r9['from_bus'],'to_bus':r9['to_bus'],'r_pu':r9['r_pu'],'x_pu':r9['x_pu'],'tap_effective':r9['tap_effective'],'bc_total_pu':r9['bc_total_pu'],'Qout_90':r9['out_Q_pred_MVAr'],'Qout_95':r95['out_Q_pred_MVAr'],'Qout_change':r95['out_Q_pred_MVAr']-r9['out_Q_pred_MVAr'],'Pout_change':r95['out_P_pred_MW']-r9['out_P_pred_MW'],'Vm_from_90':r9['Vm_from_pred'],'Vm_to_90':r9['Vm_to_pred'],'Vm_from_95':r95['Vm_from_pred'],'Vm_to_95':r95['Vm_to_pred'],'angle_diff_90':r9['angle_difference_pred_deg'],'angle_diff_95':r95['angle_difference_pred_deg']})
save('loading90-to95-budget.json',transition);save('loading90-to95-branches.json',transition_br)
# Summaries of the fixed saved operating points; no fitted statistical model.
save('analysis-summary.json',{'focus':focus,'fixed_buses':fixed,'base_metrics':{r:metrics(physics[(1.,r)]['residual']) for r in releases},'all_load_metrics':[{'loading':s,'release':r,**metrics(physics[(s,r)]['residual'])} for s in scales for r in releases],'oracle_diagnostics_only':True,'oracle_loads':[.8,.9,.95,1.,1.03,1.06],'reference_free_loads':[1.1],'comparator_profiles':prof,'script_sha256':sha(pathlib.Path(__file__)),'python':sys.executable,'platform':platform.platform()})
print('ANALYSIS COMPLETE; no model inference/solver/training calls',flush=True)
# Cancellation measured over individual incident-branch errors, not just their sum.
cancellation=[];genrows=[]
for release in releases:
 s=states[(1.,release)];ref=refs[1.];tr=physics[(1.,release)];rr=physics[(1.,'AC-reference')]
 for i in range(300):
  for comp,part in [('P','real'),('Q','imag')]:
   contributions=[float(getattr(tr['generation'][i]-rr['generation'][i],part)),-float(getattr(tr['shunt_consumption'][i]-rr['shunt_consumption'][i],part))]
   for j,side in adj[i]:contributions.append(-float(getattr((tr['sf'][j]-rr['sf'][j]) if side=='from' else (tr['st'][j]-rr['st'][j]),part)))
   denom=sum(abs(v) for v in contributions);net=sum(contributions);assert abs(net-getattr(tr['residual'][i]-rr['residual'][i],part))<1e-7
   cancellation.append({'release':release,'bus_id':busids[i],'component':comp,'sum_abs_individual_signed_error_contributions':denom,'net_signed_residual_error':net,'cancellation_fraction':None if denom==0 else 1-abs(net)/denom,'local_Vm_error_pu':s['vm'][i]-ref['vm'][i],'minimum_incident_abs_z_pu':min(abs(complex(original['branch'][j][2],original['branch'][j][3])) for j,side in adj[i])})
 for j,g in enumerate(original['gen']):genrows.append({'release':release,'gen_row_1based':j+1,'bus_id':int(g[0]),'Pg_pred_MW':s['pg_mw'][j],'Pg_ref_MW':ref['pg_mw'][j],'Pg_error_MW':s['pg_mw'][j]-ref['pg_mw'][j],'Qg_pred_MVAr':s['qg_mvar'][j],'Qg_ref_MVAr':ref['qg_mvar'][j],'Qg_error_MVAr':s['qg_mvar'][j]-ref['qg_mvar'][j]})
writecsv('base-cancellation.csv',cancellation);writecsv('base-generators.csv',genrows)
# Gauge-aligned000 must reproduce native;111 must reproduce feasible reference.
for scale in scales:
 if scale not in refs:continue
 for release in releases:
  native=next(r for r in combos if r['loading']==scale and r['release']==release and r['blocks_reference_G_V_A']=='000');allref=next(r for r in combos if r['loading']==scale and r['release']==release and r['blocks_reference_G_V_A']=='111');want=metrics(physics[(scale,release)]['residual'])
  assert max(abs(native[k]-want[k]) for k in want)<1e-6
  assert allref['P_max_MW']<1e-3 and allref['Q_max_MVAr']<1e-3
save('oracle-verification.json',{'status':'PASS','complete_network_combinations':len(combos),'expected':6*2*8,'G_block':'All online Pg and Qg together; original gen ordering','Vm_block':'All300 magnitudes','angle_block':'All300 angles aligned to original REF7049; no branch-wise independent angles','branch_and_shunt_recomputed_each_time':True,'Ybus_branch_crosscheck_asserted_every_combination':True,'000_matches_saved_native_within_1e_minus6_aggregate':True,'111_returns_independently_feasible_reference':True,'110_percent_oracle_count':0,'interpretation':'Oracle diagnostics using known AC answers, not practical predictions, feasible completions or repairs. Changes can worsen and interact.'})
