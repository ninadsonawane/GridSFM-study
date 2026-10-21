# Conversion without changing the AC-OPF problem

The shortest defensible route is **unsolved MATPOWER scenario → MATPOWER solve plus independent acceptance → neutral matrix JSON and separate solution arrays → strict native JSON converter → clean input tensors → GridSFM → original-parameter evaluation**. This avoids a second parser silently changing angle limits. It does not avoid the need to validate the JSON/tensor/solver round-trip.

## Field contract

`scripts/python/gridsfm_convert.py` accepts standard MATPOWER `baseMVA`, `bus`, `gen`, `branch`, `gencost` arrays, with optional persistent `bus_ids`, `gen_ids`, `branch_ids`. It constructs explicit external-ID→zero-based-row maps, filters inactive devices without aggregating branches, and retains original matrix row indices and removed circuit IDs. This is its own export map; it is not MATPOWER's `order` structure. If the source already used `ext2int`, retain that original map in the scenario manifest to compose the two maps. Do not reuse stale maps from either 300-bus copy.

| Source MATPOWER quantity | Native GridSFM location | Exact transformation |
|---|---|---|
| BASE_KV, BUS_TYPE, VMIN, VMAX | `bus.x=[base_kV,type,Vmin,Vmax]` | kV unchanged, voltage bounds pu; preserve PQ/PV/REF roles |
| MBASE, PG, PMIN, PMAX, QG, QMIN, QMAX, VG | first eight generator columns | MBASE in MVA unchanged; P/Q divide by **system** baseMVA, not MBASE; VG pu |
| quadratic MW cost `c2 Pg_MW²+c1 Pg_MW+c0` | generator columns 8:11, zero-based | `[c2*baseMVA²,c1*baseMVA,c0]`; zero-pad linear/constant costs exactly |
| PD/QD | `load.x=[Pd,Qd]` | MW/MVAr divide by baseMVA; negative loads preserved |
| GS/BS | `shunt.x=[Bs,Gs]` | reverse field order; divide by baseMVA. Positive GS consumes `GS*V²`; positive BS injects `BS*V²` |
| BR_R/BR_X | edge columns per schema | already pu on system base; unchanged |
| total BR_B | per-end `b_fr,b_to` | split half at each end; transformer from-end charging is subsequently tap-scaled by the π model |
| RATE_A/B/C | family-specific rate columns | MVA divide by baseMVA; retain **0 = unlimited**, no inferred rating |
| TAP, SHIFT | transformer columns 7,8 | MATPOWER TAP=0 means unity; SHIFT degrees→radians; keep original from/to orientation |
| ANGMIN/MAX | first two branch columns | degrees→radians; retain original sentinel/mask in source. MATPOWER ±360 unbounded semantics belong to the independent evaluator, not an invented ±60 constraint |
| BUS VA,VM solution | `bus.y=[theta,V]` | radians, pu; reference-align angles for comparison |
| generator PG,QG solution | `generator.y=[Pg,Qg]` | system pu |
| branch PF,QF,PT,QT solution | `edge_label=[Pt,Qt,Pf,Qf]` | reverse end-pair order as required by OPFData; divide by baseMVA |
| model branch prediction | `[Pij,Qij,Pji,Qji]` | from-end pair first: compare with label columns **2,3,0,1** |

Field evidence: [MATPOWER case format](https://matpower.org/documentation/ref-manual/legacy/functions/caseformat.html), pinned [GridSFM schema](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/schema.py), [Julia exporter](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/power_grid/US/topology_solver_pipeline/export_gridsfm_data.jl), and [loss flow target indexing](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/model/gridsfm/loss.py).

The converter rejects nonquadratic/piecewise-linear costs, nonzero reactive-cost blocks, nonrectangular PQ capability curves, dispatchable loads with their special power-factor constraints, zero-impedance/self-loop branches, invalid bounds, disconnected graphs and known nonstandard OPF extensions. A 2*ng cost block is explicitly recognized: all-zero reactive polynomial costs can be omitted with recorded metadata; nonzero ones require extending the model/loss and are rejected. Generator-cost and solution rows are filtered together. All unsupported features need an explicit extension or a documented new problem variant, not silent approximation. Unknown optional MATPOWER fields should also be reviewed before use; the intended scope is ordinary continuous AC-OPF with the listed standard fields.

The native feature schema has no general status column. A single-tie outage therefore removes precisely that branch row from the ML graph while the source case/manifest retains its persistent ID and status. Both flows and labels follow the same ordered family lists. AC lines and transformers are separate families, so concatenated prediction order differs from the original MATPOWER branch matrix: use `*_source_rows` and `*_branch_ids` to restore it.

## Why the Julia exporter needs changes

The archive and upstream exporter are byte-identical. It exports active devices, sorted original IDs, per-unit costs from PowerModels and correct reversed label order. Its exact polynomial cost rejection is useful. However, its CLI calls `PowerModels.parse_file(...,validate=true)` before solving and accepts statuses containing `LOCALLY_SOLVED`, `OPTIMAL` or `ALMOST_LOCALLY_SOLVED` without the proposed independent physical gate. It uses Ipopt `tol=1e-6` and `acceptable_tol=1e-4`, not the model card's cited training tolerance. It zeros solution tensors for unsuccessful status; those zeros must never become accepted regression labels or proof of infeasibility.

In the pinned PowerModels **0.21.5** implementation, `correct_network_data!` performs unit conversions **and** additional transformations. Specifically, angle bounds at/beyond ±90° are tightened to about ±60°; zero thermal-limit keys are removed, preserving unlimited semantics; reverse-oriented parallel circuits can be reoriented with corresponding tap, impedance, charging and shift transformations. `calc_thermal_limits!` is a separate routine that can infer missing/zero ratings; do not conflate it with zero-limit removal. [Parsing/correction sequence](https://github.com/lanl-ansi/PowerModels.jl/blob/v0.21.5/src/io/common.jl), [angle, thermal and branch-direction code](https://github.com/lanl-ansi/PowerModels.jl/blob/v0.21.5/src/core/data.jl#L1010).

Consequently, a blind exporter CLI run on native case300 does **not** preserve its unlimited angle assumptions. To reuse the exporter, separate parsing/unit normalization from corrections; snapshot and diff all fields before/after; explicitly control unbounded-angle representation in the AC formulation; preserve per-circuit identities/orientation; stop on any unapproved change; apply the same objective/constraint/residual gate used for MATPOWER. Verify treatment of inactive buses, per-end shunt conductance and exact generator capability limits. The exporter only has susceptance charging columns and assumes ordinary branch conductance through series r; a more general PowerModels network needs additional schema support.

Do not route this benchmark through `solve_topo_json.jl` to obtain a successful label. Its documented escalation widens voltage/Q limits, alters angles, multiplies ratings, changes Pmin and ultimately sheds load/removes thermal constraints. Those operations construct a different OPF. If any explicitly approved relaxed variant is ever studied, give it a new scenario ID and transformation manifest. [Pipeline relaxation table](https://github.com/microsoft/GridSFM/blob/1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6/power_grid/US/topology_solver_pipeline/README.md).

The archived `prototype_opfdata_roundtrip.py` is useful as a reverse-mapping reference: its flat initialization uses input PG/QG clipped to bounds; its `ground_truth` initialization deliberately uses solved targets. Keep that option diagnostic-only, never a conventional cold-start baseline. It reconstructs active-only data, assigns new sequential IDs, and handles exactly the represented schema. It does not prove that arbitrary MATPOWER extensions or the parser's corrections round-trip unchanged.

## Adapter and label wiring

Native `load_pyg_json`/`load_opfdata` both ignore solution labels. The FT route expects `bus.y=[theta,V]`, `generator.y=[Pg,Qg]`, per-family `.edge_label=[Pt,Qt,Pf,Qf]`, graph `.feasible`, and the optional objective. `gridsfm_adapter.py` validates shapes/endpoints/IDs, constructs clean features, applies the normal cycle and PE transforms, and **only then** attaches accepted labels. It does not pass solved fields into preprocessing. Empty node and edge types have explicit two-dimensional tensor shapes.

Use `torch.utils.data.DataLoader`, not the PyG loader that overrides user collation, with `collate_fn=gridsfm.batch_data_list`. That collator fills canonical empty families and reshapes global context consistently. Use explicit train/validation/test path manifests. Regenerate each graph from the unsolved input after perturbation; modifying a transformed graph in place can leave stale branch/cycle/PE caches.

```python
from torch.utils.data import DataLoader
from gridsfm import batch_data_list
from gridsfm_adapter import CustomCaseDataset  # scripts/python on sys.path
ds = CustomCaseDataset(train_paths, training=True)
loader = DataLoader(ds, batch_size=1, shuffle=True, collate_fn=batch_data_list,
                    num_workers=0)
```

This is a small proposed schema bridge, **not a validated new fine-tuning pipeline**. The dataset accepts only independently accepted feasible labels; synthetic-negative wrapping is disabled. Model feasibility outputs may be logged but cannot certify a dispatch. Failed local solves are retained as `solver_failure/unknown` records and optionally retried with disclosed starts, never automatically labeled infeasible.

## One-scenario round-trip acceptance

1. Freeze and hash one unsolved case300 operating point; record all transformations, case source SHA, code commit, solver/version/options, IDs, costs and rated/unrated masks. Export unsolved inputs **before** applying solver results; MATPOWER's returned `results.gen` includes optimized PG/QG and VG and must not be substituted as model inputs.
2. Run the numerical AC-OPF with original constraints; retain return status, all arrays and logs. Independently recompute objective, bus injections, shunt powers, both-end branch flows and all applicable limits using the original parameters. Only after the configured acceptance thresholds pass set `accepted_feasible=true`. `success=1` alone is insufficient. Local optimality is not global certification.
3. Convert with `python scripts/python/gridsfm_convert.py case-input.json case.pyg.json --labels accepted-labels.json`. Labels must have original-row arrays `vm,va_deg,pg_mw,qg_mvar,pf_mw,qf_mvar,pt_mw,qt_mvar`, objective and acceptance. The output refuses to overwrite an existing file. Its SHA256 describes canonical source content, not raw source-file bytes; retain both hashes in the manifest.
4. Reconstruct the represented electrical model from native fields. Check exact IDs/counts/status selection, costs and limits; compare original and reconstructed objective to relative `1e-8`, scalar input fields to `1e-12` in double precision, and solved-state reconstructed flows/injections to `1e-8` pu (proposed conversion tolerances). After float32 tensor conversion use a separately recorded float32 tolerance, initially `1e-5` pu; failure on ill-conditioned/tiny-impedance branches is a diagnosis, not permission to relax tolerances silently.
5. Run frozen inference once; delete/randomize solution fields and repeat. All input features/PE/context and predictions must agree to machine-exact CPU deterministic tolerance or a prespecified GPU tolerance. Then compare single-graph and two-graph batches; ensure every physical edge has one output row in its family and returns to the same persistent ID.
6. Repeat topology-sensitive checks with both parallel ties, each individually reversed for conversion testing, and one tie unavailable. Check expected cycle rank `m-n+c` including parallel edges, branch-node counts, incidence signs, caches, label order, finite loss and one backward pass; the two symmetric tie outages are not independent research samples.
7. Run the independent evaluator on the solver labels first, then predictions, with no learned branch-flow head involved. Report head-vs-physical-flow disagreement as a diagnostic. If an independent second solver is used, compare constraint interpretation first; dispatch differences between accepted local optima alone do not prove conversion error.

**Executed:** six dependency-free converter tests and the actual pinned cycle-function test. **Pending:** full case solver round-trip, reconstructed-network solve, tensor/PE/batch checks, checkpoint forward, loss/backward, leak-invariance at prediction level and every accuracy/runtime experiment. The optional `--model` self-check is delivered for the isolated environment, explicitly unrun here. Toy label fixtures are structural tests, not solved-case evidence.
