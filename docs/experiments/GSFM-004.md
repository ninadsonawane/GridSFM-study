# GSFM-004: bounded experiment discovery on M5 Pro / 64 GB

**Revision 2: five-hour ceiling, requested by Ninad on21October2026.** The earlier eight-hour/two-seed version is superseded. Keep the six comparisons, use one seed, reduce the update and development-evaluation budgets, and defer extra-network/MPS checks. This is exploratory evidence only.

Status: READY for the bounded local pilot below, requested by Ninad on 21 October 2026. This supersedes the operational stop after the GSFM-003 smoke check. Reuse completed GSFM-003 evidence; run its missing correctness checks before training. This is a research-direction screen, not the final paper evaluation. No experiments in this document have yet been run by the planner.

## Purpose and scope

Answer four questions with one shared dataset: Does the corrected power-balance loss change learning? How much of the model needs updating? Does pretraining offer useful early learning compared with simple predictors and random initialization? Do improvements survive a different spatial distribution of demand?

Use original MATPOWER 8.1 case300, the existing independently checked PowerModels/Ipopt solver, and the released Microsoft GridSFM v1.1 checkpoint SHA256 `f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831`. Preserve source topology, impedances, shunts, taps, costs, limits, and the 100 MVA base. RATE_A=0 means unlimited; do not invent interior thermal limits. This task authorizes a bounded pilot on the existing local machine, not an open-ended sweep, paid/cloud compute or conference submission.

Run one orchestration process. Record START/RUNNING and run ID in Exchange before execution. If another worker already owns this task, do not launch a duplicate. Preserve prior Results and artifacts; append this task's result block. Use `results/pilots/GSFM-004/<unique-run-id>/` and a separate experimental module/worktree rather than overwriting the pinned model. Make checkpoints resumable, but do not automatically restart a stopped task beyond its budget.

## Budget and hardware policy

- **Five hours total elapsed execution budget**, including implementation/debugging, labels, smoke, training, evaluation and reporting. Stop compute by4hours40minutes and use the last20minutes to report. This is a ceiling, not a runtime guarantee; finish sooner when complete. If prerequisites consume the budget, return the completed checks and blocker instead of silently escalating. If a worker already started the older version, count elapsed time from its original start, preserve completed work and stop at the next safe checkpoint if already past the new deadline. Do not reset the clock or launch another worker.
- At most **six main fits**, seed11 only. Each has at most **200 optimizer updates and25minutes including validation/checkpointing**, whichever comes first: at most150minutes of fit windows. Keep the remaining150minutes for setup, labels, checks, evaluation and reporting. Start a fit only if the remaining compute window can accommodate its predicted duration plus final evaluation. No second seed or extra-network/MPS checks in this revision. Preserve and explicitly label skipped/partial/failed work.
- Sequential execution: one model/optimizer resident, batch size 1, Torch 4 threads, BLAS 1, data-loader workers 0. Keep labels resident or in a small local cache. Do not train while generating solver labels.
- Use the working **CPU FP32 backbone and CPU float64 differentiable physics**. Preserve original-precision source parameters in an aligned physics copy; casting rounded FP32 parameters back to float64 is insufficient. Both stock/exact losses use the same precision and dtype-safe buffers. Keep model features/forward/context unchanged.
- Record process-tree peak RSS, available system memory and seconds/update. Checkpoint and stop a fit if measured process-tree RSS exceeds 32 GiB or available system memory drops below 12 GiB. These are conservative operational bounds, not measured model requirements. No parallel fits or memory-pressure workaround that changes the experiment.
- Defer MPS compatibility work. Keep the validated CPU path and identical precision across arms; no package/OS upgrades or backend changes are needed in this five-hour pilot.

## Experiment 0 — correctness and throughput gate

Hypothesis: the existing loss changes branch physics, and the custom training path can be made valid without changing the benchmark.

1. Record study/model commits, dirty diffs, source/checkpoint hashes, environment, exact commands and configuration. Sync the existing compact diagnostic scripts/provenance through the normal repository workflow after checking contents/licensing. Do not publish checkpoints, source matrices, credentials or bulky caches. Preserve local source/data artifacts with hashes and regeneration instructions.
2. Reuse frozen inference, reference reload and ID/units checks. Complete missing GSFM-003 operator/loss/gradient checks: stock versus exact KCL at identical predictions and accepted references; raw/weighted loss contributions, masks, capacity normalization and margin; gradient norms/cosines; original-parameter evaluator agreement. Skip disabled auxiliary computations rather than computing invalid values and multiplying by zero. Do not infer original pretraining behavior from the released fine-tuning loss.
3. Validate the actual labeled training path: target order `(theta,V)` and `(Pg,Qg)`, per-unit units, reference angle anchoring, all feasible masks, fresh graph copies, no target leakage, and model/batching/backward correctness. Inspect intermediate tensors, gradients and parameters for nonfinite values; the model's `nan_to_num` can conceal them. Do not count a sanitized output as a passed numerical check.
4. Use up to 8 accepted smoke-training and 4 smoke-validation scenarios from GSFM-003 if available, otherwise generate its stated samples. They are development-only and excluded from all datasets below. For each of the six variants below, run at most 20 disposable updates or 120 seconds. Then reload initial weights and reset optimizer/RNG; smoke updates never carry into main fits. Confirm that untrained LoRA+heads reproduces the frozen output, allowed parameters get gradients, frozen parameters remain unchanged, and checkpoint reload reproduces predictions.
5. Estimate a common update budget U before viewing learning outcomes: let t be the slowest variant's measured p95 full update seconds, including backward. Set `U=min(200,50*floor(900/(50*t)))`, reserving ten minutes within each25-minute window for validation/checkpointing. Measure validation overhead too. If U<50 or that overhead makes the cap impossible, return a throughput blocker instead of forcing updates or running mismatched budgets. Log U and the estimate for all six fits. Reduce U for all arms only before main training begins.

No main fit may proceed with invalid references, wrong target wiring, unhandled nonfinite gradients or failed operator alignment. A broken stock/exact operator blocks that causal comparison; independent CPU baselines and dataset audits can still finish. A failure unique to LoRA should be reported without blocking the other valid arms.

## Shared pilot dataset — all development data

Generate **50 training + 10 validation + 10 ordinary evaluation + 10 paired spatial-shift evaluation + 10 higher-load evaluation** accepted points (90 total). Do not generate, inspect or call any of these the final paper test set. Retain the same deterministic candidate streams below. If the earlier130-point dataset already exists, preserve it; use the first10 accepted points in each applicable development stream for this revision, with spatial counterparts grouped, without selecting by model performance. Do not regenerate labels or restart completed fits just to fit the smaller specification. Log any already-executed larger runs separately and compare their common saved checkpoints. This revision does not change the older proposed final study without a later amendment.

Use distinct NumPy `Generator(PCG64(seed))` seeds 30401/30402/30403/30404/30405 for training/validation/ordinary/spatial/high-load respectively. Persist actual factor arrays and candidate order, rather than relying on a seed alone. Normal training/validation/ordinary candidates use global scale U[0.90,1.03], and independently sampled per-bus U[0.98,1.02] factors shared between that bus's P and Q. Apply these factors to original nonzero loads, including their original signs; zeros remain zero. Topology/costs/limits stay fixed. Higher-load candidates use global U[1.035,1.06] and the same local jitter. These intervals are proposals, not promises of feasibility.

For the10 spatial cases, pair each with one accepted ordinary evaluation state. Change load location while preserving **both total P and total Q and each affected bus's P/Q ratio**:

- Build an undirected graph from online branches. Define four regions before evaluating models: choose the first center as the smallest positive-load bus ID, then choose each further center by greatest shortest-hop distance to existing centers (ties: smallest original ID). A region is the nearest ceil(N/4) positive-Pd buses to its center, sorted by hop distance then ID; overlap is allowed. Save region membership.
- For pair j, use region `j mod 4`. On positive-Pd buses only, form u=+1 inside and -1 outside. Form A with the current paired state's Pd and Qd vectors as rows, normalizing each nonzero row by its Euclidean norm. Compute thin SVD A=U diag(s) Vh, retain rows Vr of Vh whose singular values exceed 1e-12 times the largest, and use `d=u-Vr.T @ (Vr @ u)`. This projects into the null space of the two totals without squaring the condition number. Log numerical rank and tolerance. If max(abs(d))<1e-10, mark the perturbation degenerate and skip it; do not choose a new region based on model error.
- Let `f=1+0.10*d/max(abs(d))`, using alternating signs for successive four-region cycles. Multiply both P and Q of each eligible bus by f; keep other buses unchanged. Thus each affected load changes at most 10%, its P/Q ratio is retained, and aggregate P/Q remain unchanged to roundoff. Verify total P/Q differences <=1e-8 of max(1,sum of absolute corresponding loads); save actual residuals and demand moved into/out of each region. The projection can modify the idealized region pattern: report the actual pattern, not an assumed uniform regional shock.
- Solve each paired variant once using the same reference pipeline. An unsuccessful solve stays unknown and is not replaced with a hand-picked easier case. The accepted paired count may be below10. Keep ordinary metrics on all10 and paired shift metrics on the explicit common accepted subset. Record grouping so both members of a pair stay together in any resampling.

For training/validation/ordinary/high-load, cap attempted candidates at three times the requested accepted count per split. Use an external 30-second wall watchdog per solve in addition to the existing solver settings; record timeouts as unknown. Accept only locally solved references that pass the independent full physical checker. Do not relax limits or classify failed local solves as truly infeasible. Record all attempts and acceptance fractions. If training or validation target counts cannot be reached, stop fitting and report coverage; never silently shrink or change their ranges. Partial evaluation slices may be reported with their actual counts and selection limitation.

Save hashes of factor arrays and scenario content; exclude duplicates and smoke/previous nominal diagnostic scenarios. Apply each factor only once. No solver reference is used as a neural input. Label-conditioned acceptance means reported model performance is conditional on accepted reference cases; say so.

## Experiment 1 — cheap baselines and practical value

Hypothesis: a foundation model learns more than narrow interpolation between nearby operating points.

Fit on the same 50 training examples only:

- **Nearest training example:** input is concatenated bus Pd/Qd. Standardize nonconstant input columns using training statistics only; discard zero-variance columns. Retrieve the nearest training vector in Euclidean distance and return its entire saved voltage/dispatch solution. Anchor angles consistently. Recompute its physics using the *new* input loads.
- **Ridge regression:** the same standardized inputs predict concatenated anchored angles in radians, Vm, Pg and Qg. Standardize output columns using training-only statistics, restoring constant output columns explicitly. Fit intercept and L2 coefficient alpha from {0.01,1,100}, choosing using the common validation score below; break ties toward the larger alpha. Record the extra three-candidate tuning budget rather than portraying it as identical optimization to neural arms. Decode to physical units before scoring.
- **Frozen GridSFM:** evaluate the pinned checkpoint on precisely these same scenarios, not just the older nominal result.

Report raw predictions for every method. No hidden clipping, power-flow repair or solver projection. If optional clipping is shown, show it as a separate identically applied secondary column for all methods. A cheap predictor matching GridSFM challenges practical value; it does not prove a universal limitation of pretraining.

## Experiment 2 — does the physics correction matter?

Start three independent copies from the same released checkpoint, reset all state, and use identical 50-label data and shuffled batch order within each seed:

| ID | Trainable weights | Objective |
|---|---|---|
| S | All regression-relevant model weights | Released supervised voltage/angle/generation terms + cost, KCL disabled |
| C | Same as S | Same objective + stock clamped KCL |
| E | Same as S | Same objective + original-parameter exact KCL |

Freeze `head_feas` in all trainable arms. The disabled feasibility head is not part of "full" regression fine-tuning. Coefficients: supervised terms as released, lambda_cost=1, lambda_kcl_p=lambda_kcl_q=1 for C/E and 0 for S, lambda_feas=lambda_stress_feas=0. Disable synthetic negatives. Retain other shared released coefficients (lambda_br_p=1, lambda_br_q=1, lambda_therm=1, lambda_thermal_limit=5), but report their active counts and actual contributions: on original case300 they should have no eligible rated branches. If nonzero masks contradict the audited case, stop and investigate rather than invent ratings.

C/E differ only in the KCL denominator treatment. Match precision, weights, normalization, compression, aggregation and everything outside that KCL call path. Forward epsilon, context clipping and features remain identical. The earlier GSFM-003 contains operator implementation details.

Record whether E improves independent physical residuals versus C **and** S, with cost/state errors alongside. If E only matches S, the finding is harm from the distorted penalty, not benefit beyond fitting labels. If C and E agree, report that the diagnosed numerical difference has no demonstrated learning effect in this pilot.

## Experiment 3 — adaptation capacity and early benefit of pretraining

Add three arms using **exactly S's no-KCL objective**, same batch order, update budget and shared settings. This avoids confounding adaptation capacity with a changed loss.

| ID | Initialization and trainable parameters | Question |
|---|---|---|
| H | Released checkpoint; only `head_theta`, `head_V`, `head_Pg`, `head_Qg` | Are output-layer updates enough? |
| L | Released checkpoint; rank-2 FFN LoRA, alpha=2, dropout=0, plus the same four heads | Do small backbone updates add value beyond H? |
| R | Fresh same-architecture random initialization; train same parameter set as S | Does pretraining accelerate early learning under this fixed budget? |

LoRA targets are `blocks.{i}.ffn.{node_type}.{0,2}` using the existing wrapper. It freezes base weights including heads by default: explicitly unfreeze the four regression heads, include adapters + heads in the optimizer, and log exact names/counts. `save_adapter()` alone omits trained heads; save/reload the head state as well. Match untrained L versus frozen outputs before training. Do not add a rank or learning-rate sweep.

For R instantiate from the recorded architecture configuration without loading pretrained tensors; resetting only the heads is not a scratch baseline. Verify initialization provenance. R has the same architecture and budget, not the same starting outputs. A poorly performing short R run supports only an early-learning comparison, not superiority over adequately trained scratch.

## Shared training and model selection

Use AdamW, lr=1e-4, weight_decay=1e-4, global gradient norm clipping=1, batch=1, constant LR, no mixed-precision autocast or augmentation. Shuffle the 50 scenario indices per epoch using a seed-specific generator; save the order and reuse across arms. Set all relevant RNGs and record any nondeterministic operation. Same learning rate is a controlled screen, not a final optimal tuning comparison for every method.

Run S,C,E,H,L,R for seed11 only. Pretrained arms reload the identical checkpoint; the seed fixes batches/adapter initialization. Never start an arm from another arm's trained weights. No second seed in this revision; do not make reproducibility-across-seeds claims.

Validate at update0 and every50 updates through U. Save enough snapshots to compare matched update counts. Common validation score is `mean_s log(1+max(Pmax_s/1MW,Qmax_s/1MVAr))`, using independent exact physics. Break ties by median absolute raw cost error then earlier update. Select checkpoints using only the10 validation scenarios, never the spatial/high-load development evaluation slices. Report selected-checkpoint and fixed-U performance. If an arm times out, compare all completed arms also at their last shared saved update and label any unequal endpoints. Do not hide failed arms or present incomplete runs as final rankings.

## Experiment 4 — spatial and higher-load robustness

After model selection, evaluate all saved selected models and baselines on the ordinary, paired spatial and higher-load slices. This requires no new training. Keep evaluation inside the4hour40minute compute deadline. Do not use the results to retune and then call them untouched tests.

Hypothesis: a method that looks good on familiar loading can deteriorate when demand moves to other buses, even though total P and Q stay the same. For the spatial pairs, report within-pair change in max imbalance, raw cost error, dispatch/voltage errors and feasibility, as well as absolute scores. Show actual demand movement. Separately report higher-load results; do not mix location shift and total-load shift into one average. Identify affected regions/buses descriptively without treating buses as independent trials.

No contingency sweep, further connected networks or learned solver-start experiments in this round. They would introduce additional questions before the first adaptation evidence exists.

## Deferred experiments

The second training seed, case39/118/500 breadth audit and MPS compatibility probe are deferred. Do not fill spare time with these or start additional fits; return the results early when the specified work is complete.

## Required outputs and decision table

Return one compact Results block plus machine-readable CSV/JSON and runnable commands, with status COMPLETE/PARTIAL/BLOCKED for every experiment. Minimum artifacts: environment/provenance; exact split/factor/group manifests and solver acceptance/failure records; trainable-parameter manifests; weighted losses/gradients; per-update train/validation traces; selected/final/common-step checkpoint identifiers; per-scenario predictions and independent metrics; peak RSS/time; all failure/stop reasons; artifact hashes and retrieval/reproduction instructions.

Every summary row must identify method, seed, split, accepted/evaluated count, steps, selected checkpoint, max-P/Q residual distributions (median/p95/worst across scenarios), strict joint-feasibility count, cost error, Vm/angle/Pg/Qg errors, box/active-angle/rated-line violations, trainable count, training seconds, median/p95 seconds/update and peak RSS. In original case300 report **zero rated branches / thermal criterion not applicable**, not "no congestion." Cost on infeasible outputs is a raw diagnostic, never an achievable saving.

Use the previous independent thresholds unchanged: P/Q balance and generator violations <=1e-3 MW/MVAr, voltage <=1e-4 pu, rated-branch <=1e-3 MVA, active angle <=1e-3 degrees. Report raw residuals even if all strict feasibility rates are zero. With10 scenarios per evaluation slice and one seed, p95/worst are especially unstable; show the individual paired values and avoid significance or across-seed stability claims. No novelty claim from this screen, and no bus-level pseudo-replication.

| Observation | Research direction it supports | Limit on interpretation |
|---|---|---|
| E consistently improves over C and S without materially worse cost/state error | Study exact-physics adaptation and the numerical mechanism | Requires larger untouched evaluation and stronger replication |
| E improves over C but only matches S | Study damage caused by the altered loss | No evidence exact KCL adds value beyond supervision |
| H or L approaches S while using less measured compute/memory | Study efficient adaptation, possibly under spatial shift | Neither LoRA nor few-shot adaptation is novel by itself |
| S beats R early and also beats simple baselines | Study useful pretraining under scarce labels | R may need longer training; not a universal superiority claim |
| Ordinary performance improves but paired spatial errors worsen | Study the reliability boundary and a targeted remedy | Stress testing alone is established prior work |
| All trainable arms fail or tie simple baselines | Diagnose learning curves/targets/optimization and reconsider scope | Do not force a positive paper or immediately add more networks |

Finish with five plain-language findings: what ran, what improved, what failed, which hypothesis merits a larger study, and its measured compute estimate. **Then stop.** Do not automatically launch the final100-label/three-seed study or expand this matrix. The [previous publication plan](../research/2026-10-21-publication-plan.md) remains background; this bounded discovery protocol now controls the next hardware run.

Research context: [GridSFM few-shot adaptation](https://arxiv.org/abs/2609.30173v2), [PF LoRA adaptation](https://arxiv.org/abs/2602.18227v2), and [physical-consistency analysis](https://arxiv.org/abs/2610.05959) already cover nearby ideas. This pilot selects a defensible question; it does not establish firstness. [PESGM2027](https://pes-gm.org/2027-san-francisco/2027-call-for-papers/) has a five-page limit and 10November2026 deadline, so prefer one mechanism plus one robustness result over a broad unfinished sweep.
