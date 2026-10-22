"""Evaluate already returned states, including failed AC iterates; NO solver/model call."""
import pathlib,sys,json,math
R=pathlib.Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');D=pathlib.Path(sys.argv[1]);raw=json.loads((D/'ac-result.json').read_text());c=json.loads((D/'input.json').read_text())
if not (D/'ac-native.json').exists():
 s=raw['solution'];point={'vm':[s['bus'][str(int(b[0]))]['vm'] for b in c['bus']],'va_deg':[math.degrees(s['bus'][str(int(b[0]))]['va']) for b in c['bus']],'pg_mw':[s['gen'][str(i+1)]['pg']*100 for i in range(69)],'qg_mvar':[s['gen'][str(i+1)]['qg']*100 for i in range(69)]};(D/'ac-native.json').write_text(json.dumps(point,indent=2)+'\n')
valid=raw['termination_status']=='LOCALLY_SOLVED'
source=(R/'experiments/gsfm011c1/evaluate.py').read_text()
source=source.replace("if method=='AC-OPF':assert m['all_tested_constraints_pass']", "if method=='AC-OPF' and reference_valid:assert m['all_tested_constraints_pass']")
source=source.replace("approx.append(ar);physical.append(ph)", "\n if not reference_valid:\n  for key in ['Pg_MW','aligned_angle_deg','active_branch_flow_MW_both_ends','Qg_MVAr','Vm_pu']:ar[key]=None\n  ar['reference_status']='UNAVAILABLE: '+reference_status\n ph['solver_status']=reference_status if method=='AC-OPF' else ('CONVERGED' if isdc else 'NATIVE_RETURNED')\n approx.append(ar);physical.append(ph)")
source=source.replace("'aligned_angle_error_deg':float(angle[i])", "'aligned_angle_error_deg':float(angle[i]) if reference_valid else None")
source=source.replace("'from_error_MW':float(fp[j]-rP[j]),'to_error_MW':float(fp[j+411]-rP[j+411])", "'from_error_MW':float(fp[j]-rP[j]) if reference_valid else None,'to_error_MW':float(fp[j+411]-rP[j+411]) if reference_valid else None")
source=source.replace("'AC_reference_independently_feasible':True", "'AC_reference_independently_feasible':reference_valid,'reference_solver_status':reference_status")
# A failed iterate is used only to keep the unchanged calculation path operable;
# every reference-dependent metric and diagnostic is nulled before output.
exec(compile(source,'audited-11B-evaluator-failure-aware','exec'),{'__name__':'__main__','reference_valid':valid,'reference_status':raw['termination_status']})

if not valid:
 p=D/'verification.json';v=json.loads(p.read_text())
 for method in v['methods'].values():
  for key in ['unaligned_to_aligned_angle_max_deg','angle_wrapping_changed_error_max_deg']:
   if key in method:method[key]=None
 p.write_text(json.dumps(v,indent=2)+'\n')
