"""Generate GSFM-005 tables and scientific figures strictly from saved metrics."""
from common import *
import csv
KEYS=['max_p_residual_mw','max_q_residual_mvar','joint_log_balance','cost_error_percent','voltage_mae_pu','angle_mae_deg','pg_mae_mw','qg_mae_mvar']

def csv_write(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r));path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def extra_diagnostics(fits):
    trajectory=[]
    for p in sorted((RUN/'training/seed-11/E').glob('operator-probe-*.json')):
      rr=read(p);valid=[r for r in rr if r['valid']];trajectory.append(dict(update=int(p.stem.split('-')[-1]),n=len(rr),ratio_values=[r['ratio'] for r in rr],ratio_range=[min(r['ratio'] for r in valid),max(r['ratio'] for r in valid)],cosine_values=[r['cosine'] for r in rr],cosine_range=[min(r['cosine'] for r in valid),max(r['cosine'] for r in valid)],no_recalibration=True))
    save(RUN/'gradient-diagnostics.json',dict(initial_rho=read(RUN/'calibration.json')['rho'],E_seed11_fixed_first5_training_probe_trajectory=trajectory,fit_clipping=[dict(arm=f['arm'],seed=f['seed'],fraction=f['clipping_fraction']) for f in fits],interpretation='Initial magnitude control only; later norms and directions differ. Probes preserved RNG and mode and performed no optimizer update.'))
    ops=read(RUN/'localization/operator-comparisons.json');out=[]
    for method,seed,endpoint,split in sorted({(r['method'],r['seed'] or 0,r['endpoint'],r['split']) for r in ops}):
      rr=[r for r in ops if (r['method'],r['seed'] or 0,r['endpoint'],r['split'])==(method,seed,endpoint,split)];x=dict(method=method,seed=seed or None,endpoint=endpoint,split=split,n=len(rr),worst_bus_clamp_adjacent=sum(r['top_bus_clamp_adjacent_count'] for r in rr),worst_bus_records=sum(r['top_bus_count'] for r in rr))
      for key in ['exact_P_max_MW','exact_Q_max_MVAr','stock_P_max_MW','stock_Q_max_MVAr','same_state_max_operator_difference_P_MW','same_state_max_operator_difference_Q_MVAr']:
        v=[r[key] for r in rr];x[key]=dict(median=float(np.median(v)),range=[min(v),max(v)])
      out.append(x)
    save(RUN/'localization-summary.json',out)

def main():
    rows=read(RUN/'evaluation/all-rows.json');fits=read(RUN/'training-summary.json');fmap={(f['arm'],f['seed']):f for f in fits};manifest=read(RUN/'data/manifest.json');counts=read(RUN/'data/counts.json');summaries=[]
    groups=sorted({(r['method'],r['seed'] or 0,r['endpoint'],r['split']) for r in rows})
    for method,seed,endpoint,split in groups:
      rs=[r for r in rows if (r['method'],r['seed'] or 0,r['endpoint'],r['split'])==(method,seed,endpoint,split)];fit=fmap.get((method,seed));r=rs[0]
      s=dict(method=method,seed=seed or None,endpoint=endpoint,split=split,checkpoint_update=r['update'],actual_fit_updates=fit['actual_updates'] if fit else 0,selected_update=fit.get('selected_update') if fit else None,reference_accepted=counts[split]['accepted'],reference_attempted=counts[split]['attempted'],evaluated=len(rs),strict_feasible_n=sum(x['all_tested_constraints_pass'] for x in rs),strict_feasible_denominator=len(rs),joint_log_balance_mean=float(np.mean([x['joint_log_balance'] for x in rs])),trainable_parameters=r['trainable_parameters'],training_seconds=r['training_seconds'],peak_RSS_bytes=fit.get('peak_RSS_bytes') if fit else None,median_seconds_per_update=fit.get('median_seconds_per_update') if fit else None,p95_seconds_per_update=fit.get('p95_seconds_per_update') if fit else None,clipping_fraction=fit.get('clipping_fraction') if fit else None,stop_reason=fit.get('stop_reason') if fit else None,status=fit['status'] if fit else 'COMPLETE',thermal_criterion='not applicable; RATE_A=0')
      for key in KEYS:
        vals=[x[key] for x in rs]
        for stat,value in [('median',np.median(vals)),('p95',np.percentile(vals,95)),('worst',max(vals))]:s[key+'_'+stat]=float(value)
      for key in ['max_voltage_violation_pu','max_generator_component_violation_mw_or_mvar','max_angle_violation_deg','max_branch_violation_mva']:s[key+'_worst']=max(x[key] for x in rs)
      summaries.append(s)
    save(RUN/'summary.json',summaries);csv_write(RUN/'summary.csv',summaries);csv_write(RUN/'matched-steps.csv',[s for s in summaries if s['endpoint'] in ['200','500','1000']])
    # Paired raw changes, one row per method/seed/snapshot/accepted spatial pair.
    pairs=[];demand={r['scenario_id']:r for r in manifest['spatial'] if r['accepted']}
    for method,seed,endpoint in sorted({(r['method'],r['seed'] or 0,r['endpoint']) for r in rows}):
      ordinary={r['scenario_id']:r for r in rows if (r['method'],r['seed'] or 0,r['endpoint'],r['split'])==(method,seed,endpoint,'ordinary')}
      for s in [r for r in rows if (r['method'],r['seed'] or 0,r['endpoint'],r['split'])==(method,seed,endpoint,'spatial')]:
        o=ordinary[s['pair_id']];dm=demand[s['scenario_id']];p=dict(method=method,seed=seed or None,endpoint=endpoint,ordinary_id=o['scenario_id'],spatial_id=s['scenario_id'],region_index=dm['region_index'],demand_moved_MW=dm['demand_absolute_moved_MW_MVAr'][0],total_P_drift_MW=dm['P_Q_total_difference'][0],total_Q_drift_MVAr=dm['P_Q_total_difference'][1],feasibility_change=int(s['all_tested_constraints_pass'])-int(o['all_tested_constraints_pass']))
        for key in KEYS:p[key+'_change']=s[key]-o[key]
        pairs.append(p)
    csv_write(RUN/'paired-summary.csv',pairs)
    contrasts=[]
    for seed in [11,22,33]:
      for endpoint in ['selected','200','500','1000']:
        for split in ['ordinary','spatial','higher_load']:
          ref={r['scenario_id']:r for r in rows if (r['method'],r['seed'],r['endpoint'],r['split'])==('E',seed,endpoint,split)}
          for control in ['C_m','C','S']:
            ctl={r['scenario_id']:r for r in rows if (r['method'],r['seed'],r['endpoint'],r['split'])==(control,seed,endpoint,split)}
            if not ref or set(ref)!=set(ctl):continue
            p=dict(seed=seed,endpoint=endpoint,split=split,contrast='E-minus-'+control,n_pairs=len(ref))
            for key in KEYS:
              vals=[ref[s][key]-ctl[s][key] for s in ref];p[key+'_paired_mean_change']=float(np.mean(vals));p[key+'_paired_median_change']=float(np.median(vals))
            contrasts.append(p)
    primary=[x for x in contrasts if (x['endpoint'],x['split'],x['contrast'])==('selected','ordinary','E-minus-C_m')];effects=[x['joint_log_balance_paired_mean_change'] for x in primary]
    comparison=dict(primary_endpoint='ordinary mean log1p(max(Pmax/1 MW,Qmax/1 MVAr)) at validation-selected snapshots',primary_contrast='E minus C_m; lower is better',per_seed=primary,mean=float(np.mean(effects)),range=[min(effects),max(effects)],all_contrasts=contrasts,independence_note='Three training-order seeds conditional on one fixed training set and same evaluation cases; no seed-case or bus-level independent trials.')
    save(RUN/'contrasts.json',comparison)
    # Main table includes every seed; separate aggregation of seed means/ranges.
    aggregates=[]
    for arm in ['S','C','E','C_m']:
      for split in ['ordinary','spatial','higher_load']:
        ss=[s for s in summaries if (s['method'],s['endpoint'],s['split'])==(arm,'selected',split)];a=dict(method=arm,split=split,seeds=[s['seed'] for s in ss])
        for key in ['joint_log_balance_mean']+[k+'_median' for k in KEYS]:
          vals=[s[key] for s in ss];a[key]=dict(mean=float(np.mean(vals)),range=[min(vals),max(vals)],values=vals)
        aggregates.append(a)
    save(RUN/'seed-aggregates.json',aggregates)
    extra_diagnostics(fits)
    plots(fits,contrasts,pairs)
    def get(m,seed=0,split='ordinary',ep='selected'):
      return next(s for s in summaries if (s['method'],s['seed'] or 0,s['split'],s['endpoint'])==(m,seed,split,ep if seed else 'baseline'))
    lines=['# GSFM-005 — Experiments 5–8 results','',f'Run `{RUN.name}`. Actual start 2026-10-21 12:01:19 UTC. Controlled CPU FP32 model / original-parameter FP64 physics; one topology, fixed 50/10 train/validation, three training-order seeds.','', '## Status','', '- Experiment 5: COMPLETE. Twenty valid training-only gradient ratios; rho fixed before fitting.',f'- Experiment 6: '+('COMPLETE' if len(fits)==12 and all(f['status']=='COMPLETE' for f in fits) else 'PARTIAL')+'. All fits and poor outcomes retained.','- Experiment 7: COMPLETE subject to coverage counts below; locked fresh evaluation, no retuning.','- Experiment 8: COMPLETE. Main/matched tables, three figures, traces, hashes and scientific decision.','', '## Main comparison — validation-selected snapshots','', '| Method / seed | Step | Ordinary J | Ordinary P/Q median maxima | Spatial J | Higher-load J | Ordinary cost error % | Vm / angle MAE | Pg / Qg MAE | Feasible O/S/H | Fit s / RSS GiB |','|---|---:|---:|---|---:|---:|---:|---|---|---|---|']
    for m,seed in [('nearest',0),('ridge',0),('frozen',0)]+[(m,seed) for seed in [11,22,33] for m in ['S','C','E','C_m']]:
      a,b,c=get(m,seed),get(m,seed,'spatial'),get(m,seed,'higher_load');lines.append(f"| {m} / {seed or '—'} | {a['checkpoint_update']} | {a['joint_log_balance_mean']:.4f} | {a['max_p_residual_mw_median']:.2f} / {a['max_q_residual_mvar_median']:.2f} | {b['joint_log_balance_mean']:.4f} | {c['joint_log_balance_mean']:.4f} | {a['cost_error_percent_median']:.4f} | {a['voltage_mae_pu_median']:.5f} / {a['angle_mae_deg_median']:.3f} | {a['pg_mae_mw_median']:.3f} / {a['qg_mae_mvar_median']:.3f} | {a['strict_feasible_n']}/{a['evaluated']}; {b['strict_feasible_n']}/{b['evaluated']}; {c['strict_feasible_n']}/{c['evaluated']} | {a['training_seconds']:.2f} / {(a['peak_RSS_bytes'] or 0)/2**30:.3f} |")
    lines+=['','J is the scenario mean log1p of the worst of maximum nodal P and Q imbalance, normalized by 1 MW and 1 MVAr. P/Q columns are medians across scenario-wise maximum imbalance, in MW/MVAr. All cost/state columns are medians of per-scenario errors; Vm pu, angle degrees, Pg MW and Qg MVAr. Baseline predictor training was reused; zero new fit seconds is not its original fit cost, and missing baseline RSS is not zero memory. See GSFM-004 timing records.','', '## Matched-step comparison — ordinary J','', '| Arm / seed | 200 | 500 | 1000 |','|---|---:|---:|---:|']
    for seed in [11,22,33]:
      for m in ['S','C','E','C_m']:lines.append('| '+f'{m} / {seed}'+' | '+' | '.join(f"{get(m,seed,ep=str(k))['joint_log_balance_mean']:.4f}" for k in [200,500,1000])+' |')
    lines+=['','Full matched-step P/Q, cost/state errors, violations, feasibility, time/memory and median/p95/worst statistics: `summary.csv/json` and `matched-steps.csv`. Every seed and slice is included; `seed-aggregates.json` contains means/ranges of seed summaries.','', '## Primary control and interpretation','', f"Training-only rho={read(RUN/'calibration.json')['rho']:.9f}; initial ratio range {read(RUN/'calibration.json')['range']}. No optimizer step in calibration. Initial norm matching is approximate and does not equalize later gradients. The frozen first-five probe trajectory is retained under seed-11 E snapshots.",f"Primary per-seed E−C_m J contrasts: {effects}; mean {comparison['mean']:.6f}, range {comparison['range']}. Negative favors E. Three seeds are training-order variation, not three independent datasets. Cost/state/P/Q and fixed-step trade-offs must accompany this contrast.",'','## Coverage, physical meaning and limitations','',str(counts),'', 'Unknown solver failures are retained, not proven infeasible. Fresh input hashes exclude prior inputs. Original matrices/limits/costs and label-independent features remain unchanged. All RATE_A=0; thermal constraints are not applicable. High nodal residual is power-balance mismatch, not branch overload. Infeasible raw cost is not an achievable operating cost. Local-reference feasibility does not certify global optimality.','', 'One topology, one fixed 50-label dataset, three seeds and 30 cases per slice are exploratory. Ten validation cases make snapshot selection noisy. No significance, universal correction dominance, practical OPF replacement, useful foundation-model superiority, cost-saving or novelty claim follows.','', '## Artifacts and reproduction','', '`calibration.json`, `config.json`, `freeze.json`, `training-summary.json`, `summary.csv/json`, `matched-steps.csv`, `contrasts.json`, `paired-summary.csv`, `coverage.json`, `verification.json`, `artifact-manifest.json` and `figures/` hold compact evidence. Raw inputs/factors/solver failures, predictions, original-ID bus localization, optimizer/RNG/model snapshots and per-update traces remain local in this run directory, with SHA256 inventory and byte sizes. Checkpoint selection and predictors were frozen before evaluation generation.','', 'Commands from repository root with the existing GridSFM Python environment (no package upgrades):','```sh',f'{MODEL}/model/.venv/bin/python -B experiments/gsfm005/calibrate.py',f'{MODEL}/model/.venv/bin/python -B experiments/gsfm005/train.py',f'{MODEL}/model/.venv/bin/python -B experiments/gsfm005/fresh_data.py',f'{MODEL}/model/.venv/bin/python -B experiments/gsfm005/evaluate.py',f'{MODEL}/model/.venv/bin/python -B experiments/gsfm005/report.py',f'{MODEL}/model/.venv/bin/python -B experiments/gsfm005/verify.py','```','Use a NEW GSFM005_RUN_ID and actual GSFM005_START_UTC for any separately authorized replay; initialize its RUNNING directory. Do not rerun into this completed directory or reset its clock. Existing labels/baseline files under GSFM-004 are prerequisites. Default execution is deliberately guarded against duplicate workers.','']
    (RUN/'README.md').write_text('\n'.join(lines));log('REPORT_GENERATED',summaries=len(summaries),pairs=len(pairs),primary_effects=effects)

def plots(fits,contrasts,pairs):
    runtime='/Users/ninadsonawane/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
    subprocess.run([runtime,str(Path(__file__).with_name('plot_figures.py'))],check=True)
if __name__=='__main__':main()
