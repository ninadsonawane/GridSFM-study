# Experiment11D — saved-state diagnosis only

Completed22October2026. [Full report and tables](../../results/diagnosis/GSFM-011D/20261022-saved-states/README.md). No new inference, scenarios, training, PF or OPF calls. Do not continue automatically.

Use existing read-only11B Python3.11 environment (NumPy/SciPy/PYPOWER); no installation:

```sh
PY=/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python
"$PY" -B experiments/gsfm011d/diagnose.py
"$PY" -B experiments/gsfm011d/report.py
/Users/ninadsonawane/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B experiments/gsfm011d/plot.py
"$PY" -B experiments/gsfm011d/verify_saved.py
```

All commands are postprocessing only. Existing checkpoints are SHA256-read for identity; no neural model is imported or instantiated. The plotting command uses the existing temporary Python3.12 matplotlib dependencies at `/private/tmp/gsfm007-20261021T195824Z/plotdeps`. No environment is modified. Explicit local paths are in each script; saved raw inputs/native states are required at their original11B/11C-1 paths. They are hashed rather than duplicated. Microsoft exact source snapshot and the newer source checkout are read for audit identity, not executed. On another machine these pinned saved resources must be restored with their exact hashes before reproduction.

`diagnose.py` first verifies all source inventories, units/mappings/defaults, native and reference residuals, exact branch flows and Ybus including taps/shunts. It aborts interpretation on disagreement. It then builds signed term budgets, deterministic lower-error matches, concentration,96 oracle combinations and fixed-bus/branch loading trajectories. `report.py` generates human-readable tables, explanations and limitations. `plot.py` creates four figures and matching PDFs. `verify_saved.py` independently checks table coverage, signed identities, concentration, fixed IDs,110% reference exclusion and unchanged prior artifacts.

The eight masks are GVA (G=Pg and Qg together),1 reference/0 native. These are known-answer diagnostics, not practical repairs. Effects can worsen and interact. No oracle/reference-error state at1.10 is permitted; the prior failed AC iterate is not used. Thermal assessment remains N/A because original RATE_A=0. Seventeen of18 low-error matches are poor under the declared rule; they support descriptions, not controlled matched-bus causal claims. A relatively small residual can hide cancellation and does not imply a correct state.

The results include all600 base bus/release rows,69 generator rows per release, incident branch details keyed by original row and endpoint, all fixed load trajectories, comparator profiles, concentration and all8×6×2 oracle metrics. Large prior matrices/checkpoints/native outputs remain in their existing local artifact paths; no private full-document export is committed. `artifact-inventory.json`, provenance and the document verification record identify the delivered package. The study execution commit and exact script hashes are recorded; the final local delivery commit is reported in chat.
