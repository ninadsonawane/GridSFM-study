# Decision 0003: broaden the next hardware experiment

Date: 21 October 2026. Status: proposed experiments authorized as a bounded To-do by the user's request; not executed by the planner.

**Later same-day budget amendment:** Ninad requested4-5hours. The controlling GSFM-004 revision2 uses a five-hour cap including all work, six fits with seed11 only, <=200updates/25minutes per fit, and90development examples (50train,10validation,10ordinary,10spatial,10higher-load). Defer second seed, breadth audit and MPS probe. Compute stops by4h40m, reserving20minutes for reporting. If already running, retain work and count elapsed time from the original start. The original eight-hour design below remains historical; it is no longer authorized as the current run budget.

The user asked for multiple hardware experiments that can determine which research hypothesis is worth pursuing, using the M5 Pro with64GB. A fresh read of Exchange still showed only frozen inference/diagnosis/initialization results. GSFM-003 remained READY, without posted adaptation results.

[GSFM-004](../experiments/GSFM-004.md) now controls the next run. It retains the correctness gate from003 but expands to a fixed-recipe, at-most-eight-hour discovery pilot: six neural arms, at most two seeds, common updates <=400, at most30minutes per fit, and simple nearest-example/ridge baselines. One50-label training set,20validation examples and ordinary/spatial/higher-load development slices support all comparisons. Everything remains development data. No final paper-test set or automatic main-study run is authorized by this To-do.

The six arms are full no-KCL/stock-KCL/exact-KCL, heads only, rank2 FFN-LoRA plus heads, and a random-initialized same-architecture model. Restricted and random arms use the same no-KCL objective as full S. The repeated seed is balanced across arms instead of chosen after seeing a winner. Actual timing controls how many complete fits can run.

The broader scientific question is when small-data adaptation is useful and robust. The clamp is a causal subexperiment, not a predetermined paper conclusion. Spatial demand perturbations preserve total P/Q and local P/Q ratios using a documented null-space projection. An optional case39/118/500 operator audit adds limited breadth without new training. No further network stitching, rank sweep, outage sweep or warm-start speedup study is requested.

Use the working CPU FP32 model plus CPU original-precision float64 physics for controlled comparisons. MPS is optional and cannot change the primary precision treatment. The one common learning rate, two seeds and short scratch runs support screening only. Stronger findings require a later focused protocol and untouched evaluation.

This amends the next-step priority in [decision0002](0002-physics-loss-study.md), not its established evidence or novelty cautions. Preserve all previous results. The publication plan remains background until the pilot chooses the central claim.
