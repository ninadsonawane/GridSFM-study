# Experiments 12–14: frozen physical validity

Completed 23 October 2026 from parent commit `96888bc4ecd792022f54ada495aad90f45d989dc`. Reports are linked from the root README. Sequential CPU execution; no training, PF completion, OPF repair, or additional scenarios.

## Requirements and artifact availability

The existing Python3.11 GridSFM/PyG/PYPOWER environment and Julia PowerModels/Ipopt project are recorded in each execution-provenance.json. Both frozen source snapshots/checkpoints are required at the paths recorded in run_model.py (no checkpoint selection); source pins, whole-file hashes, default clamps and feature audit are in model-audit.json. Historical 11B/C native states/reference files must be present for13. Raw inputs, native states and logs are local-only on the execution Mac; artifact-inventory.json records every retained file path, size and SHA256. Hashes alone do not make these downloadable. No new environment installation is implied.

`electrical.py` implements dimension-independent FP64 scoring with original Ybus and an independently stamped branch-sum calculation, and the audited MATPOWER makeBdc-equivalent DC equations. `verify_delivery.py` checks saved results, exported IDs, reference feasibility, source/checkpoint/settings hashes, derivative checks and preservation of earlier 11B/C/D artifacts. It does not launch scientific runs.

## Commands used / fresh reproduction

Run from the repository root. Set these paths to the recorded existing runtimes:

```sh
PY=/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python
PLOT_PY=/Users/ninadsonawane/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
E=experiments/gsfm012_014
O12=results/comparisons/GSFM-012/20261023-frozen-two-copy
O14=results/comparisons/GSFM-014/20261023-rated-variants
```

Preparation and scientific commands below require a **fresh checkout/output location**, both checkpoint environments and prerequisite local artifacts. Preparation/runner refuse existing output; do not delete completed results to rerun. Scripts currently encode these run IDs and historical local paths; use a separate checkout or explicitly parameterize paths for independent reproduction.

```sh
"$PY" -B "$E/prepare12.py"
"$PY" -B "$E/run_cases.py" "$O12" 12
"$PY" -B "$E/report12.py"
"$PLOT_PY" "$E/plots.py" 12
"$PY" -B "$E/analyze13.py"
"$PY" -B "$E/report13.py"
"$PLOT_PY" "$E/plots.py" 13
```

Before14, retrieve the source URL in source-manifest.json to `$O14/source/pglib_opf_case300_ieee.m`, verify SHA256 `7ecf056d5942135765200ad7ae8791c28f0d35fb1dc888ba2c32dfc950f3c2f5`, and restore the tracked source-manifest.json alongside it. Preserve its CC BY4.0 header and public attribution. The full published case is used, including12 fixed-Pg generators, rather than transplanting ratings into MATPOWER.

```sh
"$PY" -B "$E/prepare14.py"
"$PY" -B "$E/run_cases.py" "$O14" 14
"$PY" -B "$E/audit_rating_features.py" microsoft-v1.1
"$PY" -B "$E/audit_rating_features.py" newer-base-v2
"$PY" -B "$E/response14.py"
"$PY" -B "$E/report14.py"
"$PLOT_PY" "$E/plots.py" 14
"$PY" -B "$E/verify_delivery.py"
```

Plotting uses matplotlib in the existing Python3.12 plotting runtime; the historical plotdeps path can be replaced by an installed matplotlib location. Full worker argv and actual statuses are in run-status.json. AC uses the prior audited PowerModels AC formulation, 3000 iterations/120 seconds, one deterministic flat retry only if necessary. DC uses the audited PIPS quadratic program, 150 iterations. Native outputs are archived before independent scoring; poisoned-label forwards are counted separately.

## Retained corrections

The first report exports mistakenly labelled normalized bus indices as IDs. Original/generated external bus IDs were restored in exports and all affected tables were regenerated solely from saved states; electrical calculations and native states were unchanged. Verification now checks every exported bus and branch endpoint against its original input.

PGLib’s valid10-column generator table triggered PYPOWER’s version-width heuristic, resetting branch angle bounds. Eight initial DC outputs failed round-trip gates and are preserved as invalid-format-attempt0 artifacts, excluded from accepted tables. Only absent optional generator columns were padded to canonical MATPOWERv2 format at the solver boundary, leaving original input/model matrices unchanged. Eight corrected solves now pass original DC constraints. **Actual14 DC calls16:8 rejected +8 corrected**, exceeding the planned8. AC calls11 (8 default,3 allowed retries); native forwards16 plus8 label-audit forwards. This incident did not cause extra cases or AC/model reruns. Fresh run_dc.py includes the corrected adapter and stops on conversion assertion failures.

Experiment12 used3 AC/3 DC calls,6 native plus4 audit forwards. Experiment13 used9 feasible saved reference points/18 model states, no solves or forwards; all7200 decomposition rows were checked. It keeps445 eligible comparisons and selects at most6 per component/release across both networks,24 total. `select13_examples.py` applied this literal display cap to the saved table without recomputing science; fresh analyze13.py incorporates it. `rescore_saved.py` is postprocessing only.
