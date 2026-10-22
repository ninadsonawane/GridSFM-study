from electrical import *
O=R/'results/comparisons/GSFM-012/20261023-frozen-two-copy';rows=read(O/'method-summary.json');bus=list(csv.DictReader((O/'bus-metrics.csv').open()));branches=list(csv.DictReader((O/'branch-flows.csv').open()));areas=list(csv.DictReader((O/'area-exchange.csv').open()));area_metrics=[];focus=[];compare=[]
for scenario in ['S0','Splus','Sminus']:
 c=read(O/scenario/'input.json');ref=read(O/scenario/'ac-native.json');ids,b,e,f,t=matrices(c);gi=np.array([ids[int(g[0])] for g in c['gen']]);slack=next(i for i,z in enumerate(b) if z[1]==3);rt=terms(c,ref)
 for method,filename in [('AC-OPF','ac-native.json'),('DC-OPF','dc-native.json'),('microsoft-v1.1','microsoft-v1.1-native.json'),('newer-base-v2','newer-base-v2-native.json')]:
  s=read(O/scenario/filename);sm,bu,br,ar=score(c,s,method,ref);dc=method=='DC-OPF';tr=None if dc else terms(c,s);af=np.array(s['pf_mw']) if dc else tr['sf'].real;at=np.array(s['pt_mw']) if dc else tr['st'].real
  for area in ['A','B']:
   ii=np.array([i for i in range(600) if identity(c,i)[0]==area]);jj=np.array([j for j in range(138) if gi[j] in ii]);ff=np.where(np.isin(f,ii))[0];tt=np.where(np.isin(t,ii))[0];rrows=[x for x in bu if x['area']==area];rP=np.array([z['P_residual_MW'] for z in rrows]);pgerr=np.array(s['pg_mw'])[jj]-np.array(ref['pg_mw'])[jj];angs=(np.array(s['va_deg'])-s['va_deg'][slack])-(np.array(ref['va_deg'])-ref['va_deg'][slack]);angs=(angs+180)%360-180;z={'scenario':scenario,'method':method,'area':area,'bus_count':len(ii),'Pg_error_per_generator':stat(pgerr),'angle_error_deg':stat(angs[ii]),'branch_P_outward_endpoint_error_MW':stat(np.r_[af[ff]-rt['sf'].real[ff],at[tt]-rt['st'].real[tt]]),'P_balance':stat(rP),'Q_balance':None if dc else stat([v['Q_residual_MVAr'] for v in rrows]),'Qg_error_per_generator':None if dc else stat(np.array(s['qg_mvar'])[jj]-np.array(ref['qg_mvar'])[jj]),'Vm_error':None if dc else stat(np.array(s['vm'])[ii]-np.array(ref['vm'])[ii]),'P_violating_bus_count':int(sum(abs(rP)>1e-3)),'Q_violating_bus_count':None if dc else sum(abs(v['Q_residual_MVAr'])>1e-3 for v in rrows),'Pg_max_excess':float(max(excess(np.array(s['pg_mw'])[jj],np.array(c['gen'])[jj,9],np.array(c['gen'])[jj,8]))),'Qg_max_excess':None if dc else float(max(excess(np.array(s['qg_mvar'])[jj],np.array(c['gen'])[jj,4],np.array(c['gen'])[jj,3]))),'Vm_max_excess':None if dc else float(max(excess(np.array(s['vm'])[ii],b[ii,12],b[ii,11])))};area_metrics.append(z)
  if not dc and method!='AC-OPF':
   selected={i for i,z in enumerate(bu) if z['original_bus_id'] in [238,231,137]}
   for co in ['P','Q']:selected.update(sorted(range(600),key=lambda i:(-abs(bu[i][co+'_residual_'+('MW' if co=='P' else 'MVAr')]),bu[i]['bus_id']))[:5])
   focus.extend([dict(scenario=scenario,**bu[i]) for i in sorted(selected)])
   for co in ['P','Q']:
    key=co+'_residual_'+('MW' if co=='P' else 'MVAr');total=sum(abs(z[key]) for z in bu);interface=sum(abs(z[key]) for z in bu if z['original_bus_id']==231);compare.append({'scenario':scenario,'method':method,'component':co,'total_absolute':total,'tie_bus_absolute':interface,'tie_bus_fraction':interface/total,'elsewhere_absolute':total-interface})
save(O/'area-accuracy-and-constraints.json',area_metrics);save(O/'focus-buses.json',focus);save(O/'interface-concentration.json',compare)
# Fixed A/B comparison, using original source rows; one global gauge for swapped scenarios.
sym=[]
for method,filename in [('AC-OPF','ac-native.json'),('DC-OPF','dc-native.json'),('microsoft-v1.1','microsoft-v1.1-native.json'),('newer-base-v2','newer-base-v2-native.json')]:
 s=read(O/'S0'/filename);br=[x for x in bus if x['scenario']=='S0' and x['method']==method];a=[z for z in br if z['area']=='A'];bb=[z for z in br if z['area']=='B'];sym.append({'method':method,'S0_Vm_A_B_MAE':None if s['vm'] is None else float(np.mean(abs(np.array(s['vm'][:300])-s['vm'][300:]))),'S0_Pg_A_B_MAE':float(np.mean(abs(np.array(s['pg_mw'][:69])-s['pg_mw'][69:]))),'S0_P_residual_A_B_MAE':float(np.mean([abs(float(x['P_residual_MW'])-float(y['P_residual_MW'])) for x,y in zip(a,bb)])),'REF_PV_distinction_source_bus':7049,'caveat':'One system angle reference; REF/PV and graph-context distinctions retained; no independent area rotations or causal bus-count/equivariance claim'})
 plus=read(O/'Splus'/filename);minus=read(O/'Sminus'/filename);perm=np.r_[np.arange(300,600),np.arange(300)];gp=np.r_[np.arange(69,138),np.arange(69)];pa=np.array(plus['va_deg']);ma=np.array(minus['va_deg'])[perm];delta=pa-ma;delta-=delta[0];delta=(delta+180)%360-180;sym[-1].update({'paired_Splus_Sminus_swap_Pg_MAE':float(np.mean(abs(np.array(plus['pg_mw'])-np.array(minus['pg_mw'])[gp]))),'paired_swap_Vm_MAE':None if plus['vm'] is None else float(np.mean(abs(np.array(plus['vm'])-np.array(minus['vm'])[perm]))),'paired_swap_angle_MAE_one_global_gauge':float(np.mean(abs(delta)))})
save(O/'AB-paired-diagnostics.json',sym)
headers=['Scenario','Method','Pg MAE MW','Angle MAE deg','Pflow MAE MW','Max P MW','Max Q MVAr','Tie excess MVA / DC MW','Joint AC']
tab=[headers]
for r in rows:
 a=r['approximation'];tab.append([r['scenario'],r['method'],f"{a['Pg_per_generator_MW']['mean']:.3f}",f"{a['aligned_angle_deg']['mean']:.3f}",f"{a['branch_P_MW']['mean']:.3f}",f"{r['P']['max']:.3g}",'N/A' if r['Q'] is None else f"{r['Q']['max']:.3g}",f"{r['thermal_max_excess_MVA_or_DC_MW']:.3f}",'N/A' if r['AC_joint_feasible'] is None else str(r['AC_joint_feasible'])])
def md(t):return '\n'.join('| '+' | '.join(map(str,x))+' |' for x in [t[0],['---']*len(t[0])]+t[1:])
save(O/'report-table.json',tab);csvsave(O/'method-summary.csv',[{'scenario':r['scenario'],'method':r['method'],'Pg_MAE':r['approximation']['Pg_per_generator_MW']['mean'],'angle_MAE':r['approximation']['aligned_angle_deg']['mean'],'branchP_MAE':r['approximation']['branch_P_MW']['mean'],'P_max':r['P']['max'],'Q_max':None if r['Q'] is None else r['Q']['max'],'AC_joint_feasible':r['AC_joint_feasible'],'thermal_max_excess':r['thermal_max_excess_MVA_or_DC_MW']} for r in rows])
(O/'README.md').write_text('''# Experiment12 — frozen releases on connected case300 copies

COMPLETE,23 October2026. Exactly S0(1/1),Splus(1.05/.95),Sminus(.95/1.05). Three AC references independently feasible; three DC runs converge and pass DC constraints; six native frozen states fail AC balance. No retry was required. Four additional poisoned-label audit forwards on S0 passed exact equality; these are correctness checks, not extra scenarios. No training, PF completion, OPF repair or result-driven network changes.

600 buses,138 generator rows,824 branches. Source original MATPOWER8.1 case300 and config network-case300x2.json unchanged. Two synthetic identical600MVA ties connect the345kV copies of original bus231; r.002,x.019,b1.127,tap0=unity,shift0. Only one REF remains (B's former REF is PV). All822 inherited lines remain unlimited. **Thermal coverage is only the two synthetic ties**, not the inherited grid. Mapping and input hashes are retained; every inherited field was checked. Original signed loads, costs, statuses, shunts, taps and parallel rows are preserved.

## Comparison

'''+md(tab)+'''

DC's Qg/Vm and AC feasibility are N/A. Its thermal column is an active-flow DC test, not apparent-power AC certification. Model branch flows use original exact FP64 phasor equations; native API outputs are archived before scoring. Full MAE/median/p95/max for Pg/Qg (per-generator and aggregated-generator-bus), Vm, angles, both-end P/Q; balance distributions/counts; bounds and rated-branch checks are in method-summary.json. Area accuracy/constraints are separate in area-accuracy-and-constraints.json. No global optimum is certified.

## Answers and electrical interpretation

1. All three constructed inputs have independently verified feasible local AC optima. Model conversion mappings, poisoned labels, solver roundtrip (loads/shunts/costs/limits) and original Ybus/branch-sum gates passed (<1e-6MW/MVAr). No constraint relaxation or impedance clamp was used. The failed-original1.10 case is unrelated and preserved.
2. DC has lower Pg and active-flow MAE than either frozen release on all three inputs. On Splus, both models have lower aligned-angle MAE than DC (MS35.581°,v234.302°,DC36.536°). This limited advantage does not establish AC feasibility or a universal ranking.
3. The600-bus construction does not remove native power-balance failures. Both releases fail on all three inputs; normalized area/bus metrics, not raw totals alone, are supplied for comparison with original300. It is not a standard IEEE600 benchmark or independent topology family, and the result does not isolate bus count or establish training exposure.
4. AC A-outward active interchange is approximately0,−337.097,+338.192MW for S0/Splus/Sminus. The opposing ends differ by tie losses (Splus B-outward+338.192MW), and reactive charging is explicit; two outward powers are not forced to negatives. On Splus both frozen models overload BOTH600MVA ties: MS maximum excess146.375MVA, v2 excess31.330MVA. They pass tie thermal tests in the other two inputs while still failing balance. Failures remain throughout inherited buses, not just the interface; interface-concentration.json quantifies the two tie buses versus elsewhere. Symmetric S0 areas produce unequal model outputs; A/B symmetry and reversed-load diagnostics are saved with the REF/PV/common-reference caveat. Differences alone do not identify their cause.
5. Interior thermal validity is N/A, and no outage, additional topology family, neural training, completion or speedup test was performed. This is inspected development evidence, not blind confirmation or a novelty guarantee.

![Constraint comparison](01-constraints.png)

![Matched A/B bus imbalance](02-AB-buses.png)

![Signed inter-area exchange](03-exchange.png)

## Reproduction and artifacts

Code:experiments/gsfm012_014/{run_cases.py,run_model.py,run_dc.py,solver_server.jl,electrical.py,report12.py,plots.py}. The existing read-only Python3.11/PyTorch/PyG/PYPOWER environment and Julia/PowerModels/Ipopt project were used. Audit settings are in scenario-manifest.json; exact commands, outcomes and default settings are in run-status.json/model metadata. AC uses audited formulation/tolerances,3000iterations/120s, one flat retry only on failure (unused). DC is audited MATPOWER-equivalent PIPS QP200 with the11B150iteration limits. Neither release's clipping was changed.

Run_cases refuses to overwrite completed attempts. Native states and raw matrices/solver containers remain local; artifact-inventory.json lists their hashes and paths. Readable tables, gates, mapping manifests, bus metrics, branch flows, area exchange, focus buses and paired diagnostics are preserved. Original11B–11D files are unchanged. This completes12;13 and14 are covered by the user's explicit instruction to run all three sequentially, with their own gates and separate reports.
''')
print('12 REPORT COMPLETE')
