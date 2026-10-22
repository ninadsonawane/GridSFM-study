import pathlib,json,hashlib,csv,sys,os,statistics
R=pathlib.Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');O=pathlib.Path(os.environ.get('GSFM011C1_OUTPUT',str(R/'results/comparisons/GSFM-011C-1/20261022-loading-only')));B=R/'results/comparisons/GSFM-011B/20261022-original-case300';E=R/'experiments/gsfm011c1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());save=lambda p,v:p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
assert all(sha(B/n)==v['sha256'] for n,v in read(B/'artifact-inventory.json').items()),'11B artifacts changed'
rowsA=[];rowsP=[];locs={};verification={};statuses=read(O/'run-status.json');assert len(statuses)==24
for scale in [.8,.9,.95,1.,1.03,1.06,1.1]:
 d=B if scale==1 else O/f'load-{scale:.2f}';a=read(d/'approximation.json');p=read(d/'physical-validity.json');v=read(d/'verification.json');assert v['status']=='PASS';locs[str(scale)]=read(d/'worst-locations.json');verification[str(scale)]=v
 if scale!=1:
  assert read(d/'dc-status.json')['success']
 for r in a:rowsA.append(dict(loading=scale,base_reused=scale==1,**r))
 for r in p:rowsP.append(dict(loading=scale,base_reused=scale==1,**r))
save(O/'approximation.json',rowsA);save(O/'physical-validity.json',rowsP);save(O/'worst-locations.json',locs)
for name,rows in [('approximation.csv',rowsA),('physical-validity.csv',rowsP)]:
 fields=list(dict.fromkeys(k for r in rows for k in r))
 with (O/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fields,lineterminator="\n");w.writeheader();w.writerows({k:json.dumps(v) if isinstance(v,dict) else v for k,v in r.items()} for r in rows)
thresholds={str(t):{method:sum(p['max_P_imbalance_MW']<=t and p['max_Q_imbalance_MVAr']<=t for p in rowsP if p['method']==method) for method in ['AC-OPF','Microsoft v1.1','Newer v2']} for t in [.001,.01,.1]};save(O/'threshold-sensitivity.json',{'balance_only_pass_counts_including_reused_base':thresholds,'denominator_per_method':7,'primary_threshold_unchanged':.001})
summary={}
for method in ['AC-OPF','DC-OPF','Microsoft v1.1','Newer v2']:
 a=[x for x in rowsA if x['method']==method];p=[x for x in rowsP if x['method']==method];summary[method]={}
 for k,vals in [('Pg_MAE_MW',[x['Pg_MW']['MAE'] for x in a if x['Pg_MW'] is not None]),('max_P_imbalance_MW',[x['max_P_imbalance_MW'] for x in p]),('max_Q_imbalance_MVAr',[x['max_Q_imbalance_MVAr'] for x in p if x['max_Q_imbalance_MVAr'] is not None])]:
  if vals:
   vals=sorted(vals);import numpy as np;summary[method][k]={'n':len(vals),'minimum':min(vals),'median':statistics.median(vals),'p95_linear':float(np.percentile(vals,95)),'maximum':max(vals)}
save(O/'scenario-summary.json',summary)
paired=[]
for a in rowsA:
 if a['method'] in ['Microsoft v1.1','Newer v2'] and a['Pg_MW'] is not None:
  dc=next(x for x in rowsA if x['loading']==a['loading'] and x['method']=='DC-OPF');paired.append({'loading':a['loading'],'method':a['method'],'Pg_MAE_difference_vs_DC_MW':a['Pg_MW']['MAE']-dc['Pg_MW']['MAE'],'angle_MAE_difference_vs_DC_deg':a['aligned_angle_deg']['MAE']-dc['aligned_angle_deg']['MAE'],'Pflow_MAE_difference_vs_DC_MW':a['active_branch_flow_MW_both_ends']['MAE']-dc['active_branch_flow_MW_both_ends']['MAE']})
assert all(x[k]>0 for x in paired for k in ['Pg_MAE_difference_vs_DC_MW','angle_MAE_difference_vs_DC_deg','Pflow_MAE_difference_vs_DC_MW']);save(O/'paired-DC-differences.json',paired)
save(O/'verification.json',{'status':'PASS','new_input_count':6,'scientific_calls':24,'new_base_calls':0,'11B_inventory_unchanged':True,'per_case':verification,'new_AC_references_verified':5,'new_DC_successes':6,'new_model_native_points':12,'failed_solves':1,'failure':'load1.10 AC: LOCALLY_INFEASIBLE; physical feasibility UNKNOWN; no reference errors','thermal_coverage':'N/A: all RATE_A=0','no_training_PF_completion_OPF_repair_or_other_scenarios':True,'code_sha256':{p.name:sha(p) for p in E.glob('*.py')}})
labels={'AC-OPF':'AC','DC-OPF':'DC','Microsoft v1.1':'MS v1.1','Newer v2':'v2'}
def fmt(x):
 if x is None:return 'N/A'
 return f'{x:.3f}' if abs(x)>=.001 else ('0' if x==0 else f'{x:.2e}')
def err(x):return 'N/A' if x is None else f"{fmt(x['MAE'])} ({fmt(x['maximum'])})"
TA=[['Load','Method','Pg MW','Angle deg','Pflow MW','Qg MVAr','Vm pu']]
for x in rowsA:TA.append([f"{x['loading']:.2f}"+('*' if x['base_reused'] else ''),labels[x['method']]]+[err(x[k]) for k in ['Pg_MW','aligned_angle_deg','active_branch_flow_MW_both_ends','Qg_MVAr','Vm_pu']])
TP=[['Load','Method','Max P @ bus','Max Q @ bus','Pg excess MW','Qg excess MVAr','Vm excess pu']]
for x in rowsP:
 loc=locs[str(x['loading'])][x['method']];pl=loc['P_balance_DC' if x['method']=='DC-OPF' else 'P_balance_AC'];ql=loc['Q_balance_AC'];TP.append([f"{x['loading']:.2f}"+('*' if x['base_reused'] else ''),labels[x['method']],fmt(x['max_P_imbalance_MW'])+' @ '+str(pl['original_bus_id'])+(' DC' if x['method']=='DC-OPF' else ''),'N/A' if ql is None else fmt(x['max_Q_imbalance_MVAr'])+' @ '+str(ql['original_bus_id']),fmt(x['max_Pg_violation_MW']),fmt(x['max_Qg_violation_MVAr']),fmt(x['max_Vm_violation_pu'])])
save(O/'document-tables.json',{'approximation':TA,'physical':TP})
def md(table):return '\n'.join('| '+' | '.join(row)+' |' for row in [table[0],['---']*len(table[0])]+table[1:])
text='''# Experiment 11C-1 — loading sensitivity only

22 October 2026. COMPLETE: exactly six new original case300 inputs, 24 scientific method calls; the 1.00 result is reused unchanged from 11B. Five AC-OPF local solutions independently pass original FP64 AC constraints; the 1.10 AC attempt returns LOCALLY_INFEASIBLE and fails the independent balance check (feasibility UNKNOWN). All six DC QPs converge and pass their own DC constraints; all twelve frozen native states fail AC balance. The failed 1.10 AC iterate/logs are retained without retry, repair or replacement. Reference-dependent errors there are N/A for every method. No training, PF completion, OPF repair, reactive-only changes, spatial changes or extra cases were run.

Before these runs, completed 11B was published as commit `1f8ab6645bc20be808d5d40d20f3d73f0856f6de` and matched remote main. The document instruction and embedded 31-input planning screenshot were read; only its six total-load inputs are in scope here. Full document screenshots remain private in `/private/tmp/gsfm011c1-20261022/`. The 1.10 failure was identified after the run; failure-aware extraction/evaluation was added to score its saved iterate without any solver retry. Original executed worker hashes remain in frozen-protocol.json; final scripts are hashed separately in verification.json.

## Frozen setup and interpretation

Each input starts from original MATPOWER 8.1 case300 SHA256 `69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5`. Only original Pd and Qd are multiplied by the stated positive factor. All original signs, zeros, IDs, parallel rows, statuses, costs, Pg/Qg/Vm bounds, taps, shifts, shunts, impedances and zero RATE_A fields are preserved and matrix-roundtrip checked. See frozen-protocol.json for input hashes and pre-run settings. Same 11B AC/DC solver settings and frozen hard-clipping defaults; no reference answers enter either model.

Microsoft v1.1: source `1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6`, checkpoint SHA256 `f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831`. Newer v2: source `517a07531ea55a11bd81a89a6c6879695a2ba4b4`, checkpoint SHA256 `9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7`. Exact frozen releases are reported separately; manuscript release selection with Dr. Li remains unresolved.

AC-OPF is a feasible local optimum, not a certified global optimum. Approximation distance to one local optimum does not itself establish infeasibility; native AC power-balance checks establish the model-state failures here. DC predicts Pg/angles and its own lossless active flows: Qg, Vm and AC feasibility are N/A. Thermal assessment is N/A for every method because all original RATE_A are zero; no finite thermal constraint was tested. No active original angle constraints (all +/-360 degrees).

## Approximation

Entries are MAE (maximum absolute error). At1.10 no feasible AC reference was obtained, so every approximation entry is N/A, including the failed AC iterate row. Angles align to original reference bus7049. Pflow uses both ends of all411 original branches: exact original AC equations for AC/GridSFM, DC-law flows for DC. Different flow definitions must be retained when interpreting approximation errors. Full RMSE and precision are in approximation.json. * = reused 11B base.

'''+md(TA)+'''

## Physical validity

P in MW and Q in MVAr; original bus IDs shown. DC P is a DC-law residual only, not an AC-feasibility evaluation. Raw bound excesses are shown even below tolerance. All accepted AC references pass; the failed 1.10 AC iterate and all native GridSFM states fail. Detailed original-ID locations are in worst-locations.json. Primary balance/Pg/Qg thresholds 1e-3 MW/MVAr, Vm1e-4 pu, angle1e-3 deg. Worst generator/voltage locations and all bus diagnostics are saved separately.

'''+md(TP)+'''

## Plots

![Generation errors](generation-error.png)

![Native power imbalance](power-imbalance.png)

## Findings

1. Five scaled AC-OPF solutions pass independent checks. At1.10 Ipopt returns LOCALLY_INFEASIBLE; its iterate fails original AC balance. Physical feasibility remains UNKNOWN, and all approximation errors there are N/A. No retry or replacement was performed. The seven-point display includes one reused base.
2. Neither frozen release gives an AC-feasible native operating point at any of the seven displayed loads. Large P/Q imbalance persists even below nominal loading; this is not solely a high-loading failure.
3. DC has lower Pg, aligned-angle and active-flow MAE than both frozen releases at all six loading points with a valid reference (five new plus reused base; paired differences saved). This is approximation to the chosen AC reference; DC remains no AC-feasibility certificate.
4. Newer v2 Pg MAE decreases from148.015MW at0.80 to88.844MW at1.06, while its Qg MAE increases; Microsoft Pg MAE has a small nonmonotonic variation near nominal loading. Shipped clipping keeps box-limit errors below the declared thresholds, but it does not enforce power balance. P/Q failures remain under balance thresholds1e-3,1e-2 and1e-1; unchanged primary thresholds are authoritative.
5. This small correlated screen diagnoses poor frozen transfer on this case across a loading range. It does not isolate a single cause, establish broad-grid generalization, guarantee novelty, test thermal security or demonstrate practical solver acceleration. No further experiment was launched.

## Reproduce and inspect

Read `experiments/gsfm011c1/README.md` before executing. `prepare.py` creates and verifies exactly the six inputs; `run_six.py` makes one AC/DC/v1.1/v2 call per input. Workers are parameterizations of the preserved 11B scripts. `summarize.py` and `plot.py` only read saved results. Output path is this directory; native states, unsolved inputs, raw solver results, logs and model feature files are retained locally and hashed in artifact-inventory.json. Compact tables, original-ID locations, verification, status and figures are reviewable separately. Environment and hardware are recorded in environment.json. Runtime is descriptive only, not a speedup claim. No large installation was performed.
'''
(O/'README.md').write_text(text);print(json.dumps(summary,indent=2))
