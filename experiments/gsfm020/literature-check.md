# Primary-source check for Experiment 20

Checked 26 October 2026. This is a narrow literature check, not an exhaustive novelty review. It establishes no novelty claim.

- **Pinned released Microsoft pipeline.** The [v1.1 README at source commit 1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/README.md) states a supported size of at least 500 buses, documents CPU inference and native per-unit outputs, and defines preprocessing before prediction. Original case300 is therefore an out-of-training-size probe. The duplicated 600-bus system satisfies that size boundary but does not establish distributional similarity or unseen pretraining membership. The README's tested platforms do not establish Windows compatibility; this experiment must verify that locally.

- **Later GridSFM work has a different evaluation boundary.** [Bhan et al., arXiv:2609.30173v2](https://arxiv.org/abs/2609.30173v2), revised 6 October 2026, combines a pretrained backbone with physics-informed adaptation and Newton power-flow completion, and assesses warm starts. Native outputs of the frozen base-v2 checkpoint here are not a reproduction or evaluation of its complete adapted/completed workflow. Its claims must not be used to assert that native frozen states satisfy every AC constraint. Conversely, failures here do not establish failure of that later workflow.

- **Accuracy and physical consistency can already disagree in prior work.** [Kim et al., arXiv:2610.05959v1](https://arxiv.org/html/2610.05959v1), 5 October 2026, examines voltage-error direction, Jacobian sensitivity and calibrated solution-subspace projection. Section 3 says all models were trained from scratch; GridSFM and LUMINA were adapted from AC-OPF to AC-PF with fixed dispatch and known-variable masking. Its scores restore known PV/slack values and mask residuals by bus type. Thus generic accuracy/physics disagreement, voltage-error amplification, and post-hoc projection are not defensible novelty claims here. This study's narrower scope is the released frozen OPF checkpoints, native dispatch and voltages, full original AC constraints, and measured operating-condition/representation sensitivity without completion or repair.

The [Microsoft May publication page](https://www.microsoft.com/en-us/research/publication/gridsfm-a-foundation-model-for-ac-optimal-power-flow/) is separate from the later September/October paper. Versioned source/checkpoint evidence takes precedence over combining their release descriptions.

## Immutable runtime identifiers

These identifiers come from the repository manifest and exact local source/checkpoint verification. The browser could not retrieve the version-pinned Hugging Face file pages during this check; local downloaded-byte hashes, not successful browser retrieval, establish runtime identity.

| Release | Source | Download URL | Required complete-file SHA-256 |
|---|---|---|---|
| Microsoft v1.1 | [1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6](https://github.com/microsoft/GridSFM/tree/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6) | [Pinned checkpoint](https://huggingface.co/microsoft/GridSFM_Open/resolve/1b41299b80252adf1869d5c3b479a4a402c52591/gridsfm_open_v1.1.pt) | `f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831` |
| Newer base v2 | [517a07531ea55a11bd81a89a6c6879695a2ba4b4](https://github.com/lukebhan/gridsfm/tree/517a07531ea55a11bd81a89a6c6879695a2ba4b4) | [Pinned checkpoint](https://huggingface.co/lukebhan/gridsfm/resolve/970a413556fd1dc8c843cafdb03b01f9f8ef6f44/base/gridsfm_open_v2.pt) | `9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7` |

Expected AC reactive response to changed Q demand or charging, and DC invariance to either, are controls rather than novelty. Any potential paper claim should concern reproducible, localized, release-specific behavior supported by nearby confirmations and should retain fixed-order and distribution limitations.
