# Experiment 11 / GSFM-008: frozen GridSFM physical validity against AC-OPF and DC-OPF

22 October 2026. Status: PROPOSED STARTER PROTOCOL, not run or inserted into Exchange To-do by the planner. The user's latest request explicitly sets adaptation, generation-cost comparisons and runtime comparisons aside. This document records every question in the professor's supplied email and maps it to evidence. It supersedes the adaptation/solver-speed emphasis for future planning; completed experiments remain preserved.

Working paper title: **Assessing the Practical Utility of GridSFM for AC Optimal Power Flow on Standard Networks**.

Central question: **How accurately does frozen GridSFM approximate an AC-OPF reference, does its predicted operating point satisfy the original electrical equations and operating limits, and when does it fail relative to a conventional DC approximation?**

## Question register — retain these IDs in results and the paper

| ID | Question from the email / necessary qualification | Evidence to produce |
|---|---|---|
| Q1 | What does GridSFM predict, and which released model are we testing? | Paper/code/checkpoint provenance; native outputs; any deterministic clipping/completion; no conflation of model generations. |
| Q2 | How far is its case300 prediction from standard AC-OPF? | Same-input Pg, Qg, Vm and reference-aligned angle errors; branch flows recomputed from voltage; per-case and original-ID errors. |
| Q3 | Is GridSFM better than DC-OPF? | Paired Pg/angle/active-flow errors on the same scenarios; separately assess dispatch usability under shared AC-PF assumptions. No single universal winner from one metric. |
| Q4 | How are Kirchhoff's laws incorporated, and are they satisfied? | Source audit of graph/cycle features, loss penalties and numerical completion; independent original-parameter P/Q nodal balance and branch-equation checks. |
| Q5 | Are active and reactive generator limits satisfied? | Separate Pg and Qg lower/upper exceedances for every online generator, including slack; do not silently clip. |
| Q6 | Are transmission thermal limits satisfied? | Both-end apparent-flow excess for positive source RATE_A only; publish coverage. Original case300 has none, so thermal validity is NOT ASSESSED there. |
| Q7 | Are bus-voltage and applicable angle constraints satisfied? | Vm excess above/below source bounds, active branch angle-limit excess and consistent reference angle. |
| Q8 | Does the predicted operating point satisfy all modeled constraints simultaneously? | Per-scenario constraint checklist and joint pass count with fixed tolerances and explicit thermal coverage. Native, recovered and solver outputs remain distinct. |
| Q9 | Under which conditions do errors or infeasible predicted points occur? | Controlled total-loading, reactive-demand and spatial-redistribution sweeps; ordinary random scenarios; maxima and tails as well as means. |
| Q10 | Where do failures originate, and which are model versus evaluation effects? | Localize buses/generators/branches; evaluate a known feasible reference in both independent and native physics operators; inspect masks/normalization/precision; distinguish measured effects from causal hypotheses. |
| Q11 | What are the limitations of the surrogate and this study? | Unknown training-topology exposure, only tested loading range, local AC reference, incomplete DC state, absent thermal ratings, ambiguous alternative optima and release-specific scope. |
| Q12 | What role do cost and computational runtime play? | Secondary for the eventual paper; not ranking objectives for this starter. Preserve the standard OPF cost functions to define the optimization problem. Record elapsed time only for reproducibility/resource control. |
| Q13 | What should be discussed with Dr. Li? | This register, exact checkpoint choice, fair DC recovery assumptions, rated-case extension, preliminary figures and paper scope. Drafting/planning does not send a message or schedule a meeting. |

## What already exists, and what is missing

Experiment 10 is complete at study commit `202c9bb`. Its [report](../../results/pilots/GSFM-007/20261021T195824Z-m5-practical/README.md) contains frozen newer-model predictions, independently checked AC references and physical metrics on case300 and PGLib118. Case300 frozen native PF failed on all 90 unique inputs; solver fallback later recovered 89/90. These are different stages, not evidence that the neural predictions were feasible. PGLib118 frozen PF converged on 90/90 but its original-physics full-feasibility count was zero. The report's 270 request counts are three repeats of 90 inputs.

Retain all earlier results. Reuse exact saved states only after matching source/input/checkpoint hashes and rescore with the common checker; do not redo training. Existing slices are now development evidence. **DC-OPF is missing from the central comparison.** The new Q-only loading study and systematic per-constraint audit also add targeted evidence. This proposed 31-input experiment is a discovery study; a later locked independent confirmation set would support final paper claims.

## 11A — Version and physics audit before interpreting predictions

Use original MATPOWER 8.1 case300, pinned in `manifests/matpower-source.json`: 300 buses, 69 generators, 411 branches. Preserve original matrices, costs, statuses, shunts, taps, phase shifts, negative/zero loads, IDs and parallel rows. Original RATE_A is zero on every branch. Do not invent ratings, remove low-impedance branches, change limits or feed solved case fields back into model inputs.

Distinguish two available frozen releases; no fitting or checkpoint selection:

- Microsoft v1.1, directly aligned with the whitepaper named in the email: source `1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6`, checkpoint SHA256 `f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831`.
- Newer release already used in Experiments 9–10: source `517a07531ea55a11bd81a89a6c6879695a2ba4b4`, base v2 checkpoint SHA256 `9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7`.

Use both as separately named frozen rows if existing environments are runnable; do not select whichever wins. If one is unavailable, record the missing comparison and restrict conclusions to the release actually tested. Confirm the main release for the manuscript with Dr. Li. A shared name does not establish identical architecture, coefficients, weights, output semantics or guarantees.

For each law/limit document four things: its representation in inputs, training-loss treatment, any hard output restriction, and any numerical enforcement after prediction. Link exact code and distinguish source capability from known checkpoint-training provenance. A soft penalty, a cycle feature or passing through a PF solver does not certify all constraints. Evaluate reference states under both the model's numerical operator and the unchanged original FP64 equations; prior denominator/rounding findings must not automatically be blamed for frozen prediction errors.

Use independent exact branch equations and original Ybus. For voltage phasors V, compute r = Cg(Pg+jQg) - (Pd+jQd) - baseMVA*diag(V)*conj(Ybus*V), with Ybus including bus shunts once. Report max/mean absolute real and imaginary residuals in MW/MVAr. Cross-check the existing independent branch-sum checker against MATPOWER makeYbus or another audited implementation on a known feasible reference, including transformer and shunt signs.

KVL/branch consistency needs careful wording: when all flows are derived from one set of nodal voltage phasors through the correct branch model, voltage/branch consistency is imposed by that reconstruction. It is not an independent demonstration that a network learned KVL. If the release predicts independent branch quantities, compare them with recomputed flows; otherwise mark that head-consistency test N/A. Cycle-angle telescoping alone cannot certify physical feasibility.

## 11B — Base-case comparison and fair DC handling

First run ONE unchanged case300 input through conventional AC-OPF, conventional DC-OPF and each frozen model. Validate the AC solver's result independently before using it as a reference. It is a feasible local optimum, not a certified global solution. Different feasible dispatches can arise from nonunique optima; distance from one reference alone does not prove infeasibility or universal inferiority.

Prefer standard MATPOWER `runopf`/`rundcopf` when already available. Otherwise reuse the audited PowerModels AC path and implement/verify a MATPOWER-equivalent DC quadratic program using the original generation costs, Pg bounds, losses-neglected P balance, shunt conductance at unit Vm, transformer tap and phase-shift terms, and applicable angle/finite-rating constraints. Audit equivalence against pinned MATPOWER `makeBdc` equations. Do not assume any solver formulation named DCP is identical. Do not require a large software installation or silently omit transformers just to produce a baseline.

Three conceptual methods remain AC-OPF, DC-OPF and frozen GridSFM; two GridSFM releases, if used, are versioned rows. Save native predictions before any numerical recovery. Main comparisons:

1. **Shared predicted quantities:** Pg, reference-aligned bus angles, and active branch flows versus AC reference. For DC report its own DC-law active flows. For GridSFM derive AC branch flows from its native Vm/theta. Report their differing definitions; these are approximation-error comparisons.
2. **Full native GridSFM state:** independently evaluate P/Q balance, Pg/Qg limits, Vm and applicable angle/thermal limits. If a release exposes only usable controls, do not fabricate a full native operating point; report native-output capability and assess its documented completion separately.
3. **DC native state:** Qg and voltage magnitudes are not predictions of DC-OPF. Mark those native metrics N/A. Do not invent Qg=0 and then rank it as an actual DC-generated AC state; a lossless DC solution is not an AC-feasibility certificate.

Optional but valuable once the base case passes: **shared AC-PF dispatch check** for both DC and GridSFM. Hold each method's non-slack Pg fixed; use identical case-derived voltage controls for both: source VG projected once into original bus Vm bounds, with every projection disclosed and shared. Set PQ initial Vm=1 and flat nonreference angles for both; use original FP64 physics, the same reference bus, tolerance 1e-8 and maximum 40 Newton iterations/backtracking. Recover slack Pg and all Qg. Report slack adjustment explicitly because losses change the original dispatch. Disable Q-limit switching for this diagnostic and independently report all resulting violations; PF convergence alone does not pass limits. No reference Vm/angles/Pg/Qg, and no AC-OPF repair. This answers dispatch usability under stated shared controls, not validity of the original predicted operating point. A model's own predicted-voltage/native completion is a separate pipeline diagnostic.

## 11C — Small controlled screen: 31 unique inputs

Freeze all scenario definitions, release settings and thresholds before inspecting new outcomes. Fixed input order and original IDs; no replacement of difficult cases.

| Family | Inputs | Construction / isolated question |
|---|---:|---|
| Unchanged base | 1 | Establish mappings and reference comparison. |
| Total loading | 6 | Multiply every original Pd and Qd by lambda in {0.80,0.90,0.95,1.03,1.06,1.10}; preserve signs and zeros. Does total load change error/validity? |
| Reactive demand | 4 | Keep Pd fixed; multiply positive original Qd by {0.80,1.10,1.20,1.30}; leave zero/negative Qd and shunts unchanged. Does reactive stress expose errors invisible to DC-OPF? |
| Spatial redistribution | 8 | Four deterministic existing graph regions x two signs, at base total P/Q. Reuse the SVD-conserving method, at most 10% relative change at eligible positive-Pd buses; preserve local P/Q ratio. Save actual moved MW/MVAr and degeneracies. |
| Ordinary variations | 12 | PCG64 seed 811300; global U[0.90,1.03] times independent per-bus U[0.98,1.02]; multiply Pd/Qd by the same factor at each bus. Does the finding extend beyond selected stress points? |

For each candidate attempt AC and DC solves and frozen inference, retain statuses and score any produced state. A failed AC reference solve means reference-dependent errors N/A; independent constraint checks can still run. Local solver failure does not prove the input physically infeasible. Distinguish an **infeasible prediction for a known feasible input** from an input without a known feasible reference. No outages, topology/cost sweeps, training or penalties search in this starter.

Reuse the existing strict thresholds: balance and generator bounds <=1e-3 MW/MVAr, Vm <=1e-4 pu, positive-rating branch excess <=1e-3 MVA, applicable angle excess <=1e-3 degrees. Publish residual magnitudes too, so conclusions do not depend only on a binary threshold. Report a prespecified balance-threshold sensitivity at 1e-3/1e-2/1e-1 MW/MVAr separately, never use it to relabel the primary result. Undefined/incomplete native states have N/A, not fabricated pass/fail results. For failed inference/completion retain failure counts in method coverage.

Report separate Pg and Qg errors/excesses, Vm errors, aligned-angle MAE/max, active branch-flow errors, joint modeled-constraint pass rates, median/p95/worst scenario violations and original-ID locations. Avoid percentage errors at zero-reference Pg/Qg; use physical-unit errors and explicitly defined aggregate normalization where helpful. Report paired differences across the same inputs for the DC versus GridSFM shared metrics. A method may win Pg error and lose angle error; retain that finding rather than invent a composite winner.

For DC reactive-demand experiments, unchanged DC inputs should produce unchanged deterministic outputs (apart from solver numerical tolerances). This is an expected formulation property/control, not a newly discovered defect. Compare whether GridSFM responds appropriately to the changed AC problem.

## Thermal coverage and extensions

The original case300 experiment cannot answer Q6 empirically because RATE_A=0 means unlimited. Its joint pass flag must say **all modeled constraints passed; thermal coverage absent**, not thermally safe. Line-flow magnitude without a rating is not an overload diagnosis.

Discuss a published rated benchmark with Dr. Li, preferably the separately identified PGLib 300-bus variant to retain the size focus; PGLib118 already has completed development evidence available. These are different parameterized problems, not a drop-in ratings-only copy. Pin the selected source, preserve its costs/limits and rerun all compared methods on the same complete variant. Do not paste PGLib ratings into original case300 or infer ratings from reference flows. This extension is deliberately outside the first 31-input run.

## Resource envelope, artifacts and writing

Suggested M5 Pro/64GB execution envelope when scheduled: at most three hours including implementation and reporting, no training. Allow 45 minutes for DC/physics correctness integration, stop new computation at 2h40, reserve 20 minutes for delivery, finish earlier if done. This is a planning cap, not a measured runtime estimate. Use CPU and established environments, sequential requests, per-solver 30s wall/1000-iteration caps, record failed attempts. If base-case correctness fails, deliver that diagnosis rather than expanding. Preserve earlier files and hash every input/source/checkpoint; use a new run directory and no automatic continuation.

Deliver a row-level table keyed by Q IDs/scenario/release/output-stage, a constraint-coverage table, loading/reactive-stress plots, original-bus violation maps, source-code constraint audit, failed/unknown cases, reproducible script/config and a one-page findings note. Every Q is marked answered, partially answered or unresolved. Initial work can support paper sections: surrogate and physics assumptions -> benchmark methodology -> approximation/constraint results -> failure conditions -> limitations. Cost/runtime plots and adaptation are deferred.

Before a final claim, freeze the corrected harness and evaluate a new prespecified independent scenario set. This first screen and older inspected results remain discovery evidence. No conference-acceptance, unseen-pretraining or architecture-novelty claim follows from creating this protocol.

## Sources

- Professor's email: supplied verbatim and in the user's screenshot, 22 October 2026; a study-direction source, not independent evidence of model guarantees.
- [MATPOWER standard AC-OPF](https://matpower.app/manual/matpower/StandardACOPF.html): variables, constraints and branch-limit definitions.
- [MATPOWER standard DC-OPF](https://matpower.app/manual/matpower/StandardDCOPF.html): omits Vm and Q, uses a linear active-power network model.
- [MATPOWER AC-PF](https://matpower.app/manual/matpower/ACPowerFlow.html): slack/Q recovery; default PF does not enforce all operating limits.
- Existing [release audit](../technical/gridsfm-audit.md), [source pins](../../manifests/gridsfm-sources.json) and [case300 audit](../../manifests/matpower-case300-audit.json). Early manifests contain dated unrun-status fields; completed Experiments 4–10 artifacts supersede those historical execution statuses, not immutable hashes.
