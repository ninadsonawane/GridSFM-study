from common import *
import csv

def distribution(v):
 v=[float(x) for x in v if x is not None and math.isfinite(x)]
 return dict(median=float(np.median(v)),p95=float(np.percentile(v,95)),worst=float(np.max(v)),mean=float(np.mean(v))) if v else None

def main():
 rr=read(RUN/'online-all.json');rows=[r for r in rr if r['repeat']>=0];summary=[];groups=collections.defaultdict(list)
 for r in rows:groups[(r['network'],r['method'],r['split'])].append(r)
 for (net,method,split),rs in sorted(groups.items()):
  for stage in ['raw','PF','final']:
   key=stage+'_metrics';ms=[r[key] for r in rs if r.get(key)];d=dict(network=net,method=method,split=split,stage=stage,requests=len(rs),unique_scenarios=len(set(r['scenario_id'] for r in rs)),valid_outputs=len(ms),PF_converged=sum(r['PF_converged'] is True for r in rs) if stage=='PF' else None,full_feasible=sum(m['all_tested_constraints_pass'] for m in ms),feasible_within_deadline=sum(r['feasible_within_deadline'] for r in rs) if stage=='final' else None,quality_pass=sum(r['quality_pass'] for r in rs) if stage=='final' else None,reference_known=sum(r['reference_known'] for r in rs),fallbacks=sum(r['fallback'] for r in rs),failures=sum(r['status']!='FEASIBLE' for r in rs) if stage=='final' else None,total_seconds=distribution([r['total_seconds'] for r in rs]) if stage=='final' else None,iterations=distribution([sum(a.get('iterations',0) or 0 for a in r['attempts']) for r in rs]) if stage=='final' else None)
   for k in ['max_p_residual_mw','max_q_residual_mvar','max_Pg_violation_MW','max_Qg_violation_MVAr','max_voltage_violation_pu','max_branch_violation_mva','max_angle_violation_deg']:d[k]=distribution([m[k] for m in ms])
   d['feasible_signed_cost_gap_percent']=distribution([m['signed_cost_gap_percent'] for m in ms if m['all_tested_constraints_pass']]);d['control_Pg_MAE_MW']=distribution([r['control_metrics']['Pg_MAE_MW'] for r in rs if r.get('control_metrics')]);d['control_Vctrl_MAE_pu']=distribution([r['control_metrics']['Vctrl_MAE_pu'] for r in rs if r.get('control_metrics')]);summary.append(d)
 save(RUN/'summary.json',summary)
 # Paired scenario medians collapse repeats. Bootstrap scenario families, preserving O/S pairing.
 paired=[];rng=np.random.Generator(np.random.PCG64(710009));offline=read(RUN/'training-summary.json');ridge={net:read(RUN/f'ridge/{net}/summary.json') for net in ['case300','pglib118']}
 for net in ['case300','pglib118']:
  for split in ['ordinary','spatial','higher_load','all']:
   subset=[r for r in rows if r['network']==net and (r['split']==split or split=='all')];defaults=collections.defaultdict(list)
   for r in subset:
    if r['method']=='conventional':defaults[r['scenario_id']].append(r)
   for method in sorted(set(r['method'] for r in subset)-{'conventional'}):
    vals=[];ids=[];counts=collections.Counter()
    for sid,ds in defaults.items():
     ar=[r for r in subset if r['method']==method and r['scenario_id']==sid];counts['all_scenarios']+=1
     if not ar:continue
     counts['method_quality_cases']+=int(all(r['quality_pass'] for r in ar));counts['default_quality_cases']+=int(all(r['quality_pass'] for r in ds))
     if all(r['quality_pass'] for r in ar+ds):vals.append(float(np.median([r['total_seconds'] for r in ds])-np.median([r['total_seconds'] for r in ar])));ids.append(sid.replace('spatial','ordinary'))
    item=dict(network=net,split=split,method=method,counts=dict(counts),joint_quality_scenarios=len(vals),mean_paired_online_saving_seconds=None,bootstrap_95CI=None,amortization='No measured comparable-quality saving')
    if vals:
     vals=np.array(vals);families=sorted(set(ids));byfam={f:[i for i,x in enumerate(ids) if x==f] for f in families};boots=[]
     for _ in range(2000):
      fs=rng.choice(families,len(families),replace=True);ix=[i for f in fs for i in byfam[f]];boots.append(float(np.mean(vals[ix])))
     mean=float(vals.mean());item.update(mean_paired_online_saving_seconds=mean,bootstrap_95CI=np.percentile(boots,[2.5,97.5]).tolist())
     if mean>0:
      fit=next((f for f in offline if method.startswith('FT-s'+str(f['seed'])+'-') and f['network']==net),None);labels=read(RUN/'prepare-complete.json')['pglib_label_seconds'] if net=='pglib118' else sum(r.get('elapsed_seconds',0) for s in ['train','validation'] for r in read(OLD/'data/manifest.json')[s]);offlinecost=(fit['fit_seconds'] if fit else 0)+(ridge[net]['tuning_seconds'] if method=='ridge' else 0)+(labels if fit or method=='ridge' else 0)
      item.update(offline_cost_seconds=offlinecost,break_even_solve_count=math.ceil(offlinecost/mean),amortization='Conditional estimate on jointly successful quality subset; labels included, resident/cache policy applies')
    paired.append(item)
 save(RUN/'paired-runtime.json',paired)
 # Paired ordinary/spatial changes, not a higher-load surrogate.
 shifts=[]
 for net in ['case300','pglib118']:
  for method in sorted(set(r['method'] for r in rows if r['network']==net)):
   by={(r['scenario_id'],r['repeat']):r for r in rows if r['network']==net and r['method']==method}
   for r in rows:
    if r['network']!=net or r['method']!=method or r['split']!='spatial':continue
    b=by.get((r['pair_id'],r['repeat']))
    if b:shifts.append(dict(network=net,method=method,scenario_id=r['scenario_id'],pair_id=r['pair_id'],repeat=r['repeat'],delta_total_seconds=r['total_seconds']-b['total_seconds'],delta_quality=int(r['quality_pass'])-int(b['quality_pass']),delta_PF_max_Qg_MVAr=(r['PF_metrics']['max_Qg_violation_MVAr']-b['PF_metrics']['max_Qg_violation_MVAr']) if r.get('PF_metrics') and b.get('PF_metrics') else None))
 save(RUN/'spatial-pairs.json',shifts)
 effects=[]
 for net in ['case300','pglib118']:
  fs=read(RUN/f'factorial-{net}.json');lookup={(r['seed'],r['scenario_id'],r['controls']):r for r in fs}
  for base in fs:
   if base['controls']!='FT_P_FT_V':continue
   for arm in ['FT_P_ridge_V','ridge_P_FT_V','ridge_P_ridge_V']:
    other=lookup[(base['seed'],base['scenario_id'],arm)];delta={k:other['metrics'][k]-base['metrics'][k] for k in ['max_Pg_violation_MW','max_Qg_violation_MVAr','max_voltage_violation_pu','max_branch_violation_mva','max_angle_violation_deg']};effects.append(dict(network=net,seed=base['seed'],scenario_id=base['scenario_id'],controls=arm,change_relative_to_FT_P_FT_V=delta,PF_convergence_change=int(other['PF_converged'])-int(base['PF_converged'])))
 save(RUN/'factorial-paired-effects.json',effects)
 # Largest violations by original physical IDs from retained first-repeat states.
 locations=[]
 for r in rows:
  if r['repeat']!=0 or not r.get('PF_metrics'):continue
  p=RUN/f'online-states/{r["network"]}/repeat-0/{r["scenario_id"]}/{r["method"]}/states.json';state=read(p)['native_PF'];record=next(x for x in read(RUN/'confirmation/manifest.json')[r['network']] if x['scenario_id']==r['scenario_id']);it=Item(record);c=it.c
  for key,boundlo,boundhi in [('pg_mw',9,8),('qg_mvar',4,3)]:
   v=[max(g[boundlo]-x,x-g[boundhi],0) for x,g in zip(state[key],c['gen'])];j=int(np.argmax(v));g=c['gen'][j];locations.append(dict(network=r['network'],method=r['method'],scenario_id=r['scenario_id'],constraint=key,violation=max(v),generator_row=j+1,original_bus_id=int(g[0]),synchronous_condenser=g[8]==g[9]==0,slack=any(b[0]==g[0] and b[1]==3 for b in c['bus'])))
  vv=[max(b[12]-x,x-b[11],0) for x,b in zip(state['vm'],c['bus'])];j=int(np.argmax(vv));locations.append(dict(network=r['network'],method=r['method'],scenario_id=r['scenario_id'],constraint='voltage_pu',violation=max(vv),original_bus_id=int(c['bus'][j][0])))
  sf,st=branch_flows(c,state['vm'],state['va_deg']);v=[max(abs(sf[i]),abs(st[i]))-b[5] if b[5]>0 else 0 for i,b in enumerate(c['branch'])];j=int(np.argmax(v));locations.append(dict(network=r['network'],method=r['method'],scenario_id=r['scenario_id'],constraint='branch_MVA',violation=max(max(v),0),branch_row=j+1,from_bus=int(c['branch'][j][0]),to_bus=int(c['branch'][j][1])))
  ids={int(b[0]):i for i,b in enumerate(c['bus'])};out=np.array([complex(b[4],-b[5])*state['vm'][i]**2 for i,b in enumerate(c['bus'])]);inj=np.array([complex(-b[2],-b[3]) for b in c['bus']])
  for j,b in enumerate(c['branch']):out[ids[int(b[0])]]+=sf[j];out[ids[int(b[1])]]+=st[j]
  for j,g in enumerate(c['gen']):inj[ids[int(g[0])]]+=complex(state['pg_mw'][j],state['qg_mvar'][j])
  residual=inj-out
  for name,values in [('P_balance_MW',residual.real),('Q_balance_MVAr',residual.imag)]:
   j=int(np.argmax(abs(values)));locations.append(dict(network=r['network'],method=r['method'],scenario_id=r['scenario_id'],constraint=name,violation=float(max(abs(values))),original_bus_id=int(c['bus'][j][0]),area=int(c['bus'][j][6])))
  av=[]
  for b in c['branch']:
   delta=state['va_deg'][ids[int(b[0])]]-state['va_deg'][ids[int(b[1])]];lo,hi=b[11:13];active=((lo!=0 and lo>-360) or (hi!=0 and hi<360) or (lo!=0 and hi==0) or (lo==0 and hi!=0));av.append(max(lo-delta if active and lo>=-360 else 0,delta-hi if active and hi<=360 else 0,0))
  j=int(np.argmax(av));locations.append(dict(network=r['network'],method=r['method'],scenario_id=r['scenario_id'],constraint='angle_deg',violation=float(max(av)),branch_row=j+1,from_bus=int(c['branch'][j][0]),to_bus=int(c['branch'][j][1])))
 save(RUN/'worst-locations.json',locations)
 lines=['# GSFM-007 — Experiment10 practical AC-OPF value','','Three optimizer seeds per network, one fixed50/10 split each; bounded1500-update adaptation, released source-defined objective and selection. Fresh fixed candidates follow a frozen protocol; original physical parameters and strict checker unchanged.','', '## Final common-solver stage (all online requests)','', '| Network | Method | Slice | Feasible / requests | Quality / known requests | Median / p95 total seconds | Fallbacks |','|---|---|---|---|---|---|---|']
 for r in summary:
  if r['stage']=='final':lines.append(f"| {r['network']} | {r['method']} | {r['split']} | {r['feasible_within_deadline']}/{r['requests']} | {r['quality_pass']}/{r['reference_known']} | {r['total_seconds']['median']:.4f}/{r['total_seconds']['p95']:.4f} | {r['fallbacks']} |")
 lines+=['','Full raw/PF/final-stage distributions including separate P/Q bounds, voltage/thermal/angle violations, signed feasible cost gaps and control errors: summary.json. All failures remain in online-rows.jsonl; each repeat is paired and method order interleaved. Three repeats are timing measurements, not independent scenarios.','', '## Protocol and interpretation','', 'The actual closed_forward function is extracted from pinned train_elastic.py and executed with the study store adapter. Training weights: elastic rho_g=rho_h10, control32, merit170; selection uses mean elastic diagnostic loss +32×mean control loss, excluding merit as in released eval_elastic/vsel. Ten cold validation closures must all converge. Source-defined reductions/top-k/masks/cost scale are retained; CPU/batch1 and serial closure are declared accommodations. LR horizon400epochs; PF tolerance reaches1e-8 at epoch25 of30. No LR/penalty search or accuracy-based duration selection. Experiment9 used a different selection rule and remains historical development evidence.','', 'Ridge predicts all online Pg, including slack, and control-bus Vm. Fixed columns and intercept/scalers use training only. Three alpha candidates are selected using the same score and PF-convergence eligibility gate. Controls remain unclipped. Ridge has no raw full-state prediction; PQ magnitudes1pu and angles/Qg placeholders are only initialization scaffolding and are not reported as raw physical predictions. Native neural completion starts from its full predicted voltage profile; this additional PQ initialization information is disclosed. The2×2 factorial diagnostic holds PQ initial magnitudes at1pu for all four swaps, isolating dispatch/control-voltage substitutions within that diagnostic.','', 'PF completion uses the native +1e-12 admittance and native stored coefficient precision, max40 Newton steps, backtracking and DC cold angles. It does not enforce Q-limit PV/PQ switching. Slack P and generator Q are recovered without clipping; raw/PF/refined outputs remain separate. The reference-control gate is an ORACLE diagnostic only.','', 'External refinement is our common original-parameter PowerModels ACP/Ipopt solve, not unavailable upstream N4. Every ordinary primal OPF variable is free; controls are starts only. Fresh model instances use identical default dual initialization, no reference duals. Same tol1e-9/constr_viol_tol1e-10/acceptable_tol1e-9/bound_relax_factor0/max_iter1000. One30s online alarm/watchdog covers preprocessing, inference, native PF, solver, feasibility validation and fallback. Failed PF invokes default; failed warm OPF gets at most one default retry within remaining time. Default starts and actual internal Ipopt iteration-zero points were verified on10 pilot scenarios with deliberate distinct label-free starts. Physical thermal/angle limits on PGLib118 are independently checked and logged in the numerical model.','', 'All fixed nonexcluded candidates are retained, including missing references; solver failure is UNKNOWN. Cases with no verified reference can still count as feasible but not reference-dependent quality. Primary quality is independent feasibility within30s and signed local-reference cost gap<=0.1%. Local optima are not global certificates. Negative feasible gaps may improve the reference.','', 'Fresh input JSON/schema/graph preparation is included in each predictor request; models and topology caches are resident. Reference data never enter features or starts. Label generation, training/tuning, initial graph setup, model loading and Julia startup are offline/cold costs reported separately. Paired-runtime intervals bootstrap scenario families after collapsing timing repeats, retaining ordinary/spatial pairing. Break-even is computed only for positive mean saving at jointly successful quality and is conditional on that subset. No forward-only speedup claim.','', '## Reproducibility','','Source protocol: docs/experiments/GSFM-007.md at4fb28fc. Model code517a07531ea55a11bd81a89a6c6879695a2ba4b4; base checkpoint9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7. PGLib118 source b1af0833849040c04babc3700631cff0d9afa66b79c5d3e13ae79bdf516cec78;35fixed-P synchronous condensers retained. Original case300 RATE_A=0 means thermal N/A. Neither benchmark is proven unseen during pretraining.','',f'Run: {RUN}. Scripts: experiments/gsfm007/. Execute with GSFM007_RUN set to a NEW durable run directory and GSFM007_START_UTC set to actual UTC start; never overwrite this completed run. Frozen scripts/config/data/checkpoint hashes are in freeze.json; all local states/checkpoints have SHA256 inventory and paths. Old Results and environment remain untouched.','', 'Commands executed (existing isolated Python environment):','```bash',f'GSFM007_RUN={RUN} {WORK}/venv/bin/python -B experiments/gsfm007/train.py',f'GSFM007_RUN={RUN} {WORK}/venv/bin/python -B experiments/gsfm007/confirm.py',f'GSFM007_RUN={RUN} {WORK}/venv/bin/python -B experiments/gsfm007/analyze.py','```','', 'Detailed five findings and source-linked figures are added after verification. No LoRA, scratch, paid compute, MPS port, case300x2, submission or additional experiment.']
 (RUN/'README.md').write_text('\n'.join(lines)+'\n');print('SUMMARY_ROWS',len(summary));print(json.dumps([p for p in paired if p['split']=='all'],indent=2))
if __name__=='__main__':main()
