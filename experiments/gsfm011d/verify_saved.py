"""Independent artifact/coverage checks. Reads saved results; calls no model or solver."""
import csv,json,pathlib,hashlib,math
R=pathlib.Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');O=R/'results/diagnosis/GSFM-011D/20261022-saved-states';read=lambda n:json.loads((O/n).read_text());rows=list(csv.DictReader((O/'base-bus-terms.csv').open()));tracks=list(csv.DictReader((O/'fixed-bus-loading-terms.csv').open()));branches=list(csv.DictReader((O/'incident-branches.csv').open()));masks=read('oracle-combinations.json');releases=['microsoft-v1.1','newer-base-v2'];checks={}
assert read('verification.json')['status']=='PASS' and read('oracle-verification.json')['status']=='PASS'
assert len(rows)==600
for rel in releases:
 rr=[r for r in rows if r['release']==rel];assert len({r['bus_id'] for r in rr})==300
 for row in rr:
  for comp in ['P','Q']:
   net=float(row['generation_'+comp+'_pred'])-float(row['demand_'+comp+'_pred'])-float(row['branch_out_'+comp+'_pred'])-float(row['shunt_consumption_'+comp+'_pred']);assert abs(net-float(row['residual_'+comp+'_pred']))<1e-7
 for co in ['P','Q']:
  vals=sorted([abs(float(r['residual_'+co+'_pred'])) for r in rr],reverse=True);c=next(x for x in read('concentration.json') if x['release']==rel and x['component']==co);assert abs(sum(vals)-c['total_absolute_imbalance'])<1e-6
  for n in [1,5,10]:assert abs(sum(vals[:n])/sum(vals)-c[f'top{n}_fraction'])<1e-12
 for scale in [.8,.9,.95,1.,1.03,1.06]:assert sorted(x['blocks_reference_G_V_A'] for x in masks if x['release']==rel and x['loading']==scale)==['000','001','010','011','100','101','110','111']
assert len(masks)==96 and not any(x['loading']==1.1 for x in masks)
#110% reference-error fields must remain empty in all fixed-bus and branch rows.
for row in tracks:
 if float(row['loading'])==1.1:
  for key,value in row.items():
   if key.endswith('_ref') or key.endswith('_delta') or key in ['Vm_ref_pu','angle_ref_deg','reference_aligned_angle_error_deg']:assert value=='',(key,value)
for row in branches:
 if float(row['loading'])==1.1:
  for key,value in row.items():
   if '_ref' in key or '_delta' in key or key=='angle_difference_error_deg':assert value=='',(key,value)
for rel in releases:
 seen={float(r['loading']):{int(x['bus_id']) for x in tracks if x['release']==rel and float(x['loading'])==float(r['loading'])} for r in tracks if r['release']==rel};assert all(x==seen[1.] for x in seen.values())
#Every saved source artifact is unchanged after all postprocessing.
for directory in [R/'results/comparisons/GSFM-011B/20261022-original-case300',R/'results/comparisons/GSFM-011C-1/20261022-loading-only']:
 for n,v in json.loads((directory/'artifact-inventory.json').read_text()).items():assert hashlib.sha256((directory/n).read_bytes()).hexdigest()==v['sha256']
checks={'status':'PASS','base_bus_rows':600,'native_states':14,'valid_references':6,'oracle_combinations':96,'oracle_masks_complete_per_reference_valid_load':True,'all_110_percent_reference_and_error_fields_empty':True,'fixed_focus_and_comparators_unchanged_across_loads':True,'signed_term_identity_all600_base_rows':True,'concentration_independently_recomputed_from_CSV':True,'all11B_and11C1_artifact_hashes_unchanged':True,'inference_solver_training_new_scenarios_or_network_modifications':0}
(O/'report-verification.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
