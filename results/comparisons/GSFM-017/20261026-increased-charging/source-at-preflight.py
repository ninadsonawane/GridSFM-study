"""GSFM-017: one predeclared positive-charging increase; reuse GSFM-015 workers."""
import sys, pathlib, copy, json, subprocess, datetime, platform, hashlib, os
R=pathlib.Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study')
sys.path.insert(0,str(R/'experiments/gsfm015'))
from electrical import read,save,sha,csvsave,score,terms,evaluate,np
O=R/'results/comparisons/GSFM-017/20261026-increased-charging'
OLD=R/'results/comparisons/GSFM-015/20261023-load-location-charging'
REL=['microsoft-v1.1','newer-base-v2']; NAME='C300-L0.90-B1.50'
def prepare():
 assert not O.exists(),'Never overwrite an existing run'
 O.mkdir(parents=True); D=O/NAME;D.mkdir()
 prior=[]
 for root in [R/'results/comparisons/GSFM-015',R/'results/comparisons/GSFM-016']:
  for p in sorted(root.rglob('*')):
   if p.is_file():prior.append({'path':str(p.relative_to(R)),'sha256':sha(p)})
 save(O/'prior-artifacts.json',prior)
 c=read(OLD/'G300-0.90/input.json');new=copy.deepcopy(c)
 changed=[]
 for i,b in enumerate(new['branch']):
  if b[4]>0:b[4]*=1.5;changed.append(i+1)
 assert len(c['bus'])==300 and len(c['gen'])==69 and len(c['branch'])==411
 for k in c:
  if k!='branch':assert c[k]==new[k],k
 for a,b in zip(c['branch'],new['branch']):
  assert all(a[j]==b[j] for j in range(len(a)) if j!=4)
  assert b[4]==(a[4]*1.5 if a[4]>0 else a[4])
 assert all(b[5]==0 for b in new['branch'])
 save(D/'input.json',new)
 row={'id':NAME,'family':'increased-positive-charging','network':'300','load_scale':.90,'positive_charging_factor':1.50,'changed_branch_rows':changed,'input_sha256':sha(D/'input.json')}
 save(O/'scenario-manifest.json',{'experiment':17,'scenarios':[row],'fixed_before_outcomes':True,'started_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'parent_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'hardware':platform.platform(),'cpu':subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),'memory_bytes':subprocess.check_output(['sysctl','-n','hw.memsize'],text=True).strip(),'base_input':str((OLD/'G300-0.90/input.json').relative_to(R)),'base_input_sha256':sha(OLD/'G300-0.90/input.json'),'original_source_manifest_sha256':sha(R/'manifests/matpower-source.json'),'only_change_vs_saved_90pct_input':'strictly positive branch total charging b multiplied by 1.50','base_equations':'unchanged original FP64 branch/Ybus equations, applied to disclosed charging intervention','training_PF_OPF_repair':False})
 files=[pathlib.Path(__file__)]+[R/'experiments/gsfm015'/x for x in ['run_cases.py','run_model.py','run_dc.py','solver_server.jl','electrical.py']]+[R/'scripts/python'/x for x in ['physics_metrics.py','gridsfm_convert.py']]
 save(O/'source-code-hashes.json',[{'path':str(p.relative_to(R)),'sha256':sha(p)} for p in files])
 print('PREPARED',NAME,'changed positive-charging rows',len(changed),'prior files',len(prior),flush=True)
def report():
 rows=[];buses=[];branches=[];clamps=[];gates=[]
 scenarios=[('50%',OLD/'C300-L0.90-B0.50'),('100%',OLD/'G300-0.90'),('150%',O/NAME)]
 for label,D in scenarios:
  c=read(D/'input.json');ref=read(D/'ac-native.json') if (D/'ac-native.json').exists() else None
  if ref is not None:assert evaluate(c,ref)['all_tested_constraints_pass'];terms(c,ref)
  for method in ['AC-OPF','DC-OPF']+REL:
   file={'AC-OPF':'ac-native.json' if ref is not None else 'ac-failed-iterate.json','DC-OPF':'dc-native.json'}.get(method,method+'-native.json')
   if not (D/file).exists():continue
   s=read(D/file);sm,bu,br,_=score(c,s,method,ref);sm.update(charging=label,reference_valid=ref is not None,artifact_directory=str(D.relative_to(R)))
   if method=='DC-OPF':assert sm['native_DC_constraints_pass']
   else:
    sm['Qg_at_bound_count']=sum(min(abs(q-g[4]),abs(q-g[3]))<=1e-3 for q,g in zip(s['qg_mvar'],c['gen']))
    sm['Qg_at_lower_count']=sum(abs(q-g[4])<=1e-3 for q,g in zip(s['qg_mvar'],c['gen']))
    sm['Qg_at_upper_count']=sum(abs(q-g[3])<=1e-3 for q,g in zip(s['qg_mvar'],c['gen']))
    sm['total_Qg_MVAr']=sum(s['qg_mvar']); sm['total_branch_Q_MVAr']=float(terms(c,s)['sf'].imag.sum()+terms(c,s)['st'].imag.sum())
    for which,key in [('P','P_residual_MW'),('Q','Q_residual_MVAr')]:
     worst=max(bu,key=lambda x:abs(x[key]));sm[which+'_worst_bus']=worst['bus_id']
   rows.append(sm)
   for dest,src in [(buses,bu),(branches,br)]:
    for x in src:x['charging']=label
    dest.extend(src)
   if method in REL:
    md=read(D/(method+'-metadata.json'));assert md['input_sha256']==sha(D/'input.json');assert md['model_input_has_solution'] is False and md['additional_PF_or_OPF'] is False and md['leaky_alpha']==0
    captures=read(D/(method+'-clamps.json'))['captures']
    for x in captures:
     a=np.array(x['input']);z=np.array(x['output']);lo=np.array(x['lo']);hi=np.array(x['hi']);assert np.array_equal(np.clip(a,lo,hi),z)
     scale=1 if x['variable']=='V' else c['baseMVA'];tol=1e-4 if x['variable']=='V' else 1e-3
     clamps.append({'charging':label,'method':method,'variable':x['variable'],'strict_clipped_count':int(sum(a!=z)),'physically_meaningful_clipped_count':int(sum(abs(a-z)*scale>tol)),'lower_clipped_count':int(sum(a<lo)),'upper_clipped_count':int(sum(a>hi)),'elements':len(a)})
  gates.append({'charging':label,'reference_valid':ref is not None,'physics_Ybus_branch_sum_pass':True,'native_predictions_before_evaluation_and_unmodified':True})
 # Branch charging is absent from the audited DC equations; require an exact null response.
 base=read(OLD/'G300-0.90/dc-native.json');new=read(O/NAME/'dc-native.json')
 assert base==new,'Unexpected DC response to charging-only change'
 for p in read(O/'prior-artifacts.json'):assert sha(R/p['path'])==p['sha256'],p['path']
 for p in read(O/'source-code-hashes.json'):assert sha(R/p['path'])==p['sha256'],p['path']
 save(O/'method-summary.json',rows);csvsave(O/'bus-metrics.csv',buses);csvsave(O/'branch-flows.csv',branches);csvsave(O/'clipping-summary.csv',clamps)
 flat=[]
 for s in rows:
  a=s['approximation'];rec={k:s.get(k) for k in ['charging','method','reference_valid','AC_joint_feasible','native_DC_constraints_pass','P_violating_buses','Q_violating_buses','Pg_violating_count','Qg_violating_count','Vm_violating_count','angle_violating_count','thermal_violating_count','Qg_at_bound_count','Qg_at_lower_count','Qg_at_upper_count','total_Qg_MVAr','total_branch_Q_MVAr','P_worst_bus','Q_worst_bus']}
  for v in ['P','Q']:
   for stat in ['mean','median','p95','max']:rec[v+'_'+stat]=None if s[v] is None else s[v][stat]
  for v,k in [('Pg','Pg_per_generator_MW'),('Qg','Qg_per_generator_MVAr'),('Vm','Vm_pu'),('angle','aligned_angle_deg'),('Pflow','branch_P_MW')]:rec[v+'_MAE']=None if a is None or a[k] is None else a[k]['mean']
  flat.append(rec)
 csvsave(O/'method-summary.csv',flat)
 save(O/'verification.json',{'status':'PASS','new_inputs':1,'reused_inputs':2,'new_native_model_predictions':2,'all_prior_files_unchanged':len(read(O/'prior-artifacts.json')),'DC_native_exactly_unchanged_vs100pct_charging':True,'gates':gates,'thermal':'N/A: original case300 RATE_A all zero','numerical_failure_policy':'UNKNOWN, never proof of infeasibility','completed_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 lines=['# Experiment17 — increased positive branch charging at90% case300 loading','','One new intervention: strictly positive original branch charging multiplied by1.50. Reuse50% and100% points fromExperiment15; all loads remain90% oforiginal. No other parameter changes, training, PF completion or OPF repair. These are synthetic parameter interventions, not physical line replacement.','','## Accuracy against independently validated AC local references','','| Charging | Method | Pg MAE MW | Qg MAE MVAr | Vm MAE pu | Angle MAE deg | Both-end active-flow MAE MW |','|---|---|---:|---:|---:|---:|---:|']
 def fmt(v):return 'N/A' if v is None else f'{v:.6g}'
 for s in flat:lines.append('| '+' | '.join([s['charging'],s['method']]+[fmt(s[k]) for k in ['Pg_MAE','Qg_MAE','Vm_MAE','angle_MAE','Pflow_MAE']])+' |')
 lines+=['','## Native physical validity and reactive constraint activity','','DC P residual is its own DC-law residual; DC Q/Vm and AC joint feasibility are N/A. Model flows are derived from nativeVm/theta using exact AC physics. Thermal assessmentN/A on every point. Counts use1e-3MW/MVAr balance and generator tolerance,1e-4pu Vm,1e-3degree angle tolerance. Qbound activity within1e-3MVAr is NOT a violation.','','| Charging | Method | Max P MW | Max Q MVAr | Mean Q MVAr | P/Q violating buses | Pg/Qg/Vm violations | Q lower/upper-bound activity | AC joint feasible |','|---|---|---:|---:|---:|---|---|---|---|']
 for s in flat:
  lines.append('| '+' | '.join([s['charging'],s['method'],fmt(s['P_max']),fmt(s['Q_max']),fmt(s['Q_mean']),str(s['P_violating_buses'])+'/'+str(s['Q_violating_buses'] if s['Q_violating_buses'] is not None else 'N/A'),'/'.join(str(s[k]) if s[k] is not None else 'N/A' for k in ['Pg_violating_count','Qg_violating_count','Vm_violating_count']),str(s['Qg_at_lower_count'])+'/'+str(s['Qg_at_upper_count']) if s['Qg_at_bound_count'] is not None else 'N/A',str(s['AC_joint_feasible']) if s['AC_joint_feasible'] is not None else 'N/A'])+' |')
 lines+=['','## Genuine clipping events','','| Charging | Release | Pg | Qg | Vm |','|---|---|---:|---:|---:|']
 for lab,_ in scenarios:
  for rel in REL:lines.append('| '+' | '.join([lab,rel]+[str(next(x['strict_clipped_count'] for x in clamps if x['charging']==lab and x['method']==rel and x['variable']==v)) for v in ['Pg','Qg','V']])+' |')
 lines+=['','Counts observe actual shipped clamp input/output without modifying inference. Complete residual distributions, worst originalbus IDs, approximation errors and constraint counts are inmethod-summary.csv/json; signed perbus terms inbus-metrics.csv.','','## Reproduction and provenance','','```sh','PYTHONDONTWRITEBYTECODE=1 ../GridSFM/model/.venv/bin/python -B experiments/gsfm017/study.py prepare','PYTHONDONTWRITEBYTECODE=1 ../GridSFM/model/.venv/bin/python -B experiments/gsfm015/run_cases.py results/comparisons/GSFM-017/20261026-increased-charging 17','PYTHONDONTWRITEBYTECODE=1 ../GridSFM/model/.venv/bin/python -B experiments/gsfm017/study.py report','```','','prepare refuses existing output paths; reproduce in a new uniquely named output by changingO. Solver argv/options/termination and failures retained inrun-status.json and scenario directory; source/input/checkpoint hashes in manifests and modelmetadata. Same pinned sources/checkpoints and default clipping asExperiment15. CPU execution, no solver speed claim. Raw inputs, native tensors and solver logs arelocal-only; sha256 inventory identifies allfiles. Compact reports/CSV/code are reviewable.','','Unresolved row-order sensitivity fromExperiment16 still limits causal interpretation. Results concern these frozen native releases, not the later paper\'s trained control-plus-Newton workflow. No outcome-selected settings or additional scenarios. Stop afterthis one input.']
 (O/'README.md').write_text('\n'.join(lines)+'\n')
 inventory=[{'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(O.rglob('*')) if p.is_file() and p.name!='artifact-sha256.json']
 save(O/'artifact-sha256.json',inventory)
 print(json.dumps(flat,indent=2));print('VERIFICATION PASS',flush=True)
if __name__=='__main__':{'prepare':prepare,'report':report}[sys.argv[1]]()
