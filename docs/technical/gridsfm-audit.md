# GridSFM implementation and reproduction audit — 21 October 2026

**Recommendation.** Target the released Microsoft **v1.1** checkpoint and the exact Microsoft commit below. Treat the new September/October paper and its separate fine-tuning implementation as related literature, not an interchangeable implementation. The first gate is an accepted solver label → native JSON → tensor → physical evaluation round-trip. Fine-tuning remains conditional on that gate; no trained case300/600 result is established here.

## Provenance and version boundary

| Artifact | Pinned identity | Evidence/status |
|---|---|---|
| Microsoft code | `1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6`, commit dated 27 May 2026 | Fresh clone inspected; MIT. [Pinned tree](https://github.com/microsoft/GridSFM/tree/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6) |
| Historical fork | `seiole-labs/GridSFM`, `feature/lora-ffn-adapters`, baseline `1e5e3a1640b27768e3eaf32680184f26b407caab` | Archive metadata; flattened files, not retained nested Git history. [Archive provenance](https://github.com/ninadsonawane/research-learning/blob/main/docs/source-repositories.json) |
| Microsoft checkpoint | HF revision `1b41299b80252adf1869d5c3b479a4a402c52591`, `gridsfm_open_v1.1.pt`, 61,061,952 bytes | HF API LFS metadata SHA256 `f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831`; actual file not downloaded. [Pinned model repository](https://huggingface.co/microsoft/GridSFM_Open/tree/1b41299b80252adf1869d5c3b479a4a402c52591) |
| Paper implementation | `lukebhan/gridsfm` HEAD `517a07531ea55a11bd81a89a6c6879695a2ba4b4` | Root/training README inspected only. Says it uses the whitepaper backbone. [Pinned README](https://github.com/lukebhan/gridsfm/blob/517a07531ea55a11bd81a89a6c6879695a2ba4b4/README.md) |
| Paper implementation base | HF `lukebhan/gridsfm` revision `970a413556fd1dc8c843cafdb03b01f9f8ef6f44`, `base/gridsfm_open_v2.pt` | 61,057,675 bytes; SHA256 `9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7`. Different file bytes; tensor equivalence **unknown**. Its harness calls this a released 15.1M-parameter backbone; that is a source claim. [Training documentation](https://github.com/lukebhan/gridsfm/blob/517a07531ea55a11bd81a89a6c6879695a2ba4b4/finetune_model/README.md) |

The source/API pins are in [the manifest](../../manifests/gridsfm-sources.json). No checkpoint, dataset or paper full text is redistributed. Only the archived MIT `lora.py` is imported, unchanged, as `scripts/python/gridsfm_lora.py`, with its license alongside it. No complete historical Git history is claimed.

An exact-byte comparison found `data.py`, `schema.py`, `loss.py`, `cycle_basis.py`, `pe_features.py`, `dc_prior.py` and the Julia exporter identical between archive and pinned upstream. The archived checkpoint loader adds `_checkpoint_metadata`; archived FT optimizes only `requires_grad` parameters; archived evaluation adds diagnostic fields; archived OPFData loading streams selected archive members rather than materializing all JSON. LoRA, the case6470 LoRA recipe and round-trip prototype exist only in the archive. All inspected file hashes are retained in [the comparison manifest](../../manifests/gridsfm-file-comparison.json).

## Suitability, size and prior exposure

The [pinned model README](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/README.md) defines supported size as at least 500 buses and recommends v1.1 for FT. The inspected loader, feature and forward code contains no 500-bus rejection. Thus case300 is an **out-of-training-size probe**, not an invalid tensor shape. No case300 forward was run. A successful 600-bus forward would not establish distributional similarity: duplicated equipment/cost patterns, a two-circuit inter-area cut, native zero ratings and load regimes still differ from training.

The pinned [model card](https://huggingface.co/microsoft/GridSFM_Open/blob/1b41299b80252adf1869d5c3b479a4a402c52591/README.md) describes approximately 540,000 scenarios and 54 base grids, including 24 PGLib cases with 500–4,661 buses plus 30 regional grids. This supports a claimed size boundary, not a complete contamination audit. Direct case300 membership is not indicated, but complete training scenario hashes/lineage were not established. Related IEEE/PGLib ancestry or previous unpublished target adaptation remains unknown. State this limitation instead of asserting guaranteed unseen pretraining. The bundled `case500_goc.pyg.json` is an installation/control sample, never a generalization test.

## What the code does and what it does not establish

| Component | Verified implementation | Consequence for this study |
|---|---|---|
| Native loader | `load_pyg_json` reads only `grid` features/edges; ignores `solution`, `metadata` and context; minimal shape checking | Valid inference input is not yet labeled training data. Validate every row, endpoint, unit and persistent identity externally. |
| Training loader | `OPFDataAdapterDataset` wraps PyG OPFDataset and assumes all returned examples feasible; archived `_opf_object_to_data` attaches `.y`, `.edge_label`, `.objective` | A new case name does not create a custom dataset. Use the explicit adapter described in [conversion](conversion.md). |
| Preprocessing | `prepare_for_grid_transformer_` promotes one branch node per physical edge and attaches cycle incidence; `attach_pe_features_` widens bus inputs and builds global context | Both transforms required. Rebuild from clean source after an outage/impedance/rating change; idempotence flags can retain stale features if already prepared objects are edited. |
| Parallel circuits | Cycle code stores a list of physical `(family,row)` edges per bus pair; additional parallel circuits create two-edge cycles. PE/DC sparse matrices sum their contributions while keeping original edge rows for branch features | Do not coalesce branches. Actual cycle-function test passed for two parallel edges, reversed orientation and one-circuit outage. Promotion/batching/loss/forward/metric end-to-end check is still pending. |
| Loss physics | `loss._flows_rx_bidir` recomputes AC flows for KCL, but clamps `r²+x²` to `1e-6`; training KCL normalizes by total generator capacity | Very small impedance branches can have altered evaluator physics. Report original-parameter physical residuals in pu and MW/MVAr independently; capacity-normalized training values are not feasibility tolerances. |
| Flow/thermal evaluation | Supervised flow terms can use `edge_flow_pred`; KCL explicitly recomputes from predicted voltage. Ratings `<=0` excluded; smoothed thermal denominator `sqrt(rate²+1e-4)` | Head agreement and smooth training penalties are not strict branch feasibility. Recompute both-end complex power against original finite ratings; report unrated branches as unconstrained. |
| DC prior | Uses detached predicted Pg, load and shunt G, scales predicted aggregate generation to demand within `[0.5,2]`, uses `1/x`, substitutes `1e-4` for tiny x, regularizes singular reduced matrix | This is a neural feature/prior, not a solved AC feasibility certificate. Its sparse sum supports parallel admittances but does not replace independent transformer physics. Exclude disconnected graphs before this path. |
| Inference leakage | Loader ignores solved fields; model/PE/DC paths use inputs, including original generator initial PG/QG and VG, not `.y` | Passing solved `results.gen` as input leaks information even if JSON labels are separate. Store unsolved scenario and solved labels separately; perturb/drop labels and confirm identical predictions. |
| Cost loss/metric | Schema costs multiply Pg in pu; cost metric divides by `max(reference_cost,1)`, loss applies log1p after nonnegative clipping | Compute and report original cost independently. Negative/zero-cost cases require absolute/safe-scaled error. These training conventions do not define achieved feasible cost. |

Sources: [loader](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/data.py), [schema](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/schema.py), [loss](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/loss.py), [evaluation](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/eval.py), [cycle basis](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/cycle_basis.py), [PE](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/pe_features.py), [DC prior](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/dc_prior.py).

## Archived LoRA audit and minimum reuse

The imported wrapper targets exactly `blocks.<block>.ffn.<node_type>.0` and `.2` for each node type. It freezes the entire backbone; each target gets `W(x) + (alpha/rank) B A(x)`, with A Kaiming-initialized and B zero-initialized. Thus initialization should reproduce the frozen forward. This is FFN-only LoRA, not attention LoRA. Its checkpoint records target names and optional base metadata. Upstream `load_model` does not attach the archived `_checkpoint_metadata`, so explicitly attach the verified checkpoint file SHA256 before saving/loading adapters; enforce the base identity at the runner as well.

The archived YAML actually selects CUDA, two epochs, rank 2/alpha 2, physical batch 4 and accumulation 2; its README labels the recipe CPU. These are historical inconsistencies, not evidence about today's hardware or case600 runtime. The YAML's comment that physical batch 8 exceeded 22 GiB on an L4 is a historical configuration claim, not a measured requirement for this study. The `case6470` script contains OPFData-specific paths, synthetic infeasibility, case labels and test selection: do not run it after merely renaming the case. Its logged outputs are not new case300/600 validation.

For matched FT, use one new runner around the same `CustomCaseDataset`, collator, loss, validation rule and scheduler. Initialize both methods from the same pinned checkpoint; wrap only LoRA's model. For initial custom-data pilots set synthetic infeasible generation off and `lambda_feas=lambda_stress_feas=0`; solver nonconvergence is unknown, not an infeasible class. Do not report classifier accuracy from a one-class accepted-feasible sample. Save selected checkpoints using validation only. A complete matched runner and GPU pilot are explicitly **not yet implemented/executed**; the October 25 gate determines whether the paper can retain adaptation.

## Reproducible setup: separate CPU smoke and GPU pilot

The source README reports Ubuntu 22.04/24.04 and macOS testing, Python >=3.10 with primary CI on 3.12. Windows is not listed as tested. Recommend an isolated Ubuntu 24.04 machine or WSL2 Ubuntu environment, with Python 3.12. WSL availability and GPU passthrough must be checked; an existing `wsl.exe` alone does not establish readiness. Native Windows is an optional smoke path, not a verified supported configuration. Keep the existing PF/OPF environment separate.

Run from this repository on the chosen Linux host (commands proposed, not run here):

```bash
git clone https://github.com/microsoft/GridSFM.git work/GridSFM
git -C work/GridSFM checkout --detach 1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6
python3.12 -m venv work/venv-gridsfm-cpu
source work/venv-gridsfm-cpu/bin/activate
python -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -c environments/gridsfm-constraints.txt -e 'work/GridSFM/model[test]'
python -m pip check
python -m pip freeze > work/gridsfm-cpu-resolved.txt
python scripts/python/gridsfm_selfcheck.py --upstream work/GridSFM --model
python scripts/python/gridsfm_fetch_checkpoint.py work/checkpoints/gridsfm_open_v1.1.pt
python -c "from gridsfm import load_model,predict; m=load_model('work/checkpoints/gridsfm_open_v1.1.pt'); o=predict(m,'work/GridSFM/model/samples/case500_goc.pyg.json'); print({k:tuple(o[k].shape) for k in ['V','theta','Pg','Qg']})"
python -m pytest work/GridSFM/model/tests -q
```

`gridsfm-constraints.txt` is a proposed direct-dependency resolution, **not** a complete tested transitive lock. Commit a platform-specific lock with hashes after installation and record the actual Python, torch, PyG, NumPy/SciPy/BLAS, driver and hardware. The pinned loader checks an internal hash of tensor names/dtypes/shapes/bytes before adapting old shapes; that hash is distinct from the entire `.pt` file SHA256 verified by our fetcher. v1.0 loading changes fusion shape for inference; do not use it in the matched experiment. [Checkpoint loader](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/checkpoint.py).

For a separate GPU environment use the same constraints and torch 2.8.0 with a driver-compatible wheel; official [PyTorch historical installation commands](https://pytorch.org/get-started/previous-versions/#v280) include CUDA 12.6/12.8/12.9 variants. Example only after checking driver compatibility: `python -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128`. Confirm `torch.cuda.is_available()`, device model/VRAM and a tensor operation before any pilot. Start batch 1 and increase only after measured forward/backward peak memory. A 16–24 GB GPU is a planning allowance, **not a proven requirement or guarantee**. Record CPU RSS and GPU allocated/reserved peaks separately; fewer trainable parameters alone prove neither memory nor runtime savings.

If testing the Julia route, upstream's checked-in Manifest pins Julia 1.11.5, PowerModels 0.21.5, JuMP 1.29.4 and Ipopt.jl 1.14.0. Instantiate that manifest rather than arbitrary latest packages. The minimum MATPOWER→neutral JSON path does not require Julia; the Julia path remains a useful independent cross-solver round-trip only after normalization auditing.

## Executed versus pending

Executed 21 October: archive instructions/provenance read; selected source inspected and hashed; upstream clone/commit verified; HF metadata retrieved; six converter checks passed; actual pinned cycle-function body executed on a two-bus multigraph with installed NumPy/SciPy/torch and a minimal store object. This is narrower than importing PyG. A tiny unrelated FFN verified the imported LoRA wrapper's target names, initial equivalence, frozen backbone and adapter gradients. The unsolved constructed600 neutral case converted successfully to 600 buses, 138 generators, 402 loads, 58 shunts, 566 AC lines and 258 transformers; both tie IDs survived. This is conversion structure, not a solve. The final check log is in [the manifest](../../manifests/gridsfm-checks.json).

Not executed: PyG preprocessing/batching/full forward/backward, checkpoint download/load, case300 or constructed600 model inference, solver export/round-trip, LoRA/FT training, performance measurement. The host's default Python is 3.9 (below GridSFM's minimum); torch and SciPy exist there but PyG does not. MATLAB/Octave/Julia/GPU executables were not found on PATH by the broader study audit. These are environment blockers for execution, not reasons to fabricate outcomes.
