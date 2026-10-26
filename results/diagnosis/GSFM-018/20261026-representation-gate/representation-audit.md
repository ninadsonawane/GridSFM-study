# Representation gate: deterministic changes before neural inference

26 October 2026. Study source inspected at `b4c2a02720e86482b7e60d3d7d41cc70fc3a2848`.

**Verified:** physically equivalent case300 row permutations change features and relations constructed by the pinned released pipelines, before a model forward. This narrows Experiment16's blocker to concrete deterministic preprocessing mechanisms. **Unresolved:** which mechanisms cause how much of its saved native prediction differences. No checkpoint, model forward, conventional PF/OPF solve, or new electrical operating point was used here. Earlier predictions and runners remain unchanged.

[Executable probe](../../../../experiments/gsfm018/probe_representation.py) and [complete numerical output](representation-probe.json) execute exact AST-extracted source functions with a minimal tensor container, because this Windows environment lacks PyG. This is a focused feature audit, not an end-to-end reproduction. Upstream imports, caches, batching and neural layers are not exercised. Feature preparation's own sparse linear algebra runs where required; that is not a conventional network solve or a repair.

## What was tested

The original MATPOWER8.1 case300 source SHA-256 is `69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5`:300 buses,69 generators,411 branches, comprising282 converted AC lines and129 transformers. Baseline, bus-only reversal, generator/cost-only reversal, branch-only reversal, and combined reversal preserve all physical coefficients. For both releases, raw bus/device/branch features and directed endpoints are asserted exactly equal after mapping. No solution fields are added. These are representation controls of one existing input, not new electrical discovery inputs.

| Component / isolated control | Microsoft v1.1 | Newer base v2 |
|---|---|---|
| Branch reversal: physical cycle supports shared with original | 29/112;83 differ | 29/112;83 differ |
| Branch reversal: cycle-to-branch incidences | 864→1072 | 864→1072 |
| Bus reversal only: cycle supports / signs | All112 supports retained; all112 cycle sign vectors globally flip | Same |
| Bus reversal: landmark set | 59/64 physical buses retained | DC/ER features removed in this release |
| Bus reversal: ER landmark moments | All300 bus rows change; max absolute feature difference0.847053528 | N/A |
| Branch reversal: transformer DC features | All129 rows change; max absolute feature difference39.8005412 | N/A |
| Generator/cost reversal only | Tested cycle/DC/ER components unchanged exactly | Tested cycle components unchanged exactly |

The numerical feature differences above are in their native feature units; they are **not** MW/MVAr prediction errors. Identical-order repeats of the executed cycle and ER components were exact in this environment. The seed-independent integer cycle differences cannot be explained by floating-point noise. This does not establish determinism of historical full forwards.

## Source trace and isolated diagnoses

**Shared cycle-basis dependence on branch order.** Both releases' `cycle_basis.py` are byte-identical (SHA-256 `4f1a324975f27bc2341387994c7c8cfbd2f4901a2769717bff5ed20dfa0d0eeb`). The function collects endpoint pairs in incoming branch order, assigns weights `1..n_pairs`, and computes a minimum spanning tree. Those are ordering weights, not electrical weights. Reversing rows therefore changes the tree and fundamental cycle supports. The code then exposes cycle length, summed absolute R/X, minimum positive rating and signed relations to the learned model. See [pair construction / MST, lines42–74](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/cycle_basis.py#L42-L74), [cycle features/relations, lines133–200](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/cycle_basis.py#L133-L200), and [v2 Hodge branch operator, lines109–155](https://github.com/lukebhan/gridsfm/blob/517a07531ea55a11bd81a89a6c6879695a2ba4b4/model/gridsfm/hodge_pe.py#L109-L155).

A different valid fundamental basis is not itself an invalid electrical network. However, there is no reason to assume the neural architecture is invariant to that basis change: after physical branch mapping, the integer operator `B2 B2^T` differs at10,912 entries, with maximum absolute entry difference24. This rules out a mere permutation or global sign flip of identical cycle columns. The full matrix is an auxiliary diagnostic; the model's Hodge operator uses separate branch-family blocks. Bus-only reversal, in contrast, changes signs but leaves this Gram matrix identical; do not claim its Hodge effect from the Gram diagnostic.

**Shared cycle-orientation inconsistency, separately checked.** Cycle signs use `+1 if a < b else -1` ([line161](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/cycle_basis.py#L161)), while promoted branch endpoint signs use the stored sender/receiver direction ([lines291–321](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/cycle_basis.py#L291-L321)). The probe executes both functions, constructs `B1` from returned endpoint signs and `B2` from returned cycle signs, and multiplies them with integer arithmetic. The boundary-of-a-boundary product has nonzero entries in31/112 original cycle columns and43/112 after branch/combined reversal; largest absolute entry2. Choosing the cycle-walk sign relative to each stored directed edge gives zero columns for every control. This demonstrates inconsistency between these two representation conventions. It is **not** an electrical KCL residual, nor proof of the cause of observed model imbalance. It remains separate from the cycle-basis effect.

**v1.1 landmark selection depends on bus row index.** A64-landmark budget is filled by slack buses, then sorted internal generator-bus indices, then degree order. With69 generator buses, reversing bus rows changes which physical buses survive truncation. See [selection, lines158–183](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/pe_features.py#L158-L183) and [moments, lines232–251](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/pe_features.py#L232-L251). In an isolated feature-only diagnostic, forcing the reversed representation to use the baseline physical landmarks reduces all ER moment differences to exactly zero. No prediction was generated from that altered diagnostic state.

**v1.1 transformer DC-feature offset counts arrays instead of edges.** `_build_topology_state` appends one whole AC-edge array and then sets transformer `start=len(edges_i)`, yielding1 instead of282. `compute_dc_features` uses that start to slice concatenated edge endpoints/susceptances before attaching the resulting rows to transformers. See [offset construction, lines113–139](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/pe_features.py#L113-L139) and [slicing/feature assembly, lines307–338](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/pe_features.py#L307-L338). In a separate feature-only diagnostic, setting the transformer start to282 reduces the branch-only reversal's mapped transformer-feature difference from39.8005412 to0; combined reversal leaves only1.49e-8. Bus DC features and AC-line DC features already match exactly for these controls. This is an identified indexing defect in the pinned v1.1 feature code, not a proposed silent replacement of released results.

**Do not transfer v1.1 findings to v2.** The pinned v2 [pe_features.py, lines1–9](https://github.com/lukebhan/gridsfm/blob/517a07531ea55a11bd81a89a6c6879695a2ba4b4/model/gridsfm/pe_features.py#L1-L9) explicitly removes DC/ER positional columns. Its shared cycle code remains. The v2 result cannot be attributed to v1.1 landmark truncation or the transformer offset.

The historical raw-equivalence audit stopped before these operations: [audit_representation_inputs.py](../../../../experiments/gsfm016/audit_representation_inputs.py), especially its explicit raw-only scope at line20. Released inference calls preparation before forwarding ([v1.1 data.py, lines175–186](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/data.py#L175-L186)); Hodge features and signed message passing then consume the prepared representation. Experiment16's runner uses seed0, CPU4 threads, eval mode and strict checkpoint loading, but does not preserve every prepared intermediate or independently vary these mechanisms.

## What remains supportable

Earlier independently checked native residuals and approximation measurements describe the saved, declared-order released-default pipelines. Exact raw-graph equivalence does not establish equivalent model-ready inputs. Their dependence on representation prevents a general invariant electrical-response claim or attribution of all changes solely to the neural network's electrical understanding.

For original-order, fixed-topology loading, P-only/Q-only, demand redistribution and positive-charging interventions, source inspection gives a narrower conclusion: cycle support/signs and cycle R/X/rating features remain fixed; v1.1 landmark selection and ER moments remain fixed as well. Demand P changes v1.1 DC input features through the intended load term, while Q or charging changes do not. The incorrect transformer offset remains fixed in these contrasts, so a demand change can still be attached through the wrong branch's DC features. These statements follow from source dependencies, not additional operating-point execution. Fixed ordering removes this particular between-case permutation change; it does not validate the pipeline or explain all saved electrical trends.

The next decisive step is a bounded mediation audit in the original hardware environment: capture full prepared inputs for repeated identical baseline forwards and the existing row controls; compare mapped features before the first learned layer; then substitute the baseline-mapped cycle graph, and separately v1.1 landmarks/DC features, in explicitly labelled diagnostic forwards. Replacing a cycle representation requires its nodes, features and all relations together. Keep native shipped-default outputs separate. First verify checkpoint/source hashes and reproduce saved baseline outputs. Same-input repeated forwards, CPU thread controls and cache-cold/warm controls distinguish numerical variation and cache effects from deterministic representation changes. No such full-model experiment ran here, and no repaired prediction should replace earlier results.

## Reproduction

Dependencies used: Python3.9.10, NumPy2.0.1, SciPy1.13.1, torch2.7.0+cpu; CPU, one thread for this source probe. No PyG or checkpoint is required. JSON records all inspected source-file hashes, study parser/converter hashes, exact input canonical hashes, diagnostics and repeat checks. The executable verifies the three executed source-file hashes per release and the MATPOWER source hash before proceeding, and refuses to overwrite an existing result.

From repository root, obtain source-only Git objects into ignored work directories. Skip clones if those directories already exist; verify/reuse them. `--no-checkout` avoids fetching model/data working-tree files.

```sh
git clone --filter=blob:none --no-checkout https://github.com/microsoft/GridSFM.git work/representation_audit/microsoft-source
git clone --filter=blob:none --no-checkout https://github.com/lukebhan/gridsfm.git work/representation_audit/newer-source
```

Run this Python snippet to materialize only the three required raw source blobs. It preserves exact LF bytes and refuses to overwrite differing files.

```python
from pathlib import Path
import subprocess
root = Path('work/representation_audit')
for repo, pin, dest in [
    ('microsoft-source', '1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6', 'source-v11'),
    ('newer-source', '517a07531ea55a11bd81a89a6c6879695a2ba4b4', 'source-v2')]:
    out = root / dest
    out.mkdir(parents=True, exist_ok=True)
    for name in ['schema.py', 'cycle_basis.py', 'pe_features.py']:
        blob = subprocess.check_output(['git', '-C', str(root / repo), 'show',
                                        pin + ':model/gridsfm/' + name])
        target = out / name
        assert not target.exists() or target.read_bytes() == blob
        target.write_bytes(blob)
```

Use the immutable case source acquired via [matpower-source.json](../../../../manifests/matpower-source.json). The recorded run used the existing original Windows checkout's `data/source/matpower-8.1/case300.m`, read-only. Substitute its actual path below; the hash gate ensures identity.

```sh
python experiments/gsfm018/probe_representation.py --case /path/to/case300.m --v11-source work/representation_audit/source-v11 --v2-source work/representation_audit/source-v2 --output work/representation_audit/reproduced-probe.json
```

Compare numerical `variants` fields with the tracked result. Source inventory can include additional inspected `.py` files, and software/platform roundoff can differ. Scientific claims here use exact integer cycle differences and large feature differences;1.49e-8 is explicitly treated as numerical. Source blobs and original case bytes remain ignored; no checkpoint or case matrices are republished.
