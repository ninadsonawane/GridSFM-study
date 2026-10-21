# GSFM-004 budget reduction

User request: reduce the experiment to roughly4-5hours. A fresh Exchange read still showed READY and unchanged frozen Results (34,150characters); no running worker or new training result was shown.

Revision2 sets a five-hour total ceiling with compute stopped at4h40m, six single-seed fits capped at200updates/25minutes, and90development examples. Original50training examples are retained; validation and each evaluation slice shrink to10. Extra seed, cross-case audits and MPS probe are deferred. Shortened fits retain the six hypothesis comparisons; single-seed findings cannot establish stability. The clock does not restart if a hardware worker has already begun.

Updated the canonical protocol and current README/HANDOFF/decision notices. Unchanged physical equations, source pinning, label validity and scoring rules are retained. This is a documentation/protocol change; no model training or solver was run here. Prior verification of the spatial arithmetic remains applicable because only the sample count and compute budget changed.
