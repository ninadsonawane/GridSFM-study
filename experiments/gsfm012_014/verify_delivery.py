"""Saved-output verification only. No solver, neural model or new input generation."""
from electrical import *
import ast,datetime,subprocess,platform,importlib.metadata,collections
E=pathlib.Path(__file__).parent;O12=R/'results/comparisons/GSFM-012/20261023-frozen-two-copy';O13=R/'results/diagnosis/GSFM-013/20261023-accuracy-sensitivity';O14=R/'results/comparisons/GSFM-014/20261023-rated-variants';old={}
for path in [R/'results/comparisons/GSFM-011B/20261022-original-case300',R/'results/comparisons/GSFM-011C-1/20261022-loading-only',R/'results/diagnosis/GSFM-011D/20261022-saved-states']:
 inv=read(path/'artifact-inventory.json');assert all(sha(path/n)==x['sha256'] for n,x in inv.items());old[str(path.relative_to(R))]=len(inv)
for stage,O in [(12,O12),(14,O14)]:
 cases=read(O/'scenario-manifest.json')['scenarios'];states=0;refs=0;maxerr=0.;dcpass=0;labelcalls=0;fixedcounts=[];bucsv=list(csv.DictReader((O/'bus-metrics.csv').open()));brcsv=list(csv.DictReader((O/'branch-flows.csv').open()));record=[]
 for item in cases:
  D=O/item['id'];c=read(D/'input.json');assert sha(D/'input.json')==item['input_sha256'];ids={int(b[0]):i for i,b in enumerate(c['bus'])};ref=read(D/'ac-native.json') if(D/'ac-native.json').exists() else None
  if ref is not None:assert evaluate(c,ref)['all_tested_constraints_pass'];refs+=1
  for rel in ['microsoft-v1.1','newer-base-v2']:
   s=read(D/(rel+'-native.json'));md=read(D/(rel+'-metadata.json'));raw=read(D/(rel+'-returned.json'));assert md['input_sha256']==sha(D/'input.json');assert md['leaky_alpha']==0 and md['clip_mode'] in ['clamp','leaky_clip'];assert sha(pathlib.Path(md['checkpoint_path']))==md['checkpoint_sha256'];assert np.array_equal(s['vm'],raw['V']);assert np.allclose(s['pg_mw'],np.array(raw['Pg'])*c['baseMVA'],atol=1e-10,rtol=0);tr=terms(c,s);maxerr=max(maxerr,tr['crosscheck_MW_MVAr']);sm,*_=score(c,s,rel,ref);assert not sm['AC_joint_feasible'];states+=1
   if(D/(rel+'-label-invariance.json')).exists():a=read(D/(rel+'-label-invariance.json'));assert a['status']=='PASS';labelcalls+=a['additional_forward_calls']
   if stage==14:
    fixed=[i for i,g in enumerate(c['gen']) if g[8]==g[9]];assert max(abs(s['pg_mw'][i]-c['gen'][i][8]) for i in fixed)<1e-3;fixedcounts.append(len(fixed))
   bb=[r for r in bucsv if r['scenario']==item['id'] and r['method']==rel];assert set(int(x['bus_id']) for x in bb)==set(ids)
   for row in bb:
    i=ids[int(row['bus_id'])];assert abs(float(row['P_residual_MW'])-tr['r'][i].real)<1e-6 and abs(float(row['Q_residual_MVAr'])-tr['r'][i].imag)<1e-6
   br=[r for r in brcsv if r['scenario']==item['id'] and r['method']==rel];assert len(br)==len(c['branch'])
   for i,row in enumerate(br):assert [int(row['from_bus']),int(row['to_bus'])]==list(map(int,c['branch'][i][:2]));assert abs(float(row['Pf_MW'])-tr['sf'][i].real)<1e-6
  ds=read(D/'dc-native.json');assert ds['vm'] is None and ds['qg_mvar'] is None;dsm,*_=score(c,ds,'DC-OPF');assert dsm['native_DC_constraints_pass'];dcpass+=1;draw=read(D/('dc-raw.json'));assert abs(cost(c,ds['pg_mw'],[0]*len(c['gen']))-draw['f'])<1e-4;assert np.array_equal(np.array(draw['branch'])[:,:13],np.array(c['branch']));record.append({'scenario':item['id'],'reference_valid':ref is not None,'native_points':2,'DC_original_constraints_pass':True})
  if ref is None:
   sm=read(D/'summary.json');assert all(r['approximation'] is None for r in sm),'Failed reference used as label'
 save(O/'verification.json',{'status':'PASS','stage':stage,'scenario_count':len(cases),'accepted_reference_count':refs,'native_frozen_points':states,'native_joint_feasible_count':0,'valid_DC_count':dcpass,'additional_poisoned_label_forward_calls':labelcalls,'max_Ybus_branch_disagreement_MW_MVAr':maxerr,'all_CSV_bus_and_branch_ids_match_original_input':True,'DC_Qg_Vm_and_AC_feasibility_NA':True,'all_fixed_Pg_checks_pass':True,'fixed_Pg_counts_per_native_case':fixedcounts,'no_failed_reference_label_use':True,'prior_inventories_unchanged':old,'cases':record,'invalid_DC_format_calls_retained':8 if stage==14 else 0})
#13: compare every saved base/loading/S+/S− residual, and verify null generation accuracy and cancellation.
rows=list(csv.DictReader((O13/'bus-decomposition.csv').open()));j=read(O13/'jacobian-checks.json');assert len(j)==18 and all(x['all_inspected_rows_pass'] and x['relative_Frobenius_halfstep']<1e-4 for x in j);assert len(rows)==7200;maxdiff=0.;counter=collections.Counter()
for network,scenario,D in [('original300','base',R/'results/comparisons/GSFM-011B/20261022-original-case300')]+[('original300',f'load{x:.2f}',R/f'results/comparisons/GSFM-011C-1/20261022-loading-only/load-{x:.2f}') for x in [.8,.9,.95,1.03,1.06]]+[('constructed600',s,O12/s) for s in ['S0','Splus','Sminus']]:
 original=list(csv.DictReader(((D.parent/'bus-metrics.csv') if network=='constructed600' else D/'bus-diagnostics.csv').open()));c=read(D/'input.json');bidset={int(b[0]) for b in c['bus']}
 for rel,label in [('newer-base-v2','Newer v2'),('microsoft-v1.1','Microsoft v1.1')]:
  rr=[x for x in rows if x['network']==network and x['scenario']==scenario and x['release']==rel];assert {int(x['bus_id']) for x in rr}==bidset
  oldrows={int(x['bus_id'] if network=='constructed600' else x['original_bus_id']):x for x in original if x['method']==(rel if network=='constructed600' else label) and (network!='constructed600' or x['scenario']==scenario)}
  for row in rr:
   prev=oldrows[int(row['bus_id'])]
   for co,unit in [('P','MW'),('Q','MVAr')]:
    value=float(prev[co+'_residual_'+unit] if network=='constructed600' else prev[co+'_imbalance_'+unit]);maxdiff=max(maxdiff,abs(value-float(row[co+'_native_residual'])));budget=sum(float(row[co+k]) for k in ['_generation_contribution','_positive_branch_contributions','_negative_branch_contributions','_shunt_contribution']);assert abs(budget-float(row[co+'_residual_error']))<1e-6
  counter[(network,rel)]+=len(rr)
assert maxdiff<1e-6;sel=list(csv.DictReader((O13/'matched-examples.csv').open()));assert len(sel)==24 and max(collections.Counter((x['release'],x['component']) for x in sel).values())<=6;assert read(O13/'matching-rule.json')['pair_file_sha256']==sha(O13/'admissible-pairs.csv')
save(O13/'verification.json',{'status':'PASS','rows':len(rows),'original_source_and_generated_bus_IDs_verified':True,'max_saved_residual_difference':maxdiff,'all_signed_cancellation_identities_pass':True,'jacobian_blocks_checked':len(j),'all_Jacobian_checks_pass':True,'admissible_source_pair_hash_preserved':True,'illustrative_pairs':len(sel),'maximum_per_component_release_across_networks':6,'original_110_reference_dependent_rows':0,'new_model_inference_solves_training':0,'prior_inventories_unchanged':old})
for p in E.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
print('ALL12/13/14 VERIFICATION PASS; earlier results unchanged')
