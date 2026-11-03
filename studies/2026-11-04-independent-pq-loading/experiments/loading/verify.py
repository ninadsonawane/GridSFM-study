"""Independent saved-state audit and final reproducibility inventory."""
from study import *
from physics_metrics import evaluate as independent
def verify():
 plan=read(ROOT/'scenario-plan.json');dirs=[ROOT/'results'/x for x in plan['baseline_ids']]+[ROOT/'results'/s['id'] for s in plan['scenarios']]
 counts={'inputs':len(dirs),'AC_checked':0,'AC_UNKNOWN':0,'DC_own_pass':0,'native_states':0,'native_AC_pass':0};unknown=[];native_worst=0;reference_worst=0;zero_dc_q=[]
 for d in dirs:
  c=read(d/'input.json');spec=next((s for s in plan['scenarios'] if s['id']==d.name),None)
  if spec:assert sha(d/'input.json')==spec['input_sha256'];assert np.array_equal(c['gen'],read(ROOT/'cases'/spec['network']/'base.json')['gen']);assert np.array_equal(c['branch'],read(ROOT/'cases'/spec['network']/'base.json')['branch'])
  ac=read(d/'ac-status.json');counts['AC_checked' if ac['reference_valid'] else 'AC_UNKNOWN']+=1
  if not ac['reference_valid']:
   attempt_details=[]
   for i,a in enumerate(ac['attempts']):
    s=read(d/f'ac-attempt{i}-state.json');tr=terms(c,s);bad=np.flatnonzero(abs(tr['r'].imag)>1e-3)
    attempt_details.append({'attempt':i,'solver_status':a.get('solver_status'),'Q_violating_buses':[{'bus_id':int(c['bus'][j][0]),'Q_residual_MVAr':float(tr['r'][j].imag)} for j in bad],'P_max_MW':max(abs(tr['r'].real)),'Q_max_MVAr':max(abs(tr['r'].imag)),'interpretation':'Local infeasibility status under two starts; no global infeasibility certificate.'})
   unknown.append({'scenario':d.name,'attempts':attempt_details})
  for method,fn in [('AC-OPF','ac-native.json'),('DC-OPF','dc-native.json')]+[(r,r+'-native.json') for r,_,_ in REL]:
   if not (d/fn).exists():assert method=='AC-OPF' and not ac['reference_valid'];continue
   s=read(d/fn);m,*_=evaluate(c,s,method)
   if method=='DC-OPF':assert read(d/'dc-status.json')['solver_success'];counts['DC_own_pass']+=int(m['DC_own_constraints_pass']);assert s['vm'] is None and s['qg_mvar'] is None;continue
   other=independent(c,s);assert other['all_tested_constraints_pass']==m['AC_joint_pass'],(d.name,method,other)
   if method=='AC-OPF':assert m['AC_joint_pass'];reference_worst=max(reference_worst,m['P_balance_MW']['max_abs'],m['Q_balance_MVAr']['max_abs'])
   else:
    counts['native_states']+=1;counts['native_AC_pass']+=int(m['AC_joint_pass']);md=read(d/(method+'-metadata.json'));assert md['native_saved_before_evaluation'] and not md['model_input_has_solution'] and not md['additional_PF_or_OPF'];assert md['mapping']['bus_external_ids']==[int(b[0]) for b in c['bus']];assert md['mapping']['gen_source_rows']==[i for i,g in enumerate(c['gen']) if g[7]>0]
    raw=read(d/(method+'-returned.json'));assert np.array_equal(s['vm'],raw['V']);assert np.allclose(s['va_deg'],np.rad2deg(raw['theta']),rtol=0,atol=1e-12)
    for key,rkey in [('pg_mw','Pg'),('qg_mvar','Qg')]:assert np.array_equal(np.array(s[key])[md['mapping']['gen_source_rows']],np.array(raw[rkey])*c['baseMVA'])
  # State errors stay N/A when no valid AC reference exists.
  if not ac['reference_valid']:
   assert all(all(v is None for v in m.get('accuracy',{}).values()) for m in read(d/'metrics.json'))
 # A Q-only perturbation cannot affect this fixed native DC problem.
 for net in ['case300','case300x2','case500goc']:
  base=read(ROOT/'results'/f'{net}-base/dc-native.json')
  for spec in plan['scenarios']:
   if spec['network']==net and spec['group'] in ['Q','sensitivity-Q']:
    s=read(ROOT/'results'/spec['id']/'dc-native.json');err=max(np.max(abs(np.array(s[k])-base[k])) for k in ['pg_mw','va_deg','pf_mw','pt_mw']);assert err<1e-8;zero_dc_q.append({'scenario':spec['id'],'maximum_DC_array_difference':err})
 save(ROOT/'paper/reference-failure-investigation.json',unknown)
 result={'status':'PASS','verified_UTC':now(),'counts':counts,'maximum_accepted_reference_balance_residual_MW_MVAr':reference_worst,'independent_evaluator_agreement':True,'raw_native_mapping_verified':True,'Q_only_DC_invariance':zero_dc_q,'reference_failures_retained':unknown,'limitations':['Training scenario overlap is not recoverable from checkpoint metadata; see training-exposure.json.','Only fixed original order and the selected releases are evaluated.','No global infeasibility or optimality certificates.']}
 save(ROOT/'final-verification.json',result);print(json.dumps({k:v for k,v in result.items() if k in ['status','counts','maximum_accepted_reference_balance_residual_MW_MVAr']}))
 inventory={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*') if p.is_file() and p.name!='artifact-sha256.json' and '__pycache__' not in p.parts}
 save(ROOT/'artifact-sha256.json',inventory)
if __name__=='__main__':verify()
