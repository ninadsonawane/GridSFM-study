# Frozen GridSFM inference: original case300 and connected case300x2

Executed 21 October 2026 on Ninad's Mac. Two nominal operating points, no adaptation, repair or load perturbations. These are new numerical results, distinct from the earlier study-design package.

| Metric | Original case300 | Constructed case300x2 |
|---|---:|---:|
| Buses / generators / branches | 300 / 69 / 411 | 600 / 138 / 824 |
| Reference local AC-OPF cost, cost units/hour | 719725.098880 | 1439466.449121 |
| Cost of raw predicted dispatch, cost units/hour | 324075.498046 | 1191424.442667 |
| Absolute cost error | 54.9723% | 17.2315% |
| Voltage MAE, pu | 0.0268688 | 0.0266741 |
| Reference-aligned wrapped angle MAE, degrees | 23.3051 | 30.1990 |
| Active generation MAE, MW per generator | 195.1338 | 122.5297 |
| Reactive generation MAE, MVAr per generator | 89.0968 | 89.3016 |
| Maximum nodal active imbalance, MW | 3754.0796 | 1141.6350 |
| Maximum nodal reactive imbalance, MVAr | 8937.9681 | 9376.4491 |
| Raw prediction passes all tested constraints | No | No |
| Reference passes all tested constraints | Yes | Yes |

The predicted costs are evaluations of the generator cost functions on physically infeasible outputs, not achieved operating costs or savings. Physical metrics are recomputed from predicted voltage/angles/generation and original circuit parameters, not the model's flow head. The model's feasibility classifier returns 0.0 for both inputs; both inputs nevertheless have independently validated feasible numerical reference solutions. Classifier output is not proof of network infeasibility.

## Inputs and execution

- Official MATPOWER 8.1 case300 from commit `1a828c7af590714499284e36ee9c81273388c594`, original source SHA-256 `69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5`. Original signed loads, costs, shunts, branch parameters, bounds and initial input PG/QG/VG retained. No optimized values substituted as inputs.
- Two-copy construction uses the study's unchanged `configs/network-case300x2.json`: original bus231 (345kV) in A connects to original bus231 in B through two separate identical parallel circuits. Their parameters are r=0.002pu, x=0.019pu, b=1.127pu on100MVA;600MVA per circuit. These are provisional synthetic interconnection assumptions. One reference bus remains; the other former reference retains PV status. Both original load profiles remain unchanged.
- All411 original branch ratings are zero/unlimited; all822 copied interior branches remain unlimited. Thermal checks cover only the two new ties. Both ties are available. This run does not test outages or load-transfer stress. By symmetry, reference active transfer is approximately zero; each tie supplies approximately62.24MVAr from each end due to charging. This is not yet a useful active-transfer stress test.
- Existing local Seiole GridSFM fork at `1e5e3a1640b27768e3eaf32680184f26b407caab`, frozen pretrained Microsoft v1.1 checkpoint SHA-256 `f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831`. All model module hashes and actual dependencies saved. CPU FP32,4 torch threads, seed0, deterministic algorithms. No package install or backbone modification.
- Reference: existing Julia1.11.9 / PowerModels0.21.5 / Ipopt.jl1.14.0, polar AC-OPF, local solutions. Parsing uses `validate=false` followed only by per-unit conversion, avoiding default angle tightening. Custom standard ACP builder omits only disabled +/-360-degree angle constraints. Original zero ratings remain unlimited. No feasibility relaxation, load shedding or inferred ratings. Solver tolerances and options are explicit in `solve.jl`; both runs returned `LOCALLY_SOLVED`. This is not a global optimality certificate or a MATPOWER/MIPS execution.

## Validation and artifacts

Original-to-PowerModels parameter checks passed for costs, loads, shunts, branch orientation/impedance/taps/charging/ratings and generator/voltage bounds. Reversing native GridSFM electrical fields reproduces original parameters and reference physical evaluation. Reference branch flows match the independent evaluator. Maximum reference P/Q residuals are below2e-9MW/MVAr. Primary prediction thresholds:1e-3MW/MVAr balance and generator components,1e-4pu voltage,1e-3MVA rated-branch violation and1e-3degree active angle violation.

Prediction outputs are bitwise identical with/without accepted solution labels and on repeat inference. Full preprocessing retains112/225 cycles (expected m-n+1),411/824 branch outputs and both tie IDs. Shipped case500 control obtains0.5384% absolute cost error and0.0011116pu voltage MAE against its shipped labels; this sanity check is not an independent feasibility certification. Package disk caching was unavailable in the sandbox; in-memory caches worked.

`summary.json` / `summary.csv`: results; `environment.json`, `checks.json`, `provenance.json`: runtime, checks and hashes. Ignored local artifacts retain original source, input matrices, native model inputs, raw model outputs, predictions, reference solutions, per-case physical metrics and solver logs. They remain local, recoverable by the scripts and checksums; no checkpoint copied and no remote publication performed.

Reproduce on this host, from this run directory after retrieving the pinned `case300.m`:

```sh
python3 -B prepare.py
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B infer.py
/Users/ninadsonawane/julia/bin/julia --startup-file=no --project=/Users/ninadsonawane/workspace/research-dev/GridSFM/power_grid/US/topology_solver_pipeline solve.jl > solver.log 2>&1
python3 -B analyze.py
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B verify_inference.py
```

Interpretation: frozen v1.1 performs poorly on these two original-parameter nominal inputs despite a working supported-size control. case300 is below the documented500-bus training-size range; merely doubling to600 buses does not ensure similar electrical/input distributions. No attribution to a specific cause, general robustness claim, statistical comparison, speedup or adaptation benefit follows from these two points.
