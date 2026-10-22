# Experiment 12 — frozen GridSFM on two connected case300 systems

Status: **COMPLETE, 23 October 2026.** [Verified report](../../results/comparisons/GSFM-012/20261023-frozen-two-copy/README.md). Executed sequentially under Ninad’s explicit instruction to run 12–14 and push results. Earlier planning/review gates below are preserved as protocol history.

## Question

Do the case300 physical-validity failures persist in a connected 600-bus construction, and what happens when demand shifts between its two areas?

This is a synthetic system derived from IEEE case300, not a standard IEEE 600-bus benchmark. It meets the documented 500-bus lower size range, but that alone does not establish training-distribution membership. Joining two grids changes topology and electrical conditions as well as size; this is not a causal bus-count experiment.

## 12A. Build and validate the unchanged construction

Reuse `configs/network-case300x2.json` and the existing constructor. Do not choose a new tie location or tune parameters after seeing predictions.

- Two original MATPOWER case300 copies: 600 buses, 138 generator rows, 822 inherited branch rows.
- Add two distinct, identical parallel tie rows from area A original bus 231 to area B original bus 231. Both terminals are 345 kV.
- Each tie: r=0.002 pu, x=0.019 pu, total charging b=1.127 pu on the common 100 MVA base; MATPOWER tap=0 means unity, shift=0, angle bounds [-360,360] degrees, status=1, RATE_A/B/C=600 MVA.
- These are the existing illustrative impedance/charging parameters and declared synthetic ratings, not measured interconnection equipment. Preserve them as-is and report them.
- Retain one REF bus; turn the second copy's former REF into PV without discarding its generator or voltage control. Verify one connected component and one reference angle.
- Preserve all 824 branch rows, including the two parallel ties. All 822 inherited RATE_A values remain zero/unlimited. Thermal assessment here covers only the two ties.

Create explicit tables mapping every generated bus/generator/branch to area and original ID. Confirm that each inherited block equals its source, apart from necessary IDs and the stated REF/PV change. Hash the construction and scenario inputs.

The old config's “PF/OPF not executed” text is historical: prior base runs exist. Reuse one only if its hashes/settings satisfy the shared reuse rule; do not silently mix older Seiole-fork predictions with the two pinned released baselines.

## 12B. Run exactly three scenarios

Scale signed Pd and Qd by the listed factor, once. Keep generation capacities, costs, shunts, branch parameters and both tie statuses unchanged.

| Scenario | Area A load | Area B load | Purpose |
|---|---:|---:|---|
| S0 | 1.00 | 1.00 | Balanced base |
| S+ | 1.05 | 0.95 | Shift demand toward A, same system total |
| S− | 0.95 | 1.05 | Reverse the shift |

For each input run AC-OPF, DC-OPF and the two frozen GridSFM releases under the shared gates. Complete and verify S0 first; stop if construction, mapping or independent-equation checks fail. A reference-solve failure is reported under the shared UNKNOWN rule, not repaired by changing the case.

This yields three reference attempts, three DC runs and six native predictions, excluding the bounded solver retry. No sweep of ties, outages or load levels. No training or completion.

## 12C. Evaluate and explain

1. Report all shared accuracy and constraint metrics, for the whole network and separately for each area. Compare with existing single-case300 results using means/percentiles and rates; total absolute imbalance naturally changes with network size.
2. For each tie, report both-end P/Q/|S|, losses, rating excess and reference error. Report total interchange from each area's outward-facing endpoints. Check that the sum of the two areas' outward P values equals tie active losses, rather than forcing them to be exact negatives. Keep charging/reactive exchange explicit.
3. Check each area's balance using its generation, demand, internal losses, shunts and outgoing tie powers. Explain whether errors concentrate at the interface or remain throughout the inherited grids.
4. Inspect the copies of buses 238, 231 and 137, plus each release's top-five P and top-five Q imbalance buses. Save every bus's terms for Experiment 13. Do not run the full eight-way oracle analysis yet.
5. For S0, compare corresponding A/B bus states and residuals, aligned to the one system reference. Flag the REF/PV input distinction and any positional features. Similar areas do not imply that an implementation must produce identical raw outputs; differences alone do not identify their cause.
6. Compare S+ with S− after mapping A↔B, but describe this as a paired diagnostic with the same reference-bus caveat. Establish whether the AC reference actually changes interchange; an unequal demand pattern does not guarantee substantial transfer under these costs and capabilities.

## Deliverables and stop

Save `scenario-manifest.json`, `gates.json`, `method-summary.csv`, `bus-metrics.csv`, `branch-flows.csv`, `area-exchange.csv`, states and hashes. Supply three compact figures: constraint comparison; matched A/B bus imbalance; signed inter-area exchange across S0/S+/S−.

End the report with plain answers:

1. Is the constructed case solvable to an independently feasible AC reference in each scenario?
2. On which shared outputs, if any, is each GridSFM release more accurate than DC-OPF?
3. Does increasing to this 600-bus construction remove the observed balance failures?
4. Do interface behavior and asymmetric loading introduce a different failure pattern?
5. What remains untested? In particular, inherited-line thermal feasibility remains N/A.

Stop. Do not start Experiment 13 until this report is reviewed.
