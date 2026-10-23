"""Saved-state analysis for distinct mechanisms; no solves/inference."""
from electrical import *
import copy,collections,datetime,subprocess
O=R/'results/comparisons/GSFM-016/20261024-electrical-mechanisms';M=read(O/'scenario-manifest.json');reuse=read(O/'reused-inputs.json');newids={x['id'] for x in M['scenarios']};entries=[dict(x,source=str((O/x['id']).relative_to(R))) for x in M['scenarios']]+reuse;rows=[];clamps=[];events=[];gates=[];busout=[];branchout=[];areaout=[];points={};cases={};records={};fullaudit=[]
for x in entries:
 D=R/x['source'];c=read(D/'input.json');assert sha(D/'input.json')==x['input_sha256'];cases[x['id']]=c;records[x['id']]=x;ref=read(D/'ac-native.json') if (D/'ac-native.json').exists() else None
 if ref is not None:assert evaluate(c,ref)['all_tested_constraints_pass'];terms(c,ref)
 validDC=None
 for method,file in [('AC-OPF','ac-native.json' if ref is not None else 'ac-failed-iterate.json'),('DC-OPF','dc-native.json'),('microsoft-v1.1','microsoft-v1.1-native.json'),('newer-base-v2','newer-base-v2-native.json')]:
  if not(D/file).exists():continue
  s=read(D/file);points[(x['id'],method)]=s;sm,bu,br,ar=score(c,s,method,ref);sm.update(scenario=x['id'],network=x['network'],family=x['family'],reference_valid=ref is not None,reference_status='VERIFIED_LOCAL_REFERENCE' if ref is not None else 'UNKNOWN',reused=x['id'] not in newids)
  active=np.array([g[7]>0 for g in c['gen']]);online=np.array([b[10]>0 for b in c['branch']]);sm['online_generator_count']=int(active.sum());sm['online_branch_count']=int(online.sum());sm['objective_raw_original_units']=float(cost(c,s['pg_mw'],[0]*len(c['gen']) if method=='DC-OPF' else s['qg_mvar']))
  if method=='DC-OPF':
   status=read(D/'dc-status.json');success=status.get('solver_success',status.get('success',False));sm['solver_success']=success;validDC=bool(success and sm['native_DC_constraints_pass']);assert (not success) or sm['native_DC_constraints_pass'];assert s['vm'] is None and s['qg_mvar'] is None
  else:
   assert all(s['pg_mw'][i]==s['qg_mvar'][i]==0 for i in range(len(c['gen'])) if not active[i]);metrics=evaluate(c,s);assert abs(sm['P']['max']-metrics['max_p_residual_mw'])<1e-6 and abs(sm['Q']['max']-metrics['max_q_residual_mvar'])<1e-6;assert sm['AC_joint_feasible']==metrics['all_tested_constraints_pass']
   sm['Pg_at_bound_count']=int(sum(min(abs(v-g[9]),abs(v-g[8]))<=1e-3 for v,g in zip(s['pg_mw'],c['gen']) if g[7]>0));sm['Qg_at_bound_count']=int(sum(min(abs(v-g[4]),abs(v-g[3]))<=1e-3 for v,g in zip(s['qg_mvar'],c['gen']) if g[7]>0));sm['V_at_bound_count']=int(sum(min(abs(v-b[12]),abs(v-b[11]))<=1e-4 for v,b in zip(s['vm'],c['bus'])))
  if ref is not None:
   sm['active_branch_P_MAE_MW']=float(np.mean([abs(z[k]) for z in br if c['branch'][z['branch_row_1based']-1][10]>0 for k in ['P_error_from','P_error_to']]));sm['active_branch_Q_MAE_MVAr']=None if method=='DC-OPF' else float(np.mean([abs(z[k]) for z in br if c['branch'][z['branch_row_1based']-1][10]>0 for k in ['Q_error_from','Q_error_to']]))
  else:sm['active_branch_P_MAE_MW']=sm['active_branch_Q_MAE_MVAr']=None
  assert {z['bus_id'] for z in bu}=={int(b[0]) for b in c['bus']}
  for j,z in enumerate(br):assert [z['from_bus'],z['to_bus']]==[int(v) for v in c['branch'][j][:2]]
  for target,source in [(busout,bu),(branchout,br),(areaout,ar)]:
   for z in source:z.update(scenario=x['id'],family=x['family'],network=x['network'])
   target+=source
  if method in ['microsoft-v1.1','newer-base-v2']:
   CD=R/x.get('capture_dir',x['source']);md=read(CD/(method+'-metadata.json'));assert md['checkpoint_sha256']==('f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831' if method=='microsoft-v1.1' else '9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7');assert md['leaky_alpha']==0 and md['clip_mode'] in ['clamp','leaky_clip'];assert md['input_sha256']==x['input_sha256'];assert not md['model_input_has_solution'];arows=md['mapping']['gen_source_rows'];assert arows==list(np.flatnonzero(active));assert sorted(md['mapping']['ac_line_source_rows']+md['mapping']['transformer_source_rows'])==list(np.flatnonzero(online))
   if x.get('capture_dir'):assert read(CD/(method+'-native.json'))==s
   audit={k:v for k,v in md.items() if k not in ['mapping','checkpoint_metadata']};audit.update(scenario=x['id'],active_gen_rows_1based=[i+1 for i in arows],excluded_offline_generator_rows_1based=[i+1 for i in range(len(c['gen'])) if not active[i]]);fullaudit.append(audit)
   for capture in read(CD/(method+'-clamps.json'))['captures']:
    var=capture['variable'];scale=1 if var=='V' else c['baseMVA'];key={'Pg':'pg_mw','Qg':'qg_mvar','V':'vm'}[var];ii=list(range(len(c['bus']))) if var=='V' else arows;v=np.array(capture['input']);out=np.array(capture['output']);lo=np.array(capture['lo']);hi=np.array(capture['hi']);assert np.array_equal(np.clip(v,lo,hi),out);assert np.array_equal(out*scale,np.array(s[key])[ii]);delta=(out-v)*scale;threshold=1e-4 if var=='V' else 1e-3;clamps.append({'scenario':x['id'],'method':method,'family':x['family'],'network':x['network'],'variable':var,'elements':len(ii),'strict_count':int(sum(v!=out)),'meaningful_count':int(sum(abs(delta)>threshold)),'lower_count':int(sum(v<lo)),'upper_count':int(sum(v>hi)),'max_abs_change':float(max(abs(delta))),'sum_abs_change':float(sum(abs(delta)))})
    for k,j in enumerate(ii):events.append({'scenario':x['id'],'method':method,'variable':var,'source_row_1based':j+1,'bus_id':int(c['bus'][j][0]) if var=='V' else int(c['gen'][j][0]),'preclip':float(v[k]*scale),'postclip':float(out[k]*scale),'signed_change':float(delta[k]),'clipped':bool(v[k]!=out[k])})
  rows.append(sm)
 gates.append({'scenario':x['id'],'input_hash_pass':True,'reference_valid':ref is not None,'DC_valid':validDC,'exact_Ybus_branch_sum':True,'native_mapping_and_clamp_pass':True})
lookup={(r['scenario'],r['method']):r for r in rows};flat=[]
for r in rows:
 a=r['approximation'];flat.append({k:r.get(k) for k in ['scenario','family','network','reference_valid','reference_status','method','online_generator_count','online_branch_count','objective_raw_original_units','AC_joint_feasible','native_DC_constraints_pass','Pg_max_excess','Qg_max_excess','Vm_max_excess','angle_max_excess_deg','thermal_violating_count','thermal_max_excess_MVA_or_DC_MW','rated_online_branch_count','active_branch_P_MAE_MW','active_branch_Q_MAE_MVAr','Pg_at_bound_count','Qg_at_bound_count','V_at_bound_count']}|{'P_mean':r['P']['mean'],'P_max':r['P']['max'],'Q_mean':None if r['Q'] is None else r['Q']['mean'],'Q_max':None if r['Q'] is None else r['Q']['max']}|{k:None if a is None or a[m] is None else a[m]['mean'] for k,m in [('Pg_MAE','Pg_per_generator_MW'),('Qg_MAE','Qg_per_generator_MVAr'),('Vm_MAE','Vm_pu'),('angle_MAE','aligned_angle_deg')]})
# Compare reference-dependent error directions only when BOTH independent references pass.
deltas=[]
for x in M['scenarios']:
 for method in ['AC-OPF','DC-OPF','microsoft-v1.1','newer-base-v2']:
  a=lookup.get((x['id'],method));b=lookup.get((x['baseline'],method))
  if not a or not b:continue
  d={'scenario':x['id'],'family':x['family'],'network':x['network'],'baseline':x['baseline'],'method':method,'reference_valid':a['reference_valid'],'both_references_valid':a['reference_valid'] and b['reference_valid'],'P_max_change':a['P']['max']-b['P']['max'],'Q_max_change':None if a['Q'] is None else a['Q']['max']-b['Q']['max'],'P_mean_change':a['P']['mean']-b['P']['mean'],'Q_mean_change':None if a['Q'] is None else a['Q']['mean']-b['Q']['mean'],'cost_percent_change':100*(a['objective_raw_original_units']-b['objective_raw_original_units'])/abs(b['objective_raw_original_units']),'thermal_count_change':None if a['thermal_violating_count'] is None else a['thermal_violating_count']-b['thermal_violating_count']}
  for var,metric in [('Pg','Pg_per_generator_MW'),('Qg','Qg_per_generator_MVAr'),('Vm','Vm_pu'),('angle','aligned_angle_deg')]:d[var+'_MAE_change']=None if not d['both_references_valid'] or a['approximation'][metric] is None else a['approximation'][metric]['mean']-b['approximation'][metric]['mean']
  d['Pflow_MAE_change']=None if not d['both_references_valid'] else a['active_branch_P_MAE_MW']-b['active_branch_P_MAE_MW']
  for v in ['Pg','Qg','V']:
   aa=next((z for z in clamps if z['scenario']==x['id'] and z['method']==method and z['variable']==v),None);bb=next((z for z in clamps if z['scenario']==x['baseline'] and z['method']==method and z['variable']==v),None);d[v+'_clip_count_change']=None if aa is None else aa['strict_count']-bb['strict_count']
  deltas.append(d)
# Physically equivalent representation controls: restore baseline row/ID order first.
reprrows=[]
for x in M['scenarios']:
 if x['family']!='representation':continue
 c=cases[x['id']];base=cases[x['baseline']];mapping=x['representation_mapping'];br=mapping['bus_to_base_rows'];gr=mapping['gen_to_base_rows'];er=mapping['branch_to_base_rows'];canon=copy.deepcopy(c)
 for field,perm in [('bus',br),('gen',gr),('gencost',gr),('branch',er)]:
  canon[field]=[None]*len(perm)
  for i,j in enumerate(perm):canon[field][j]=copy.deepcopy(c[field][i])
 if 'relabel_old_to_new' in mapping:
  back={int(v):int(k) for k,v in mapping['relabel_old_to_new'].items()}
  for b in canon['bus']:b[0]=back[int(b[0])]
  for g in canon['gen']:g[0]=back[int(g[0])]
  for b in canon['branch']:b[0]=back[int(b[0])];b[1]=back[int(b[1])]
 assert all(canon[k]==base[k] for k in ['bus','gen','branch','gencost'])
 def restore(s):
  out=copy.deepcopy(s)
  for key,perm in [('vm',br),('va_deg',br),('pg_mw',gr),('qg_mvar',gr),('pf_mw',er),('pt_mw',er)]:
   if s.get(key) is None:continue
   out[key]=[None]*len(perm)
   for i,j in enumerate(perm):out[key][j]=s[key][i]
  return out
 for method in ['AC-OPF','DC-OPF','microsoft-v1.1','newer-base-v2']:
  if (x['id'],method) not in points:continue
  s=restore(points[(x['id'],method)]);b=points[(x['baseline'],method)];rec={'scenario':x['id'],'method':method,'input_physics_equivalence':'EXACT_ALL_MATRICES','Pg_max_difference_MW':float(max(abs(np.array(s['pg_mw'])-b['pg_mw']))),'Qg_max_difference_MVAr':None if method=='DC-OPF' else float(max(abs(np.array(s['qg_mvar'])-b['qg_mvar']))),'Vm_max_difference_pu':None if method=='DC-OPF' else float(max(abs(np.array(s['vm'])-b['vm'])))}
  slack=next(i for i,z in enumerate(base['bus']) if z[1]==3);da=(np.array(s['va_deg'])-s['va_deg'][slack])-(np.array(b['va_deg'])-b['va_deg'][slack]);rec['angle_max_aligned_difference_deg']=float(max(abs((da+180)%360-180)))
  if method!='DC-OPF':
   aterms=terms(base,s);bterms=terms(base,b);rec['flow_P_max_difference_MW']=float(max(abs(np.r_[aterms['sf'].real-bterms['sf'].real,aterms['st'].real-bterms['st'].real])));rec['residual_P_max_difference_MW']=float(max(abs(aterms['r'].real-bterms['r'].real)));rec['residual_Q_max_difference_MVAr']=float(max(abs(aterms['r'].imag-bterms['r'].imag)));actual=terms(c,points[(x['id'],method)]);assert max(abs(aterms['r']-np.array(actual['r'])[np.argsort(br)]))<1e-6
  else:rec['flow_P_max_difference_MW']=float(max(abs(np.array(s['pf_mw'])-b['pf_mw'])))
  reprrows.append(rec)
# Nodal, both-end, clamp and reference-independent records remain separate.
for name,data in [('method-summary.json',rows),('model-audit.json',fullaudit),('gates.json',gates),('representation-controls.json',reprrows)]:save(O/name,data)
for name,data in [('method-summary.csv',flat),('paired-contrasts.csv',deltas),('clipping-summary.csv',clamps),('clipping-events.csv',events),('bus-metrics.csv',busout),('branch-flows.csv',branchout),('area-exchange.csv',areaout)]:csvsave(O/name,data)
for z in read(O/'prior-artifacts.json'):assert sha(R/z['path'])==z['sha256'],z['path']
audit=[]
for name in ['GENOUT-300','TIEOUT-600']:
 for rel in ['microsoft-v1.1','newer-base-v2']:
  a=read(O/name/(rel+'-label-invariance.json'));assert a['status']=='PASS';audit.append({'scenario':name,'release':rel,**a})
save(O/'new-active-set-label-audits.json',audit)
summary={'status':'PASS','inputs':len(entries),'new_inputs':len(newids),'reused_inputs':len(reuse),'reference_valid':sum(g['reference_valid'] for g in gates),'reference_unknown':[g['scenario'] for g in gates if not g['reference_valid']],'DC_own_constraints_pass':sum(g['DC_valid'] for g in gates),'native_states':sum(r['method'] in ['microsoft-v1.1','newer-base-v2'] for r in rows),'native_joint_feasible':sum(r['AC_joint_feasible'] is True for r in rows if r['method'] in ['microsoft-v1.1','newer-base-v2']),'prior_files_unchanged':len(read(O/'prior-artifacts.json')),'new_active_set_label_audits':len(audit),'finished_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()};save(O/'verification.json',summary);print('VERIFIED',summary,flush=True)
