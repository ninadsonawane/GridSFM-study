# Experiment17 — increased positive branch charging at90% case300 loading

One new intervention: strictly positive original branch charging multiplied by1.50. Reuse50% and100% points fromExperiment15; all loads remain90% oforiginal. No other parameter changes, training, PF completion or OPF repair. These are synthetic parameter interventions, not physical line replacement.

## Main observations

- AC localreference passes: upperQg-bound activity falls16→11, lower-bound activity rises6→10; totalbound count22→21. TotalQg falls5480.33→3146.06MVAr. More charging reduces net reactive generation required in this comparison but increases lower-bound activity. Activity is not a violation.
- Microsoftv1.1: PgMAE192.71→193.49MW, QgMAE79.12→84.52MVAr, VmMAE0.02751→0.03668pu; maxQ12796.76→12895.34MVAr. Pg/Qg/voltage accuracy and maximumQ worsen.
- Newerbasev2: PgMAE126.91→129.09MW, QgMAE88.00→95.20MVAr, VmMAE0.04643→0.05501pu. MaxQ21338.70→21308.18MVAr improves slightly, but meanQ470.85→474.69MVAr worsens. No broad feasibility improvement.
- DC state exactly unchanged across100→150% charging; its PgMAE16.99→16.65MW changes because the AC reference changes. DC Q/Vm remainN/A.
- At150%, Microsoft P/Q-violating counts299/300; v2 counts300/300. NativePg/Qg/Vm and angle bounds pass forboth; neither native point is AC-feasible. Worst P/Q bus238 forboth. ThermalN/A.
- StrictQg-clamp count7→8 forMicrosoft but meaningfulchanges above1e-3MVAr remain7→7; v2Qg26→26. StrictVmcounts37→36 and280→281, respectively; the newv2event is below1e-4pu. Do not interpret roundoff-level clamp events as new material violations.


## Accuracy against independently validated AC local references

| Charging | Method | Pg MAE MW | Qg MAE MVAr | Vm MAE pu | Angle MAE deg | Both-end active-flow MAE MW |
|---|---|---:|---:|---:|---:|---:|
| 50% | AC-OPF | 0 | 0 | 0 | 0 | 0 |
| 50% | DC-OPF | 18.2163 | N/A | N/A | 5.52255 | 17.2108 |
| 50% | microsoft-v1.1 | 192.273 | 97.7711 | 0.0286067 | 63.3861 | 94.8011 |
| 50% | newer-base-v2 | 127.476 | 99.8649 | 0.0461776 | 47.1698 | 108.98 |
| 100% | AC-OPF | 0 | 0 | 0 | 0 | 0 |
| 100% | DC-OPF | 16.9856 | N/A | N/A | 5.26663 | 16.1551 |
| 100% | microsoft-v1.1 | 192.714 | 79.1214 | 0.0275099 | 63.7245 | 95.3167 |
| 100% | newer-base-v2 | 126.912 | 87.999 | 0.0464311 | 47.3779 | 110.11 |
| 150% | AC-OPF | 0 | 0 | 0 | 0 | 0 |
| 150% | DC-OPF | 16.6536 | N/A | N/A | 5.1562 | 15.8136 |
| 150% | microsoft-v1.1 | 193.488 | 84.5199 | 0.0366815 | 66.0164 | 96.2101 |
| 150% | newer-base-v2 | 129.092 | 95.1972 | 0.0550132 | 47.3456 | 110.832 |

## Native physical validity and reactive constraint activity

DC P residual is its own DC-law residual; DC Q/Vm and AC joint feasibility are N/A. Model flows are derived from nativeVm/theta using exact AC physics. Thermal assessmentN/A on every point. Counts use1e-3MW/MVAr balance and generator tolerance,1e-4pu Vm,1e-3degree angle tolerance. Qbound activity within1e-3MVAr is NOT a violation.

| Charging | Method | Max P MW | Max Q MVAr | Mean Q MVAr | P/Q violating buses | Pg/Qg/Vm violations | Q lower/upper-bound activity | AC joint feasible |
|---|---|---:|---:|---:|---|---|---|---|
| 50% | AC-OPF | 1.25908e-11 | 1.13598e-10 | 1.93303e-12 | 0/0 | 0/0/0 | 2/26 | True |
| 50% | DC-OPF | 3.2685e-12 | N/A | N/A | 0/N/A | 0/N/A/N/A | N/A | N/A |
| 50% | microsoft-v1.1 | 4930.51 | 12641.7 | 321.582 | 300/300 | 0/0/0 | 2/5 | False |
| 50% | newer-base-v2 | 7735.18 | 21371.5 | 470.132 | 300/300 | 0/0/0 | 6/19 | False |
| 100% | AC-OPF | 2.413e-11 | 1.00773e-10 | 2.09691e-12 | 0/0 | 0/0/0 | 6/16 | True |
| 100% | DC-OPF | 3.2685e-12 | N/A | N/A | 0/N/A | 0/N/A/N/A | N/A | N/A |
| 100% | microsoft-v1.1 | 4991.08 | 12796.8 | 325.757 | 300/300 | 0/0/0 | 2/5 | False |
| 100% | newer-base-v2 | 7724.55 | 21338.7 | 470.847 | 300/300 | 0/0/0 | 6/20 | False |
| 150% | AC-OPF | 4.24407e-11 | 1.4735e-10 | 2.55689e-12 | 0/0 | 0/0/0 | 10/11 | True |
| 150% | DC-OPF | 3.2685e-12 | N/A | N/A | 0/N/A | 0/N/A/N/A | N/A | N/A |
| 150% | microsoft-v1.1 | 5043.03 | 12895.3 | 329.969 | 299/300 | 0/0/0 | 3/5 | False |
| 150% | newer-base-v2 | 7705.67 | 21308.2 | 474.686 | 300/300 | 0/0/0 | 6/20 | False |

## Genuine clipping events

| Charging | Release | Pg | Qg | Vm |
|---|---|---:|---:|---:|
| 50% | microsoft-v1.1 | 27 | 7 | 38 |
| 50% | newer-base-v2 | 44 | 25 | 279 |
| 100% | microsoft-v1.1 | 27 | 7 | 37 |
| 100% | newer-base-v2 | 44 | 26 | 280 |
| 150% | microsoft-v1.1 | 27 | 8 | 36 |
| 150% | newer-base-v2 | 45 | 26 | 281 |

Counts observe actual shipped clamp input/output without modifying inference. Complete residual distributions, worst originalbus IDs, approximation errors and constraint counts are inmethod-summary.csv/json; signed perbus terms inbus-metrics.csv.

## Reproduction and provenance

```sh
PYTHONDONTWRITEBYTECODE=1 ../GridSFM/model/.venv/bin/python -B experiments/gsfm017/study.py prepare
PYTHONDONTWRITEBYTECODE=1 ../GridSFM/model/.venv/bin/python -B experiments/gsfm015/run_cases.py results/comparisons/GSFM-017/20261026-increased-charging 17
PYTHONDONTWRITEBYTECODE=1 ../GridSFM/model/.venv/bin/python -B experiments/gsfm017/study.py report
```

prepare refuses existing output paths; reproduce in a new uniquely named output by changingO. Solver argv/options/termination and failures retained inrun-status.json and scenario directory; source/input/checkpoint hashes in manifests and modelmetadata. Same pinned sources/checkpoints and default clipping asExperiment15. CPU execution, no solver speed claim. Raw inputs, native tensors and solver logs arelocal-only; sha256 inventory identifies allfiles. Compact reports/CSV/code are reviewable.

Unresolved row-order sensitivity fromExperiment16 still limits causal interpretation. Results concern these frozen native releases, not the later paper's trained control-plus-Newton workflow. No outcome-selected settings or additional scenarios. Stop afterthis one input.
