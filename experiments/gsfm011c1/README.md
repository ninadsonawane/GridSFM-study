# Experiment11C-1: six fixed load scalings

This is the completed22October2026 loading-only screen. Read the report at `../../results/comparisons/GSFM-011C-1/20261022-loading-only/README.md`. All24 scientific method calls are finished. Do not rerun to replace the1.10 AC failure.

## Prerequisites and commands

Use the existing read-only11B environments; no installation is needed. Python3.11 with Torch2.8.0/PyG2.8.0.post1/PYPOWER5.1.21, Julia1.11.9 with the existing PowerModels0.21.5/Ipopt1.14.0 project, exact Microsoft/v2 snapshots and both manifest-pinned checkpoints. Paths/defaults are explicit in workers. Microsoft exact source is exported in `/private/tmp/gsfm011b-20261022/microsoft-source`; pinned MATPOWER makeBdc/opf_setup/makeAang audit files are alongside it. Preserve or restore those exact pinned11B resources before reproducing on another machine. Large checkpoint/input/state files are not in Git. See11B provenance, inventory and `frozen-protocol.json`.

Executed sequence (repository root; the initial run used an identical temporary run_six copy):

```sh
PY=/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python
"$PY" -B experiments/gsfm011c1/prepare.py
"$PY" -B experiments/gsfm011c1/run_six.py
"$PY" -B experiments/gsfm011c1/evaluate_saved.py results/comparisons/GSFM-011C-1/20261022-loading-only/load-1.10
"$PY" -B experiments/gsfm011c1/summarize.py
/Users/ninadsonawane/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/gsfm011c1/plot.py
```

The explicit1.10 evaluation extracts its ALREADY SAVED failed iterate, evaluates physics, and nulls reference errors. It makes no solver/model call. It was added after discovering the retained AC failure; final run_six now invokes that failure-aware path for every returned case. Numerical thresholds were not changed. Final code/hashes differ only in reporting, failure handling and overwrite protection; frozen-protocol.json retains pre-run worker hashes. Postprocessing can be repeated safely. Workers match the exact11B options; AC Ipopt1000iterations/30CPU seconds with120s outer process guard (including Julia startup), DC PIPS150iterations with30s process guard. All observed attempts finish well below30s. These are descriptive timings, not an acceleration benchmark.

prepare/run_six refuse to overwrite any completed attempts. For an independently authorized reproduction, set GSFM011C1_OUTPUT to a fresh absolute directory before the sequence. That does not authorize additional runs now. Hard-coded baseline1.00 remains reused; no1.00 solve is performed.

plot.py uses only the existing temporary Python3.12 matplotlib installation at `/private/tmp/gsfm007-20261021T195824Z/plotdeps`. A Python3.11 plotting attempt encountered an ABI mismatch before drawing anything; the compatible existing3.12 runtime succeeded. Neither environment was modified. Computational states were not rerun.

## Failure and metric definitions

run_ac saves full solver JSON before checking termination. A failed termination is retained and reported UNKNOWN, never proof of infeasibility. The original11B evaluator is used through evaluate_saved, which nulls all approximation/diagnostic errors without a feasible reference. AC1.10 native JSON is the returned failed iterate, NOT a feasible operating point. Model native states are saved before evaluation; neither model worker reads references. DC Qg/Vm are null, not fabricated. Thermal assessment is N/A with original zero ratings. Exact original branch/Ybus checks are authoritative.

No training, PF completion, OPF repair, additional loading points, reactive-only input changes or spatial families are part of this screen. Stop here.
