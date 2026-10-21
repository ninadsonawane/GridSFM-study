# A publication decision after the frozen-model experiments

Prepared 21 October 2026, Asia/Kolkata. **Recommendation, not a completed adaptation study or acceptance prediction.** Read the [latest VM report](../context/2026-10-21-exchange-results.txt), then [decision 0002](../decisions/0002-physics-loss-study.md). The original report and decision remain historical records.

## Recommendation in plain language

Make **original MATPOWER case300** the primary benchmark. Investigate whether the model is being fine-tuned against equations that differ from that benchmark, and whether correcting those equations improves predictions on new operating conditions with the same amount of data and training. This is a more defensible candidate than another demonstration of OOD failure, simply connecting networks, or adding LoRA.

The proposed question is: **Does numerical clipping in the released GridSFM power-balance loss impede target-grid adaptation, and can an original-parameter loss improve its accuracy–physical-consistency trade-off at a fixed label budget?**

Five decisions matter: use the pinned v1.1 release; retain unmodified case300; vary only the KCL operator in matched adaptation; score with independent original-network physics; decide whether to proceed by 27 October. FFN-LoRA and the 600-bus construction become secondary extensions. No main training was run in this research turn.

Working title: **“Numerical Physics Mismatch in GridSFM Adaptation: A Controlled IEEE 300-Bus Study.”** If results do not demonstrate adaptation effects, remove the adaptation-benefit claim rather than implying a successful method.

## What the latest results actually establish

The separate VM reports the following. The Windows research session read and archived its document, and checked relevant source code, but did **not** independently run its solver or inspect its complete raw arrays.

| Reported evidence | Consequence |
|---|---|
| case300 cost error54.97%, max P/Q imbalance3,754/8,938 MW/MVAr; case300x2 error17.23%, max P/Q1,142/9,376 | Neither raw dispatch is physically usable. Lower infeasible cost is not an operating saving. |
| Shipped case500 control cost error0.538%, yet P/Q imbalance114/72 MW/MVAr and18.6 MVA rated-line violation | “The control works” must be qualified: checkpoint execution and low cost error do not certify physical feasibility. |
| Original-parameter references, export/reload, maps and input/label separation pass | Repeating the whole conversion investigation is unnecessary unless new training-path evidence fails. |
| Loss denominator floor changes three original branches; a valid reference obtains about244 MW false maximum imbalance | A concrete *fine-tuning-operator* inconsistency is already identified; its influence on learning is still unmeasured. |
| Forward epsilon causes comparatively tiny flow differences; context clipping is separate | Do not conflate loss, forward and feature pathways or change all three at once. |
| Unlimited ratings interpreted as tiny ratings in stress features | The classifier cannot be interpreted normally here. During adaptation its auxiliary gradients must be disabled or separately corrected. |
| Default versus model starts: at0.90–1.05 load all reach matching local solutions, but model starts are slower; both fail locally at1.10 | Stop pursuing the current warm-start speedup claim. Failed local solves do not certify physical infeasibility. |

Hardware is now **reported**, not guessed: Apple M5 Pro,18 CPU cores,64 GB RAM; CPU FP32 inference, four torch threads; Python3.11.17,torch2.8.0,PyG2.8.0.post1; Julia1.11.9/PowerModels0.21.5/Ipopt.jl1.14.0. Full training/backward throughput and Apple MPS compatibility are unmeasured. Use the functioning CPU environment for smoke checks; do not make accelerator installation a prerequisite.

Raw result/script bundles remain on `/Users/ninadsonawane/workspace/research-dev/GridSFM-study`. The GitHub main branch was still `c74c2bd1685108f7c991274ef7a09d4c52e8f2fb` when checked this turn. The archived document is a report, not a substitute for syncing reproducible numerical artifacts.

## Conference requirements and fit

The [official 2027 CFP](https://pes-gm.org/2027-san-francisco/2027-call-for-papers/) lists San Francisco,25–29 July2027 and **10 November2026** full-paper deadline. The public [MIRA portal](https://submissions.mirasmart.com/PESGM2027/login.aspx) was rechecked without login: **23:59 Eastern on10 November =10:29 IST on11 November**. No later extension is assumed. The [PES Author’s Kit](https://ieee-pes.org/publications/authors-kit/preparation-and-submission-of-conference-technical-papers/) counts references, figures and tables within **five pages**. Use the official conference template, ≤150-word abstract and ≤5 index terms. Internal ready date:8 November18:00 IST.

This fits power-system analytical methods and reliable AI-assisted AC-OPF. The CFP accepts general power/energy research; no invented data-center application is needed. The [official2026 program](https://pes-gm.org/wp-content/uploads/2026/07/2026-IEEE-PES-GM-Print-Program.pdf), PDFp26, includes a foundation-model task force under analytical methods. A [PESGM2025 paper by Yue et al.](https://doi.org/10.1109/PESGM52009.2025.11225353) already studies physics-informed PF learning on IEEE300. Its IEEE abstract/program were accessible; full text was not inspected. Case300 is therefore a reasonable venue fit, but its use alone is not new.

## Closest work: what would repeat existing research

The focused search covered GridSFM, OPF/PF foundation models, parameter-efficient adaptation, physical-loss consistency, restoration and numerical conditioning, including October2026 work. Primary full papers/code were read where stated in the linked detailed notes. This is a bounded literature search, not proof of firstness. Each row below is an author-reported finding, not our reproduction.

| Source / status | Closest established idea | What remains different in the proposed experiment |
|---|---|---|
| [Microsoft GridSFM whitepaper, May2026, §§7–9](https://www.microsoft.com/en-us/research/wp-content/uploads/2026/05/GridFM_white_paper.pdf), technical report | Zero-shot degradation, few-shot/full FT on6470, solver initialization | Same released checkpoint, but isolate a specific target-equation mismatch rather than repeat “FT helps.” |
| [Bhan et al., GridSFM v2,6Oct2026](https://arxiv.org/abs/2609.30173v2), preprint |100-example adaptation with changed control-output/backbone and Newton PF completion | Our release-specific loss study does not compare against or establish superiority to this later pipeline. |
| [Kim et al., Physics-Informed but Not Physics-Consistent,5Oct2026](https://arxiv.org/abs/2610.05959), preprint | Error geometry, GridSFM across31systems, calibrated subspace correction | Closest overlap. Their fixed-dispatch AC-PF setup and correction differ from pretrained AC-OPF adaptation. Large residuals despite small voltage errors are **already known**. |
| [Li et al., LUMINA](https://arxiv.org/abs/2603.04300), [author venue record](https://yli697.github.io/publications/), ICLR2026 FM4Science workshop | Pretraining/FT, constraint-aware objectives, concentrated errors at difficult nodes | Loss comparisons and locating bad buses are established; our intervention must be the particular operator inconsistency. |
| [LUMINA-Bench](https://arxiv.org/abs/2605.02133),2026preprint | Standardized constrained-learning comparisons including precision and conditioning | Match arithmetic and non-treatment settings; “we measured feasibility” is insufficient novelty. |
| [Lupo Pasini et al., HydraGNN OPF foundation models](https://arxiv.org/abs/2605.23194v2),Sep2026revision; v1methods and v2metadata/abstract inspected | Full/partial/head-only adaptation and IEEE118 tasks | Small-target adaptation and fewer trainable weights are not new alone. |
| [Karim et al., parameter-efficient PF adaptation](https://arxiv.org/abs/2602.18227v2),May2026preprint | Attention-LoRA/full/head comparisons on4–32-bus PF grids | FFN-LoRA for economic AC-OPF differs, but placement alone is a weak contribution. |
| [Park et al., UNION](https://arxiv.org/abs/2608.25784),Aug2026preprint | Sparse differentiable PF, remaining inequality treatment and restoration | Do not attempt a new projection/implicit-layer framework within20days. |
| [Arowolo and Cremer, GNN generalization](https://arxiv.org/abs/2510.06860), [author journal record](https://olayiwola-arowolo.com/publication/2026-gnn-generalization-ac-opf),Energy and AI2026 | Multi-grid transfer/FT and warning that PF recovery can violate OPF inequalities | Full constraint checks and paired FT are already necessary baseline practice. |
| [Seiole report](https://seiole.com/posts/taking-gridsfm-on-a-spin),technical blog | v1.1 distribution-shift failures and independent checks | Another basic zero-shot failure report would add little; article does not report completed FT. |
| [Guennoun/Rabasse/Wallaert author project,Dec2025](https://medium.com/@hippowal/accelerating-the-grid-enhanced-solving-of-optimal-power-flow-with-graph-neural-networks-4d8a6de2cc59),non-peer-reviewed | Omitted shunts make a physics loss penalize valid labels | Even the broad principle “wrong physics can hurt learning” has precedent. Claim only a measured, version-specific mechanism and useful adaptation evidence. |

The existing [literature table](../literature/evidence-and-novelty.md) additionally covers OPFData, PGLib, DeepOPF, Smart-PGSim, PowerGraph-LLM and LoRA. Retain these citations where they establish benchmark semantics or rule out a “first” claim. Detailed new readings are saved in [adaptation review](../literature/2026-10-21-adaptation-update.md), [physics assessment](../technical/2026-10-21-physics-assessment.md), and [conference update](../technical/2026-10-21-conference-update.md).

## The specific mechanism and limits of the claim

For series impedance z=r+jx, exact admittance is `(r-jx)/(r²+x²)`. The inspected [released loss](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/loss.py) instead uses `max(r²+x²,10^-6)`. It therefore retains the fraction `alpha=min(1,|z|²/10^-6)` of the correct series admittance. This changes the electrical equations; it is not merely rescaling the final residual.

The VM identifies alpha=0.2152,0.37,0.40 for37–9001,231–237,235–238. A learning objective can then demand both fitting the valid reference and satisfying a different network's balance equations. **Whether that conflict materially affects optimization is the hypothesis, not an established result.**

Two controls strengthen the mechanism beyond a one-line fix:

- **Unchanged physical system, different per-unit base.** At Snew=kSold, scale r/x by k and charging b by1/k, while physical loads/limits/costs and voltage bases stay fixed. Exact physical flows at the same state remain unchanged; the fixed clamp retains `alpha(k)=min(1,k²|z|²/epsilon)`. Measure25/100/400MVA operator results, without running new neural inference or changing the primary100MVA benchmark. This is an established invariance used as a diagnostic, not an invented theorem.
- **Negative and exposure controls.** Verify case39 has no floor-activating branches and require exact/stock operators to agree there. Audit all available shipped samples for affected branches and valid-reference residuals; without validated references report exposure only. These audits do not prove pretrained generalization or become additional training benchmarks.

Do not conflate this with frozen failure. The file is documented as the **fine-tuning** loss; the original pretraining implementation is not established. Also leave forward epsilon and graph-context clipping unchanged in the main experiment. The zero-rating stress issue affects a different pathway and is not the primary intervention.

## Tangible minimum experiment

The next bounded executable request is [GSFM-003](../experiments/GSFM-003.md): source/evidence sync, loss-term audit, original-precision operator checks, gradient influence and20-update smoke checks. **A smoke check is not evidence that adaptation generalizes.**

Only after a successful smoke check and a measured compute estimate, propose the following paper matrix:

| Arm | Starting weights | KCL treatment | Role |
|---|---|---|---|
| F | Released v1.1, frozen | No optimization | Reported failure baseline, evaluated on new test scenarios |
| S | Same v1.1, full FT | KCL weights zero | Shows what fitting labels/cost alone achieves; other shared auxiliary settings held constant |
| C | Same v1.1, full FT | Clamped KCL | Controlled reference adaptation |
| E | Same v1.1, full FT | Exact original-parameter KCL | Intervention; same normalization/weights/aggregation |

Case300 has RATE_A=0 everywhere. Upstream branch-flow/thermal losses also require positive ratings and `abs(x)>0.01`, so those terms have no active original branches. Report this fact rather than silently describing the objective as having full branch supervision. Disable feasibility BCE, stress-feasibility and synthetic negatives in **all** arms. Ensure disabled NaN-producing code cannot contaminate gradients via0×NaN. Do not alter shared helper behavior for unrelated terms while correcting KCL.

Use original float64 physics parameters in a separately aligned copy for C/E, while preserving FP32 backbone features. Make all buffers/scatters dtype-safe in both arms. Promoting already-rounded FP32 values does not restore source precision. Keep the same network parameters, context, checkpoint, output architecture, batch order, data losses, loss weights, clipping and optimizer budget. Report native-FP32 differences as a numerical diagnostic, not part of the treatment.

**Dataset proposal:**100 accepted training,30 validation and100 untouched test operating points. Training/validation and50 same-regime test points use global P/Q scale U[0.90,1.03] and shared per-load P/Q jitter U[0.98,1.02], preserving local power factor. The other50 test points use U[1.035,1.06] with the same jitter as a declared higher-load slice. Save actual arrays and attempt order; failed local solves are unknown, not negative labels. Cap candidates at3×requested count per split; report acceptance rates and insufficient coverage. These intervals are engineering proposals, not known feasible regions. Alter them only using the pilot, before final test generation; retain the original plan and amendment.

Use distinct deterministic split seeds3002026/3002027/3002028/3002029 and training seeds11/22/33. The diagnostic nominal cases and smoke examples are development data, not final test cases. Hash factor arrays, exclude duplicates, group any derived paired variants. This supports operating-point generalization on a single topology, not unseen-grid transfer. Existing uniform five-load results are insufficient as a training/test dataset.

**Training proposal:**three trainable arms×three seeds=9fits at one100-label budget. Start with batch1,AdamW lr1e-4,weight_decay1e-4,gradient-norm clipping1; at most20epochs/2,000updates per fit. These are proposed starting settings, to lock after smoke/validation-only pilot. Give each arm identical update budget and a recorded validation checkpoint rule; also report the fixed final-step result to expose selection sensitivity. No learning-rate/rank grid or second label budget is required. If measured total time plus validation is excessive, reduce the common update budget before final runs, not the number of adverse results reported.

Proposed common validation rule: minimize `mean_s log(1 + R_s)` where `R_s=max(max_i|Pmis_i|/(1 MW),max_i|Qmis_i|/(1 MVAr))`, using the independent evaluator; break ties with cost error, then earlier checkpoint. This dimensionless score prioritizes balance, not economic optimality; also show the separate P/Q errors, error–residual trade-offs and fixed-step endpoint. Lock it before training and retain costs/voltage/dispatch errors even when balance improves.

**Primary outcomes:**per-scenario maxima of absolute P and Q imbalance; paired median/p95/worst distributions; strict joint feasibility rate; V/angle/Pg/Qg errors; generator/voltage violations; raw cost error explicitly labeled infeasible when applicable. Keep the existing thresholds:1e-3MW/MVAr balance and generator bounds,1e-4pu voltage,1e-3MVA rated branches,1e-3degrees active angle bounds. A residual reduction is not a feasibility guarantee. In case300 the thermal criterion has no active original limits and cannot support an interior-congestion claim.

Report all three seed results and paired scenario effects; use scenario-level paired bootstrap intervals within each fixed test slice, conditional on the trained seed, alongside across-seed ranges. Do not pretend300×bus observations are independent trials or that bootstrap intervals establish generalization across network families. Record CPU time/update and process peak RSS. No efficiency advantage follows from parameter count alone.

## Decision gates and optional extensions

- **Technical gate,23–24October:** exact operator matches source-precision reference physics, controls pass, custom labeled dataset/batching/backward path works, gradients stay finite, and measured runtime fits the remaining schedule. Source true zero impedance/invalid taps stop the experiment rather than trigger invented parameters.
- **Learning gate,27October:** run a modest validation-only pilot with more than one seed. Look for repeatable exact-versus-stock improvements in physical residuals and a useful error trade-off. As a provisional engineering target, a≥30% reduction in median maximum residual without>1percentage-point worsening of median raw cost error would justify main runs. This is a project decision threshold, not an accepted scientific definition or significance test. Report both outcomes even if it fails.
- **Causal qualification:** compare E with S as well as C. If E merely catches up to removing KCL, the useful finding is that the distorted auxiliary loss hurts; do not claim exact KCL adds benefit beyond supervision. If C/E agree, the clamp is semantically wrong but has no demonstrated practical adaptation effect under this setup. Quantify the actual normalized weighted gradients before interpreting either result.
- **Optional only after the primary result:** one FFN-LoRA rank, stock/exact operators and matched data, asking whether the effect survives restricted adaptation. Alternatively one independent supported-size case selected by operator exposure before performance evaluation. Do not do both by default. case300x2 can show correlated replication, but not independent scale evidence; its symmetric zero-transfer base is not an inter-area stress study.

The honest no-go outcome is a reproducibility/implementation report with no demonstrated adaptation gain. A correction alone may be too small for this conference; a negative finding needs breadth and careful causal evidence. Do not force novelty or submission because the date is near.

## Five-page paper and schedule

Provisional contribution statements, to convert to factual claims only after results:

1. Quantify a version-specific difference between benchmark AC equations and a released adaptation objective, including original-reference and unit-base controls.
2. Determine its effect on held-out AC-OPF adaptation using matched stock/exact/no-KCL experiments.
3. Release the audit, splits, source pins and compact reproducible results, while respecting source-data licensing.

Allocate0.85page to title/abstract/problem/closest work;1.0 to mechanism and intervention;0.75 to protocol;1.55 to results;0.25 to limitations/conclusion;0.60 to references. One figure shows affected-branch/operator/reference mismatch; one shows held-out residual/error trade-offs by arm and seed; one table gives all-constraint pass rates, error, compute and sample counts. All adaptation result cells remain **unrun**.

| IST dates | Deliverable |
|---|---|
|21–22Oct | Archive latest report, sync VM evidence, freeze question and control definitions |
|23–24Oct | Exact-operator/gradient tests and bounded training smoke; runtime estimate |
|25–27Oct | Validation-only adaptation pilot; scientific go/no-go with professor/postdoc |
|28Oct–2Nov | Prespecified main matrix,3seeds, independent scoring; no new architecture |
|3–5Nov | Freeze tables/plots, write complete5-page draft |
|6–7Nov | Coauthor scientific review and targeted repairs |
|8Nov18:00 | Ready-to-submit internal target, source/format check |
|9–10Nov | Buffer; official cutoff11Nov10:29IST |

No email, conference account, submission, paid compute or long training was initiated. The next task requests only evidence and bounded smoke work on the already available machine. The main matrix is a concrete proposal whose cost and scientific value must pass its gates.
