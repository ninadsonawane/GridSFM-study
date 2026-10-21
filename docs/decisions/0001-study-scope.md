# Decision 0001: a gated matched-adaptation study

Date: 2026-10-21 (Asia/Kolkata). Status: proposed research plan, awaiting scientific discussion; initial package authorized.

Later 21 October amendment: primary recommendation superseded by [decision 0002](0002-physics-loss-study.md) after VM experiments and new literature review. The original proposal below is preserved, not an active instruction to launch its training matrix.

Primary question: **For a fixed constructed interconnection of two case300 systems, can FFN LoRA match full fine-tuning in AC-OPF accuracy and independently checked physical feasibility with 100 or 500 target scenarios, including held-out load stress and a single-tie outage?** Frozen predictions are the baseline. This is a restricted empirical comparison, not a new foundation model or proof of unseen-grid generalization.

Why: existing 6470-bus work supplies adapter code, but its cross-study full-FT comparison and missing matched physical evaluation leave a specific evidence gap. A 600-bus construction alone is not a contribution. One interconnection, two data budgets, one fixed rank and three training seeds fit a small paper better than a broad method sweep.

Gate: by 25 October require preserved original OPF semantics, one-scenario numerical round trip, parallel-edge tests, a functioning one-batch backward pass and a full-FT GPU memory pilot. If any fails, cut adaptation and propose a frozen-model robustness/representation audit with the professor; do not claim the fallback is automatically publishable. If inference/conversion also fails, deliver the negative integration report and do not force a conference submission.

Rejected for the minimum: warm-start acceleration (already close prior art and requires solver integration); head-only/last-K/rank sweeps (dilutes the question); cost asymmetry together with loading asymmetry (confounds stress); both tie outages (islands); unrelated frequency/converter/dynamics studies. Optional extensions remain in the experiment plan.

Provisional construction: two same-voltage terminals, two identical physical AC branch rows between the same pair. Keep one angle reference in the connected island and preserve voltage control at the former second reference. Synthetic tie parameters/rating require professor/postdoc review and a training-only pilot. Freeze them before validation/test generation.

Changes must be dated below, never silently erase the original decision. No experimental support exists yet for the hypotheses.
