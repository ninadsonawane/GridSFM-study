# GSFM-005 — Experiments 5–8 results

Run `20261021T120300Z-m5-seeds11-22-33`. Actual start 2026-10-21T12:01:19+00:00. Controlled CPU FP32 model / original-parameter FP64 physics; one topology, fixed 50/10 train/validation, three training-order seeds.

## Status

- Experiment 5: COMPLETE. Twenty valid training-only gradient ratios; rho fixed before fitting.
- Experiment 6: COMPLETE. All fits and poor outcomes retained.
- Experiment 7: COMPLETE subject to coverage counts below; locked fresh evaluation, no retuning.
- Experiment 8: COMPLETE. Main/matched tables, three figures, traces, hashes and scientific decision.

## Main comparison — validation-selected snapshots

| Method / seed | Step | Ordinary J | Ordinary P/Q median maxima | Spatial J | Higher-load J | Ordinary cost error % | Vm / angle MAE | Pg / Qg MAE | Feasible O/S/H | Fit s / RSS GiB |
|---|---:|---:|---|---:|---:|---:|---|---|---|---|
| nearest / — | 0 | 3.0162 | 19.22 / 8.64 | 4.4471 | 3.6205 | 0.2541 | 0.00059 / 0.154 | 0.910 / 1.336 | 0/30; 0/28; 0/30 | reused / not measured |
| ridge / — | 0 | 2.6493 | 12.46 / 6.10 | 4.0417 | 2.7606 | 0.1049 | 0.00058 / 0.107 | 1.000 / 1.248 | 0/30; 0/28; 0/30 | reused / not measured |
| frozen / — | 0 | 9.2332 | 4331.32 / 10519.55 | 9.2445 | 8.9955 | 56.5431 | 0.02711 / 42.415 | 195.547 / 84.306 | 0/30; 0/28; 0/30 | reused / not measured |
| S / 11 | 1000 | 7.9866 | 2925.94 / 1094.92 | 7.9995 | 7.9725 | 0.6422 | 0.00179 / 1.338 | 6.257 / 5.922 | 0/30; 0/28; 0/30 | 447.13 / 0.843 |
| C / 11 | 950 | 6.3604 | 547.86 / 465.77 | 6.3888 | 6.5666 | 1.3463 | 0.00160 / 1.405 | 7.109 / 4.542 | 0/30; 0/28; 0/30 | 449.03 / 0.881 |
| E / 11 | 950 | 5.5750 | 253.83 / 157.90 | 5.6251 | 6.0411 | 1.1489 | 0.00202 / 1.985 | 8.256 / 6.017 | 0/30; 0/28; 0/30 | 470.38 / 1.391 |
| C_m / 11 | 700 | 6.4130 | 612.03 / 339.10 | 6.4701 | 6.5208 | 1.7411 | 0.00247 / 1.646 | 8.472 / 7.487 | 0/30; 0/28; 0/30 | 455.97 / 0.947 |
| S / 22 | 50 | 8.2089 | 2702.99 / 3622.00 | 8.2033 | 8.3894 | 1.2831 | 0.00889 / 5.512 | 18.865 / 22.787 | 0/30; 0/28; 0/30 | 456.46 / 0.947 |
| C / 22 | 800 | 6.1250 | 375.69 / 437.92 | 6.1215 | 6.5237 | 0.5251 | 0.00130 / 1.247 | 4.788 / 4.732 | 0/30; 0/28; 0/30 | 458.62 / 0.948 |
| E / 22 | 250 | 5.6224 | 281.20 / 194.83 | 5.7140 | 5.9165 | 2.3701 | 0.00301 / 3.909 | 11.144 / 6.520 | 0/30; 0/28; 0/30 | 445.18 / 0.944 |
| C_m / 22 | 300 | 5.9961 | 287.61 / 351.07 | 6.0486 | 6.3879 | 1.1182 | 0.00285 / 3.407 | 9.316 / 7.118 | 0/30; 0/28; 0/30 | 459.08 / 0.947 |
| S / 33 | 50 | 8.2822 | 2956.21 / 3955.28 | 8.2761 | 8.4055 | 1.4514 | 0.00916 / 4.566 | 19.879 / 24.753 | 0/30; 0/28; 0/30 | 452.50 / 0.945 |
| C / 33 | 800 | 5.4285 | 171.52 / 226.21 | 5.6743 | 5.4678 | 2.7098 | 0.00199 / 3.212 | 10.568 / 8.528 | 0/30; 0/28; 0/30 | 441.21 / 0.948 |
| E / 33 | 850 | 4.8345 | 111.70 / 124.52 | 5.1514 | 5.0684 | 0.9909 | 0.00155 / 3.813 | 6.820 / 6.214 | 0/30; 0/28; 0/30 | 441.10 / 0.947 |
| C_m / 33 | 900 | 5.7632 | 134.44 / 384.24 | 5.9172 | 5.1879 | 0.6462 | 0.00214 / 3.650 | 5.148 / 5.238 | 0/30; 0/28; 0/30 | 460.53 / 0.943 |

J is the scenario mean log1p of the worst of maximum nodal P and Q imbalance, normalized by 1 MW and 1 MVAr. P/Q columns are medians across scenario-wise maximum imbalance, in MW/MVAr. All cost/state columns are medians of per-scenario errors; Vm pu, angle degrees, Pg MW and Qg MVAr. Baseline predictor training was reused; zero new fit seconds is not its original fit cost, and missing baseline RSS is not zero memory. See GSFM-004 timing records.

## Matched-step comparison — ordinary J

| Arm / seed | 200 | 500 | 1000 |
|---|---:|---:|---:|
| S / 11 | 9.5968 | 8.6554 | 7.9866 |
| C / 11 | 6.5784 | 6.5799 | 7.3005 |
| E / 11 | 6.6316 | 6.3566 | 5.8280 |
| C_m / 11 | 6.7570 | 7.3376 | 6.5730 |
| S / 22 | 9.6122 | 8.8499 | 8.2950 |
| C / 22 | 6.7246 | 6.8057 | 6.4840 |
| E / 22 | 6.8485 | 5.7608 | 6.1745 |
| C_m / 22 | 6.6578 | 6.6815 | 6.4542 |
| S / 33 | 9.6235 | 8.9611 | 8.4723 |
| C / 33 | 6.9073 | 6.6081 | 5.5430 |
| E / 33 | 6.0091 | 6.1950 | 5.3590 |
| C_m / 33 | 6.7770 | 6.7917 | 5.8614 |

Full matched-step P/Q, cost/state errors, violations, feasibility, time/memory and median/p95/worst statistics: `summary.csv/json` and `matched-steps.csv`. Every seed and slice is included; `seed-aggregates.json` contains means/ranges of seed summaries.

## Primary control and interpretation

Training-only rho=1.789784409; initial ratio range [1.7256417824817376, 1.8278548475244945]. No optimizer step in calibration. Initial norm matching is approximate and does not equalize later gradients. The frozen first-five probe trajectory is retained under seed-11 E snapshots.
Primary per-seed E−C_m J contrasts: [-0.8379895242186216, -0.3737262475734134, -0.9287331248231173]; mean -0.713483, range [-0.9287331248231173, -0.3737262475734134]. Negative favors E. Three seeds are training-order variation, not three independent datasets. Cost/state/P/Q and fixed-step trade-offs must accompany this contrast.

## Coverage, physical meaning and limitations

{'ordinary': {'accepted': 30, 'attempted': 30}, 'higher_load': {'accepted': 30, 'attempted': 30}, 'spatial': {'accepted': 28, 'attempted': 30}}

Unknown solver failures are retained, not proven infeasible. Fresh input hashes exclude prior inputs. Original matrices/limits/costs and label-independent features remain unchanged. All RATE_A=0; thermal constraints are not applicable. High nodal residual is power-balance mismatch, not branch overload. Infeasible raw cost is not an achievable operating cost. Local-reference feasibility does not certify global optimality.

One topology, one fixed 50-label dataset, three seeds, 30 ordinary, 28 accepted spatial and 30 higher-load cases are exploratory. Ten validation cases make snapshot selection noisy. No significance, universal correction dominance, practical OPF replacement, useful foundation-model superiority, cost-saving or novelty claim follows.

## Artifacts and reproduction

`calibration.json`, `config.json`, `freeze.json`, `training-summary.json`, `summary.csv/json`, `matched-steps.csv`, `contrasts.json`, `paired-summary.csv`, `coverage.json`, `verification.json`, `artifact-manifest.json` and `figures/` hold compact evidence. Raw inputs/factors/solver failures, predictions, original-ID bus localization, optimizer/RNG/model snapshots and per-update traces remain local in this run directory, with SHA256 inventory and byte sizes. Checkpoint selection and predictors were frozen before evaluation generation.

Commands from repository root with the existing GridSFM Python environment (no package upgrades):
```sh
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B experiments/gsfm005/calibrate.py
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B experiments/gsfm005/train.py
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B experiments/gsfm005/fresh_data.py
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B experiments/gsfm005/evaluate.py
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B experiments/gsfm005/report.py
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B experiments/gsfm005/verify.py
```
Use a NEW GSFM005_RUN_ID and actual GSFM005_START_UTC for any separately authorized replay; initialize its RUNNING directory. Do not rerun into this completed directory or reset its clock. Existing labels/baseline files under GSFM-004 are prerequisites. Default execution is deliberately guarded against duplicate workers.

## Controlled trade-offs and localization

At selected snapshots E improves ordinary J versus C_m for all three seeds, and the same sign holds at1000 updates. At200 updates seed22 reverses (E-minus-C_m J=+0.19069; paired mean Pmax +65.92 MW and Qmax +325.42 MVAr). The500 and1000 contrasts favor E for every seed. This is not uniform superiority over every training endpoint.

Selected E-minus-C_m paired mean Pmax changes are -345.81/-40.68/-19.34 MW, Qmax changes -176.83/-171.04/-211.53 MVAr (seeds11/22/33). Mean raw cost-error changes are -0.6045/+1.0571/+0.3969 percentage points; angle MAE changes +0.425/+0.774/+0.139 degrees. Lower joint-balance error has state/cost trade-offs. Ridge remains much better in absolute physical error, including spatial evaluation; every prediction remains strictly infeasible.

The three clamp-affected branch rows are1 (37–9001),317 (231–237) and321 (235–238). On fresh ordinary solver references, exact median P/Q maxima are1.85e-11 MW/7.26e-11 MVAr; stock equations give226.44 MW/192.35 MVAr on identical states. Same-state predicted-state discrepancies are recorded separately; they are not substituted for authoritative exact metrics. Original bus IDs/areas/regions, residuals, voltage/angle errors, incident branches and generator errors are in local localization/ files. Only306 of1659 dependent selected-E ordinary top-bus union records are adjacent to these branches; poor prediction error is not confined to clamp adjacency. This descriptive count is not causal or independent-trial evidence.

Spatial accepted pairs move411.66–694.20 MW. Recorded total-P/Q drift is at most3.27e-11 MW/1.00e-11 MVAr. Mean paired delta-J for E is +0.0614/+0.0971/+0.3143, versus C_m +0.0602/+0.0672/+0.1064. E therefore does not establish superior resistance to relocation despite lower absolute scores. Ridge delta-J=+1.4074, but its spatial absolute J=4.0417 remains better than the neural arms.

## Selected joint-score aggregation across seeds

| Arm | Ordinary mean [range] | Spatial mean [range] | Higher-load mean [range] |
|---|---|---|---|
| S | 8.1592 [7.9866, 8.2822] | 8.1597 [7.9995, 8.2761] | 8.2558 [7.9725, 8.4055] |
| C | 5.9713 [5.4285, 6.3604] | 6.0616 [5.6743, 6.3888] | 6.1860 [5.4678, 6.5666] |
| E | 5.3439 [4.8345, 5.6224] | 5.4968 [5.1514, 5.7140] | 5.6753 [5.0684, 6.0411] |
| C_m | 6.0574 [5.7632, 6.4130] | 6.1453 [5.9172, 6.4701] | 6.0322 [5.1879, 6.5208] |

Final figures were visually checked. A layout-only script moves overlapping x-axis labels and legends; original renders remain in figures-initial-layout/. Scientific source/config/selections stayed byte-identical to the pre-evaluation lock, and the complete verification passed again. After report.py, run the bundled Python on experiments/gsfm005/render_final_figures.py for the final layout, then verify.py. No numerical outcome or recipe was changed.

## Five findings and paper decision

What ran: twelve fresh pretrained full-regression fits, S/C/E/C_m × seeds11/22/33, all1000 updates, original50/10 train/validation, and fresh locked ordinary/spatial/higher-load evaluation with counts {'ordinary': {'accepted': 30, 'attempted': 30}, 'higher_load': {'accepted': 30, 'attempted': 30}, 'spatial': {'accepted': 28, 'attempted': 30}}.

What improved: validation-selected ordinary E-minus-C_m joint-log-balance changes by seed11/22/33 are [-0.8379895242186216, -0.3737262475734134, -0.9287331248231173]; mean -0.713483, range [-0.9287331248231173, -0.3737262475734134]. Negative favors E; separate MW/MVAr, state/cost and fixed200/500/1000 effects are in contrasts.json and matched-steps.csv.

What failed: every method/snapshot/slice has zero strictly feasible raw predictions. Ridge ordinary J=2.649312; compare it with every neural arm before discussing utility. No infeasible raw cost is an achievable saving.

What the magnitude control changed: rho=1.789784409, from20 valid first-training-case ratios, range [1.7256417824817376, 1.8278548475244945]. It was fixed before training. Seed11 E trajectory shows later gradient norms/directions differ, so this is an initial magnitude control only. All primary seed signs favor E beyond this control.

Next paper decision: E improves the primary joint-balance score beyond this particular initial gradient-norm control for all three training-order seeds. A sign reversal at a matched fixed endpoint shows endpoint sensitivity; uniform superiority is not established. This remains a candidate numerical-loss consistency study for professor review, not an established practical OPF replacement or novelty claim. Do not automatically expand the experiment matrix.

## Execution qualification

The first seed11/S fit completed all1000 steps and reload verification, then summary assembly duplicated an arm key. The saved state/trace was recovered without any optimizer step repeated; initial failure/summary/logs are retained. Its recovered available-memory minimum comes from per-update samples; other fits report the 0.2s monitor minimum. No numerical training failure or recipe retuning was introduced. Calibration also retained its initial summation-order equality-check failure, fixed before fitting.

Main-fit time: 90.62 minutes. Maximum process-tree RSS: 1.391 GiB. Minimum observed available memory: 34.33 GiB. All caps passed.
