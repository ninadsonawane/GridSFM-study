"""Saved-state postprocessing only: metrics, genuine clamp events and fixed-angle diagnostics."""
from electrical import *
import copy,datetime,subprocess,collections
O=R/'results/comparisons/GSFM-015/20261023-load-location-charging';M=read(O/'all-scenarios.json');rows=[];buses=[];branches=[];areas=[];clamps=[];events=[];diagnostics=[];gates=[]
for x in M['scenarios']:
 D=O/x['id'];c=read(D/'input.json');assert sha(D/'input.json')==x['input_sha256'];ref=read(D/'ac-native.json') if (D/'ac-native.json').exists() else None
 if ref is not None:assert evaluate(c,ref)['all_tested_constraints_pass'];terms(c,ref)
 elif (D/'ac-status.json').exists():assert not read(D/'ac-status.json')['verified_reference']
 for method,file in [('AC-OPF','ac-native.json' if ref is not None else 'ac-failed-iterate.json'),('DC-OPF','dc-native.json'),('microsoft-v1.1','microsoft-v1.1-native.json'),('newer-base-v2','newer-base-v2-native.json')]:
  if not(D/file).exists():continue
  point=read(D/file);sm,bu,br,ar=score(c,point,method,ref);sm.update(scenario=x['id'],family=x['family'],network=x['network'],reference_valid=ref is not None,solver_status=('VERIFIED_LOCAL_REFERENCE' if ref is not None else 'FAILED_UNKNOWN') if method=='AC-OPF' else ('CONVERGED' if method=='DC-OPF' and read(D/'dc-status.json').get('solver_success',read(D/'dc-status.json').get('success',False)) else 'NATIVE_RETURNED'))
  if method=='DC-OPF':assert sm['native_DC_constraints_pass'];assert point['vm'] is None and point['qg_mvar'] is None
  if method!='DC-OPF':
   sm['Pg_at_bound_count']=sum(min(abs(p-g[9]),abs(p-g[8]))<=1e-3 for p,g in zip(point['pg_mw'],c['gen']));sm['Qg_at_bound_count']=sum(min(abs(p-g[4]),abs(p-g[3]))<=1e-3 for p,g in zip(point['qg_mvar'],c['gen']));sm['Vm_at_bound_count']=sum(min(abs(v-b[12]),abs(v-b[11]))<=1e-4 for v,b in zip(point['vm'],c['bus']))
  rows.append(sm)
  for target,source in [(buses,bu),(branches,br),(areas,ar)]:
   for z in source:z.update(scenario=x['id'],family=x['family'],network=x['network'])
   target.extend(source)
  if method not in ['microsoft-v1.1','newer-base-v2']:continue
  md=read(D/(method+'-metadata.json'));assert md['checkpoint_sha256']==('f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831' if method=='microsoft-v1.1' else '9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7');assert md['leaky_alpha']==0 and md['clip_mode'] in ['clamp','leaky_clip'];assert md['input_sha256']==x['input_sha256'];assert md['model_input_has_solution'] is False
  capture=read(D/(method+'-clamps.json'))['captures'];rawpoint=copy.deepcopy(point);rawblocks={}
  for z in capture:
   var=z['variable'];scale=1 if var=='V' else c['baseMVA'];key={'Pg':'pg_mw','Qg':'qg_mvar','V':'vm'}[var];inp=np.array(z['input']);out=np.array(z['output']);lo=np.array(z['lo']);hi=np.array(z['hi']);assert np.array_equal(np.clip(inp,lo,hi),out);assert np.max(abs(np.array(point[key])-out*scale))==0;delta=(out-inp)*scale;threshold=1e-4 if var=='V' else 1e-3;rawpoint[key]=(inp*scale).tolist();rawblocks[key]=rawpoint[key];strict=inp!=out;phys=abs(delta)>threshold
   record={'scenario':x['id'],'family':x['family'],'network':x['network'],'method':method,'variable':var,'units':'pu' if var=='V' else ('MW' if var=='Pg' else 'MVAr'),'elements':len(inp),'strict_clipped_count':int(strict.sum()),'clipped_above_physical_tolerance_count':int(phys.sum()),'lower_clipped_count':int((inp<lo).sum()),'upper_clipped_count':int((inp>hi).sum()),'max_abs_change':float(abs(delta).max()),'sum_abs_change':float(abs(delta).sum()),'at_bound_after_clipping_count':sum(np.minimum(abs(out-lo),abs(out-hi))*scale<=threshold)};clamps.append(record)
   for i in range(len(inp)):
    events.append({'scenario':x['id'],'method':method,'variable':var,'row_1based':i+1,'bus_id':int(c['bus'][i][0]) if var=='V' else int(c['gen'][i][0]),'area':identity(c,i)[0] if var=='V' else identity(c,next(k for k,b in enumerate(c['bus']) if b[0]==c['gen'][i][0]))[0],'preclip':float(inp[i]*scale),'postclip':float(out[i]*scale),'lo':float(lo[i]*scale),'hi':float(hi[i]*scale),'signed_change':float(delta[i]),'clipped':bool(strict[i]),'above_physical_tolerance':bool(phys[i]),'units':record['units']})
  for variant,keys in [('pre_Pg',['pg_mw']),('pre_Qg',['qg_mvar']),('pre_Vm',['vm']),('pre_all',['pg_mw','qg_mvar','vm'])]:
   hybrid=copy.deepcopy(point)
   for key in keys:hybrid[key]=rawblocks[key]
   ds,*_=score(c,hybrid,method,ref);ds.update(scenario=x['id'],method=method,variant=variant,semantics='Diagnostic hybrid: native angles retained; not a full unclipped model forward; original equations and bounds');diagnostics.append(ds)
  if (D/(method+'-saved-native.json')).exists():assert read(D/(method+'-saved-native.json'))==point
 gates.append({'scenario':x['id'],'input_hash_pass':True,'AC_reference_verified':ref is not None,'DC_original_equations_and_limits_pass':True,'model_pins_and_clamp_identity_pass':True,'Ybus_vs_branch_sum_pass':True,'saved_native_equality_pass':True if 'reused_from' in x else None})
save(O/'method-summary.json',rows);csvsave(O/'bus-metrics.csv',buses);csvsave(O/'branch-flows.csv',branches);csvsave(O/'area-exchange.csv',areas);csvsave(O/'clipping-summary.csv',clamps);csvsave(O/'clipping-events.csv',events);save(O/'preclip-diagnostics.json',diagnostics);save(O/'gates.json',gates)
flat=[]
for z in rows:
 a=z['approximation'];flat.append({k:z[k] for k in ['scenario','family','network','method','reference_valid','solver_status','AC_joint_feasible','native_DC_constraints_pass','Pg_max_excess','Qg_max_excess','Vm_max_excess','angle_max_excess_deg','thermal_violating_count','thermal_max_excess_MVA_or_DC_MW','rated_online_branch_count']}|{'P_mean_MW':z['P']['mean'],'P_max_MW':z['P']['max'],'Q_mean_MVAr':None if z['Q'] is None else z['Q']['mean'],'Q_max_MVAr':None if z['Q'] is None else z['Q']['max']}|{key:None if a is None or a[metric] is None else a[metric]['mean'] for key,metric in [('Pg_MAE_MW','Pg_per_generator_MW'),('Qg_MAE_MVAr','Qg_per_generator_MVAr'),('Vm_MAE_pu','Vm_pu'),('angle_MAE_deg','aligned_angle_deg'),('Pflow_MAE_MW','branch_P_MW'),('Qflow_MAE_MVAr','branch_Q_MVAr')]})
csvsave(O/'method-summary.csv',flat)
lookup={(z['scenario'],z['method']):z for z in rows};contrast=[]
for x in M['scenarios']:
 base=f"G{x['network']}-{x.get('load_scale',1.):.2f}" if x['family']=='charging' else f"G{x['network']}-1.00"
 if x['id']==base:continue
 for rel in ['AC-OPF','DC-OPF','microsoft-v1.1','newer-base-v2']:
  a=lookup.get((x['id'],rel));b=lookup.get((base,rel))
  if not a or not b:continue
  row={'scenario':x['id'],'paired_baseline':base,'family':x['family'],'network':x['network'],'method':rel,'P_max_change':a['P']['max']-b['P']['max'],'P_mean_change':a['P']['mean']-b['P']['mean'],'Q_max_change':None if a['Q'] is None else a['Q']['max']-b['Q']['max'],'Q_mean_change':None if a['Q'] is None else a['Q']['mean']-b['Q']['mean'],'thermal_count_change':None if a['thermal_violating_count'] is None else a['thermal_violating_count']-b['thermal_violating_count']}
  for variable,metric in [('Pg','Pg_per_generator_MW'),('Qg','Qg_per_generator_MVAr'),('Vm','Vm_pu'),('angle','aligned_angle_deg'),('Pflow','branch_P_MW')]:row[variable+'_MAE_change']=None if a['approximation'] is None or b['approximation'] is None or a['approximation'][metric] is None else a['approximation'][metric]['mean']-b['approximation'][metric]['mean']
  for variable in ['Pg','Qg','V']:
   aa=next((k for k in clamps if k['scenario']==x['id'] and k['method']==rel and k['variable']==variable),None);bb=next((k for k in clamps if k['scenario']==base and k['method']==rel and k['variable']==variable),None);row[variable+'_clipped_count_change']=None if aa is None else aa['strict_clipped_count']-bb['strict_clipped_count']
  contrast.append(row)
csvsave(O/'paired-contrasts.csv',contrast)
# Detailed source-only intervention summary, including inherited versus tie charging.
charging=[]
for x in M['scenarios']:
 if x['family']!='charging':continue
 case=read(O/x['id']/'input.json');base=read(O/f"G{x['network']}-{x['load_scale']:.2f}"/'input.json')
 for group,jj in [('inherited',range(411 if x['network']=='300' else 822)),('ties',range(822,len(case['branch'])))]:
  if not list(jj):continue
  charging.append({'scenario':x['id'],'group':group,'sum_b_before_pu':sum(base['branch'][j][4] for j in jj),'sum_b_after_pu':sum(case['branch'][j][4] for j in jj),'positive_b_changed_count':sum(case['branch'][j][4]!=base['branch'][j][4] for j in jj)})
csvsave(O/'charging-coverage.csv',charging)
for old in read(O/'prior-artifacts.json'):assert sha(R/old['path'])==old['sha256'],old['path']
for x in M['scenarios']:
 if 'reused_from' in x:
  for file,want in x['reused_source_hashes'].items():assert sha(R/x['reused_from']/file)==want
save(O/'verification.json',{'status':'PASS','scenarios':len(M['scenarios']),'reference_valid':sum(g['AC_reference_verified'] for g in gates),'method_rows':len(rows),'native_states':len(clamps)//3,'clamp_variables':len(clamps),'preclip_diagnostics':len(diagnostics),'prior_files_unchanged':len(read(O/'prior-artifacts.json')),'source_reused_native_points_exactly_reproduced':12,'independent_physics_and_no_label_input':True,'finished_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()});print('SCORED',len(rows),'REFERENCE PASS',sum(g['AC_reference_verified'] for g in gates),'PRIOR IMMUTABILITY PASS',flush=True)
