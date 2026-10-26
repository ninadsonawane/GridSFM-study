# GSFM-018 — representation gate and bounded original-case300 continuation

Date: 26 October 2026 (Asia/Kolkata). Parent: `b4c2a02720e86482b7e60d3d7d41cc70fc3a2848`.

The current user objective authorizes staged autonomous investigation but requires resolving Experiment 16's row-permutation interpretation blocker before dependent electrical discovery. This supersedes older completed-task stop instructions only for this bounded task. No publication, correspondence, training, fine-tuning, checkpoint selection, sigmoid override, PF completion or OPF repair. Only original MATPOWER 8.1 case300 is in scope. Earlier data and predictions remain immutable.

## Gate before electrical discovery

Inspect both pinned released pipelines from original matrix conversion through prepared node/edge/context features, positional features, cycle features, DC prior and forward output mapping. Use original and reversed-row inputs already defined in Experiment 16; these are representation diagnostics, not new electrical conditions. Verify physical equivalence and model-ready feature equivalence separately. Inspect deterministic ordering and repeatability before assigning differences to numerical nondeterminism. Record the first non-equivariant operation and test a proposed cause separately from released defaults. An identified feature discrepancy alone does not prove the size of its contribution to the historical output discrepancy.

Missing preserved raw states, checkpoints or the historical environment must be reported before dependent work. A reconstruction from tracked diagnostic tables is a labelled derivative, never a replacement raw model return. No repeated historical solve or forward solely to hide missing artifacts. A minimal forward repetition is justified only to isolate the representation cause, with source, checkpoint, input and environment hashes and an explicit diagnostic label. Keep any experimental pipeline correction separate; never silently replace prior results.

**Stop gate:** do not launch the electrical schedule below if native-output mediation remains unresolved or a faithful four-method run is unavailable. Deliver the source/probe evidence, a complete saved-evidence synthesis, limits on supportable conclusions, and the next decision. An early stop is a valid outcome. No new model inference or OPF solve is implied by this protocol file.

## Stage A — hypotheses fixed before new electrical inputs

These hypotheses are motivated by already inspected Experiments 11C and 15–17; this is not a retrospective claim that those observations were preregistered. Original IDs/order, parallel rows, shunts, taps, phase shifts, statuses, costs, negative/zero loads and limits remain unchanged except for the named field. All RATE_A stay zero: thermal assessment is N/A. Reuse a historical point only after matching complete input and release/settings hashes.

| Mechanism | Conventional expectation and assumptions | Model hypothesis and plausible explanation | Evidence against the explanation |
|---|---|---|---|
| P-only versus Q-only global loading | Scale signed Pd or Qd only. P growth generally changes real dispatch/losses and may change Q/voltage active sets; monotonic cost or residual growth is not guaranteed. Q-only is an exact DC null control because Qd is absent from this DC formulation. Verified AC equations remain satisfied at accepted local optima. | A lower Pg MAE may arise from movement of the AC reference toward clipped native dispatch, while voltage/angle errors across high-admittance branches worsen local imbalance. Separate native changes from reference changes. | Native Pg moves toward AC more than reference movement explains; or severity and accuracy improve together across mean, tail and maximum, without the proposed voltage/angle contribution. |
| Fixed-total local redistribution | Reuse Experiment15 source-selected five-bus groups and proportions. Preserve total Pd and Qd separately. Local voltage/Q response and losses can change despite constant net demand; the admittance proxy is not a validated weak-grid classification. | Distribution of load changes voltage/angle predictions and amplifies residuals at stiff branches, with little change in aggregate Pg accuracy. | Effect disappears at both nearby strengths; depends on only a single summary maximum; or prepared-feature/order variation, clipping or reference active-set changes account for it without the proposed electrical pathway. |
| Positive branch charging at 90% loading | Scale strictly positive branch b only; negative/zero charging and bus shunts unchanged. Extra capacitive charging often reduces required Qg, conditional on changed V and losses. More lower-Q-bound activity is possible. DC is exactly invariant. Synthetic parameter intervention, not line replacement. | More capacitive support need not improve native Qg/V accuracy. A lower maximum residual may coexist with worse average/tail imbalance because output errors and cancellation move. | Qg/V errors and all residual distribution metrics improve consistently at nearby strengths, or changes are fully explained by movement of the AC reference with invariant native states. |

## Stage B — fixed discovery schedule, at most 10 new distinct electrical inputs

Run the following in listed order only after the gate passes. Do not fill the budget with extra inputs. Reuse saved 100% loading, P-only +10%, Q-only +10%, full-strength redistribution in both directions, and 90%-loading charging factors 0.50/1.00/1.50 when hashes match.

1. P-only factors **1.05, 1.15** at original Qd (2 new).
2. Q-only factors **1.05, 1.15** at original Pd (2 new).
3. Redistribution strengths **0.50, 1.50** times the saved Experiment15 transfer, in each of its two directions (4 new). At strength 1, the transfer is 20% of the smaller group's total, separately for P/Q. Multiply the same source-fixed transfer vectors; verify positive recipients/donors do not cross zero and totals match FP64 tolerance.
4. Positive charging factors **0.75, 1.25** at 90% Pd/Qd (2 new).

Every new input gets AC-OPF, DC-OPF and both frozen native releases. Save native returns before evaluation. Use existing AC 120-second/3,000-iteration cap and at most one deterministic flat retry; retain failure as UNKNOWN. No result-driven replacements. Stop early on input preservation, label-invariance, original-physics, feature-preparation or environment failures. If execution fails before all four methods return, retain the input and all partial statuses; it counts toward the budget.

## Stage C — conditional confirmation, at most 6 additional inputs

Do not select or run confirmation until discovery is complete and reviewed for correctness. Before inspecting their results, save an immutable selection manifest (maximum six points) that names the candidate, nearest bracketing points, at least two summary metrics and the relevant null/representation control. Prefer the strongest coherent multi-metric pattern, not the best isolated number. No unplanned mechanism or benchmark. Total newly tested electrical inputs must never exceed 18, and this plan initially commits only 10. Unused allowance is not an instruction to expand.

## Evaluation and interpretation

Use independent FP64 original equations and branch-sum/Ybus agreement below 1e-6 MW/MVAr. Accept AC only when all original constraints pass; local optimum, not global certificate. Balance/generator tolerances 1e-3 MW/MVAr; voltage 1e-4 pu; angle 1e-3 degrees. Report native signed P/Q, absolute mean/median/p95/max, fixed-tolerance bus counts, Pg/Qg/Vm/angle excess counts/magnitudes/locations, joint feasibility, true pre/post clamp counts/material magnitudes and separate lower/upper bound activity. Saturated counts require severity/distribution/location reporting. Clipping and bound activity are not violations or joint feasibility.

Against each accepted AC reference report Pg/Qg/Vm/aligned-angle/both-end active-flow MAE. DC Qg/Vm/joint AC feasibility are N/A. DC flows use DC laws; neural flows use exact AC reconstruction from native phasors. Reference-dependent errors are N/A for UNKNOWN AC outcomes. Explain changes using original bus/gen/branch IDs and native versus reference movement; oracle block substitutions are labelled diagnostics, never practical repairs or causal proof.

Retain every attempted input and failure, identify reused evidence, preserve the original ordering for primary electrical comparisons, and distinguish discovery from confirmation. No novelty claim without primary-source checks. Finish with either a scoped defensible finding or "no defensible new finding", plus one next decision for Dr. Li.
