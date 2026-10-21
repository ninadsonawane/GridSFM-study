# Decision 0004 — Controlled KCL follow-up after GSFM-004

Date: 21 October 2026. Status: planned hardware work, explicitly requested by the user; no new experiment run by the planner.

GSFM-004 completed all six 200-update fits and found lower selected balance errors with exact KCL, but no strict feasible predictions and much stronger ridge baselines. Exact/stock gradients were nearly aligned at one smoke state, with different magnitudes. Fixed-step and state-error trade-offs prevent a uniform-benefit claim.

Run [GSFM-005, Experiments 5–8](../experiments/GSFM-005.md): a training-only, fixed initial gradient-magnitude control; four full-tuning arms across seeds 11/22/33 for up to 1,000 updates; fresh evaluation after freezing the recipe; and an honest paper decision. Five hours inclusive, 12 fits maximum. Keep the old training/validation data and mandatory ridge/nearest/frozen controls. Defer LoRA, scratch, connected grids, extra topologies, MPS and broad sweeps.

Use C_m (stock KCL multiplied by a training-only norm ratio) instead of a large validation-weight search. This targets the observed confound at lower compute cost and avoids extra hyperparameter selection on ten validation points. It only matches initial KCL gradient magnitudes approximately; changes during optimization remain measured limitations.

A positive result is not required to evaluate the frozen recipe or to report the run. Repeatable differences could support a narrowly scoped numerical-loss study; they do not establish a new OPF method, practical feasibility, generalization to unseen grids, firstness or conference acceptance. Original case300's absent finite thermal ratings remain explicit.
