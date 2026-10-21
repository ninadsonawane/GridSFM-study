# GSFM-005 — Controlled follow-up, Experiments 5–8

Prepared 21 October 2026. Status: **READY FOR HARDWARE; NOT RUN BY THE PLANNER**. The user requested the next experiments in Exchange's To-do. This authorizes a new bounded follow-up on the existing M5 Pro/64 GB worker. GSFM-004 is complete; preserve its data, code and results. This protocol controls the next run and supersedes earlier operational stop instructions only for the work specified here.

## Question and evidence

**Does correcting the KCL operator improve learning beyond increasing the strength of its penalty, and does that effect repeat after longer training?** All adaptation below is full regression fine-tuning of the released GridSFM v1.1 checkpoint, with `head_feas` frozen. There is no LoRA experiment in this follow-up.

The [completed pilot](../../results/pilots/GSFM-004/20261021T104843Z-m5-seed11/README.md) used 50 training labels, 200 updates and one seed. Selected E improved balance versus C, but matched-step Q and state errors showed trade-offs. Ridge had much smaller imbalance, and every method was strictly infeasible. The one smoke gradient comparison had cosine 0.998958 and exact/stock norms 11.840/6.578. That motivates a magnitude control; it is not evidence of conflicting gradient directions or a universal scaling factor.

## Ownership, budget and implementation

- Mark Exchange To-do RUNNING with a unique GSFM-005 run ID, worker and actual UTC start before implementation. Use `results/pilots/GSFM-005/<run-id>/`; never reuse a GSFM-004 directory or reset a running clock. One worker only.
- **Five-hour inclusive ceiling**, with compute stopped by 4 h 40 min and 20 min reserved for verification/reporting. Stop early when finished. Maximum **12 main fits**, each at most **1,000 updates AND 15 minutes**, including validation and checkpointing. No extra fits to use spare time. Budget a measured reserve for all evaluation before starting another fit.
- Based on GSFM-004's slowest measured 0.499 s/update, 12,000 updates alone would take about 100 minutes. This excludes implementation, gradient probes, checkpointing, references and evaluation; it is an estimate, not a guaranteed runtime or a requirement to fill five hours.
- Use the validated CPU FP32 backbone/FP64 original-parameter physics, Torch 4 threads, BLAS 1, batch 1, workers 0. One training process; no simultaneous solver/training jobs. Stop/checkpoint on process-tree RSS >32 GiB, available memory <12 GiB, nonfinite tensors/gradients or deadline. Preserve failures.
- Build a separate, parameterized `experiments/gsfm005/` runner by reusing audited logic. Do not modify installed GridSFM or old experiment artifacts. The old `make_model()` resets seed 11, the old order generator hard-codes 11, and `common.py` points at a completed run: explicitly fix these in the new runner. Set/reset Python, NumPy, Torch and scenario-order RNGs with the actual seed; save the realized order and RNG states. Verify seeds are not merely relabeled copies.
- Pin checkpoint SHA256 `f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831`, source/config hashes, environment, commands and dirty diff. Reuse the existing M5 environment. No backend/package upgrade, paid compute or Windows training is needed.

## Shared data and unchanged conditions

Reuse the exact 50 training and 10 validation examples from `GSFM-004/20261021T104843Z-m5-seed11`, with hashes. Reuse its nearest/ridge predictors and training-only scalers; ridge alpha remains 0.01. Reconstruct only if needed and verify equivalent coefficients/predictions. Frozen GridSFM is also mandatory. Do not retune these on evaluation data. The original 30 evaluation examples remain development data, and can be reported separately for continuity.

Original case300, 100 MVA base, topology, costs, limits, impedances, units, labels, features, forward/context computation and auxiliary masks remain unchanged. Preserve exact-precision parameters separately from rounded model features. All RATE_A values are zero: thermal constraints are not applicable. No invented ratings, clamping of raw outputs, PF repair or OPF projection.

Retain AdamW lr=1e-4, weight decay=1e-4, global gradient clipping=1, constant LR, batch 1 and all GSFM-004 supervised/cost formulas and coefficients. Disable feasibility/stress objectives and synthetic negatives identically; skip invalid disabled computations. Train the same regression-relevant parameter set in every arm; `head_feas` stays frozen. No learning-rate, rank, data-size or architecture sweep.

## Experiment 5 — Separate equation correction from penalty magnitude

**Plain question:** Did E improve because its equations were more faithful, or because it pushed harder on balance?

1. Reuse passing operator, reference, conversion and leakage checks. Recheck the new runner's seed plumbing, objective coefficients, disabled auxiliaries and checkpoint reload. Confirm lambda zero reproduces S's objective and multiplier one reproduces C/E's old objectives on identical tensors. No need to repeat all frozen/solver-start studies.
2. At the common released checkpoint, select the **first 20 accepted training examples in the saved manifest order**, before learning. Use eval mode with autograd enabled, no optimizer step and a fresh graph per example. For identical predictions, calculate gradients with respect to the same trainable model parameters of `K_C=log1p(kp_stock)+log1p(kq_stock)` and `K_E=log1p(kp_exact)+log1p(kq_exact)`. These are KCL-only gradients before total-gradient clipping.
3. Define one fixed multiplier `rho = median_i(||grad K_E||_2 / ||grad K_C||_2)`. Keep finite positive ratios with both norms >1e-12; record every excluded example and require at least 16 of 20 valid ratios. Save ratios, median/range, cosine and loss contributions. Do not substitute the old smoke ratio of approximately 1.8, choose rho on validation, or search weights.
4. Add **C_m**, whose objective is `L_shared + rho * (log1p(kp_stock) + log1p(kq_stock))`. The multiplier is **outside** log1p and identical for P and Q. C has rho=1; E uses exact physics with multiplier 1; S has no KCL. Everything else is shared. Freeze rho in the manifest before fitting; never adapt it during a fit or separately by seed. Do not silently clip it. If calibration is undefined, continue the valid S/C/E comparison, mark C_m blocked and the primary comparison incomplete.
5. Save initial KCL-only and total-gradient norms/cosines, and clipping information. Initial norm matching is a diagnostic control, not equality throughout training. Do not claim all gradient-scale effects have been removed.

Allow up to 30 minutes for implementation-specific checks/calibration; if these reveal a real correctness issue, stop dependent fits and report it rather than changing the benchmark to pass.

## Experiment 6 — Longer training and three independent training seeds

Run these **four arms for seeds 11, 22 and 33**: S (no KCL), C (stock, weight 1), E (exact, weight 1), C_m (stock, frozen rho). Total: 12 fits. All start fresh from identical released weights, with fresh optimizer/RNG state; no continuation from a selected GSFM-004 checkpoint. The seed changes minibatch order/stochastic operations, not the pretrained checkpoint. It does not create a new training dataset.

Within each seed, use exactly the same shuffled scenario order for all arms. Save a complete 1,000-update order. Execute seed blocks 11,22,33; arm orders S/C/E/C_m, C/E/C_m/S, E/C_m/S/C respectively, so partial completion is explicit. Record actual updates and all failures; never select the best seed.

Validate at 0 and every 50 updates. Use only the existing 10 validation cases and the unchanged score:

`mean_s log(1 + max(Pmax_s / 1 MW, Qmax_s / 1 MVAr))`.

Tie-break by median absolute raw cost error, then earlier update. Save every validation score, the best checkpoint, and fixed snapshots 200/500/1000, together with optimizer/RNG/order metadata. Retain additional snapshots locally if already written; do not delete prior artifacts. Reload and verify selected/fixed snapshots before scoring.

Log per-update loss contributions, full-gradient norm, clipping input norm/frequency, update time and memory. At snapshots 0/200/500/1000 for the seed-11 E trajectory, evaluate both KCL operators and their gradients on the same first five training cases without updating weights. Reset RNG afterward. This shows whether the initial magnitude match remains informative; do not recalibrate from these diagnostics.

Report selected checkpoints **and** matched 200/500/1000 endpoints. If any fit is truncated, report the common completed saved step across the affected comparison in addition to its actual endpoint. Unequal training budgets are not a matched comparison. Longer training can worsen validation performance; show the curve rather than assuming 1,000 updates improves anything. Ten validation cases provide noisy model selection, a stated limitation.

## Experiment 7 — Fresh, locked evaluation and where errors concentrate

Freeze and hash the complete run configuration, rho, all checkpoint selections, baseline parameters and metric code before generating/reading new evaluation results. The gate is correctness and remaining time, **not a positive result**. Run this evaluation even if adaptation looks poor, provided the gate passes. If no complete four-arm seed is available, prioritize truthful partial reporting; do not make the primary controlled claim.

Generate new candidate streams after the freeze:

| Slice | Target | NumPy PCG64 seed | Construction |
|---|---:|---:|---|
| Ordinary | 30 accepted | 30503 | Global U[0.90,1.03]; bus P/Q-shared jitter U[0.98,1.02] |
| Spatial | One per accepted ordinary case, up to 30 | Deterministic, no RNG | Same GSFM-004 four-region SVD null-space perturbation and alternating sign, up to 10% local change |
| Higher load | 30 accepted | 30505 | Global U[1.035,1.06]; same bus jitter |

Apply factors to original loads once, including original signs; zeros stay zero. Reuse the saved region membership and GSFM-004 pairing rule. Preserve both aggregate P and Q and each affected bus's P/Q ratio; record actual movement and numerical drift. Do not replace a failed spatial pair. Cap ordinary/higher attempts at 90 each; each solve has the existing external 30-second watchdog. Stop reference generation after 35 minutes if needed and report actual coverage. Reuse the audited PowerModels/Ipopt conversion and independent acceptance checker; failed local solves remain unknown, not proven infeasible.

Hash inputs/factors and exclude exact duplicates against all previous train/validation/smoke/development/new examples. Save attempts and rejection reasons; don't hand-pick easy cases. Once evaluation is opened, no retuning or choosing a preferred seed. If later work changes the recipe based on these results, relabel this set development and obtain a new held-out set.

Evaluate S/C/E/C_m at validation-selected and fixed 200/500/1000 endpoints, all available seeds, plus nearest/ridge/frozen. If budget is tight, selected and fixed-1000 for all completed fits take priority, then 200/500. Reuse identical snapshot scores where selected equals a fixed snapshot. The old 30-case development evaluation is optional and lower priority than the fresh comparison.

**Primary endpoint:** ordinary-slice mean log(1+max(Pmax/1 MW,Qmax/1 MVAr)) at validation-selected checkpoints; **primary contrast E minus C_m**, lower is better. Secondary: E versus C/S, each P/Q metric, cost/state trade-offs, fixed-step comparisons and both shift slices. Keep the same evaluation cases paired across methods. Show each seed's contrast, mean and range; do not treat three seeds times 30 cases, or 300 buses, as independent trials. Seeds assess training-order variation conditional on one fixed training set, not dataset/topology generalization. No significance claim from three seeds alone.

For each slice report median/p95/worst scenario-maximum P/Q residuals, strict joint-feasible counts/denominators, cost/state errors and constraint violations. P95/worst remain uncertain with 30 cases. For spatial pairs, report paired changes and actual demand moved. Retain thresholds: P/Q and generator violations <=1e-3 MW/MVAr, Vm <=1e-4 pu, active angle <=1e-3 degrees; rated-line threshold <=1e-3 MVA only where applicable (none here).

Add a descriptive bus/branch localization file: original bus IDs, residuals, regions, voltage/angle errors, and adjacency to branches with original `r^2+x^2 < 1e-6`. Compare the original and clamped operator at the **same solver-reference state and the same prediction** to isolate numerical mismatch from prediction error. A high bus residual is a power-balance mismatch, not evidence of branch overloading. Correlation with clamp-affected branches is not causal proof; do not use this localization to retune on the new set.

## Experiment 8 — Evidence package and paper decision

Deliver one main table, three small figures and runnable compact artifacts:

1. Main table: selected ordinary/spatial/higher outcomes, all seed values plus mean/range, strict feasibility, raw cost/state errors, time/memory. Baselines mandatory. Separate matched-step table.
2. Figures: validation learning curves; per-seed E−C_m contrasts with separate P/Q trade-offs; ordinary-to-spatial paired change for ridge/C/E/C_m. Generate from saved CSV/JSON, not manual transcription.
3. Diagnostics: calibration ratios and gradient/clipping traces; reference-state mismatch and bus localization; acceptance/failure coverage; configs/hashes/commands and actual compute breakdown.

Interpretation is conditional:

| Result | Permitted conclusion / next paper decision |
|---|---|
| E beats C but loses or ties C_m | Initial penalty magnitude is a plausible explanation; correction benefit beyond this control is unestablished. |
| E beats C_m in all three primary contrasts with useful raw-unit effect sizes | Evidence of an effect beyond this particular initial norm match; inspect fixed-step, P/Q and cost/state trade-offs before claiming a mechanism. Not complete scale invariance or proven novelty. |
| Seed signs differ or effects reverse at matched endpoints | Report instability; do not headline uniform superiority. |
| E beats C but not S | Evidence may concern harm from the stock penalty; no demonstrated benefit beyond supervision. |
| Ridge remains better / strict feasibility stays zero | Do not claim a practical OPF replacement, achievable cost savings or useful foundation-model superiority. A reproducible loss-consistency study remains only a candidate for professor review. |

The potential five-page story is one numerical mechanism, its controlled learning effect and its limitations under demand relocation. Standard fine-tuning, LoRA and OOD testing themselves are established; use the [prior-art review](../literature/2026-10-21-adaptation-update.md). One topology, one 50-label dataset, three training seeds and a small holdout do not settle publishability. Cross-case mechanism replication or a targeted remedy may be needed later; do not launch them automatically in this session.

Append a new GSFM-005 Results block to Exchange; preserve every GSFM-004 result. State COMPLETE/PARTIAL/BLOCKED by experiment, what ran, what improved, what failed, whether the magnitude control changed the interpretation, and the next scientific decision. Include a short honest professor-update draft in the artifacts if useful, but do not send it. Review/commit/push scripts and compact non-sensitive results normally; retain raw matrices/checkpoints/predictions locally with hashes and retrieval instructions, disclose their local-only status. No force push, email, submission or publication is authorized. **Then stop.**
