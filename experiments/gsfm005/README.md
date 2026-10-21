# GSFM-005 controlled follow-up

The pinned protocol is docs/experiments/GSFM-005.md (c547542).
Use the existing GridSFM Python/Julia environments, CPU FP32 backbone with original-parameter FP64 physics, Torch4/BLAS1. No installed model code is changed.

Default run: 20261021T120300Z-m5-seeds11-22-33. Actual start is 2026-10-21T12:01:19Z; the ID is only a label. Compute cutoff 16:41:19Z; total cutoff 17:01:19Z. Never reset the clock. Separate replays require an explicitly authorized NEW GSFM005_RUN_ID / GSFM005_START_UTC and RUNNING directory.

Sequential entry points: calibrate.py, train.py, lock.py, fresh_data.py, evaluate.py, report.py, verify.py. train.py refuses an existing training directory. Its explicit --continue-preserved option only reuses already COMPLETE summaries, then runs missing planned arms; it never repeats completed optimizer updates. recover_summary.py repairs only the recorded seed11/S post-fit dictionary-key serialization error, verifies its final saved predictions, preserves the original failure, and performs no optimizer step.

recipe.json fixes all coefficients, streams and thresholds before fresh evaluation. Calibration uses only the first20 training cases. Rho is frozen outside log1p. Twelve fits maximum, seed blocks11/22/33 and the protocol's arm ordering, same within-seed scenario order, original 50/10 examples. Frozen/nearest/ridge predictors and scalers are reused without tuning. lock.py hashes source/config/selections/weights before fresh references are generated.

Large original matrices, solver results, prediction states and model/optimizer/RNG snapshots are local-only under results/pilots/GSFM-005/<run-id>; compact summaries, figures, source and SHA256/byte inventory are tracked. Rebuild prerequisites through the prior GSFM-004 runner and pinned original MATPOWER/checkpoint sources; do not assume large files exist on GitHub.
