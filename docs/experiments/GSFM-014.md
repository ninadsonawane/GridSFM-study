# Experiment 14 — thermal-limit assessment on rated 300- and 600-bus variants

Status: **PROPOSED, not run.** Read [shared instructions](GSFM-012-014-common.md). Start after review of the earlier experiments. No adaptation or numerical repair.

## Question and benchmark choice

On networks with specified branch ratings, do native GridSFM operating points respect thermal limits as well as nodal balance, generator limits and voltage limits? Does the released model respond appropriately when those ratings are supplied?

Original MATPOWER case300 has no finite internal RATE_A limits, so its earlier results cannot answer the thermal question. Use the complete published **PGLib-OPF case300_ieee Typical Operations** case and a connected two-copy derivative. These are separate rated benchmarks; do not overwrite original MATPOWER results or call the PGLib case “original case300 plus ratings.” Other fields differ too.

## 14A. Acquire and validate the published rated case

Source: [PGLib case300 at pinned commit](https://raw.githubusercontent.com/power-grid-lib/pglib-opf/dc6be4b2f85ca0e776952ec22cbd4c22396ea5a3/pglib_opf_case300_ieee.m), repository commit `dc6be4b2f85ca0e776952ec22cbd4c22396ea5a3`, header v23.07 Typical Operations.

Expected source SHA-256, independently retrieved by the planner on 22 October 2026:

`7ecf056d5942135765200ad7ae8791c28f0d35fb1dc888ba2c32dfc950f3c2f5`

The planner's source-only parse found 300 buses, 69 generators, 411 online branches, 411 positive RATE_A values ranging from 6 to 9,900 MVA, and 12 generators with Pmax=Pmin. This is an input audit, not a solved-case or inference result. Verify these counts and the hash on hardware before continuing. Preserve the source's attribution/license notice.

Preserve the full published demands, costs, generator bounds, voltage bounds, branch parameters and angle limits. Audit differences from original MATPOWER case300 in a table. Treat fixed-P generators correctly; do not drop them or divide by zero in normalization. If released preprocessing cannot represent them faithfully, report a compatibility failure without silently widening bounds.

Construct `pglib300x2-parallel-v0` by copying this complete rated case twice and applying the same bus-231 parallel ties, IDs, REF/PV treatment and tie parameters as Experiment 12. Do not copy old MATPOWER interior matrices into it. Expect 600 buses, 138 generator rows, 824 online branches and 824 positive RATE_A values, including the two synthetic 600 MVA ties. Keep published interior ratings and synthetic tie ratings distinct in provenance and results.

Verify that branch ratings survive both solver conversion and model preprocessing, including units and the treatment of unlimited values. Inspect which rating fields the model actually consumes. Record any discarded rating information as an implementation finding rather than quietly changing the released architecture.

## 14B. Run the bounded matrix

For each listed input run the AC reference, DC-OPF and both frozen models. Apply the shared correctness gates. Complete the two rated base inputs first; if a conversion or equation gate fails, stop before further execution.

| ID | Network | Load condition | Thermal limits | Purpose |
|---|---|---|---|---|
| R300-base | Published PGLib300 | 1.00 | Published | Main rated benchmark |
| R600-base | Two-copy PGLib300 | A=1.00, B=1.00 | Published interiors, fixed synthetic ties | Main rated construction |
| U300-base | Same PGLib300 | 1.00 | Interior ratings disabled | Matched rating control |
| U600-base | Same two-copy PGLib300 | A=1.00, B=1.00 | Interior ratings disabled; ties unchanged | Matched rating control |
| R300-low | Published PGLib300 | 0.95 | Published | Lower load |
| R300-high | Published PGLib300 | 1.05 | Published | Higher load |
| R600-A | Two-copy PGLib300 | A=1.05, B=0.95 | Published interiors, fixed synthetic ties | Area imbalance |
| R600-B | Two-copy PGLib300 | A=0.95, B=1.05 | Published interiors, fixed synthetic ties | Reversed imbalance |

For U controls only, set inherited branch RATE_A/B/C to zero, the MATPOWER unlimited convention. Everything else must be bitwise identical to the corresponding R base input. Leave both synthetic tie ratings unchanged. These are explicitly modified controls, not published PGLib cases and not rated-feasibility claims. Archive a field-level diff proving that only the declared ratings changed.

Run each U control through fresh preprocessing and inference with its own correct input. Comparing U and R isolates the effect of those rating changes; comparing original MATPOWER with PGLib does not. Keep all outcomes, including a lack of model response or a solver failure.

The maximum is eight input cases, eight AC reference attempts, eight DC runs and sixteen frozen native predictions, excluding the bounded solver retry. No additional loading search, branch derating, outage or post-hoc choice of a “difficult” example.

## 14C. Evaluate thermal limits and the response to them

1. Report every shared physical/operational metric. For each branch, retain P/Q and |S| at both ends, RATE_A, the controlling end, loading ratio and excess. Summarize inherited branches and ties separately, as well as the full network.
2. Report whether each verified AC reference is itself constrained by ratings. Flag near-binding branches using `RATE_A - max(|S_from|,|S_to|) <= max(0.1 MVA,0.001*RATE_A)`; label this a reporting definition, not the feasibility tolerance.
3. For each rated input, report native overloaded-branch count, maximum MVA excess, maximum ratio and which branches fail. Cross-reference endpoint voltage/angle errors and local imbalance. Passing thermal checks alone is not AC feasibility.
4. Evaluate every U-base output both against its own unlimited-control constraints and, separately, against the paired R-base ratings. The latter is a counterfactual thermal audit, not a different solve. Show whether removing ratings actually changed the AC reference or created violations when the rated constraints are restored for scoring.
5. Compare each model's U-to-R changes in Pg, Qg, Vm, angles and flows with the numerical reference's changes. If ratings are nonbinding and both references are similar, unchanged model outputs do not establish neglect of ratings. If the reference response is material but the model responds poorly, localize the discrepancy. Do not interpret input sensitivity as proof of feasibility.
6. DC's |P| limit compliance is a result under the DC approximation. Its absent Q and Vm mean native AC thermal feasibility is **N/A**, even when its active-flow limits pass. Compare active-flow accuracy against AC, but do not add a completion pipeline here.

PGLib ratings are published benchmark data, not evidence of the actual historical equipment's thermal capabilities. Some supplied ratings are very large; report coverage and binding status instead of assuming every finite limit is restrictive. If no rated case stresses a constraint, report that result and propose a separate prespecified stress study for review. Do not manufacture overloads to support a narrative.

## Deliverables and stop

Save source manifest/hash, construction and mapping tables, MATPOWER-versus-PGLib differences, R/U field diffs, scenario manifest, all states and gate results, method summary, both-end thermal table, rating-response table and README. Supply three compact figures: rated-case joint feasibility; ranked loading ratios with the reference; paired U-to-R changes for numerically relevant branches.

Answer plainly:

1. Which rated cases have a verified feasible AC reference?
2. Do either frozen model's predictions satisfy thermal limits, and do they satisfy all constraints together?
3. Does DC-OPF better approximate the shared AC quantities on these inputs?
4. Did supplying ratings change the model appropriately where the reference changed?
5. Are the earlier sensitivity/cancellation mechanisms still visible, and what remains unknown?

Stop for discussion. These results would support a bounded evaluation of physical validity and limitations; they do not establish general performance across unrelated grid families or guarantee conference acceptance.
