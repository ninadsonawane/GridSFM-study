# Reproduce the saved-state analysis

Download both immutable evidence archives linked in [FINAL-ARTIFACTS](publication/FINAL-ARTIFACTS.md), verify their published SHA-256 values, and extract them. Keep the prior archive separate. `manifests/execution.json` pins the author source, environment, case inputs, checkpoints, settings and executable adapter hashes. Original machine paths are provenance, not portable installation instructions.

For analysis, set `GRIDSFM_PRIOR_EVIDENCE_ROOT` to the extracted `GridSFM-loading-study` root and `GRIDSFM_OFFICIAL_SOURCE_ROOT` to the exact author tree at `517a07531ea55a11bd81a89a6c6879695a2ba4b4`. Use the recorded Python/Numpy/SciPy/PyTorch/PyG versions. Analysis imports the stage definitions but does not run inference or a solver. Run from this extension directory:

```text
python code/summarize.py
python code/diagnose.py
python code/analyze_results.py
python code/make_figures.py
python code/audit_saved_results.py --prior <prior-root> --source <author-root> --base-checkpoint <base-v2.pt> --adapted-checkpoint <case500-n0100-control_model.pt>
```

The audit reads saved states and compares re-evaluated original-case metrics and every detailed table; it also validates all prior payload hashes, original source hashes, checkpoint hashes and plotting points. The optional checkpoint arguments relocate binaries without changing the historical manifest. Matplotlib is required for plots. Analysis regeneration changes derived figure/PDF metadata, so preserve the published archive when comparing exact artifact hashes.

The full numerical execution is retained in frozen `code/adapter.py` and `code/run_extension.py`, with `baseline`, `main` and `sensitivity` phases. Existing status files make runs resumable and prevent replacing outcomes. For a new numerical replication, create a separate copy/output directory, resolve the recorded checkpoint paths for that machine, validate all integration gates first and freeze a new execution manifest. Do not edit historical manifests or call existing archived outcomes a new run. No fresh numerical replication on another machine is claimed here.

The source contains the author Newton kernel, but the author evaluation exporter mentioned by a caller is absent at the pin. Our original-row export and allocation adapter is explicitly part of this reproduction. Compatible adapted case300/case300x2 weights are unavailable; do not substitute case500 weights for them.

To build the paper, use IEEEtran with the supplied vector figures and bibliography. The verified local build used Tectonic 0.17.0:

```text
cd paper
tectonic --untrusted --keep-logs --keep-intermediates manuscript.tex
```

Render all pages with Poppler and inspect them before running `python code/audit_paper.py --all-five-pages-visually-inspected` from the extension root. This check requires pypdf and records page count, fonts, abstract length and layout review. Authorship or content changes require another five-page check.
