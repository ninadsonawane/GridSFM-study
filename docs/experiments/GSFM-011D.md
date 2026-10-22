# Experiment 11D — explain native power-balance failures on case300

**23 October handoff note: archived planning specification, not a new task.** The hardware worker completed 11D on 22 October; read the [executed result report](../../results/diagnosis/GSFM-011D/20261022-saved-states/README.md) for actual coverage and checks. Some stronger requested comparator checks below were not achieved: the executed analysis reported 17 of 18 poor matches. [Experiment 13](GSFM-013.md) addresses that gap. Preserve the original planning text below; do not rerun it automatically or treat every requested item as completed.

22 October 2026. Status: proposed hardware analysis; not executed by the planner. User requested a detailed investigation of worst versus low-error buses before expanding experiments. This is a diagnostic interlude after 11C-1, not the planned reactive-demand sweep. Do not automatically run other 11C families.

## Purpose and interpretation

Question: **Which prediction errors and local network features produce the measured nodal power imbalance, where are they concentrated, and how do their contributions change with loading?**

Kirchhoff's laws remain the physical criterion; their violation does not make the laws irrelevant. Loading changes the reported errors, but not monotonically. Branch-flow error against an AC reference is different from violation of a branch equation. Native flows are reconstructed from predicted voltages: the main inconsistency is between those flows and predicted net generation minus demand.

11B is published at `1f8ab6645bc20be808d5d40d20f3d73f0856f6de`. 11C-1 was read from Exchange by the planner; its underlying artifacts were not yet on remote main at planning time. Treat all seven operating points as inspected discovery data. Do not claim independent confirmation, an OOD cause, checkpoint-training provenance, or the historical loss clamp as the cause of these prediction errors.

## Scope, inputs and stopping rule

- M5 Pro / 64 GB, established CPU environments. Reuse saved native outputs and original-parameter AC references for loads 0.80, 0.90, 0.95, 1.00, 1.03, 1.06, 1.10 from 11B and 11C-1. Keep Microsoft v1.1 and newer base v2 separate, with shipped hard clipping as actually recorded.
- No training, new load cases, fresh model inference, PF completion, OPF repair, topology modification, impedance floor changes, new ratings or tolerances. No installations.
- At 1.10, use model states for reference-free residual localization only. The failed AC iterate is NOT a reference. Do not fill reference-dependent tables or hybrids there. No retry in this task.
- Stage 1: analyse and explain the unchanged base case. Stage 2: apply the same fixed diagnostic to existing loads. Stop expansion if exact reconstruction checks fail.
- Suggested two-hour inclusive cap, reserving the last 20 minutes for delivery. This is a budget, not a runtime prediction. Finish earlier when complete; do not start a second job to fill the time.
- Use a new `experiments/gsfm011d/` analysis script and `results/diagnostics/GSFM-011D/<run-id>/`. Preserve all earlier files. Missing saved states are a blocker to the affected comparisons; report them instead of reconstructing predictions from rounded tables.

## 1. Revalidate the saved evidence

Record source, checkpoint, native-output, input and reference hashes, execution commit, actual environment and prior-run IDs. Confirm only Pd/Qd changed across loading cases and original IDs/parallel rows/taps/shunts/statuses are preserved. Read full precision arrays, not formatted report cells.

Recompute all seven native residuals and six valid-reference residuals with original FP64 equations, and reproduce the corresponding 11B/11C-1 metrics. Cross-check branch-sum and Ybus implementations. Validate external IDs, radians/degrees, MW/per-unit and from/to orientation. Freeze existing pass thresholds; discrepancies must be resolved before interpreting results.

Save maximum reconstruction disagreement per state, using a numerical gate of `abs(error) <= 1e-7 MVA + 1e-10 * sum(abs(component terms))` for algebra identities, distinct from the unchanged physical-feasibility tolerance. Report actual disagreements even when the gate passes.

## 2. Make an exact power ledger for every bus

Use outgoing branch-end complex powers, with transformers and charging included in their branch equations, and bus shunt power counted once:

`r_i = sum(Sg at i) - Sd_i - sum(outgoing Sbranch at i) - Sshunt_i`.

For each valid reference, form the exact identity:

`r_pred - r_ref = Cg*(Sg_pred - Sg_ref) - sum(Sbranch_pred - Sbranch_ref) - (Sshunt_pred - Sshunt_ref)`.

Demand cancels because each comparison uses the SAME input. Use the calculated reference residual, not assumed exact zero. Produce separate P and Q signed ledgers in MW/MVAr. This tells us whether mismatch comes from generation error, incident branch-flow differences, shunt differences, or their combination.

Save all buses and all incident branch contributions, not just maxima. Show signed contribution and magnitude: large opposing flows can cancel. Do not call the sum of absolute branch errors the net nodal residual or interpret it as overload. For buses with no generator, explicitly show generation contribution zero.

For each release/load, report max, median, p95, mean absolute P/Q residual, fraction of buses exceeding tolerance, and the top 1/5/10 buses' shares of total absolute P and Q residual separately. Report the remaining-bus residual distribution too. Retain the original whole-network validity result regardless of concentration.

## 3. Worst versus low-error bus comparison

Always include original IDs 238, 231 and 137. Also select the top five P and top five Q residual buses for each release at the BASE load; retain their union, even if a named bus is not ranked highest. Keep this focus set fixed across loading levels; separately record any new worst bus at other levels.

Select low-error comparators by a recorded deterministic procedure, per release at base load:

1. Rank all buses by `max(abs(rP), abs(rQ))`, since the declared P/Q tolerances are equal; use the bottom quartile as the low-error pool and publish the complete ranking.
2. For each focus bus, prefer the same source bus type and generator-presence status. Match as closely as possible on log(1+degree), base kV, abs(Pd), abs(Qd) and shunt-presence, using source-only standardized features; drop zero-variance columns. Tie-break by original bus ID. Choose up to two controls; disclose unavailable strata or poor matches instead of silently broadening them.
3. Keep controls fixed across loads. Show load-bearing and zero-injection buses separately so that a trivial zero-injection bus is not treated as a comparable success without explanation. Outcome-based comparator selection is descriptive discovery, not causal evidence.

For focus/control buses and their one-hop neighborhoods show: bus type, demand, generation, degree, base kV, shunts, each branch's r/x/charging/tap/shift, original branch row ID and neighbors. Include two-hop topology only as context if needed. Preserve parallel circuits individually.

Compare predicted/reference Vm, aligned angle, Pg/Qg and local residual. For each incident branch compare endpoint Vm, branch angle difference, effective phase-shift-adjusted angle difference, both-end P/Q and predicted-minus-reference flow. Preserve reference orientation; report signed unwrapped differences and wrapped display angles separately. A global angle offset cannot explain flow errors, whereas differences across a branch can.

Record inverse impedance magnitude continuously and its rank. Test whether branches with large admittance also have large endpoint-state/flow errors; do not assume that small impedance is the explanation or change it. Compare with similar-admittance branches outside focus neighborhoods, including branches with low flow error. These are associations, not proof of a training mechanism.

## 4. Separate voltage-magnitude, angle and generation contributions

For both releases at each of the SIX reference-valid loads, evaluate the eight combinations of three blocks being model-predicted versus reference-valued:

- G: all online generator Pg AND Qg, with original bus mapping;
- M: voltage magnitudes at all buses;
- A: voltage angles at all buses, aligned to the same reference.

For example: all predicted; reference M only; reference A only; reference G only; all three pair replacements; all reference. Recompute flows and shunts with unchanged original FP64 physics for EVERY hybrid. Never copy old flows onto changed voltages. These are 8 algebraic evaluations per release per input (96 total), not solver runs.

Report maximum and mean absolute P/Q residual and total squared P/Q residual separately, globally and at focus/control buses. Save the 8-row table, including negative improvements. The all-reference row must reproduce the valid reference check. All-predicted must reproduce the native check.

These are **oracle diagnostic substitutions**: they use known answers to test which output blocks account for the residual. They are NOT usable inference methods, repaired solutions, performance improvements or feasible states by construction. Replacing an entire block can worsen balance by removing accidental error cancellation.

Because AC flow is nonlinear, single substitutions do not yield additive contributions. If reporting a percentage attribution, compute exact three-block Shapley allocation of reduction in the separately defined total squared P and Q residual across all six replacement orders. Retain negative allocations and verify they sum to the all-predicted minus all-reference score. Otherwise present the eight combinations without claiming additive percentages. This attributes this diagnostic metric, not the underlying cause of learned errors.

Do not replace individual focus-bus voltages with reference values and claim a local cure: doing so affects every incident branch and neighboring bus. Global-block substitution plus exact branch ledgers is the primary design.

## 5. Explain loading response with fixed diagnostic definitions

Apply stages 2–4 to saved loading levels. For 1.10 omit all reference differences, oracle substitutions and reference-error rankings; raw ledgers and branch parameters remain available.

Track each fixed focus/control bus across load, including whether it remains a maximum. Highlight the newer model's reported change between 0.90 and 0.95 and the Microsoft model's changing angle errors without assuming a discontinuity from two points. Plot neighboring endpoint angles/magnitudes and branch-flow contributions to see what changes alongside the residual.

Record output proximity to clipping bounds for Pg/Qg/Vm at every load (both exact stored-FP32 boundary matches and distance to original bounds), with fixed/fused bounds flagged separately. Boundary occupancy alone does not show that clipping caused the error; pre-clipping activations are unavailable unless already saved. Do not rerun the model or attribute a switch to clipping without that evidence.

Use all-bus distributions and matched controls to distinguish: repeated local concentration; widespread errors; changes in which bus dominates; and cancellation. Compare the exact-physics result with existing numerical-operator discrepancies only if the SAME state is available. A discrepancy previously measured on a reference state is not an explanation of model-state residuals.

## 6. Deliverables and interpretation

Return a concise report and reproducible full-precision tables:

1. Verification/provenance JSON and input/output hashes.
2. All-bus P/Q ledgers, all-branch flow/state differences, rankings and deterministic focus/control selection with matching quality.
3. One plain-language case study each for buses 238, 231 and 137, plus at least one low-error comparator: what enters/leaves, what differs from AC-OPF, which terms dominate, and what remains unexplained.
4. Eight-combination oracle tables, and Shapley tables only if calculated correctly and clearly labelled.
5. Four compact figures: residual concentration; signed branch-contribution ledger for focus buses; load versus fixed focus/control residuals; oracle substitution effect. Include units, release, loading and missing-reference annotation.
6. Five evidence-based conclusions, each tagged supported/contradicted/unresolved and linked to rows/figures. State whether the observations explain the electrical mismatch or merely correlate with it.

End by answering in simple words: Where is the error? Is it concentrated? Which generation/voltage/angle differences produce it? What distinguishes low-error buses? How does it change with load? What remains unknown about why the model learned these outputs?

Do not claim AC-OPF is globally optimal, DC-OPF is AC-feasible, branch flow error is overload, native bound compliance is joint feasibility, or an OOD/training-loss cause has been established. Original case300 thermal coverage remains absent. No new experiment is automatically authorized after this analysis. Deliver and STOP for review with Ninad.
