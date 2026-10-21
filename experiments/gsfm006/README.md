# Experiment 9 — newer pipeline pilot

Exact executed drivers are preserved here. See the run README, freeze.json, provenance.json and delivery.json for source/config/hardware/artifact identity and commands.

The upstream source is MIT, preserved alongside these study adapters as UPSTREAM_LICENSE. Source was not patched. We added actual availability columns to the existing active-only converter, used native prepare/forward/closure/loss APIs, checked finite values before zero sanitizers and exported recovered generator injections. The release references an unavailable completion/export module; this explicit exporter is study code. All multiple-generator-bus allocation is range-affine without clipping; original case300 has one generator per generator bus.

Setup used a separate public checkout at517a07531ea55a11bd81a89a6c6879695a2ba4b4 and only the documented base/gridsfm_open_v2.pt (SHA2569e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7). An isolated Python3.11 venv reads the old environment's installed dependencies through a .pth file; no packages or old source/results were changed. XDG_CACHE_HOME points at the isolated run.

Executed sequence: gate.py → run.py → extra_audit.py → solver_timing.py → semantic_audit.py → timing_e2e.py → report.py → verify.py. All model work uses Torch4/BLAS1 on CPU. The bounded run.py has200updates/30fit-minutes/45adaptation-minutes and an original four-hour task deadline. It preserves the published400epoch LR horizon and25epoch closure-tolerance schedule, not a compressed4epoch schedule. report/verify do not update weights.

For replay, first make a NEW working/output directory and set ROOT/SRC/WORK/START in a copied common.py; preserve completed runs. Download the immutable checkpoint, create the isolated environment and check its actual packages. Run the commands under the new environment with PYTHONDONTWRITEBYTECODE=1. Exact paths used for this run are listed in the report. Changes to source/config require new hashes and a new freeze before evaluating. This is a previously viewed development comparison; no fresh-test or complete-paper reproduction claim.
