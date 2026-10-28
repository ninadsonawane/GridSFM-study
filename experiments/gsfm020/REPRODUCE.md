# Reproduce or inspect Experiment 20

For another device, start with [REMOTE-ARTIFACTS.md](REMOTE-ARTIFACTS.md): GitHub report links, the complete evidence ZIP, checksum and download instructions. The local paths below preserve the original executed environment.

This report accompanies the completed local run. The evidence snapshot contains every saved attempt and prior tracked study file, without Git metadata, installed runtimes, caches or checkpoint binaries. Public checkpoint URLs and full hashes are in `results/comparisons/GSFM-020/20261026-local-operating-conditions/environment/environment-summary.json`. `artifact-manifest.json` in the delivery root hashes all delivered evidence files; `package-verification.json` records archive verification.

## Verified identities and environment

| Item | Pinned identity |
|---|---|
| Study baseline | `2aa8778e0cc97cc39e748b40fdb8b36a475e4d0f` |
| Microsoft source | `1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6` |
| Newer source | `517a07531ea55a11bd81a89a6c6879695a2ba4b4` |
| v1.1 checkpoint SHA256 | `f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831` |
| v2 checkpoint SHA256 | `9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7` |
| MATPOWER 8.1 case300 source SHA256 | `69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5` |
| Existing 300 input SHA256 | `b17262cb24fffd05fb0bf7aeb8be13aafab47cc676a112016921c2969772deed` |
| Existing 600 input SHA256 | `73883ff8c061999d8b50aa27c43bd9b40527b448ffe98fab9aacd073bf04c0f6` |
| Confirmation plan SHA256 | `2f107d8e49c936773737169b379342c7677a6057846dd02adeceda98148d3e2a` |
| Final verification SHA256 | `e178d99599b687ef9bc8d78de394be92a635fc80cdceabb7f7c6862944a0960f` |

Executed on Windows 11, CPU FP32, seed 0, four Torch threads. Python 3.13.16; Torch 2.8.0; PyG 2.8.0.post1; NumPy 2.4.6; SciPy 1.17.1; PYPOWER 5.1.21; matplotlib 3.10.8. The complete Python freeze is retained. Julia 1.11.9, PowerModels 0.21.5, Ipopt 1.14.0, JuMP 1.29.4 and MathOptInterface 1.49.0 are pinned by `experiments/gsfm020/julia/Project.toml` and `Manifest.toml`. Julia uses one thread, BLAS one thread and `--compiled-modules=existing` on this host.

Exact sources/checkpoints and direct scientific versions match the earlier study; the historical Mac platform and every transitive dependency were not reproduced. Local versus historical base replay differs slightly: maximum Pg difference 0.000429 MW for v1.1 and 0.001913 MW for v2. Cross-platform equality is not claimed. Windows cache paths were shortened before retrying two preprocessing failures; no model math or source was altered.

AC uses PowerModels ACP with Ipopt tol1e-9, constraint tolerance1e-10, acceptable tolerance1e-9, bound relaxation0, maximum 3000 iterations and 120 seconds including build per attempt. One deterministic flat retry follows a failed default attempt. DC uses the audited PYPOWER PIPS 200 path,150 iterations, feasibility tolerance1e-10 and gradient/complementarity1e-9. Exact invocations, requests, solver logs and all failure iterates are retained per case.

Fixed physical acceptance tolerances are 1e-3 MW/MVAr for balance/generator limits,1e-4 pu for voltage,1e-3 degrees for angle and1e-3 MVA for finite thermal ratings. Independent branch-stamp/Ybus agreement must be below 1e-6 MVA. Original branch charging, shunts, transformer ratios/shifts, statuses and generator costs are checked. Accepted references are feasible local optima, not certified global optima. Worst accepted residuals were 5.54e-10 MW and 1.236e-9 MVAr.

## Read saved evidence locally

The following PowerShell commands use the retained original runtime. They perform saved-state analysis; they do not run model inference or optimization. Run in a disposable evidence copy if preserving derived-file timestamps matters.

```powershell
$studyPath = 'C:\Users\Ninad\Documents\Codex\2026-10-26\don-t-wait-for-max-anything\work\GridSFM-study'
$studyPython = 'C:\Users\Ninad\Documents\Codex\2026-10-26\don-t-wait-for-max-anything\work\runtime\python\Scripts\python.exe'
Set-Location -LiteralPath $studyPath
& $studyPython -B experiments/gsfm020/analyze.py
& $studyPython -B experiments/gsfm020/postprocess_mechanisms.py
& $studyPython -B experiments/gsfm020/figures.py
& $studyPython -B experiments/gsfm020/review_confirmations.py
```

The original `final_verify.py --out final-recheck.json` command was executed during the bounded run and intentionally rejects execution after 21:45:13 UTC on 26 October 2026. Its saved PASS report is retained unchanged. For later saved-state rechecks, use `review_confirmations.py` above, or `audit_ac_references.py --help` for the independent AC audit. The original final verifier additionally checks adjacent `runtime/sources/{microsoft,newer}` Git checkouts and `runtime/checkpoints/` bytes. For use elsewhere, restore those exact public pins and the Python environment at the same relative layout, or adjust the explicit runtime paths in a separate reproduction copy. No such second-host execution is claimed. `analyze.py` and the saved CSV/JSON tables can be inspected without rerunning inference.

## Commands used for experimental execution

These are documentary commands, **not additional runs requested by this report**. Each original invocation is saved in `run-status.json` and the worker metadata. `prepare.py` refuses to replace an existing plan, `run_batch.py` refuses an implicit replay, and the original deadline remains enforced. A future rerun needs its own explicitly authorized output directory and clock; retain the original record unchanged.

```powershell
# Initial construction: exact historical300/600 network hashes were verified.
& $studyPython -B experiments/gsfm020/prepare.py init

# Each discovery batch was frozen and completed before the next was chosen.
& $studyPython -B experiments/gsfm020/prepare.py batch experiments/gsfm020/batch01.json
& $studyPython -B experiments/gsfm020/run_batch.py results/comparisons/GSFM-020/20261026-local-operating-conditions/batches/01-load-transition/plan.json

# Subsequent frozen plans:02-clamp-onset,03-P-Q-isolation,
# 04-fixed-total-location,05-existing-two-area-location,06-confirmation.
# Templates:batch02.json,batch03.json,batch04.json,batch05.json,confirmation.json.

# Exact standalone model interface (choose a NEW output directory for any future rerun).
& $studyPython -B experiments/gsfm020/model_worker.py --release microsoft-v1.1 --source ../runtime/sources/microsoft --checkpoint ../runtime/checkpoints/gridsfm_open_v1.1.pt --input results/comparisons/GSFM-020/20261026-local-operating-conditions/cases/G300-0.93/input.json --out NEW_REPLAY_DIRECTORY
# v2 uses release newer-base-v2,source ../runtime/sources/newer,
# checkpoint ../runtime/checkpoints/gridsfm_open_v2.pt.
```

`diagnostic.py --help` documents the bounded representation schedule; its original frozen protocols and failed attempts are under `diagnostic/`. No further diagnostic forwards were run after the 19-forward gate. All operating workers saved native returns before conversion/scoring, and all models ran on unsolved inputs before the corresponding conventional solves. Altered prepared features appear only in explicitly named diagnostic outputs.

## Artifact map

All paths below are relative to the `study` directory in the delivery. Let `O = results/comparisons/GSFM-020/20261026-local-operating-conditions`.

- `experiments/gsfm020/`: report, protocol, batch templates, model worker, solver adapters, independent audits, mechanism analysis and plotting code.
- `O/ledger.json`, `O/batches/*/plan.json`: every attempted condition, frozen hypotheses, intervention values, paired controls, timestamps and input hashes.
- `O/cases/<ID>/input.json`, `field-differences.json`: exact original matrices and the permitted changes.
- `O/cases/<ID>/*-returned.pt`, `*-returned.json`, native/metadata/prepared-feature/clamp files: native tensors and their mapping before physical scoring. Use the manifest for exact filenames.
- `O/cases/<ID>/ac-*`, `dc-*`, `run-status.json`: solver requests, raw returns, logs, accepted states, failed iterates and statuses. The two UNKNOWN AC cases are `A600-plus075` and `A600-minus075`.
- `O/method-summary.csv`, `live-table.md`: all 104 method rows; five error families and P/Q distributions; counts and severity for generator, voltage, angle and applicable thermal limits. UNKNOWN-reference errors and inapplicable DC/thermal fields remain N/A.
- `O/cases/<ID>/bus-metrics.csv`, `branch-flows.csv`, `violations.json`, `clipping-summary.json`: spatial details and actual clipping distinct from bound activity.
- `O/mechanisms/confirmation-checks.json`: all six confirmation outcomes, frozen expectations, component controls, native/reference movement, localized balances and counterevidence.
- `O/mechanisms/`: cumulative 42 paired comparisons, exact signed budgets, constraint locations, clipping activity and full source-hash manifest.
- `O/diagnostic/diagnostic-review.md`, `O/diagnostic-effects.csv`, `O/cross-platform-replay.json`: representation mediation, repeatability and platform limits.
- `O/final-verification.json`, `O/prior-tracked-sha256.json`, `O/provenance.json`: independent audit and preservation evidence.
- `O/figures/`: exportable PNG/PDF scientific figures; discovery and confirmation markers are distinct.

The original branch row321 is235–238; the existing tied network has 824 branches, with finite ratings only on its final two ties. Demand-location groups are 609,531,154,173,179 and 2,1,77,118,37; their unchanged historical selection and weights are in `results/comparisons/GSFM-015/20261023-load-location-charging/local-selection.json`. This experiment does not change network topology, branch parameters, generator limits, costs or ratings.
