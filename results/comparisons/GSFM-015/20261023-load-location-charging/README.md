# Experiment15 — global loading, local redistribution and line charging

COMPLETE,23 October2026. Eighteen unique inputs:12 new solver inputs and6 reused. Both frozen releases use shipped hard clamps, seed0, CPU FP32; independent original-parameter electrical scoring is FP64. No training, PF completion, OPF repair, extra topology, or invented branch ratings.36 instrumented native forwards capture real clamp inputs/outputs;12 reused native points reproduce saved outputs exactly. Earlier scientific artifacts are hash-verified unchanged.

## Main outcomes

Accepted feasible local AC references:12/18. UNKNOWN after default+allowed deterministic flat retry:C300-L0.90-B0.00, C300-L1.06-B0.50, C300-L1.06-B0.00, C600-L0.90-B0.00, C600-L1.06-B0.50, C600-L1.06-B0.00. Numerical failure is not proof of infeasibility. All18 DC solves satisfy their own original DC equations/limits. All36 native model points fail joint AC feasibility. Reference errors are N/A on UNKNOWN inputs; model balance/bound checks remain reference-free. DC Qg/Vm/AC-Q/AC-thermal/joint feasibility are N/A.

## Tests and interpretation

## What the three tests found

| Test | Observed result | Meaning for clipping and limits |
|---|---|---|
| Global loading | On300, v2 maxQ imbalance is21339/7958/9233MVAr at90/100/106%; on600 it is21360/9231/9228. | Lighter loading is not uniformly easier for the surrogate. All generator/voltage excess counts stay0 within tolerance because of clipping; balance still fails. |
| Fixed-total location | Moving63.82MW and16.02MVAr between the selected300 groups changes v2 maxQ to21162MVAr for the low-admittance recipient versus8019 for the reverse direction. v1.1 changes much less:8901 versus9007. On600 Splus overloads both ties; Sminus does not. | Location and transfer direction matter even at the same totals. This does not prove the admittance proxy causes failure. Both releases remain infeasible. |
| Reduced charging | At90% loading, halving positive b raises AC-reference generators at Q bounds from22 to28 on300, and44 to56 on600. Only2/8 charging cases yield verified references;6 remain UNKNOWN after retries. DC states match the corresponding unchanged-charging cases within1e-6. | Reduced reactive support stresses AC solutions, while DC ignores charging. Some model imbalances decrease even where no feasible AC reference was obtained; that is not proof of improved accuracy or feasibility. |

Actual clipping is extensive: base300 MS1.1 clips21/69 Pg,8/69 Qg,39/300 V; v2 clips51/69 Pg,27/69 Qg,281/300 V. Base600 counts are39/138,20/138,99/600 forMS1.1 and97/138,54/138,567/600 forv2. Counts reflect exact nonzero operations, not merely bound equality; meaningful-tolerance counts/magnitudes are also saved. v2 base300 maximum clamp changes are1782.25MW Pg,659.81MVAr Qg and1.8843pu V. These are checkpoint/default-specific observations, not results for a sigmoid fine-tuned control model.

In all36 joint fixed-angle preclip diagnostics, native clipping reduces mean absolute P and Q imbalance; maximum P/Q does not increase. Clipping prevents still larger errors in that diagnostic but is not a power-balance solve. Pg-only/Qg-only/Vm-only results retain interactions and any worsening separately.

Across all12 reference-valid inputs, DC has lower Pg and active-line-flow MAE than either frozen model. Each model beats DC's angle MAE on1/12 inputs (the reused600 Splus); angle advantage does not imply AC feasibility. No single scalar ranks all operating-point qualities.

| Test | Frozen intervention | What this can establish |
| --- | --- | --- |
| 15A global | Pd,Qd ×0.90/1.00/1.06 on300/600 | Changes need not be monotonic; compare errors and clipping separately. |
| 15B location | 300:63.82MW/16.02MVAr shifted between fixed source-selected5-bus groups;600:Splus/Sminus reused | Equal network totals do not imply equal prediction quality. These groups are admittance-proxy contrasts, not causal proof of strength. |
| 15C charging | Positive branch b ×0.5/0 at loads0.90/1.06 on300/600 | Removing reactive charging changes the AC problem; DC is invariant by its approximation. Failed AC references remain UNKNOWN. |

Original300 inherited RATE_A remains zero/unlimited: thermal assessment N/A. Constructed600 thermal assessment covers only the two synthetic600MVA ties. Charging reduction includes inherited and tie positive b; bus capacitive/inductive shunts and negative branch b are untouched. All other electrical parameters, generator capacities/costs and bounds remain unchanged. charging-coverage.csv separates inherited and tie charging.

## Compact model result tables

Clipping counts are exact nonzero clamp changes Pg/Qg/V (69/69/300 or138/138/600 elements); clipping-summary.csv also distinguishes changes above1e-3MW/MVAr or1e-4pu and reports magnitudes. Bound activity is not synonymous with clipping. P/Q below are maximum native imbalance in MW/MVAr.

### global

| Input | Release | AC ref | Pg MAE MW | Vm MAE pu | Angle MAE deg | Pflow MAE MW | P max MW | Q max MVAr | Clipped Pg/Qg/V | Overloaded ties |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G300-0.90 | MS1.1 | PASS | 193 | 0.0275 | 63.7 | 95.3 | 4.99e+03 | 1.28e+04 | 27/7/37 | N/A |
| G300-0.90 | v2 | PASS | 127 | 0.0464 | 47.4 | 110 | 7.72e+03 | 2.13e+04 | 44/26/280 | N/A |
| G300-1.00 | MS1.1 | PASS | 195 | 0.0269 | 23.3 | 77.1 | 3.75e+03 | 8.94e+03 | 21/8/39 | N/A |
| G300-1.00 | v2 | PASS | 106 | 0.0435 | 48.8 | 98.3 | 3.21e+03 | 7.96e+03 | 51/27/281 | N/A |
| G300-1.06 | MS1.1 | PASS | 199 | 0.0283 | 29.4 | 72.3 | 3.15e+03 | 7.98e+03 | 21/9/42 | N/A |
| G300-1.06 | v2 | PASS | 88.8 | 0.0422 | 50.7 | 99.5 | 3.87e+03 | 9.23e+03 | 51/27/285 | N/A |
| G600-0.90 | MS1.1 | PASS | 135 | 0.0263 | 28 | 76.4 | 3.6e+03 | 1.25e+04 | 42/21/105 | 0 |
| G600-0.90 | v2 | PASS | 126 | 0.0439 | 47 | 108 | 7.65e+03 | 2.14e+04 | 81/50/559 | 0 |
| G600-1.00 | MS1.1 | PASS | 123 | 0.0267 | 30.2 | 71.5 | 1.14e+03 | 9.38e+03 | 39/20/99 | 0 |
| G600-1.00 | v2 | PASS | 106 | 0.0422 | 49 | 94.7 | 4.92e+03 | 9.23e+03 | 97/54/567 | 0 |
| G600-1.06 | MS1.1 | PASS | 120 | 0.0275 | 28.6 | 76.8 | 698 | 7.52e+03 | 37/18/87 | 0 |
| G600-1.06 | v2 | PASS | 89.3 | 0.0419 | 51 | 95.6 | 5.35e+03 | 9.23e+03 | 102/54/573 | 0 |


### local

| Input | Release | AC ref | Pg MAE MW | Vm MAE pu | Angle MAE deg | Pflow MAE MW | P max MW | Q max MVAr | Clipped Pg/Qg/V | Overloaded ties |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L300-weak | MS1.1 | PASS | 195 | 0.0271 | 23.6 | 77 | 3.73e+03 | 8.9e+03 | 21/8/39 | N/A |
| L300-weak | v2 | PASS | 107 | 0.0457 | 49.1 | 118 | 7.8e+03 | 2.12e+04 | 50/27/274 | N/A |
| L300-strong | MS1.1 | PASS | 196 | 0.0267 | 23.2 | 77.5 | 3.79e+03 | 9.01e+03 | 21/8/40 | N/A |
| L300-strong | v2 | PASS | 106 | 0.0432 | 48.6 | 95.7 | 3.24e+03 | 8.02e+03 | 52/26/283 | N/A |
| L600-Splus | MS1.1 | PASS | 126 | 0.027 | 35.6 | 87.1 | 1.4e+03 | 9.34e+03 | 39/20/95 | 2 |
| L600-Splus | v2 | PASS | 106 | 0.0435 | 34.3 | 103 | 5.08e+03 | 9.23e+03 | 96/54/557 | 2 |
| L600-Sminus | MS1.1 | PASS | 120 | 0.0266 | 56 | 79.6 | 940 | 8.76e+03 | 38/19/92 | 0 |
| L600-Sminus | v2 | PASS | 106 | 0.0435 | 73.7 | 101 | 5.02e+03 | 9.24e+03 | 96/54/557 | 0 |


### charging

| Input | Release | AC ref | Pg MAE MW | Vm MAE pu | Angle MAE deg | Pflow MAE MW | P max MW | Q max MVAr | Clipped Pg/Qg/V | Overloaded ties |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C300-L0.90-B0.50 | MS1.1 | PASS | 192 | 0.0286 | 63.4 | 94.8 | 4.93e+03 | 1.26e+04 | 27/7/38 | N/A |
| C300-L0.90-B0.50 | v2 | PASS | 127 | 0.0462 | 47.2 | 109 | 7.74e+03 | 2.14e+04 | 44/25/279 | N/A |
| C300-L0.90-B0.00 | MS1.1 | UNKNOWN | N/A | N/A | N/A | N/A | 4.86e+03 | 1.26e+04 | 27/7/37 | N/A |
| C300-L0.90-B0.00 | v2 | UNKNOWN | N/A | N/A | N/A | N/A | 7.75e+03 | 2.14e+04 | 44/25/280 | N/A |
| C300-L1.06-B0.50 | MS1.1 | UNKNOWN | N/A | N/A | N/A | N/A | 3.13e+03 | 7.91e+03 | 20/9/43 | N/A |
| C300-L1.06-B0.50 | v2 | UNKNOWN | N/A | N/A | N/A | N/A | 3.58e+03 | 9.2e+03 | 50/27/286 | N/A |
| C300-L1.06-B0.00 | MS1.1 | UNKNOWN | N/A | N/A | N/A | N/A | 3.1e+03 | 7.88e+03 | 20/9/43 | N/A |
| C300-L1.06-B0.00 | v2 | UNKNOWN | N/A | N/A | N/A | N/A | 3.43e+03 | 9.17e+03 | 50/28/287 | N/A |
| C600-L0.90-B0.50 | MS1.1 | PASS | 134 | 0.0284 | 27.9 | 75.4 | 3.58e+03 | 1.25e+04 | 42/21/103 | 0 |
| C600-L0.90-B0.50 | v2 | PASS | 125 | 0.0448 | 46.8 | 107 | 7.66e+03 | 2.14e+04 | 82/52/559 | 0 |
| C600-L0.90-B0.00 | MS1.1 | UNKNOWN | N/A | N/A | N/A | N/A | 3.56e+03 | 1.25e+04 | 42/21/102 | 0 |
| C600-L0.90-B0.00 | v2 | UNKNOWN | N/A | N/A | N/A | N/A | 7.68e+03 | 2.14e+04 | 82/52/561 | 0 |
| C600-L1.06-B0.50 | MS1.1 | UNKNOWN | N/A | N/A | N/A | N/A | 680 | 7.48e+03 | 37/18/88 | 0 |
| C600-L1.06-B0.50 | v2 | UNKNOWN | N/A | N/A | N/A | N/A | 5.21e+03 | 9.2e+03 | 101/54/573 | 0 |
| C600-L1.06-B0.00 | MS1.1 | UNKNOWN | N/A | N/A | N/A | N/A | 656 | 7.45e+03 | 37/17/89 | 0 |
| C600-L1.06-B0.00 | v2 | UNKNOWN | N/A | N/A | N/A | N/A | 5.16e+03 | 9.17e+03 | 98/54/571 | 0 |


## AC/DC baselines and all error/limit fields

| Input | Method | AC ref | Pg MAE MW | Angle MAE deg | Pflow MAE MW | P max MW | Q max MVAr | AC joint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G300-0.90 | AC-OPF | PASS | 0 | 0 | 0 | 2.41e-11 | 1.01e-10 | True |
| G300-0.90 | DC-OPF | PASS | 17 | 5.27 | 16.2 | 3.27e-12 | N/A | N/A |
| G300-1.00 | AC-OPF | PASS | 0 | 0 | 0 | 1.23e-10 | 1.66e-09 | True |
| G300-1.00 | DC-OPF | PASS | 26.1 | 7.23 | 21.1 | 5.12e-12 | N/A | N/A |
| G300-1.06 | AC-OPF | PASS | 0 | 0 | 0 | 3.17e-11 | 1.62e-10 | True |
| G300-1.06 | DC-OPF | PASS | 37.9 | 7.19 | 23.5 | 7.28e-12 | N/A | N/A |
| G600-0.90 | AC-OPF | PASS | 0 | 0 | 0 | 1.44e-11 | 8.54e-11 | True |
| G600-0.90 | DC-OPF | PASS | 17 | 5.27 | 16.1 | 5.02e-12 | N/A | N/A |
| G600-1.00 | AC-OPF | PASS | 0 | 0 | 0 | 2.03e-11 | 1.01e-10 | True |
| G600-1.00 | DC-OPF | PASS | 26.1 | 7.23 | 21.1 | 1.09e-11 | N/A | N/A |
| G600-1.06 | AC-OPF | PASS | 0 | 0 | 0 | 1.78e-11 | 1.43e-10 | True |
| G600-1.06 | DC-OPF | PASS | 37.9 | 7.2 | 23.4 | 9.46e-12 | N/A | N/A |
| L300-weak | AC-OPF | PASS | 0 | 0 | 0 | 2.86e-11 | 7.82e-11 | True |
| L300-weak | DC-OPF | PASS | 25.8 | 6.98 | 20.6 | 7.74e-12 | N/A | N/A |
| L300-strong | AC-OPF | PASS | 0 | 0 | 0 | 2.19e-11 | 1.39e-10 | True |
| L300-strong | DC-OPF | PASS | 26.5 | 7.48 | 21.7 | 9.38e-12 | N/A | N/A |
| L600-Splus | AC-OPF | PASS | 0 | 0 | 0 | 2.25e-11 | 1.83e-10 | True |
| L600-Splus | DC-OPF | PASS | 31.6 | 36.5 | 38.6 | 6.62e-11 | N/A | N/A |
| L600-Sminus | AC-OPF | PASS | 0 | 0 | 0 | 1.59e-11 | 1.22e-10 | True |
| L600-Sminus | DC-OPF | PASS | 31.6 | 36.3 | 38.6 | 8.1e-11 | N/A | N/A |
| C300-L0.90-B0.50 | AC-OPF | PASS | 0 | 0 | 0 | 1.26e-11 | 1.14e-10 | True |
| C300-L0.90-B0.50 | DC-OPF | PASS | 18.2 | 5.52 | 17.2 | 3.27e-12 | N/A | N/A |
| C300-L0.90-B0.00 | AC-OPF | UNKNOWN | N/A | N/A | N/A | 1.52e-09 | 12.7 | False |
| C300-L0.90-B0.00 | DC-OPF | UNKNOWN | N/A | N/A | N/A | 3.27e-12 | N/A | N/A |
| C300-L1.06-B0.50 | AC-OPF | UNKNOWN | N/A | N/A | N/A | 1.18e-09 | 47.3 | False |
| C300-L1.06-B0.50 | DC-OPF | UNKNOWN | N/A | N/A | N/A | 7.28e-12 | N/A | N/A |
| C300-L1.06-B0.00 | AC-OPF | UNKNOWN | N/A | N/A | N/A | 3.34 | 465 | False |
| C300-L1.06-B0.00 | DC-OPF | UNKNOWN | N/A | N/A | N/A | 7.28e-12 | N/A | N/A |
| C600-L0.90-B0.50 | AC-OPF | PASS | 0 | 0 | 0 | 2.32e-11 | 7.27e-11 | True |
| C600-L0.90-B0.50 | DC-OPF | PASS | 18.2 | 5.52 | 17.2 | 5.02e-12 | N/A | N/A |
| C600-L0.90-B0.00 | AC-OPF | UNKNOWN | N/A | N/A | N/A | 1.53e-09 | 12.7 | False |
| C600-L0.90-B0.00 | DC-OPF | UNKNOWN | N/A | N/A | N/A | 5.02e-12 | N/A | N/A |
| C600-L1.06-B0.50 | AC-OPF | UNKNOWN | N/A | N/A | N/A | 1.18e-09 | 47.3 | False |
| C600-L1.06-B0.50 | DC-OPF | UNKNOWN | N/A | N/A | N/A | 9.46e-12 | N/A | N/A |
| C600-L1.06-B0.00 | AC-OPF | UNKNOWN | N/A | N/A | N/A | 3.34 | 465 | False |
| C600-L1.06-B0.00 | DC-OPF | UNKNOWN | N/A | N/A | N/A | 9.46e-12 | N/A | N/A |

Full MAE/median/p95/max of Pg/Qg/Vm/angles/both-end P/Q, separate P/Q residual distributions/counts, generator and voltage excesses, active angle constraints and tie loading are in method-summary.json/csv; signed bus and both-end branch tables are local with hashes. Locations use original external IDs and A/B mappings, including distinct parallel rows. Reference points are feasible local optima, not global certificates. Solver bound-activity counts are in method-summary.json.

## Clipping diagnosis: what was actually measured

The passive observer records the exact argument and result of the original _leaky_clip call and returns the original tensor unchanged. Pg/Qg preclip inputs INCLUDE the shipped midpoint offsets; Vm is the direct head value. All captures exactly equal elementwise hard clipping and API outputs. Outputs are saved before any evaluation. No sigmoid override or unclamped neural forward was run.

Preclip-Pg-only, Qg-only, Vm-only and joint substitutions are diagnostic HYBRIDS, keeping native angles; those angles were computed using clipped Pg in the DC prior. They isolate direct state-block changes at fixed angles, not the full counterfactual removal of internal clipping. They may violate bounds and are not candidate repairs. preclip-diagnostics.json and clipping-physics-effects.csv retain improvements and worsening, signed; no additive attribution is claimed.

## Reproduction and artifacts

Protocol:docs/experiments/GSFM-015.md. Code:experiments/gsfm015. Existing Python/Julia environments and both frozen source/checkpoint hashes are unchanged from11A/B and12; new metadata records exact paths/pins. Raw states/input matrices/logs are local-only on this Mac with inventory hashes, not remotely downloadable from hashes. Manifest/input/group selection was frozen before outcomes.

```sh
PY=/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python
O=results/comparisons/GSFM-015/20261023-load-location-charging
# Fresh output only: preparation and runner refuse overwrite.
"$PY" -B experiments/gsfm015/prepare.py
"$PY" -B experiments/gsfm015/run_cases.py "$O" 15
"$PY" -B experiments/gsfm015/capture_reused.py
"$PY" -B experiments/gsfm015/analyze.py
"$PY" -B experiments/gsfm015/report.py
```

Fixed protocols/paths require recorded local prerequisites; restore source/checkpoints and old saved states before independent reproduction. Reuse does not assume hash-only artifacts are available elsewhere. Current study is a small inspected sensitivity screen; no broad transfer, publication novelty, solver speedup, dynamic-stability or causal training explanation is established. Stop after these three tests.
