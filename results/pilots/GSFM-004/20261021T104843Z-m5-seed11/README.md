# GSFM-004 Revision2 — completed bounded discovery pilot

Run `20261021T104843Z-m5-seed 11`. Original start 21 October 2026 10:48:43 UTC. CPU FP32 model, original-parameter FP64 C/E physics; seed 11 only. No additional topology, MPS, second seed or final-paper test run.

## Status and shared data

- Experiment 0: COMPLETE. Operator/loss/gradient/data-path checks and six disposable 20-update smokes passed.
- Experiment 1: COMPLETE. Nearest-example, three-alpha validation-selected ridge and frozen baselines evaluated.
- Experiment 2: COMPLETE. S/C/E completed 200 matched updates.
- Experiment 3: COMPLETE. H/L/R completed 200 matched updates; heads saved with adapters.
- Experiment 4: COMPLETE. All methods evaluated on 10 ordinary, 10 paired spatial and 10 higher-load development cases.

Accepted/attempted: smoke_train 8/8, smoke_validation 4/4, train 50/50, validation 10/10, ordinary 10/10, higher_load 10/12, spatial 10/10. Two higher-load solver failures remain unknown. Results are conditional on accepted references, and all 90 shared cases are development data. Twelve separate smoke cases are excluded. Four regions were defined before model evaluation using farthest-hop centers and nearest ceil(N_positive/4) memberships; exact factor arrays and SVD rank/totals are local.

## One comparison table (validation-selected checkpoints)

| Method | Selected update | Ordinary median P/Q max,MW/MVAr | Spatial median P/Q max | Higher-load median P/Q max | Ordinary median raw cost error | Feasible ordinary/spatial/high | Trainable parameters | Fit seconds | Peak RSS GiB |
|---|---:|---|---|---|---:|---|---:|---:|---:|
| nearest | 0 | 18.86/7.82 | 83.13/32.44 | 38.31/19.99 | 0.4039% | 0/0/0 of10each | 0 | 0.04 | 0.059 |
| ridge | 0 | 10.39/4.70 | 58.19/23.55 | 17.84/8.31 | 0.1241% | 0/0/0 of10each | 272,625 | 0.05 | 0.065 |
| frozen | 0 | 4229.27/10128.48 | 4417.19/10291.00 | 3248.82/8108.20 | 56.2489% | 0/0/0 of10each | 0 | 0.00 | 0.547 |
| S | 50 | 2209.43/3659.80 | 2282.36/3699.83 | 2277.44/4421.24 | 0.2178% | 0/0/0 of10each | 15,137,858 | 88.70 | 0.881 |
| C | 200 | 706.96/628.27 | 720.77/667.91 | 1254.13/868.60 | 0.8443% | 0/0/0 of10each | 15,137,858 | 89.12 | 0.881 |
| E | 100 | 251.44/393.95 | 246.94/443.25 | 436.93/463.40 | 0.5086% | 0/0/0 of10each | 15,137,858 | 95.98 | 0.883 |
| H | 100 | 1071.80/2087.08 | 1075.57/2151.68 | 823.54/1819.15 | 19.2758% | 0/0/0 of10each | 68,164 | 37.45 | 0.825 |
| L | 100 | 999.31/2038.51 | 996.51/2079.22 | 771.09/1996.65 | 9.8550% | 0/0/0 of10each | 211,524 | 66.18 | 0.872 |
| R | 200 | 853.27/2633.13 | 845.24/2655.28 | 893.62/2792.57 | 6.7135% | 0/0/0 of10each | 15,137,858 | 95.21 | 0.887 |

Each P/Q statistic is a median across scenario-wise worst nodal residuals, not across pooled buses. Full median/p95/worst distributions; state/cost errors; limits; selected AND fixed-U endpoints; reference counts; actual updates; measured time/memory and stop reasons are in `summary.csv/json`. All six common endpoints are200; no unequal truncation.

S=pretrained full regression without KCL; C=same with stock floor; E=same with exact KCL; H=four regression heads only; L=rank2 FFN LoRA(alpha2)+the same heads; R=fully random same-architecture regression model. head_feas is frozen and its disconnected forward tail is skipped. Branch objectives have zero eligible branches because RATE_A=0; no synthetic ratings/negative labels. Infeasible raw cost is not an achieved operating cost.

## Mechanism evidence and correctness

On the first smoke state, supervised/cost objective=11.741085; weighted stock/exact KCL=0.265108/0.498780. Gradient norms: supervised=68.5935,stock=6.5781,exact=11.8405. Stock/exact gradient cosine=0.998958; total-C/total-E cosine=0.998788. These are largely aligned signals of different magnitude, not evidence of strongly conflicting gradients. Full raw/weighted components, capacity normalization(326.78435/140.9018pu),80%worst/20%mean aggregation,1%capacity margin, directional probes and active masks are in operator-audit.json.
Exact original-precision reference/prediction operator checks agree with the independent evaluator within1.5e-11MW/MVAr, and exact physical metrics are invariant on25/100/400MVA representations. The stock operator biases the exact reference by243.99MW/193.29MVAr. Labels, source-row ordering, system-base units, feasible masks, fresh batches, two-graph forward, feature/prediction independence from labels, pre-sanitizer/module tensors, parameter gradients, zero-LoRA equivalence, frozen parameters and full-state/head reload were checked. No installed model code or forward feature/context/flow equations was changed.

A setup-only error assumed checkpoint metadata always contains arch; the released loader uses default architecture if absent. The same fallback was adopted for R; its original error/source/log are retained in checks/failure-before-random-default-fix. Passed checks and five successful smokes were reused; only the missing R smoke was run afterwards. This is not a numerical training failure.

## Learning curves, matched endpoints and demand shift

- S: 200 updates; selected50; validation scores 0:9.2131, 50:8.2040, 100:9.5710, 150:9.5543, 200:9.6040; fit88.70s; median/p95 update0.410/0.415s; min available34.67GiB; stop reason=None. See training/S/ for losses, gradients, manifests and resumable checkpoints.
- C: 200 updates; selected200; validation scores 0:9.2131, 50:7.1270, 100:7.2638, 150:6.6533, 200:6.6337; fit89.12s; median/p95 update0.410/0.427s; min available34.37GiB; stop reason=None. See training/C/ for losses, gradients, manifests and resumable checkpoints.
- E: 200 updates; selected100; validation scores 0:9.2131, 50:6.4712, 100:6.0819, 150:6.4115, 200:6.6539; fit95.98s; median/p95 update0.453/0.464s; min available34.44GiB; stop reason=None. See training/E/ for losses, gradients, manifests and resumable checkpoints.
- H: 200 updates; selected100; validation scores 0:9.2131, 50:8.2764, 100:7.6095, 150:8.0063, 200:8.1109; fit37.45s; median/p95 update0.154/0.165s; min available34.38GiB; stop reason=None. See training/H/ for losses, gradients, manifests and resumable checkpoints.
- L: 200 updates; selected100; validation scores 0:9.2131, 50:8.1977, 100:7.6280, 150:7.9972, 200:8.0398; fit66.18s; median/p95 update0.290/0.336s; min available33.48GiB; stop reason=None. See training/L/ for losses, gradients, manifests and resumable checkpoints.
- R: 200 updates; selected200; validation scores 0:8.7790, 50:8.1871, 100:8.2885, 150:8.0806, 200:7.8824; fit95.21s; median/p95 update0.423/0.466s; min available33.32GiB; stop reason=None. See training/R/ for losses, gradients, manifests and resumable checkpoints.

Spatial paired changes (mean of paired difference,spatial minus ordinary; all 10 pairs):

| Method | Δ maximum P,MW | Δ maximum Q,MVAr | Δ raw cost error,percentage points | Δ Vm MAE,pu |
|---|---:|---:|---:|---:|
| nearest | 66.8534 | 23.9044 | 1.465061 | 0.0024092 |
| ridge | 47.6308 | 17.5940 | 1.655689 | 0.0021321 |
| frozen | 2.2356 | -52.7982 | -0.231218 | -0.0000078 |
| S | 28.5674 | 63.4690 | 0.479847 | 0.0006904 |
| C | 30.8214 | 58.5927 | 0.219443 | 0.0016654 |
| E | -0.0553 | 54.3715 | 0.237485 | 0.0009840 |
| H | -17.5527 | -43.8333 | -0.379768 | 0.0000447 |
| L | -13.4930 | -31.7160 | -0.347447 | 0.0000498 |
| R | -3.6390 | 13.4912 | -0.043581 | 0.0004028 |

Spatial moves: 429.06–696.17MW; maximum total-P drift4.37e-11MW and total-Q drift5.46e-12MVAr. Local P/Q ratios and <=10%affected-load change are retained by the recorded SVD projection. Demand movement is not an assumed uniform regional shock. paired-summary.csv/json reports every pair's P/Q, cost, voltage,angle,Pg,Qg and feasibility changes; it is not a bus-level significance test.

Matched200-update ordinary median P/Q maxima(MW/MVAr): S 14978.42/2529.71; C 706.96/628.27; E 392.37/759.49; H 670.81/3432.37; L 937.24/3214.41; R 853.27/2633.13. At matched200, E has lower P residual but higher Q residual than C; selected-checkpoint improvements are not uniform endpoint dominance.

Cost/state trade-off: selected E ordinary cost error0.5086% is better than C0.8443%, but worse than S0.2178%. E/C ordinary Vm MAE0.00520/0.00247pu, angle MAE5.264/3.495degrees,Pg MAE12.757/7.444MW,Qg MAE8.935/6.365MVAr: lower E balance residuals come with larger state errors than C. S does not uniformly beat scratch R: at200 updates S has substantially worse P balance but better angle/cost accuracy. H/L use fewer parameters and less fit time, but do not match the stronger physics-penalty arms and have large raw cost errors. No clean pretraining or parameter-efficiency dominance is established.

## Five findings

What ran: 90 accepted shared development cases plus 12 separate smoke cases; six independent seed 11 fits × 200 updates; three 10-case development slices(30 evaluation cases total) and cheap/frozen controls. Main-fit wall time including validation/checkpointing was7.88minutes.
What improved: on ordinary cases, selected E median P/Q max=251.44/393.95, versus C=706.96/628.27 and S=2209.43/3659.80; interpret cost/state/slice changes jointly, with fixed200 endpoints also reported.
What failed: strict raw feasibility is absent where the table shows0/10; the frozen model and adapted arms must be compared with ridge, whose ordinary median P/Q max is10.39/4.70. S/R ordinary median P/Q max are2209.43/3659.80 and853.27/2633.13; a200-update scratch comparison is early learning only.
Which hypothesis merits a larger study: a narrow numerical-loss trade-off study, with ridge mandatory as a baseline, is better supported than a claim of useful foundation-model adaptation. Selected E lowers balance residuals, but has worse state errors than C and worse raw cost error than S; at matched200 updates its reactive residual is worse than C. Exact-KCL dominance is therefore not established. Do not expand to a large paper matrix before resolving that trade-off.
Measured compute estimate: this complete six-arm main-fit screen took472.6s. A like-for-like three-seed repeat would be about23.6main-fit minutes on this host before data/evaluation/report overhead; a1000-update fit is roughly7.8minutes of updates alone at the measured slowest p95, not a guaranteed scaling forecast. No larger study was started.

## Limits, artifacts and reproduction

One seed and10 accepted cases per evaluation slice support descriptive hypothesis screening only. p95/worst estimates are unstable; no across-seed repeatability, significance, universal pretraining advantage, optimal hyperparameter comparison, global optimality, operational feasibility or conference acceptance claim is justified. Ridge had three validation-only alpha candidates; common neural lr is a controlled screen, not each method’s optimum.

Training uses AdamW1e-4,weight decay1e-4,clip1,batch1,Torch4/BLAS1/workers0. Common U=200 was fixed from slowest smoke p95 before viewing main outcomes. Per-fit25minute and update caps,4h40compute cutoff,5hour total cutoff and RSS32GiB/available12GiB bounds were enforced. Peak RSS is sampled process-tree residency every0.2s; NN/ridge timing/RSS were supplemented by a standalone NumPy-only reconstruction at the same fixed parameters, with no additional alpha search; contexts differ and no matched memory-saving claim is made. Original ridge tuning time is separately retained.

Raw matrices, factor arrays, solver results/failures, model/optimizer/RNG checkpoints and per-scenario predictions remain local under this run directory with hashes. Compact summaries/scripts are committed and pushed; do not assume ignored data or weights exist on GitHub. Rebuild labels from pinned MATPOWER source and saved manifest seeds/factors, then run the same scripts. Original base evidence remains in results/inference and results/diagnosis.

Explicit new replay (never reset the current run clock):

```sh
export GSFM004_RUN_ID=<new-unique-run-id>
export GSFM004_START_UTC=<actual-new-start-ISO8601-with-timezone>
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B experiments/gsfm004/data.py
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B experiments/gsfm004/audit.py
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B experiments/gsfm004/fit.py
```

Create the new output directory first with a RUNNING status; original source/checkpoint and working Julia project are prerequisites. Complete commands, environment, all hashes, ignored-artifact inventory and local paths are in provenance.json and artifact-manifest.json. Checkpoints include model,optimizer,RNG,update/order and base-checkpoint identity; no automatic resume beyond the original cutoff.
