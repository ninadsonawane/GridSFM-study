# Static review of the bounded mediation diagnostic

26 October 2026. Source inspected directly from the exact pinned local Git blobs. This review ran no model forwards. Syntax parsing passed; runtime correctness still requires the recorded repeatability/mapping gates.

## Intervention correspondence

1. **Cycle graph:** upstream `cycle_basis.py:attach_cycle_basis_` attaches `cycle.x` and both directions of the AC-branch and transformer cycle relations. The worker replaces the complete cycle node store and every relation touching `cycle`. It maps each baseline branch-family index through the converter's source branch row, then the permutation map, then the target branch-family index. It leaves branch electrical features and endpoint relations native. This restores the baseline cycle representation on the same physical branches; it neither repairs the shared sign defect nor constructs a new electrical topology. Replacing only cycle feature rows would have been insufficient.

2. **v1.1 landmark moments:** pinned `pe_features.py:attach_pe_features_` concatenates five resistance moments and three DC columns after the four original bus columns, then appends four bus-type columns. Thus prepared `bus.x[:,4:9]` is exactly the landmark-moment block and total width is 16. The worker copies these five columns using variant-bus-to-original-bus mapping. It preserves DC columns, original bus features, one-hot types, graph context and all cycle relations.

3. **v1.1 transformer DC features:** the same upstream function appends four DC columns to the 11 original transformer columns in promoted `branch_tr.x`; width is 15. The worker replaces only the last four columns, mapped by physical transformer source rows. These are the baseline shipped values, which retain the known offset defect. This is an isolated mediation intervention, not the output of corrected preprocessing. It intentionally leaves original transformer `edge_attr` and all physical network coefficients unchanged.

4. **Combined branch intervention:** replacing both the cycle graph and transformer DC block permits an interaction check. Its effect must not be reported as the sum of the two individual effects. None of these altered-feature predictions can replace a shipped-default native prediction.

## Capture and execution checks

- Both pinned `__init__.py:predict` functions read module-global `prepare_for_inference`, so the temporary wrapper intercepts exactly the intended preparation path. The worker asserts exactly one invocation. Default calls return the same prepared object without changing it.
- Pinned `HodgePE.forward` returns a dictionary of tensors; the observing hook clones it without returning a replacement. Projection pre-hooks similarly capture inputs without altering them. All hooks and wrapper functions are restored after each call, including exceptions.
- The first baseline starts with a new process and unique cache directory; its warm repeat shares the same model/caches. A poison-label control uses the same electrical graph. Both controls require exact equality of all returned values, not just voltage/dispatch summaries.
- Before any outcomes, the diagnostic schedule added a final independent-process baseline with its own new cache directory for each release. This separates within-process cache repeatability from a fresh import/model/feature path. It also requires exact equality of all returned values. The fixed schedule totals 19 forwards: 11 v1.1 and eight v2; there is no automatic twentieth retry.
- Returned tensors and the complete returned JSON dictionary are saved before state conversion or physical evaluation. Prepared default/used tensors, Hodge outputs, projection inputs, exact clamp inputs/outputs, source/checkpoint hashes and mapping metadata remain available separately.
- Existing `input.json` bytes are preserved after parsed equality checking. New JSON uses explicit LF newlines. Each imported source Python file is compared byte-for-byte with its pinned Git object before model import. Strict checkpoint state loading and the whole-file SHA-256 gate both apply.

## Interpretation limits and remaining gates

Copying baseline cycles across row permutations can leave floating-point reduction-order effects. Full feature mediation therefore need not give bit-identical reordered predictions. Native output deltas should be compared with same-input repeat variation and reported numerically. Raw angle deltas in the diagnostic summary are not gauge-aligned accuracy errors; the physical evaluator performs reference-angle alignment separately.

The diagnostic measures sensitivity of these released pipelines. It does not show that any altered-feature point is more physically correct, that a source fix is safe for the released checkpoint, or that learned electrical mechanisms are representation independent. Fixed-original-order electrical comparisons may proceed only after faithful mappings and independent physical scoring are established. No additional substantive source-indexing error was found in the three implemented substitutions during this review.
