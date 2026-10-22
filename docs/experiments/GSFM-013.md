# Experiment 13 — accuracy, electrical sensitivity and cancellation at individual buses

Status: **COMPLETE, 23 October 2026.** [Verified report](../../results/diagnosis/GSFM-013/20261023-accuracy-sensitivity/README.md). Executed sequentially under Ninad’s explicit instruction to run 12–14 and push results. Earlier planning/review gates below are preserved as protocol history.

## Question and why this adds something

Within the same prediction, does a bus have small imbalance because its prediction is accurate, because its electrical neighborhood is less sensitive, or because large signed errors cancel?

Experiment 11D already demonstrated all three possibilities in selected examples, but 17 of its 18 high-/low-error comparator matches were marked poor. This experiment measures the three quantities separately and abstains when a valid structural comparison does not exist. It must not merely repeat the worst-bus tables.

Use original case300 and the connected construction from Experiment 12. The copied areas provide useful homologous comparisons without introducing another benchmark. The newer release is the primary presentation; analyze Microsoft v1.1 separately as replication, without choosing the better-looking release after analysis.

## 13A. Select saved states and verify them

- Primary: original case300 at base load from 11B, and the balanced connected system S0 from Experiment 12.
- Descriptive consistency checks: saved original loads 0.80, 0.90, 0.95, 1.03, 1.06 from 11C-1, and S+/S− from 12 where references passed.
- Exclude original 1.10 loading from reference-dependent analysis; its failed AC solve is not a label. Preserve its earlier reference-free results without reclassifying it.
- Verify source/state hashes and reproduce the saved residuals under both independent FP64 formulations. A missing local state is missing evidence, not permission to regenerate it silently.

## 13B. Measure three different things for every bus

### 1. Prediction accuracy: how wrong are the state variables?

Against the same independently feasible AC reference, record signed and absolute local Vm error, reference-aligned angle error, generator Pg/Qg errors where generators exist, and bus-aggregated generation error. No-generator prediction accuracy is N/A for Pg/Qg; a zero generation term is not a successful generator prediction.

Also record one-hop neighbor Vm errors, endpoint angle-difference errors and both-end branch-flow errors. A locally accurate Vm can sit next to an inaccurate neighbor. Report local and neighborhood errors separately; do not call a low balance residual “accurate prediction.”

Use the verified AC state as one feasible local reference, not a unique globally optimal truth. Different feasible dispatches can have nonzero state error; balance violations are independently meaningful.

### 2. Electrical sensitivity: how much can a fixed small voltage error change power?

At the common AC reference, let x=[Vm,theta] with angles in radians and f(x) be exact nodal active/reactive network injection, including shunts. Compute the Jacobian J=df/dx from the original network. Use one system angle gauge; exclude the fixed reference-angle coordinate.

Implement an analytical derivative or central finite differences. If finite differences are used, start with steps 1e-6 pu and 1e-6 rad; compare with half-steps. Require relative Frobenius disagreement below 1e-4 for the voltage and angle blocks, and for inspected rows require maximum entry disagreement below `1e-3 + 1e-4 * max(abs(row))` in the corresponding derivative units. Retain diagnostics and stop sensitivity interpretation if this fails. This is equation evaluation, not another model prediction or solve.

Report separate, dimensionally explicit row scores for P and Q:

`H_V(i) = sum_j |d f_i / d Vm_j| * 0.001 pu`

`H_theta(i) = sum_j |d f_i / d theta_j| * 0.001 rad`

These are worst-case linear response bounds for a declared uniform perturbation box, in MW or MVAr. They are neither observed model errors nor empirical probabilities. Do not add unlike raw derivative units or label high sensitivity an inaccurate prediction.

For the actual saved voltage error dx, compute J*dx and compare it with the exact change f(x_pred)-f(x_ref), separately for P/Q. Retain the signed nonlinear remainder. Large prediction errors can make the local linear approximation poor; report that limitation rather than forcing the Jacobian to explain everything. Report generation error separately from network-voltage sensitivity.

### 3. Cancellation: do opposing errors hide each other?

For each bus and separately for P and Q, form signed reference-error contributions:

`c = [each generator error, minus each incident outgoing branch-power error, minus bus-shunt-consumption error]`

Keep individual parallel rows and individual generators separate. Demand is identical in the two states. Verify:

`sum(c) = residual_pred - residual_ref`

Report gross error `G=sum(abs(c))`, net error `N=abs(sum(c))`, and cancellation fraction `C=1-N/G`. If G<=1e-3 MW/MVAr, report C as N/A because there is no material gross error to cancel. Retain native residual separately from residual error. Do not hide large gross errors behind a high cancellation percentage.

Additionally report cancellation among branch contributions alone, and cancellation between aggregate generation, branch and shunt blocks. The number depends on grouping, so use these fixed definitions throughout. A small net error with large G is not evidence of an accurate or robust operating point.

## 13C. Compare structurally similar buses without forced matches

Build the admissible-pair list from unsolved network features before joining prediction outcomes. Freeze the list and its hash. Use two complementary comparisons:

**Within one area/network:** exact match on bus type, online generator count, base-kV, structural zero-injection status, nonzero-shunt presence, incident transformer count and parallel-branch excess count. Define a transformer as a non-unity effective tap, nonzero phase shift or unequal endpoint base-kV. Permit incident-row degree and unique-neighbor degree differences of at most one. For signed Pd and Qd independently, require `abs(a-b)/max(10,abs(a),abs(b)) <= 0.25`, with loads in MW/MVAr. Structural zero injection requires zero demand, no online generator and no bus shunt.

Do not match on predicted errors, derivatives or impedance magnitude: electrical sensitivity is an explanatory quantity we want to measure. Include impedance/admittance distributions and one-hop neighbor bus-type counts in the table so residual structural differences remain visible. These matches are descriptive controls, not randomized causal controls.

**Across copied areas at balanced S0:** pair A(i) with B(i) by source ID. Verify their source feature agreement; exclude the REF/PV-mismatched pair and mark all pairs whose one-hop input-type pattern differs. Keep these distinct from within-area matches. This controls much of the inherited structure but not the whole model context or reference-angle choice.

For each release and each P/Q component separately, label high imbalance as the top quartile and low imbalance as the bottom quartile at the base state, tie-breaking by external ID. Enumerate all admissible high/low pairs; do not silently relax calipers when none exist. Report eligible counts and all unmatched hotspots, especially 238, 231 and 137. “No comparable low-error bus” is a valid outcome.

For up to six illustrative pairs per component/release, order first by smallest normalized source-feature distance, then high-bus and low-bus IDs. Freeze these pairs for load tracking. Publish the complete admissible-pair table, not only favorable examples. Report high/low prediction-error classifications separately from high/low imbalance; do not combine the two into one score.

## 13D. Interpretation and outputs

For all buses and the matched examples, show whether the evidence is consistent with:

1. Smaller local and neighboring prediction errors.
2. Similar prediction error amplified more strongly by electrical sensitivity.
3. Large component errors hidden by cancellation.
4. A combination or a substantial nonlinear remainder that remains unexplained.

Do not force a mutually exclusive label or claim that correlation identifies the neural training cause. A large admittance is not sufficient by itself to explain a residual. Do not infer “the model learned this bus better” solely from smaller imbalance.

Save `bus-decomposition.csv`, `jacobian-checks.json`, `matching-rule.json`, `admissible-pairs.csv`, `matched-examples.csv`, `load-tracking.csv`, hashes and a README. Provide four figures: state-error versus imbalance; standardized sensitivity versus network-injection error; gross versus net error colored by cancellation; signed budgets for selected matched pairs. Identify release/network/scenario on every plot; avoid pooling dependent buses into significance claims.

Conclude with three plain-language examples where available: a genuinely accurate neighborhood; an electrically sensitive neighborhood; a low-imbalance bus whose errors cancel. If an example is absent, say so. Explain what this establishes beyond 11D and what it cannot establish about training or generalization.

Stop for review. Experiment 14 does not start automatically.
