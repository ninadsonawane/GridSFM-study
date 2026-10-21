# Decision 0002: investigate numerical physics mismatch before adaptation claims

Date: 21 October 2026 (Asia/Kolkata). Status: **recommended research protocol; short diagnostic next task prepared, main training not launched or authorized by this document**.

This supersedes decision 0001's primary emphasis on a two-copy LoRA/full-FT comparison. Preserve that original proposal as history. The professor's standard-case300 request remains the anchor. The later frozen-first baseline has now been completed on the separate VM, according to its report in Exchange.

## Evidence that changed the decision

The [VM report](../context/2026-10-21-exchange-results.txt) reports infeasible raw predictions on case300, case300x2 and the shipped case500 control; no unresolved conversion/evaluation error; and no solver-initialization benefit at four successful case300 load levels. The fifth level (1.10) failed locally for both starts and is not a certified infeasible case. Raw numerical artifacts remain on the other machine and have not been independently reproduced here.

The report also isolates a concrete discrepancy in the released adaptation loss: its denominator floor changes three case300 branch admittances and gives an otherwise accepted reference approximately 244 MW of false maximum imbalance. The exact cause of poor frozen predictions remains unresolved. In particular, inspecting a *fine-tuning* loss does not establish which loss generated the pretrained checkpoint.

## Recommended question

**Does a numerically altered AC power-balance loss hinder adaptation of the released GridSFM checkpoint to case300, and does preserving the original branch physics improve held-out predictions at the same label and update budget?**

Primary comparison: frozen checkpoint; supervised/cost adaptation with KCL disabled; matched adaptation with the stock clamped KCL operator; matched adaptation with an exact original-parameter KCL operator. Use the same training method first (full FT), data, checkpoint, loss aggregation and optimizer budget. Disable feasibility/stress auxiliaries identically, because unlimited branch ratings contaminate their semantics. Do not change context features, model forward physics, ratings or network parameters in the main ablation.

LoRA is optional after the mechanism survives the pilot. The contribution is a controlled implementation/physics consistency study, not a new AC equation, new LoRA algorithm, first physics-informed OPF, or first demonstration of physical violations. The newest nearby work already covers those broad ideas.

## Gate and scope cuts

The immediate task measures actual loss contributions and gradients, validates exact versus clamped physics and runs a bounded training smoke check. At most 20 updates and 120 seconds per arm; it is not the main experiment. A successful smoke check establishes executability, not adaptation quality. Main training requires a measured runtime estimate and subsequent authorization.

By 27 October, the validation pilot must show a reproducible, practically useful difference or a sufficiently broad, well-supported negative mechanism result. If only a one-line implementation defect remains without meaningful learning consequences, do not promise a conference paper. Retain a technical report and seek coauthor judgment. Do not replace a failed hypothesis with post-hoc test-set tuning.

The minimum does not expand to five connected networks, an IEEE39 training sweep, arbitrary tie outages, a new feasibility-repair method, or another warm-start benchmark. IEEE39 is a cheap **operator negative control**, case300x2 a correlated replication, and the shipped samples a source-operator audit. None is automatically an independent unseen-grid test.

See the [revised research plan](../research/2026-10-21-publication-plan.md) and [VM next task](../experiments/GSFM-003.md).
