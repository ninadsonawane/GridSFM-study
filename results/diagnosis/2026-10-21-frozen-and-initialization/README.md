# Frozen-model diagnosis and case300 initialization pilot

Executed 21 October 2026. Model/checkpoint/case300x2 parameters unchanged. Existing base results preserved byte-for-byte; no training, repaired prediction score, new 600-bus scenario, limit change or remote push.

## Outcome

No unresolved conversion/evaluator/mapping error was found. All three reference states pass the same original-parameter evaluator, including native-label export/reload for case300/600. Model-side physics mismatches are present, but do not fully explain the poor frozen dispatch. GridSFM-based initialization provided no benefit in this bounded pilot.

## A: same independent physical metrics

| Case | P max / median / p95,MW | Q max / median / p95,MVAr | Voltage / generator / rated-branch violation | Cost error |
|---|---|---|---|---|
| control-case500 | 114.016 / 6.03271 / 76.3568 | 71.5284 / 6.74397 / 37.0758 | 2.38419e-08pu / 3.41492e-05MW or MVAr / 18.5993MVA (728 rated) | 0.5384% |
| case300 | 3754.08 / 15.715 / 250.046 | 8937.97 / 73.7492 / 718.042 | 2.38419e-09pu / 4.76837e-06MW or MVAr / 0MVA (0 rated) | 54.9723% |
| case300x2 | 1141.64 / 9.17505 / 115.138 | 9376.45 / 53.7043 / 511.886 | 0pu / 9.53674e-06MW or MVAr / 0MVA (2 rated) | 17.2315% |

All raw predictions fail the joint criterion. Voltage/generator roundoff is within thresholds. Original case300 has no finite interior thermal limits; zero branch violation there is not a thermal certificate. The 600-bus case checks only its two synthetic rated ties. All states use the same thresholds:1e-3MW/MVAr balance/generator components,1e-4pu voltage,1e-3MVA branch,1e-3degree active angle violation.

Control identity: `GridSFM/model/samples/case500_goc.pyg.json` at model commit `1e5e3a1640b27768e3eaf32680184f26b407caab`, PGLib `pglib_opf_case500_goc.m` per shipped samples README. Exact JSON SHA256 and saved prediction hashes are in `provenance-A.json`. Reference source is that file’s shipped `solution`, metadata `LOCALLY_SOLVED`, objective454945.978311201. Its producing solver/version and PGLib revision are not recorded; no new solver provenance is invented. Reconstructed728 native branches all have finite ratings. The reloaded shipped reference has Pmax2.24e-8MW,Qmax1.50e-7MVAr and passes, unlike its prediction.

Existing conversion/label-independence/cycle/branch-order checks are linked by immutable hashes in `provenance-A.json`; those model checks were not rerun. `reference-export-reload-check.json` specifically decodes saved native labels through bus/generator source-row maps, converts radians→degrees and pu×100MVA, and evaluates against original matrices. State differences are3.55e-15 or smaller; both references pass. Physical evaluation computes source-oriented branch flows with system-base costs and shunts once; output bus/generator rows preserve maps.

`worst-buses.md` and `worst-buses.json` give the ten worst P and Q buses for each target, original IDs/area, predicted/reference voltage magnitude and angle, generator errors, bus shunts and every incident circuit’s r/x/tap/phase/charging. `nodal-residuals.csv` contains every bus. The worst case300 P/Q bus is238; the 600-bus worstP isA:235 and worstQ B:9001. Extreme errors concentrate around tiny-impedance branches235–238,37–9001 and231–237, but are not confined to them.

### Quantified model physics differences

`loss.py:190` uses max(r²+x²,1e-6). Three original branches are affected:37–9001 (21.52% series admittance retained),231–237 (37%),235–238 (40%); the 600-bus case has six. On the SAME saved prediction, this changes case300 maxP/Q from3754.08/8937.97 to1946.06/4433.47MW/MVAr, and600-bus from1141.64/9376.45 to645.46/2955.75. Even the exact feasible references falsely incur244MW maximum imbalance with this loss formulation. This is a confirmed evaluation/loss physics mismatch, not proof that it caused all pretrained prediction errors.

The forward static flow functions instead use r²+x²+1e-12. On the same predictions their maximum bus residual differences from exact physics are0.00788MW/0.02494MVAr (case300) and0.00339MW/0.04156MVAr (600)—far too small to explain the thousands of MW/MVAr. Actual torch loss and forward routines were checked in float64 against diagnostic complex-admittance calculations; disagreements<1.2e-10 in power units. The original exact matrices and exact metrics remain authoritative. No impedance or limit was changed.

`stress_features.py:155` treats zero/unlimited RATE_A as1e-9pu: the411/822 unlimited branches generate false maximum loading ratios8.48e10/8.94e10. These features feed the feasibility head after the voltage/generation outputs are computed, so the semantic mismatch undermines the classifier, but cannot itself explain the dispatch errors. No causal claim that the clamp explains the entire0.0 score is made. The graph-context admittance summary also floors r²+x² at1e-6: maximum |y| is clipped from2155.65 to1000pu on both targets (a feature statistic, not an exact physical flow). Actual saved FP32 forward-flow differences from exact physics are at most0.03194/0.04025MVA per branch; see `fp32-and-context-check.json` and `fp32_context.py`. Reactance safeguards at|x|<1e-10 in DC/PE do not activate on these inputs; no tap fallback activates on valid positive effective taps. Other numerical attention/normalization safeguards are not replacements for the exact electrical evaluator.

## B: five-point initialization pilot

| Load scale | Feasible successes D / G | Iterations D / G (each repeat) | Median end-to-end ms D / G | Accepted objective,cost units/hour |
|---|---|---|---|---|
| 0.90 | 3/3 / 3/3 | 20 / 39 | 133.50 / 268.88 | 625251 |
| 0.95 | 3/3 / 3/3 | 20 / 34 | 130.97 / 264.13 | 671938 |
| 1.00 | 3/3 / 3/3 | 22 / 25 | 138.16 / 236.93 | 719725 |
| 1.05 | 3/3 / 3/3 | 26 / 28 | 147.61 / 249.30 | 770082 |
| 1.10 | 0/3 / 0/3 | 197 / 209 | 690.90 / 770.67 | none |

D=PowerModels default primal starts; G=GridSFM-based primal starts. One warm-up per input/method then three timed repeats, alternating method order by repeat. Persistent model/server; fresh solver model per run. Four lower load levels reach matching local objectives (difference<7e-8cost units/hour) and exact feasibility in all repeats; maxima<2e-9MW/MVAr. At 1.10, both return `LOCALLY_INFEASIBLE`, with Q imbalance33.13/33.25MVAr. This is failure to obtain a feasible point, not a proof of network infeasibility. Its diagnostic objectives846779.48/846809.28 are retained in JSON/CSV with feasibility=false and are not operating costs. No fallback was used or timed.

Same ordinary polar AC-OPF, original topology/limits/costs; only signed Pd/Qd are uniformly scaled. Both methods use Ipopt tol1e-9,constr_viol_tol1e-10,acceptable_tol1e-9,max_iter1000,max_cpu_time180s,bound_relax_factor0. No reference solutions appear in model inputs. At1.00 freshly timed predictions exactly match the saved predictions. Raw physical/cost errors per load are in `pilot-raw-prediction-summary.json`; raw feasibility remains separate from final solver feasibility. No accepted cost reference exists at 1.10.

GridSFM initialization clips only Vm/Pg/Qg to the original boxes (at nominal, oneVm by2.38e-9pu and fiveQg by at most4.77e-6MVAr), anchors angles to the original slack, and initializes branch primal powers by exact pi-model flows from those voltages. No PF projection or repair. Default starts are Vm=1,angles=0,Pg/Qg/branch flows=0 subject to bounds/fixed variables and normal Ipopt interior pushes. Full actual JuMP starts and Ipopt iteration-zero traces are saved for every run. Fresh-process probes additionally call `GetIpoptCurrentIterate` to capture the actual internal unscaled primal, verifying consumption beyond the start-value buffer. Nominal GridSFM internal shifts are up to0.0012pu Vm,0rad angle,0.01pu Pg and0.012pu Qg due to fixed variables/interior pushes; recorded iteration-zero objective324330.435 differs markedly from the default. `initialization-consumption-evidence.json` holds both complete vectors.

End-to-end includes input read, GridSFM conversion/JSON/preprocessing/inference where applicable, clipping/branch-start construction, server transport, MATPOWER parse/per-unit conversion, solver model build, solve and raw-result serialization. Independent post-solve assessment and report generation are outside the timer. Setup/import/checkpoint/JIT costs are separate, not amortized into warm results. Topology caches are warm; memory-only fallback is disclosed. Timings are a local pilot, not a general speedup benchmark. Per-run timings/ranges/iterations/failures are in CSV/JSON.

### Cold first calls

- default: Julia fresh-process startup 1.405s; first end-to-end call 3.320s. Python shared-harness imports 0.926s; checkpoint load 0.189s (the shared harness loads it even for default, so do not charge this as an intrinsic default-solver requirement).
- gridsfm: Julia fresh-process startup 1.406s; first end-to-end call 3.418s. Python shared-harness imports 0.923s; checkpoint load 0.189s (the shared harness loads it even for default, so do not charge this as an intrinsic default-solver requirement).

The earlier warm-up first-call records are also retained, but their sequential calls are not a matched cold comparison. Cold probes use separate fresh Python/Julia processes and the same nominal input. Initial instrumentation mistakenly iterated a JuMP DenseAxisArray with `pairs`;40 pre-solve harness failures were retained under attempt141507 and its archived source/log, then the logging implementation was corrected. These are not AC-OPF convergence failures and are excluded from timing summaries. The successful timed attempt is141557.

## Reproduce and inspect

Runtime: existing Python 3.11.17 / torch2.8.0 / PyG2.8.0.post1 / NumPy2.4.6 / SciPy1.17.1; CPU, 4 torch threads; Apple M5 Pro, 18 CPU cores,64 GB RAM; Julia1.11.9,PowerModels0.21.5,Ipopt.jl1.14.0; BLAS, 1 thread. Checkpoint SHA256 `f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831`; study starting commit `c74c2bd1685108f7c991274ef7a09d4c52e8f2fb`. Actual scripts and hashes accompany results; no installed model code changed.

From this artifact directory, using the existing model environment (commands produce new attempt IDs and retain old solver records):

```sh
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B diagnose.py
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B forward_check.py
python3 -B check_reference_export.py
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B pilot.py
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B pilot.py cold-default
/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python -B pilot.py cold-gridsfm
```

`pilot.py` launches `solver_server.jl` using the existing GridSFM Julia project. `solver-server-timed.jl` preserves the exact timed-server version; the current server adds actual-internal-iterate capture only for cold probes and otherwise uses the same path. To reproduce a preserved result without overwriting report-level files, run a copy in a new directory. `report.py` is bound to the recorded successful attempt for archival reporting, not a generic new-run selector.

`provenance-A.json`, `provenance-final.json` and `artifact-index.json` contain source/input/checkpoint hashes, commands and paths. Raw records retain original execution paths under `/private/tmp/gridsfm-diagnosis-20261021`; the identical `pilot/` relative paths in this saved artifact directory are their durable local copies. `.gitignore` keeps source-derived input matrices, raw records and large outputs local. No artifact was pushed or externally shared. Existing checks are at `../../inference/2026-10-21-base-cases/checks.json`, references/round-trip code alongside them.

Decision evidence: retain frozen-model failure as observed; the small-impedance loss floor and zero-rating stress semantics need separate treatment in any later methodological work. This pilot supports neither adaptation nor solver acceleration, and supplies no reason to expand600-bus scenarios now.
