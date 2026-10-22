# Experiments 12–14: shared hardware instructions

Prepared 22 October 2026. **PROPOSED; not executed by the planner.** These protocols implement the user's requested extension of the professor-directed frozen-model physical-validity study. They supersede older instructions deferring the two-copy system only for this bounded work. They do not resume adaptation.

**23 October hardware handoff:** Read [the context and question register](../context/2026-10-23-hardware-handoff.md) first. These documents are being published at Ninad's request. Pulling or reading them does not launch an experiment; wait for Ninad's start instruction in the hardware account. The run instructions below apply after that instruction.

Run one experiment at a time: [12](GSFM-012.md), review its report, [13](GSFM-013.md), review, then [14](GSFM-014.md). Do not launch a later experiment automatically. Each protocol is a specification for the hardware agent to implement, not an assertion that its runner already exists.

## Scientific scope

Compare a verified numerical AC-OPF reference, conventional DC-OPF, frozen Microsoft GridSFM v1.1, and the frozen newer GridSFM v2. Primary outcomes are approximation error, nodal balance and operating-constraint compliance. No training, LoRA, PF completion, OPF repair, checkpoint selection or solver-speed study. Retain cost and timing as provenance only.

Use the native predictions before any numerical completion. Preserve shipped settings separately for each release; do not reuse the sigmoid override from Experiments 9–10. Keep failed predictions and failed solves in the report.

## Locked sources and settings

| Item | Pin |
|---|---|
| Original MATPOWER case300 | MATPOWER 8.1, commit `1a828c7af590714499284e36ee9c81273388c594` |
| Original case300 SHA-256 | `69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5` |
| Microsoft code | `1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6` |
| Microsoft checkpoint SHA-256 | `f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831` |
| Microsoft native clipping | Released leaky clipping with alpha 0 |
| Newer code | `517a07531ea55a11bd81a89a6c6879695a2ba4b4` |
| Newer checkpoint SHA-256 | `9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7` |
| Newer native clipping | Shipped `clamp`, alpha 0 |

Reuse the audited Experiment 11 solver/conversion environment on the M5 Pro/64 GB worker. Model inference remains FP32; authoritative electrical calculations remain FP64 with original parameters. Record installed versions and settings rather than claiming that the Windows planning environment ran anything.

Read the completed 11B, 11C-1 and 11D reports from the hardware checkout first. The reviewed remote includes the 11D archive at commit `4473a5b` and historical diagnostics at `fb32703`. Do not reset a checkout to those commits or overwrite local raw results. Older README/HANDOFF historical status paragraphs are not evidence of current execution status.

## Correctness gates

1. Hash source cases, generated inputs, code, checkpoints and saved states. Preserve original external bus IDs, generator row IDs and individual parallel-branch IDs. Derived networks require an area/original-ID mapping.
2. Retain taps, phase shifts, charging, bus shunts, signed demands, generator bounds, costs, angle bounds and statuses. No impedance clamp or rounding in the independent evaluator. A zero MATPOWER rating means unlimited, not zero capacity.
3. Verify the input-to-model and input-to-solver round trip. Solved Pg/Qg/Vm/angles must not leak into model features. Reuse the established poisoned-label invariance check for each newly introduced network format.
4. On saved AC and native states, independently compare Ybus-based injections with incident-branch sums plus bus-shunt consumption. Require maximum disagreement below `1e-6 MW/MVAr`; investigate a failure before interpreting results. Count shunts once.
5. Accept an AC reference only after independently checking all specified constraints. Use the existing audited solver settings, capped at 120 seconds and 3,000 iterations per solve. One retry from a deterministic, declared flat start is allowed; retain both attempts. No bound relaxation or model-guided reference initialization. Failure remains **UNKNOWN**, not proof of infeasibility. Model residuals can still be evaluated without a reference, but reference errors and oracle diagnostics must be N/A.
6. Preserve the existing DC formulation, including shunts under its assumptions, taps, shifts, bounds and applicable ratings. Verify its own equations separately. DC-OPF has no native reactive dispatch or voltage-magnitude prediction: mark those comparisons N/A. Do not manufacture an AC state using Vm=1 and Qg=0.

## Common metrics

- **Prediction accuracy:** MAE, median, 95th percentile and maximum absolute error versus the verified AC reference for Pg, Qg, Vm, aligned angles and derived both-end branch P/Q. Report per-generator and bus-aggregated generation separately. Compare DC with GridSFM only on shared outputs: Pg, aligned angles and active branch flows.
- **Nodal balance:** signed and absolute P and Q residuals, separately; mean, 95th percentile, maximum, violating-bus count and total absolute imbalance. Formula: generation minus demand minus outgoing branch power minus bus-shunt consumption. A signed network total must not replace bus-level checks.
- **Bounds:** violating counts and maximum excess for Pg/Qg, Vm and applicable branch-angle limits. Report native bound clipping as part of the pipeline, not proof of learned physics.
- **Thermal:** for each online branch with RATE_A>0, independently reconstruct both endpoint complex powers. Use `max(|S_from|, |S_to|)` against RATE_A, retaining the controlling end. Report coverage, maximum MVA excess, maximum loading ratio and violating branch count. DC's own active-flow limit test is separate and cannot certify AC apparent-power feasibility.
- **Joint feasibility:** all applicable physical and operational tests must pass together. Use the Experiment 11 tolerances: `1e-3 MW/MVAr` for balance and generator excess, `1e-4 pu` for voltage excess, `1e-3 MVA` for thermal excess and `1e-3 degree` for angle excess. Retain unrounded values.

Angle errors use one common reference per connected network; use endpoint angle differences for local branch analysis. Do not independently rotate the two connected areas. For multi-generator buses, avoid interpreting a different allocation between equivalent units as proof of infeasibility.

## Reporting and stopping

Write a new run directory for each experiment, with a readable README, machine-readable tables, input/settings manifest, hashes, environment and gate results. Save raw states in the established hardware artifact location and identify which artifacts are local-only. Do not claim that hashes alone make raw artifacts remotely retrievable.

Keep releases, networks, scenarios and native/DC/reference outcomes distinct. Report denominators and UNKNOWN cases; do not pool dependent buses or the two copied areas as independent statistical trials. Reuse old states only after matching every relevant input, checkpoint and setting hash; otherwise label them historical.

Suggested inclusive planning caps: Experiment 12 90 minutes, Experiment 13 90 minutes, Experiment 14 120 minutes. These are stop budgets, not measured runtime estimates. Finish earlier when complete; on timeout report partial results and the exact unfinished step. Run sequentially, batch size 1, using the established CPU environment; do not install a new accelerator stack or start paid compute.

On each completion, return a short report suitable for Exchange Results and stop for review. This package is repository documentation; it does not launch hardware jobs or send messages. GitHub publication was explicitly requested on 23 October; Exchange edits are not part of that handoff request.
