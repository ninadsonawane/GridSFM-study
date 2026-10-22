# Hardware Codex handoff — questions, findings and Experiments 12–14

23 October 2026. **Start here when continuing from another Codex account.** This is a concise research-context handoff, not a full chat transcript. Existing result files remain the evidence; the detailed next protocols are linked below. No Experiment 12–14 run is claimed.

## 1. What Ninad and the professor want

Working title: **Assessing the Practical Utility of GridSFM for AC Optimal Power Flow on Standard Networks**. The intended manuscript is a five-page experimental evaluation for IEEE PES General Meeting 2027. The proposed contribution is careful, reproducible assessment and electrical explanation; no new neural architecture or acceptance guarantee is claimed.

Professor Surya Santoso's supplied email directs the study to compare GridSFM with AC-OPF and DC-OPF on case300, check physical and operational constraints, and identify conditions producing significant errors or infeasible operating points. Generation cost and computational runtime are secondary. He also requested discussion with Dr. Li; this handoff does not authorize contacting anyone.

The thread initially explored Seiole Labs' transfer/OOD observations, LoRA/full fine-tuning, physics-loss numerics and practical solver completion. Ninad subsequently set adaptation and speed/cost comparisons aside in favor of the professor's frozen-model questions. Preserve earlier adaptation results as supporting history; do not resume training or silently treat historical adapted/repaired outputs as frozen predictions.

The chosen two-copy construction, detailed bus diagnostics and PGLib thermal extension are the next study designs developed in this thread. Do not attribute these specific choices to the professor. The user wants one experiment and a simple explanation at a time, with review before continuing.

## 2. The ten core questions and their current answers

These retain Q1–Q10 from [the original question register](../experiments/GSFM-008.md). That older document also lists study limitations, secondary cost/runtime metrics and discussion with Dr. Li as Q11–Q13; those remain scope/review items, not extra completed experiments.

| ID | Core question | Current evidence and remaining work |
|---|---|---|
| Q1 | What does GridSFM predict, and which release are we evaluating? | **Audited in 11A.** Microsoft v1.1 and newer base v2 are separately pinned. Native outputs include Pg/Qg/Vm and angles, with clipping, a DC angle prior and derived branch flows. Native prediction is separate from nonlinear PF completion or OPF refinement. |
| Q2 | How far are its predictions from AC-OPF? | **Answered for tested original case300 inputs in 11B/C-1.** State and flow errors are saved against independently checked local AC references. Experiment 12 extends to the two-copy construction; 14 to rated variants. |
| Q3 | Is GridSFM better than DC-OPF? | **Answered only for shared quantities and tested cases.** DC had smaller Pg, aligned-angle and active-flow MAEs than both frozen releases at all six reference-valid load points. This is not a general ranking or proof that DC produces an AC-feasible state. |
| Q4 | How are Kirchhoff's laws incorporated, and do the predictions satisfy them? | **Audited and measured.** Soft loss terms/features and flow reconstruction do not guarantee nodal power balance. Both frozen releases fail original P/Q balance. Branch consistency imposed by reconstructing flows from one voltage field is not proof of learned KVL. |
| Q5 | Are generator active/reactive limits satisfied? | **Measured.** Native Pg/Qg satisfy the stated bounds within the fixed tolerances on these runs, consistent with hard clipping. Historical PF-completed states are a different stage and may violate limits. Recheck all new cases. |
| Q6 | Are transmission thermal limits satisfied? | **Unanswered for original case300:** all 411 RATE_A values are zero/unlimited. Experiment 12 assesses only its two rated synthetic ties; Experiment 14 supplies published interior ratings in distinct PGLib variants. |
| Q7 | Are bus-voltage and applicable angle constraints satisfied? | **Measured with coverage limits.** Native Vm is within tolerance after clipping. Original branch-angle bounds are disabled at +/-360 degrees, so no nontrivial angle-limit stress was tested. Reassess the actual constraints in new cases. |
| Q8 | Is the complete predicted operating point feasible? | **No for all 14 saved frozen states** across two releases and seven original load levels: balance fails. Six inputs have known feasible AC references; input feasibility at 1.10 remains UNKNOWN. Thermal safety is not assessed on original case300. |
| Q9 | Under which conditions do errors occur or change? | **Partially answered.** The loading screen covers 0.80–1.10; errors change nonmonotonically and the worst bus can change. Separate reactive-demand and spatial/random families from the old 31-input plan were not executed. Experiments 12/14 add prescribed inter-area and rated-case conditions, not an exhaustive failure envelope. |
| Q10 | Where do failures originate, and are they prediction or evaluation effects? | **Partially answered by 11A/D.** Independent formulations agree; voltage/angle/generation errors, sensitive branches and cancellation explain measured residuals. They do not identify the training cause. Experiment 13 improves structural comparisons and measures accuracy, sensitivity and cancellation separately. |

## 3. What the previous experiments actually established

| Evidence | Short conclusion | Read when needed |
|---|---|---|
| Experiments 9–10 | Adaptation improved some PF completion outcomes, but PF convergence did not establish full feasibility. Historical settings/stages differ from the frozen default study; do not pool them. | [Experiment 9](../../results/pilots/GSFM-006/20261021T171629Z-m5-new-pipeline/README.md), [Experiment 10](../../results/pilots/GSFM-007/20261021T195824Z-m5-practical/README.md) |
| 11A | Both frozen releases runnable; label-independence and original-equation checks passed. Native bounds are clipped. Stock loss-operator mismatch on a feasible state was measured, but is not established as the cause of frozen failure. | [Audit](../../results/audits/GSFM-011A/20261022-case300-pipeline/README.md) |
| 11B | Original base case has a verified feasible AC reference; both native models fail balance, while DC is closer on the three shared MAEs. | [Base comparison](../../results/comparisons/GSFM-011B/20261022-original-case300/README.md) |
| 11C-1 | Six additional load inputs, with the base reused. Five new AC references pass; 1.10 has no accepted reference. All 12 additional native predictions fail balance. | [Loading comparison](../../results/comparisons/GSFM-011C-1/20261022-loading-only/README.md) |
| 11D | Saved-state diagnosis reproduces residuals; inconsistent endpoint voltages/angles and generation errors explain the signed budgets. Low residuals sometimes conceal cancelling errors. Seventeen of 18 comparator matches were poor. | [Detailed diagnosis](../../results/diagnosis/GSFM-011D/20261022-saved-states/README.md) |

Useful base-case anchors: DC Pg MAE is 26.09 MW, Microsoft 195.13 MW and newer v2 106.40 MW. Microsoft maximum P/Q imbalance is about 3,754/8,938 MW/MVAr; newer v2 about 3,211/7,958. These are source-report values checked in the repository for this handoff, not new hardware reruns.

The named buses are **238, 231 and 137**, using original external IDs. In 11D, inconsistent voltages across the low-impedance 235–238 connection amplify reactive-flow errors; a small angle-difference error on 231–237 produces large active-flow error; newer v2's voltage at 137 is far from its neighbors. Failures remain widespread beyond these hotspots. Reference substitutions are oracle diagnostics, not practical fixes.

**Defensible present conclusion:** on these tested original case300 operating points, native frozen GridSFM does not return physically valid AC operating points, despite nearly compliant individual bounds. DC is closer to the accepted AC reference on the shared measures tested. We can explain important electrical mechanisms of the failures, but cannot conclude that the whole model is universally bad, that OOD exposure is the proven cause, or that fine-tuning necessarily solves them.

## 4. Exactly what comes next

Read [the common protocol](../experiments/GSFM-012-014-common.md) before the individual experiment. It contains checkpoint/source pins, independent checks, metrics, thresholds, artifact rules and bounded resource plans.

| Experiment | Detailed protocol | Scope and intended finding |
|---|---|---|
| **12** | [GSFM-012.md](../experiments/GSFM-012.md) | Original MATPOWER case300 + case300, using the existing two parallel bus-231 ties. Three conditions: A/B loads 1.00/1.00, 1.05/0.95 and 0.95/1.05. Compare AC, DC and both frozen releases. Assess inherited-grid failures and inter-area exchange. |
| **13** | [GSFM-013.md](../experiments/GSFM-013.md) | Saved-state analysis of original 300 and constructed 600. Separate prediction accuracy, standardized electrical sensitivity and signed cancellation. Use admissible structural matches and corresponding A/B buses; report unmatched buses rather than forcing a comparison. No new inference or solves. |
| **14** | [GSFM-014.md](../experiments/GSFM-014.md) | Complete published rated PGLib300 and its two-copy derivative. Eight prescribed inputs including rated bases, matched rating-disabled controls and bounded load changes. Measure both-end thermal violations, response to ratings and joint feasibility. |

This is a **600-bus construction**, not a standard IEEE case600 or a second independent topology family. Increasing bus count alone establishes neither in-distribution status nor the cause of performance differences. The PGLib variants also change fields other than ratings relative to MATPOWER; use their matched rating-disabled controls for the specific ratings-effect question.

Experiment 13's newer-release-first presentation is a protocol choice, not a final manuscript decision with Dr. Li. Retain both releases and all outcomes. All current case300 observations are inspected development evidence; these extensions do not retroactively turn them into blind confirmation.

## 5. How the other account should continue

1. In the existing hardware checkout, inspect branch/status and fetch `origin`. Preserve local result directories, untracked raw states and any work in progress. Fast-forward `main` with `git pull --ff-only origin main` only when appropriate. If local commits diverge or files would be overwritten, report the exact situation; do not reset, clean or discard anything.
2. Read `AGENTS.md`, the latest section of `HANDOFF.md`, this document and the four 12–14 protocol files. Prefer completed result reports to old planning statuses. This account does not need the full prior chat or access to Exchange to understand the task.
3. Check that the existing hardware environments, source cases, model weights and saved raw states are accessible. Git contains compact evidence and hashes, but some raw artifacts remain local-only. An account switch does not prove they are available. Missing paths, changed hashes or undocumented settings must be reported, not guessed or replaced.
4. First return a brief understanding/readiness report. **Reading or pulling this handoff is not an instruction to start computation.** Ninad will give the execution instruction in the hardware account. On “Start Experiment 12,” implement/run only 12, report and stop. Continue to 13 and 14 only after their respective review/start instructions.
5. During execution, preserve completed evidence, record actual rather than predicted status, and return plain-language conclusions linked to Q IDs. Ask Ninad if a required fact or design choice is missing and cannot be established from the repository. Do not expand scope, change constraints or make a result-driven choice silently.

This handoff authorizes no external messages, paper submission, new training, paid compute or automatic experiment sequence. The current task publishes documentation to GitHub only; the hardware runs will happen under the user's instructions in the other account.
