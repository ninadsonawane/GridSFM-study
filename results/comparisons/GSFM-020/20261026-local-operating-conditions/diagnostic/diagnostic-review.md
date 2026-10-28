# Independent review of local repeatability and output mediation

26 October 2026. Saved-artifact review only: no additional forwards, electrical inputs or solves. The evidence supports fixed-original-order electrical continuation, while retaining the shipped preprocessing defects. It does not validate a corrected model or representation-independent behavior.

## Repeatability and mapping

Both releases match **every returned value exactly** across the within-process warm repeat, poisoned-label control and independent cold-process retry. The two original cold-process invocations failed while writing an overlong Windows cycle-cache path, before the neural forward. Their files and failed summaries remain preserved. A preregistered path-only amendment shortened the unique per-run cache directory. Final count: **21 invocations, 19 executed neural forwards, two preprocessing failures, zero new electrical inputs**. The separate [diagnostic gate](../diagnostic-gate.json) records PASS; the original failed summaries are not rewritten.

For every completed output, this review independently remapped its state into original bus/generator order and rescored the original matrices. P/Q summary metrics agree with evaluation of the variant matrices below 1e-6 MW/MVAr. Inspection of all saved prepared-default/used tensors found changes only in the declared intervention blocks. All diagnostic outputs remain jointly AC-infeasible; repeats and altered representations are not independent operating conditions.

## Quantitative mediation

Numbers below are **maximum differences from the original-order model prediction**, not approximation errors against AC. Arrows compare the reversed shipped pipeline with the named altered-feature diagnostic.

| Release / row reversal | Isolated prepared-feature substitution | Pg difference MW, before→after ↓ | Vm difference pu, before→after ↓ |
|---|---|---:|---:|
| v2 / branch rows | Complete baseline cycle graph | 247.118→0.000358 | 0.120000→0.00000113 |
| v2 / bus rows | Complete baseline cycle graph | 269.463→0.000906 | 0.120000→0.00000513 |
| v1.1 / branch rows | Baseline cycles plus mapped transformer DC columns | 125.185→0.000429 | 0.085898→0.000000238 |
| v1.1 / bus rows | Complete baseline cycle graph | 123.892→0.103331 | 0.085991→0.000194 |

For v1.1 branch reversal, cycles alone leave a 174.713-MW maximum Pg difference; transformer columns alone leave 114.147 MW. Their combination restores the baseline closely. These effects interact and cannot be added. For v1.1 bus reversal, landmark-only substitution moves predictions by at most 0.04658 MW Pg, 0.14692 MVAr Qg and 0.0001689 pu Vm, while leaving the large cycle-related discrepancy. The remaining error after cycle substitution is not fully isolated because a combined bus-cycle/landmark intervention was not run.

Thus the cycle representation mediates the large v2 effects and most v1.1 bus-order effects. The v1.1 transformer-feature association additionally matters for branch reversal. Restoring cycles is not a correction of the upstream cycle-sign convention. The earlier invariant cycle Gram matrix under bus reversal did not imply invariance of the full learned pipeline.

## Clipping and physical significance

Actual strict Pg/Qg/Vm clip counts under branch reversal are **21/8/39→27/13/34** for v1.1 and **51/27/281→52/28/281** for v2. The combined v1.1 substitution and cycle-only v2 substitution restore the respective baseline counts. Counts alone conceal movement: v2 branch reversal changes a preclip Vm value by as much as **2.284 pu**, despite an unchanged total of 281 voltage clips; the corresponding maximum preclip Pg change is **1,461.20 MW**, versus a 247.12-MW maximum change after clipping. These are observed head/clamp quantities, not generator/voltage violations.

Physically identical row reversals can appear better by one residual metric: v2 bus reversal lowers maximum Q imbalance **7,958.03→4,696.12 MVAr**, despite no electrical intervention. Restoring baseline cycles returns it to 7,958.10 MVAr. This prevents interpreting representation changes as operational improvement. Fixed original ordering is therefore essential. Small residual differences persist after feature matching; they are not evidence of exact equivariance or feasibility.

## Replay against historical Mac states

The historical states are checksum-verified derivatives recovered from tracked diagnostic tables; their complete original raw return dictionaries are unavailable. The new Windows baseline is close but not bit-identical:

| Release | Max Pg difference MW | Max Qg difference MVAr | Max Vm difference pu | Max aligned-angle difference degrees |
|---|---:|---:|---:|---:|
| v1.1 | 0.000429 | 0.000173 | 2.38e-7 | 9.56e-5 |
| v2 | 0.001913 | 0.000596 | 1.37e-6 | 6.83e-5 |

Fresh baseline maximum Q imbalance remains **8,937.95 MVAr (v1.1)** and **7,958.03 MVAr (v2)**. Neither native state is feasible. Cross-platform state drift must remain separate from exact local repeatability; the v2 maximum Pg drift exceeds 0.001 MW, so no blanket claim that every cross-platform difference is below every feasibility tolerance is justified.

Reproduce this analysis with `python -B experiments/gsfm020/review_diagnostic.py`. [Machine-readable differences](independent-differences.json) contain the full physical scores, aligned state differences, preclip changes, actual clamp counts and prepared-tensor audit for all completed diagnostic forwards.
