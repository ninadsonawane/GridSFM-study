# Experiment 11B — one original MATPOWER8.1 case300

**COMPLETE —22 October2026.** Exactly one conventional AC-OPF, one conventional DC-OPF and one native frozen forward per release. No training, sigmoid override, numerical completion/repair, scenarios or11C. All four runs completed; no solve failures occurred. Native outputs, raw solver logs/statuses and hashes are retained locally. Prior results unchanged.

## Approximation against the independently verified AC reference

Cells are **MAE (maximum absolute error)**. Generator errors use all69 original generator rows; angles align each state to original reference bus7049, then compare wrapped angular differences (wrapping changed no error here). Active-flow errors include **both ends of all411 branches**, including transformers and parallel rows. AC-reference self-errors are zero by definition.

| Method | Pg MW | Aligned angle degrees | Active branch flow MW | Qg MVAr | Vm pu |
|---|---:|---:|---:|---:|---:|
| AC-OPF | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| DC-OPF | 26.09 (108.3) | 7.228 (23.8) | 21.13 (256.9) | N/A | N/A |
| Microsoft v1.1 | 195.1 (897.8) | 23.31 (38.18) | 77.14 (3407) | 89.1 (546.7) | 0.02687 (0.1105) |
| Newer v2 | 106.4 (1333) | 48.83 (78.96) | 98.32 (2729) | 98.66 (553.2) | 0.04353 (0.12) |

DC flows use the lossless DC law with opposite from/to-end active flows. GridSFM flows are derived from its saved native Vm/angle using the **unchanged original FP64 AC branch equations**, not the release’s epsilon-modified derived-flow values. Those API values are saved separately, and discrepancies are logged. These are approximation comparisons between different model definitions, not feasibility tests. Distances from one local AC optimum do not rule out other feasible/nonunique dispatches.

## Native physical validity

Values are maxima, with **one maximizing original bus ID** shown. Small bound discrepancies are reported without rounding them to zero. All bus areas below are1.

| Method | P imbalance MW | Q imbalance MVAr | Pg-bound violation MW | Qg-bound violation MVAr | Vm violation pu |
|---|---:|---:|---:|---:|---:|
| AC-OPF | 1.225e-10 @bus9005 | 1.664e-09 @bus9053 | 0 | 0 | 0 |
| DC-OPF | 5.116e-12 @bus137 **DC law only** | N/A | 0 | N/A | N/A |
| Microsoft v1.1 | 3754 @bus238 | 8938 @bus238 | 0 | 4.768e-06 @bus124 | 2.384e-09 @bus63 |
| Newer v2 | 3211 @bus231 | 7958 @bus137 | 3.815e-05 @bus7003 | 4.768e-06 @bus124 | 2.384e-09 @bus4 |

**DC AC-P/Q balance, Qg, Vm and AC feasibility are N/A.** Its table entry checks DC active balance only; no Qg=0 or nominal Vm was invented as an AC state. PYPOWER’s copied/default Qg/Vm result-container fields are excluded from `dc-native.json`. The newer Pg maximum is generator row48 at bus7003; both releases’ Qg maximum is generator row12 at bus124. Voltage maxima can be tied; one maximizing bus is shown. Full signed residuals, limits and original IDs are in [locations](worst-locations.json) and [bus diagnostics](bus-diagnostics.csv).

AC reference: local ACP/Ipopt solution, objective719725.0988803704 per hour, status LOCALLY_SOLVED. It independently passes original P/Q balance and Pg/Qg/Vm/angle constraints. The Ybus residual agrees with the already audited independent branch checker. Tolerances remain1e−3MW/MVAr balance/generator bounds,1e−4pu voltage,1e−3degree active angle bounds. The native GridSFM box discrepancies above are below these tolerances; both fail decisively on balance. All original angle bounds are disabled ±360degrees. **Thermal assessment is N/A for every row: all411 original RATE_A values are0 (unlimited).**

## DC formulation and reproducibility

MATLAB/Octave executables were not available; no installation was attempted. AC reuses the audited PowerModels ACP/Ipopt builder, using only conventional/default starts. DC uses existing PYPOWER5.1.21 rundcopf/PIPS (QP algorithm200). It is not assumed equivalent merely because a formulation is named DCP. The DC constructor and constraints were checked against these immutable MATPOWER8.1 sources: [makeBdc](https://github.com/MATPOWER/matpower/blob/1a828c7af590714499284e36ee9c81273388c594/lib/makeBdc.m#L57), [opf_setup](https://github.com/MATPOWER/matpower/blob/1a828c7af590714499284e36ee9c81273388c594/lib/opf_setup.m#L276), [makeAang](https://github.com/MATPOWER/matpower/blob/1a828c7af590714499284e36ee9c81273388c594/lib/makeAang.m). No MATPOWER executable was run; equivalence is a source/equation audit plus numerical stamp/output checks.

The independently constructed Bbus/Bf/phase-injection matrices agreed with PYPOWER to1e−12 or better. Branch susceptance is status/(x·tap), shift injections are −status/(x·tap)·shift_rad, and balance includes Pd+Gs at unit Vm. Original polynomial MW costs, Pg bounds and applicable angle/positive-rating constraints are retained; none are invented. A pure branch-stamp algebra check exercises nonzero phase/tap and offline status without solving another network. Recomputed DC-law flows, balance, cost and original external row ordering passed. See [DC audit](dc-equation-audit.json), [DC status](dc-status.json), [verification](verification.json). DC objective706292.3242436093 is for the lossless approximation and is not achieved feasible AC savings.

Original case-file SHA25669a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5. Both model source-file inventories match11A. Microsoft source1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6 / checkpointf8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831; newer source517a07531ea55a11bd81a89a6c6879695a2ba4b4 / checkpoint9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7. Each used shipped hard-clamp defaults, leaky_alpha0; the newer clip_mode remained clamp. No checkpoint selection or sigmoid override. The inference workers do not load the AC reference. Both native model states and complete returned dictionaries were saved before evaluation.

All raw matrices and full solver/model states remain durable local-only in this result directory, indexed by [artifact inventory](artifact-inventory.json). Compact metrics, report, source/equation audit, per-bus/per-branch diagnostics and commands are reviewable. [Provenance](provenance.json). No run was excluded or silently replaced.

Commands from repository root, using the existing read-only environment (exact Microsoft Git snapshot preparation as in11A):
```sh
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B experiments/gsfm011b/run_baselines.py
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B experiments/gsfm011b/run_model.py microsoft-v1.1
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B experiments/gsfm011b/run_model.py newer-base-v2
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B experiments/gsfm011b/evaluate.py
```
Commands write `/private/tmp/gsfm011b-20261022/results`; this completed copy is immutable evidence. Use a fresh temporary/durable directory and update paths explicitly for any future authorized rerun; do not overwrite this run.

## Five plain-language findings

1. **The AC reference is feasible under the original checked equations and limits.** Its maximum P/Q residuals are about1.23e−10MW/1.66e−9MVAr. It is a feasible local optimum, not a certified global solution.

2. **DC-OPF was closer to this AC reference on all three shared MAEs.** Pg/angle/active-flow MAEs were26.09MW/7.23degrees/21.13MW, versus195.13/23.31/77.14 for Microsoft and106.40/48.83/98.32 for newer v2. This is one operating point; its differing flow law and the possibility of other feasible dispatches prevent a universal ranking.

3. **Neither frozen model returned an AC-feasible native operating point.** Microsoft’s largest P/Q imbalances were3754.08MW/8937.97MVAr; newer v2’s were3210.67MW/7958.03MVAr. The decisive failures are nodal power balance, despite nearly box-compliant Pg/Qg/Vm.

4. **Neither GridSFM release won every approximation measure.** Newer v2 reduced mean Pg error but had larger worst Pg error, larger mean angle/flow/Qg/Vm errors, and still failed balance. Shared branding does not make the releases interchangeable.

5. **DC balance is not AC feasibility, and no thermal claim is possible here.** DC produces neither Qg nor Vm; its AC-state metrics remain N/A. No PF recovery or OPF repair was used to fill them. All original branch ratings are unlimited. These results stop at the single-case11B comparison;11C was not run.
