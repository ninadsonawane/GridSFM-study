# Physics-consistency contribution: adversarial assessment

Independent technical-review notes. The controlling sample counts and execution limits are in [publication-plan.md](../research/2026-10-21-publication-plan.md) and [GSFM-003](../experiments/GSFM-003.md). Proposed alternatives below are analysis, not additional queued experiments.

Prepared 2026-10-21. Read-only audit of the pinned Microsoft release plus primary literature. VM numerical results below were supplied by the parent agent; I did not independently rerun them. No experiments, repository edits, or Google Doc edits were made by this subagent.

## Recommendation and boundary

The defensible candidate is **a controlled study of whether physically inconsistent fine-tuning losses impede adaptation of a released AC-OPF foundation model to a standard target network**. It is not a new OPF algorithm, the first physics-informed loss, the first small-grid study, or the first demonstration that voltage accuracy can conceal infeasibility. A one-line denominator correction alone is a software issue, not a strong research contribution. A compact conference study becomes more credible if it demonstrates the mechanism, its occurrence beyond one edge list, matched held-out adaptation outcomes, and a reproducible way to detect this class of mismatch.

The causal claim must remain narrow: **the released fine-tuning objective differs from the original case300 equations**. This does not establish that the same implementation trained the released checkpoint, nor that it caused the checkpoint's frozen inference errors. Changing a training loss without training does not change a frozen prediction.

## Closest prior work and overlap

- [Kim et al., Physics-Informed but Not Physics-Consistent, arXiv:2610.05959v1, 5 October 2026](https://arxiv.org/html/2610.05959v1): very close and essential citation. It studies voltage-error geometry and post-training calibrated subspace projection, including GridSFM over 31 systems and four models on a 2224-bus system. However, its section 3 states that all models are trained from scratch; GridSFM and LUMINA are adapted to AC-PF by fixing generator dispatch and predicting voltage states. Its correction is not exact feasibility projection. This excludes generic claims about the accuracy/consistency gap, cross-grid failure, or projection as our novelty. It does not, in the inspected paper, analyze the released OPF fine-tuning denominator clamp or an adaptation comparison differing only in that operator.
- [LUMINA-Bench, arXiv:2605.02133v1](https://arxiv.org/html/2605.02133v1): already compares supervised and constraint-aware AC-OPF objectives, architecture, pretraining/adaptation, numerical precision, and diagnostic error concentration. Its implementation invariants standardize non-treatment factors. Therefore, "physics loss helps transfer" and "fine-tuning helps" are insufficient contributions. Our possible distinction is a specific benchmark-semantics mismatch with a causal correction, not another broad loss comparison. Its conditioning and precision experiments motivate controlling precision in both arms.
- [LUMINA, arXiv:2603.04300v1](https://arxiv.org/html/2603.04300v1): establishes topology transfer and feasibility-aware foundation-model design as existing work. Avoid claiming the basic transfer framework.
- [Nellikkath and Chatzivasileiadis, EPSR 2022](https://www.sciencedirect.com/science/article/pii/S0378779622005636): embeds AC-OPF equations during learning and studies constraint violations. Exact AC equations in a training objective are long established.
- [Power Flow Analysis using Dynamically Weighted DNNs, PESGRE 2023](https://ieeexplore.ieee.org/document/10404644/): dynamic weighting addresses gradient imbalance in physics-informed PF learning across IEEE 5/33/57/118. Any later adaptive-weighting idea needs comparison, not a novelty assertion.
- [SafePowerGraph, Energy and AI, 2026](https://doi.org/10.1016/j.egyai.2026.100819): simulator-independent PF/OPF benchmarks, heterogeneous components, perturbations, and physics-aware training already exist. Do not call our proposed audit the first safety-aware benchmark.

Targeted searches did not identify a paper specifically evaluating the GridSFM `r*r+x*x >= 1e-6` fine-tuning clamp. This is limited search evidence, not proof of firstness. Newest direct overlap was checked rather than relying on older source lists.

## Confirmed source mechanics

Pinned code: [Microsoft/GridSFM commit 1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6](https://github.com/microsoft/GridSFM/tree/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm).

1. `loss.py:190` uses `z2=(r*r+x*x).clamp_min(1e-6)`, then `g=r/z2`, `b=-x/z2`. Thus it scales the true **series** admittance by `alpha=min(1,(r*r+x*x)/1e-6)`; charging terms remain as supplied. Parent-reported alpha values for three case300 branches are 0.2152, 0.37, 0.40. This is a changed physical operator, not merely residual normalization.
2. `model.py` forward branch flows instead add `PI_Z2_EPS=1e-12`. The parent reports this changes flows by less than 0.05 MVA in tested cases, far below observed raw violations. It is a separate implementation difference; preserve it in the causal training comparison and score all predictions with independent original equations.
3. `pe_features.py:433,463,470` clamps admittance magnitude at 1000 through the same squared-impedance floor in graph context. This can affect frozen forward predictions. Do not simultaneously change it in the primary loss experiment; that would confound the intervention.
4. `stress_features.py:155` clamps zero RATE_A to `1e-9`; original MATPOWER case300's RATE_A=0 means no thermal limit. Stress only feeds the feasibility head in frozen forward, so it cannot explain frozen dispatch errors. **During training**, `compute_loss` adds a stress regularizer, and feasibility BCE also has a differentiable path through stress into predicted states. Disable both equally across primary arms or fix them in a separate experiment.
5. `_gather_flow_inputs` requires positive rating AND `abs(x)>0.01` even for supervised branch flow loss. Consequently original case300 has no eligible branches for these flow/thermal terms. Report active-term counts; do not imply the model receives branch-supervision signals when it does not.
6. KCL loss divides by total generator capacity, gives 80% weight to a worst-bus term after a 1%-capacity margin, and 20% to the mean. A raw false residual of about 244 MW can have a small actual training contribution. Measure gradient contributions before assuming practical impact.
7. Several `torch.zeros` constructions in KCL helpers omit dtype. Casting inputs alone does not make the whole path float64 and can fail scatter operations. A shared dtype-aware implementation is required for both arms.
8. Promoting already-rounded FP32 graph parameters or reference labels to float64 cannot recover original precision. Keep source neutral-JSON physics parameters and accepted reference states in float64 for truth tests. If the backbone needs FP32 features, a separate map-aligned float64 physics copy can serve both loss arms. Quantify any conversion-roundoff floor rather than blaming the operator for it.

## Immediate task: short diagnostic and 20-step pilot

### A. Operator evidence, no neural training required

- Pin source commit, checkpoint hash, original case hash, all conversion maps, solver version/options, and exact accepted reference states. A solver `success` flag alone is insufficient; retain independent physical checks.
- At each accepted exact AC-OPF reference, compute raw MW/MVAr residuals under (i) exact original MATPOWER equations, (ii) current clipped fine-tuning operator, (iii) forward operator. Use identical states, parameters, taps, charging, shunts, and float64. Report per-bus residuals, affected edges, false-residual maxima, and absolute totals.
- Audit all shipped sample networks for count/fraction of branches below the loss threshold. Without validated reference solutions this is **exposure**, not a demonstrated violation rate.
- Add original IEEE39 as a cheap negative control. The inspected MATPOWER8.1 case39 branches have magnitudes above 0.001 p.u.; stock and exact loss operators should agree at ordinary baseMVA. No extra case39 training matrix is needed.
- Demonstrate gradient conflict carefully. Stock loss uses abs/amax; near-zero reference residual can have a nonzero subgradient due to numerical roundoff. Do not require its exact-loss gradient to vanish. Use `0.5*sum(raw_P_residual^2+raw_Q_residual^2)` as an explicitly separate smooth diagnostic, and report actual training-objective parameter-gradient norms and cosines at real predictions. A measured descent conflict is evidence; do not presume it.

### B. Small per-unit rebase control of the physics operator only

This is a derived consistency check, not a new inference test or a change to the main benchmark. For baseMVA `S0` and new base `S1=k*S0`, with voltage bases unchanged:

- Set `baseMVA=S1`, branch `r'=k*r`, `x'=k*x`, branch charging `b'=b/k`.
- Keep physical MW/MVAr loads, generator quantities/limits, shunt GS/BS entries, branch MVA ratings, costs, voltage magnitudes/angles, taps, phase shifts, and baseKV unchanged. Converter-produced per-unit power and shunt admittance then change by `1/k` automatically.
- Use bases 25, 100, 400 MVA for the same physical reference; independently confirm physical branch flows, cost, and exact residuals are unchanged up to numerical tolerance. Never re-solve to hide a transformation mistake.
- The exact series admittance obeys `y'=y/k`; the clipped operator instead retains `alpha(k)=min(1,k^2*|z|^2/epsilon)` of the true series admittance. Therefore its physical-MW residual can change solely because the numerical base changes. Show the measured result, not only the formula.
- Do not demand full pretrained neural predictions be invariant to arbitrary bases: its feature training convention may assume a fixed base. The test targets the physical loss function. Do not claim per-unit invariance itself is novel.

### C. Matched adaptation smoke test

Use 32 accepted training scenarios, with separate validation and locked test IDs prepared now. Start each trainable arm from the identical checkpoint. Only 20 optimizer steps per arm initially; record wall time, RSS, losses, finite gradients, and gradient norms. This authorizes neither a long run nor a large hyperparameter search.

Arms: frozen inference; supervised/cost fine-tuning with KCL off; same fine-tuning with stock clipped KCL; same with exact KCL. Disable feasibility BCE, stress regularizer, and synthetic infeasible generation equally. Retain identical graph context, architecture, normalization, aggregation, optimizer, batch order, precision, and KCL weights. Both KCL operators use float64 arithmetic so denominator treatment is the intervention; stock float32 is diagnostic only.

The supervised/cost arm is not the unmodified full upstream training recipe. Name the auxiliary configuration explicitly. Record which losses are nonzero and why case300 thermal/flow supervision is absent. Skip disabled auxiliary computations when needed to avoid `0*NaN` contamination.

Pilot acceptance: all arms run with reproducible inputs and finite outputs; exact/reference operator test passes; measured throughput supports the remaining timetable; gradient evidence shows whether KCL has a meaningful influence. Twenty steps can establish wiring and compute feasibility, not a paper-quality generalization result.

## If the pilot supports continuation

Suggested core: 100 accepted training, 30 validation, 100 untouched test scenarios, three training seeds for the three trainable arms. Include independent spatial demand perturbations rather than only five common global multipliers. Fix P/Q scaling rules and accepted-scenario policy beforehand; retain failed solves as failure/unknown counts, not automatic infeasible labels. Use the same validation selection rule across arms and report a fixed-step endpoint as a robustness check.

Primary outcomes: independently recomputed raw P/Q residual distributions (mean, median, tail, maximum), all-bus all-constraint feasibility fraction at declared tolerances, voltage/generator bounds, prediction error, and cost error identified as error of potentially infeasible dispatch. For rating-free case300 do not claim thermal feasibility as a substantive achievement. Report uncertainty across paired test scenarios and training seeds, not only pooled averages.

Connected case300x2 is a secondary replication, not an independent benchmark topology or evidence of scale generalization. PGLib-case300 is a semantic variant, not an independent grid; it also changes the task. LoRA can be a later compute comparison if time remains, but is unnecessary for the central causal question. Full fine-tuning being slower is not established until measured on the actual CPU/MPS setup.

No claimed CPU timetable should precede actual per-step measurement. Budget roughly `number_of_arms * seeds * optimizer_steps * measured_step_time` plus preprocessing, validation, solver labels, reruns, and writing. Leave several days for analysis and submission formatting. If the exact operator gives no held-out benefit, report that honestly: the study has found a correctness issue but has not established adaptation benefit or conference-level novelty.

## Publication decision

Best positive result: a benchmark-correct physical loss removes false penalties and improves true held-out feasibility at matched prediction accuracy/compute, with mechanism-specific negative controls and released reproducible artifacts. This is materially stronger than connecting two case300s or adding LoRA.

Weak result: one solved case, one loss value, one successful training run, or only cost improvement while residuals remain huge. Those support a reproducibility report or upstream issue, not a defensible claim of a new solver. A broader benchmark/repair paper would require more independent networks and time than the current plan guarantees. Acceptance cannot be promised.
