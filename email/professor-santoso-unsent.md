# UNSENT draft to Professor Surya Santoso

Subject: Proposed GridSFM study and five-page PES GM outline

Dear Professor Santoso,

Following your suggestion, I have prepared a source-backed plan starting with MATPOWER case300 and a constructed system of two copies connected by two parallel AC circuits.

My proposed focus is a matched comparison of frozen GridSFM, FFN-LoRA and full fine-tuning under changes in area loading and inter-area transfer. I would use 100 and 500 target scenarios, with a held-out single-circuit outage, and check power balance and equipment limits independently of the model. This would extend the earlier 6470-bus adapter work with a matched baseline.

Two details need care: official case300 has no finite branch thermal ratings, so the tie ratings would be explicit study assumptions; and the newer GridSFM paper's workflow differs from Microsoft's released v1.1 path. The first milestone is therefore solver validation and a one-scenario conversion check. No case300/600 experiments have been completed yet.

The five-page outline is: motivation; network construction and assumptions; matched adaptation/evaluation; results; limitations and references. If custom fine-tuning is not working by 25 October, I propose narrowing to frozen-model robustness.

Could you and your postdoc advise on three points?

1. Did you intend both circuits to connect the same terminal pair, and is an illustrative 345-kV interconnection with separately disclosed tie ratings suitable?
2. Is the matched adaptation question the right focus, or would you prefer a frozen-model robustness study for this deadline?
3. Could we arrange a short technical review by 23 October and reserve review of a full draft around 3 November? I would also appreciate guidance on available GPU/solver access.

The current portal gives 10 November 2026 at 11:59 p.m. Eastern Time, with references included in the five-page limit. I am targeting 8 November for a submission-ready version.

The research package is at https://github.com/ninadsonawane/GridSFM-study.

Best regards,
Ninad Sonawane

---
Draft only. Not sent. Review dates are requests, not agreed appointments. Edit spacing and personal voice before sending if desired; do not change experimental status to completed.
