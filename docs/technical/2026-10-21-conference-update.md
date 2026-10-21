# PESGM 2027 fit and focused study plan

Verified 21 October 2026 (user timezone: Asia/Kolkata). Read-only public research; no account accessed, submission created, or Google Doc edited by this subtask.

## Official requirements

The [current official call](https://pes-gm.org/2027-san-francisco/2027-call-for-papers/) confirms the 2027 IEEE PES General Meeting, 25–29 July 2027 in San Francisco, and a full-paper deadline of 10 November 2026. Its theme is “Grid Modernization: Scaling the Grid for Emerging Demand.” The call accepts all power and energy topics, with emphasis on large loads, monitoring, cost/security, and flexibility. This work can fit the general scope without adding a superficial data-center application. The call requires presentation for publication and at least one paid author registration for an accepted paper; these are later commitments, not actions taken here.

The [public MIRA portal](https://submissions.mirasmart.com/PESGM2027/login.aspx) was re-read in the browser today. It explicitly displays a deadline of **10 November 2026, 11:59 pm Eastern time**. Eastern is EST (UTC−5) on that date, so this is **11 November 2026, 10:29 am IST**. The portal says “EXTENDED TO” but names exactly the date in the current CFP; no later extension is established. Today to 10 November is 20 calendar days. Use **8 November, 18:00 IST** as the internal ready-to-submit target rather than depending on the final hours.

[PES Author’s Kit, Part 3](https://ieee-pes.org/publications/authors-kit/preparation-and-submission-of-conference-technical-papers/) limits the paper to **five pages including references, figures, tables, and attributions**. Names and affiliations appear in the paper; the PDF must embed its fonts and have no password/security restrictions. [Part 4b](https://ieee-pes.org/publications/authors-kit/preparation-of-a-formatted-conference-paper/) limits the abstract to 150 words and index terms to five; keep the conference template’s formatting. These verified requirements support one narrow experimental question rather than a broad survey plus multiple unrelated methods.

## Evidence that the topic fits

The [official 2026 PESGM print program](https://pes-gm.org/wp-content/uploads/2026/07/2026-IEEE-PES-GM-Print-Program.pdf), PDF page 26 (printed page 25), lists an AMPS Computer Analytical Methods task-force meeting on foundation models for situational awareness, computation, and analysis. The program also includes Intelligent Systems, Big Data Analytics, and computer analytical-method sessions. These demonstrate an existing audience; they are not acceptance criteria or promises. A methodological AC-OPF surrogate/adaptation paper naturally aligns with **Analytic Methods for Power Systems (AMPS)** and AI-based analytical computation. The exact 2027 submission topic choices must be checked when preparing submission, not invented from the 2026 program.

Two particularly close examples:

1. **Han Yue, Wentao Zhang, Yuzhang Lin, Hongfu Liu, “Data-Centric Physics-Informed Graph Neural Networks for Ultra-Fast Power Flow Analysis,” PESGM 2025**, DOI [10.1109/PESGM52009.2025.11225353](https://doi.org/10.1109/PESGM52009.2025.11225353). The [IEEE abstract](https://ieeexplore.ieee.org/abstract/document/11225353/) was returned by web search; direct fetch was blocked. It describes influence-function-guided data generation for a physics-informed PF GNN and evaluation on IEEE 300 buses. The [official poster program](https://pes-gm.org/wp-content/uploads/2025/07/Poster-Session-Handout-final-7-14-25b.pdf) independently lists the paper under AMPS Big Data Analytics. Its full text was not inspected. Consequence: case300, physics-informed learning, and reducing data cost are already present at this conference. A new paper must distinguish AC-OPF foundation-model adaptation and its particular numerical/physics mechanism.

2. **Shimiao Li, Aaron Tuor, Draguna Vrabie, Larry Pileggi, Jan Drgona, “Homotopy-Guided Self-Supervised Learning of Parametric Solutions for AC Optimal Power Flow,” arXiv:2511.11677v1.** The [author preprint](https://arxiv.org/html/2511.11677v1) was inspected. It develops curriculum-like deformation of objectives, bounds, loads, and admittances for self-supervised AC-OPF learning; its reported AC-OPF experiment is case30 with 100 test instances and compares feasibility residuals against a plain penalty baseline. The [arXiv metadata](https://arxiv.org/abs/2511.11677) identifies a submission to PESGM 2026. An ACM SIGEnergy bibliography lists a later PESGM 2026 DOI, 10.1109/PESGM58988.2026.11693405, but IEEE publication metadata could not be independently fetched here, so do not claim the venue status from this subtask alone. Consequence: physics penalty training and gradual constraint tightening are not new by themselves.

Also flagged to the main literature review: [Memon et al., “Towards Systematic Generalization for Power Grid Optimization Problems,” arXiv:2605.02026](https://arxiv.org/abs/2605.02026), a shared graph backbone for AC-OPF and SCUC with physics-informed objectives and cross-case transfer. The [authors’ project](https://argonne-gridfm.github.io/) identifies KDD 2026 AI for Science. Only the abstract/project overview was inspected in this subtask; parent literature work should assess any closer overlap.

## Recommended publication positioning (conditional on results)

**One question:** Does correcting a demonstrably mismatched physical residual improve adaptation of the existing GridSFM checkpoint on networks whose branch parameters trigger that mismatch?

Possible working title: **“Physics-Consistent Adaptation of a Pretrained AC-OPF Surrogate on Impedance-Sensitive Networks.”** Do not label the title or method “novel” until the main literature comparison and controlled results support it. Exact AC equations and fine-tuning are established; the possible contribution is a reproducible causal failure analysis, a specific correction, and evidence of practical benefit under controlled adaptation. “GridSFM fails OOD,” “we used case300,” “we connected two case300s,” or “LoRA works” alone is too weak.

The central ablation should hold checkpoint, adapter type/capacity, data, initialization, seeds, optimizer budget and validation selection fixed while varying only the physical residual implementation. Use independent original-network physics for final evaluation. A frozen baseline plus same-data standard-loss adaptation and corrected-loss adaptation is the minimum meaningful comparison. Full fine-tuning and LoRA can be added as a secondary parameter-efficiency axis if compute permits, but should not obscure the causal comparison.

Separate raw predictions from solver-repaired predictions. Never interpret a lower infeasible predicted generation cost as achieved economic dispatch. Include failures and strict feasibility thresholds, original unmodified case300, and a control network/parameter regime where the suspected issue is absent. Additional replicated networks should test a hypothesis, not merely raise bus count.

## Five-page allocation (recommendation)

| Content | Pages |
|---|---:|
| Title, abstract, introduction, precise gap and nearest related work | 0.85 |
| AC-OPF formulation, observed mechanism and proposed correction | 1.00 |
| Data, controls, split/seed protocol, methods and metrics | 0.75 |
| Main comparison, causal ablation, stress/generalization result | 1.55 |
| Limitations and conclusion | 0.25 |
| References | 0.60 |
| Total | 5.00 |

Aim for two compact figures (mechanism/ablation; feasibility/error or sample-efficiency curve) and one main table. Prefer one well-supported mechanism over many lightly tested variants. Reviewers should be able to see what was changed, which factor caused the improvement, and what remains infeasible.

## 20-day schedule and decision gates (recommendation)

| Dates, IST | Deliverable / gate |
|---|---|
| 21–22 October | Reconcile latest VM results with saved raw arrays; independently reproduce solver-label residuals; lock version/checkpoint and exact suspected mechanism. Do not begin an expensive method sweep before this passes. |
| 23–24 October | Implement and numerically validate residual correction; generate a small deterministic pilot split; compare unmodified versus corrected physics on identical states. |
| 25–27 October | Run the tightly matched adaptation pilot. By 27 October decide whether the effect survives independent evaluation and more than one seed. If not, revise or stop the novelty claim rather than expanding networks. |
| 28 October–2 November | Complete the prespecified main split, multiple seeds, supported-network control and one relevant stress/transfer test. Training budget measured on actual VM hardware, not assumed. |
| 3–5 November | Freeze results, compute uncertainty/failure counts, generate figures and write the five-page draft. |
| 6–7 November | Professor/coauthor scientific review; check closest work and whether claims exceed evidence; repair only material gaps. |
| 8 November | Final scientific/format/reproducibility audit, ready-to-submit by 18:00 IST. |
| 9–10 November | Submission buffer; final official cutoff is 11 November 10:29 IST. Submission itself remains the author’s decision. |

If the pilot only reproduces known OOD failure or gives no reliable correction effect, it does not yet justify promising a publication. A transparent negative/mechanistic result may still be useful, but needs breadth and causal evidence; deadline pressure is not evidence of novelty.
