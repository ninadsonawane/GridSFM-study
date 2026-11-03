# Versioned workflow and stage availability

Author source: [`lukebhan/gridsfm` at 517a07531ea55a11bd81a89a6c6879695a2ba4b4](https://github.com/lukebhan/gridsfm/tree/517a07531ea55a11bd81a89a6c6879695a2ba4b4). Exact exported file hashes are in `manifests/execution.json`. The executable study adapter was frozen at study commit `f48daa3e22c09fb13e93f1d74e50a3000b8cb539` before the numerical sweep; later analysis scripts do not change it.

| Published stage | Inspected implementation / evidence | This study |
|---|---|---|
| Pretrained backbone produces native heads | `model/gridsfm/model.py`; default clamp | Reuse exact V1 and base-V2 native states/prepared inputs from prior archive; no inference rerun or altered clipping. |
| Target-grid physics-informed adaptation | `finetune_model/README.md`, run-label table; `src/train_elastic.py`; `config/case500_goc_finetune.yaml` | Use released case500 `n0100/control_model.pt`, selected before results. README identifies n0100 as elastic training on 100 cases and control_model as the validation-selected deliverable. Training itself is not rerun. |
| Control extraction | `src/store.py:72-75` returns generator head column 0 and bus head column 1 in float64 | Active generator Pg and full predicted Vm; native Qg does not enter Newton. Adapted weights loaded strictly into base architecture with sigmoid, as README instructs. |
| Cold inference initialization | `src/train_elastic.py:251-302`, `src/closure.py:370-414` | Author `dc_init_V` with predicted Pg/full Vm; clamp controlled magnitudes to their predictions. No AC solution, previous scenario or training cache is used. |
| Newton completion | `src/closure.py:238-306`, `ACPFClosure.forward` and `_forward_worker` | Unmodified `newton_pf`, SuperLU, backtracking, maximum 40 iterations, residual infinity norm tolerance 1e-5 p.u. Paper IV-A preset chosen before runs. Case500 config uses final 1e-8 p.u.; that difference is explicit, not a claim to reproduce the config preset. At 100 MVA base, 1e-5 p.u. is 1e-3 MW/MVAr. |
| Recover dependent quantities | Author closure returns complex voltage, not an original-matrix study state | Disclosed study adapter recovers Qg and balancing Pg and maps outputs to original row IDs. This exporter/allocation is study code. |
| Original-case evaluation | Prior validated `experiments/loading/study.py:evaluate`, independent `electrical.terms` | Same original matrices, prescribed signed loads, statuses and frozen tolerances; two-end branch checking. Convergence, original-equation balance, and joint feasibility are separate. |
| Projection and full warm-started AC-OPF | GridSFM paper IV-C and VI | Separate downstream procedures, unrun and outside the benchmark. They are not hidden in the PF row. |

The comments in `train_elastic.py` reference `evaluate_model/completion.py`, but it is absent from the pinned 76-file source tree. We reproduce the available Newton kernel and inspected forward-call controls/initialization through a validated adapter. We do not claim a byte-identical full author evaluation workflow.

## Physics and bus roles

The released extractor uses float32 graph features and `r*r + x*x + PI_Z2_EPS` with `PI_Z2_EPS=1e-12`. Its admittance is not bit-identical to the original matrices. Reference-control validation converges in graph equations but fails the strict original-equation tolerance; see `validation/adapter-gates.json`. Before model PF runs, `validation/adapter-decision.md` logged the exact-matrix diagnostic. This changes only closure physics to original FP64 branches, taps, phase shifts, charging, shunts and demand; the same Newton kernel, predicted controls and primary preset are retained. Both outcomes are saved. It is not silently substituted for the official-graph row.

case300 uses balancing bus 7049; case300x2 uses 257. In case500goc, the original REF bus 311 has no online generator. The study applies MATPOWER/PYPOWER `bustypes` fallback to the first eligible PV bus, 272. No generator is switched on; original limits and network matrices remain fixed. This changes the balancing generator, not merely the angle gauge. Reported angles are shifted back to the original reference for comparison. The untouched-extractor reference diagnostic is retained separately, not counted as a model result.

For co-located online generators, recovered bus Q is allocated as `Qmin_i + (Qmax_i-Qmin_i)/sum(Qmax-Qmin) * (Qtotal-sum(Qmin))`; zero total range uses equal allocation. There is no clipping. Per-generator Q accuracy depends on this rule, so `paper/aggregate-bus-Q-limits.csv` also checks total bus Q against summed Q bounds. At a balancing bus the first online generator absorbs the residual active injection; other Pg controls stay fixed. Offline outputs remain zero. All saved PF records assert fixed Pg changes below 1e-9 MW and controlled Vm changes below 1e-12 p.u. Q-limit PV/PQ switching is not applied.

## Availability and exposure

| Stage | case300 (29 inputs) | case300x2 (15) | case500goc (15) |
|---|---|---|---|
| AC references | 28 checked, 1 UNKNOWN | 14 checked, 1 UNKNOWN | 15 checked |
| DC native / V1 native / V2 native | Available, reused | Available, reused | Available, reused |
| Frozen V2 + official PF | 29 attempted | 15 attempted | 15 attempted |
| Frozen V2 + exact-matrix PF diagnostic | 29 attempted | 15 attempted | 15 attempted |
| Released adapted native / official PF / exact diagnostic | UNAVAILABLE: no compatible released target checkpoint | UNAVAILABLE: no compatible released target checkpoint | 15 outcomes for each stage |
| New training / projection / warm-start OPF | Unrun | Unrun | Unrun |

Adapted weights: Hugging Face revision `970a413556fd1dc8c843cafdb03b01f9f8ef6f44`, path `case500_goc/n0100/control_model.pt`, SHA-256 `8903c5270be2bd651e1c21ffa98ad3f3f3be46f77e799b6c7231af26d372f3bc`. The author case500 matrices match the study source exactly. Base-V2 checkpoint SHA-256 is `9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7`; V1 is `f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831`.

The prior `paper/training-exposure.json` remains authoritative for V1/base V2: V1 exact topology membership is unverified; the V2 paper identifies case500goc as a pretraining topology. case300 lies below the documented size range; the two-copy network is study-created. These facts do not establish exact checkpoint/scenario membership. The adapted checkpoint is target-grid-specific; exact overlap of these operating points with its train/validation data is unverified. No held-out generalization or exposure-based causal claim follows.

## Reproduction boundary

Use the immutable prior archive for all reused states, the checkpoint release for all new numerical states, and the latest study code/figures/manuscript for analysis. `GRIDSFM_PRIOR_EVIDENCE_ROOT` and `GRIDSFM_OFFICIAL_SOURCE_ROOT` locate the extracted evidence and exact author tree. Execution manifests retain original machine paths and exact environment versions. The supplied Mac research-note/checklist/audit paths are not mounted on this Windows host; they were not represented as read. Instead, the complete prior published evidence and every inventory hash were verified locally. This is a disclosed location limitation, not permission to invent missing notes.
