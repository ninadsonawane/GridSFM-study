# Reading the full results

All conclusions use the original case and prescribed demand. Each P/Q/PQ path includes nominal once plus 1%, 2%, 5% and 10%. Shared nominal appears on all three path plots but is counted once in unique-input summaries.

## Completion by network and path

| Network | Path | Stage | PF converged / 5 | Original P/Q balance passes / 5 | Scenarios violating Pg / Qg / V / thermal |
|---|---|---|---:|---:|---|
| case300 | P | V2-frozen+official-PF | 0/5 | 0/5 | 5 / 5 / 5 / N/A |
| case300 | Q | V2-frozen+official-PF | 0/5 | 0/5 | 5 / 5 / 5 / N/A |
| case300 | PQ | V2-frozen+official-PF | 0/5 | 0/5 | 4 / 5 / 5 / N/A |
| case300x2 | P | V2-frozen+official-PF | 0/5 | 0/5 | 4 / 5 / 5 / 5 |
| case300x2 | Q | V2-frozen+official-PF | 0/5 | 0/5 | 5 / 5 / 5 / 5 |
| case300x2 | PQ | V2-frozen+official-PF | 0/5 | 0/5 | 5 / 5 / 5 / 5 |
| case500goc | P | V2-adapted+official-PF | 5/5 | 0/5 | 5 / 5 / 5 / 0 |
| case500goc | P | V2-adapted+official-PF-exact-matrix | 5/5 | 5/5 | 5 / 5 / 5 / 0 |
| case500goc | P | V2-frozen+official-PF | 2/5 | 0/5 | 5 / 5 / 5 / 5 |
| case500goc | Q | V2-adapted+official-PF | 5/5 | 0/5 | 5 / 5 / 3 / 1 |
| case500goc | Q | V2-adapted+official-PF-exact-matrix | 5/5 | 5/5 | 5 / 5 / 3 / 1 |
| case500goc | Q | V2-frozen+official-PF | 0/5 | 0/5 | 5 / 5 / 5 / 5 |
| case500goc | PQ | V2-adapted+official-PF | 5/5 | 0/5 | 5 / 5 / 5 / 0 |
| case500goc | PQ | V2-adapted+official-PF-exact-matrix | 5/5 | 5/5 | 5 / 5 / 5 / 0 |
| case500goc | PQ | V2-frozen+official-PF | 2/5 | 0/5 | 5 / 5 / 5 / 5 |

Finite failed iterates are included in severity counts but are not completed operating points. All completed model stages have zero joint passes. Missing ratings remain N/A. Exact frozen diagnostics have the same convergence count as frozen official PF; see the full path table for every stage.

case300 and case300x2 have no frozen completed operating point on any path. Their failed-iterate residual and equipment changes are diagnostic only. The case300 internal branches are unrated; case300x2 thermal results concern only the two synthetic ties. No threshold of full-feasibility loss is identifiable because every model candidate already fails.

case500 frozen PF converges only at P/PQ factors 1.05 and 1.10. Adapted PF converges at every tested input, including the half steps. Original-matrix PF removes the small released-graph balance discrepancy while generator violations remain. Adapted P-only and combined paths have no thermal violations; Q-only at 1.10 overloads branch 390 (258 to 272), with 252.99 MVA against 190.07 MVA. Q-only voltage violations disappear at 1.05 and 1.10, so increased loading does not worsen every selected metric.

The active-power budget for exact-matrix Q +10% explains the balancing burden: prescribed P demand is unchanged, non-balancing Pg falls by 185.72 MW and active branch losses rise by 5.90 MW. Balancing Pg therefore rises by 191.62 MW. This accounts for the electrical redistribution; it does not establish a causal training mechanism. `paper/response-budget.json` retains the signed P/Q generation, demand, branch, shunt and residual terms for every nonbaseline case500 input and each adapted stage.

## All metrics and responsible locations

- `paper/all-metrics.csv` and three `paper/baseline-*.csv` files contain every agreed metric, with DC and reference-UNKNOWN applicability preserved.
- `paper/figures/all-metrics/` contains 36 PDF/PNG figures on shared network/path axes; `metric-plot-index.json` ties every plotted value to its scenario/method. Cross markers identify failed PF iterates.
- `paper/native-completion-metric-changes.csv` retains all 3,688 paired values. `paper/completion-change-summary.csv` gives lower/higher/unchanged counts separately for every metric, network, path and completion stage. Changes within 1e-9 in the metric unit count as unchanged for this descriptive summary only; evaluator tolerances are unchanged. It is not an aggregate quality score.
- `paper/native-to-completed-bus-changes.csv` identifies every improving/worsening P/Q bus. `paper/constraint-locations.csv` and `paper/angle-violation-locations.json` identify violated generators, voltages, rated branches and angle rows. Original per-entity records remain under each result.
- `paper/aggregate-bus-Q-limits.csv` tests whether Q allocation among co-located units could remove the observed violation. Nominal adapted PF violates 11 aggregate bus Q limits as well as 22 unit Q limits.

## Case 3 and final sensitivity

`paper/case3/` contains every bus and adjacent-flow accounting term for the 0.93-to-0.94 comparison. Three `paper/figures/case3-*.pdf` plots include all 14 original/refinement/control inputs and track maximum, mean, p95 and count together. Native V2 improves 141 buses and worsens 159; its maximum falls while p95/count rise. Branch 321 receiving-end Q changes by -8907.81 MVAr, mostly its voltage-gap term (-8889.18 MVAr). Neither frozen PF endpoint converges, so the native effect cannot be promoted to a completed-response claim.

`paper/sensitivity-summary.csv` contains 270 V/Pg/Qg finite-response rows for P and Q and all three step intervals; full entity details are archived. The 108 failed-PF secants are excluded from operating interpretation. Adapted case500 Q completion improves direction agreement and nominal Q accuracy but worsens Q-response RMSE relative to adapted-native at every tested interval. The half-step checked reference has no bound-set change; switching alone cannot explain that contrast. The Q +1% exact budget is 45.88 MVAr additional demand + 3.05 branch net Q + 2.18 shunt Q = 51.11 MVAr recovered generation. See `CLAIMS.md` for rejected overclaims and `literature/comparison.md` for what was already known.
