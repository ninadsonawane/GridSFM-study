# Bounded Windows cache-path correction

Recorded 26 October 2026 before retry outcomes. The first17 scheduled diagnostic neural forwards succeeded; repeat and label-poison controls matched exactly. Both final independent-process invocations failed in preprocessing at `torch.save` of the cycle cache under a long Windows filename. Their tracebacks and attempted records remain unchanged. Neither reached the neural model call or produced a native return.

Change only the cache directory: hash the requested directory into a unique short path beneath the workspace's `work/runtime/cache`. Pinned upstream source, weights, tensors, seed, clipping and model math remain unchanged. Retry those two independent cold-process checks into new `cold-retry` directories; never overwrite the failures. This makes21 invocation attempts, including two preprocessing failures, and at most19 executed diagnostic neural forwards, within the20-forward cap. New electrical inputs remain zero. No further diagnostic forwards are planned.

Compare every raw returned value against its release's first original-order baseline. Preserve the original failed summaries and place the final correctness decision in a separate gate file. A repeatability discrepancy stops dependent electrical work.
