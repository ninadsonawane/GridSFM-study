# GSFM-006 — Experiment 9: newer pipeline on original case300

**Status:** 9A compatibility COMPLETE with quantified physics discrepancy; 9B frozen evaluation COMPLETE; 9C 200-update adaptation COMPLETE; 9D shift checks COMPLETE, refinement NOT RUN (implementation absent).

This is a development comparison on previously viewed cases, not a fresh final test or an isolated denominator ablation. All physical metrics use unchanged original equipment and strict tolerances.

## Ordinary development comparison (30/30 cases)

| Method | Median max P MW | Median max Q MVAr | PF converged | Strict feasible | Raw cost error median % |
|---|---:|---:|---:|---:|---:|
| frozen raw | 2681.16 | 2997.98 | N/A | 0/30 | 50.8997 |
| frozen + PF | 1003.57 | 1148.11 | 0/30 | 0/30 | 29.3608 |
| selected raw | 9667.89 | 6230.35 | N/A | 0/30 | 0.7521 |
| selected + PF | 0.00117571 | 0.0110974 | 30/30 | 0/30 | 0.1566 |
| final raw | 9667.89 | 6230.35 | N/A | 0/30 | 0.7521 |
| final + PF | 0.00117571 | 0.0110974 | 30/30 | 0/30 | 0.1566 |
| old frozen | 4331.32 | 10519.6 | N/A | 0/30 | 56.5431 |
| ridge | 12.4632 | 6.09805 | N/A | 0/30 | 0.1049 |
| old E seed11 | 253.83 | 157.902 | N/A | 0/30 | 1.1489 |
| old E seed22 | 281.196 | 194.828 | N/A | 0/30 | 2.3701 |
| old E seed33 | 111.697 | 124.521 | N/A | 0/30 | 0.9909 |
| hybrid ridge + PF | 0.00137109 | 0.0110331 | 30/30 | 0/30 | 0.0017 |
| hybrid E-11 + PF | 0.00154776 | 0.0110714 | 30/30 | 0/30 | 0.0749 |
| hybrid E-22 + PF | 0.00171479 | 0.0105037 | 30/30 | 0/30 | 0.4977 |
| hybrid E-33 + PF | 0.00174408 | 0.0108105 | 30/30 | 0/30 | 0.1549 |
| conventional AC-OPF | 1.64704e-11 | 7.55067e-11 | N/A | 30/30 | 0.0000 |

Costs on infeasible outputs are diagnostic, not achieved operating costs. Conventional objective is a validated local AC-OPF reference, not a globally certified optimum. Full statistics and violation counts: summary.json; all states and failures retained in evaluation/.

## What ran and what the reference audit means

CPU FP32 backbone, FP64 SuperLU closure;15,146,823 parameters; strict checkpoint reload. Same 50/10 training/validation examples. One full-regression fit, seed11, 200 updates in 107.31s; selected update 200. Original epochs/horizons retained:200 updates are 4 epochs, closure tolerance reaches 0.013335214 pu, rather than the final scheduled 1e-8 pu. This is a short adaptation pilot, not the full 400-epoch published recipe.

The old converter needed explicit availability columns for the new schema; all are actual active rows. No ratings, impedances, limits, costs, negative loads or reference values were altered. Native new preparation replaces old PE inputs and uses the released normalized backbone plus sigmoid control clipping. Raw theta/Qg heads are reported but discarded by closure. Controls are generator P and PV/slack V; closure solves non-slack theta and PQ V, then slack P and PV/slack Q are recovered. No reference controls initialize prediction evaluation. Reference controls appear only in the separate ORACLE diagnostic.

Five verified TRAINING references: exact original equations remain near1e-10MW/MVAr; old stock residuals210.91–245.06MW /190.05–194.30MVAr. New +1e-12 operator at original precision gives0.0009996–0.0011535MW /0.0007684–0.0007887MVAr. With native FP32 parameter storage it gives0.001150–0.001507MW /0.010988–0.011076MVAr. All 5oracle PF solves converge, but 0/5pass strict original-physics checks. This is an identified implementation approximation, not evaluation-path evidence that exact feasible references were wrong. Original-precision oracle isolation is in checks/original-precision-oracle.json; it is not substituted into the main pipeline.

Export adapter: the release contains closure.py but omits the referenced evaluate_model/completion.py module. Our small state exporter recovers bus injections with the unmodified closure Ybus and allocates Q and slack P affinely by generator capability range; no clipping or additional solve. case300 has no multiple-generator buses (verified in checks/semantic-roundtrip.json), making this allocation unique here. No PV/PQ Q-limit switching is performed. Bound violations remain scored. PF convergence is not full OPF feasibility.

## Training, timing and scope

Recipe: case500_goc_finetune.yaml, rho_g=rho_h10, control weight32, merit170, Adam1e-4, clipping1, no weight decay. Original LR400epoch and closure25epoch schedules retained; batch1/serial closure and seed11 are disclosed accommodations. Validation score = aggregate Pg absolute error / aggregate absolute reference Pg ×100 +1000×PV/slack voltage MAE; exact ties prefer earlier update. Only validation selects checkpoints; all 50-step and final endpoints saved. No tuning from evaluation results.

Selected and final endpoints: 200 and200; fit memory and traces in training-summary.json /training-trace.jsonl. Loss at training tolerance and strict original-physics evaluation are different quantities.

One excluded warmup and3 sequential repeats×30ordinary cases per frozen/selected pipeline and conventional solver. See timing-summary.json; preprocessing is recorded separately in each evaluation row. Cached timings exclude parsing/preparation; timing-e2e.json separately repeats fresh preprocessing + model + completion for all 3 × 30 cases. End-to-end preprocessing includes input and reference JSON reads, schema conversion and graph preparation; reference arrays are never model features. Cold import/model loading are in cold-start.json; excluded warmups are retained in timing.json and timing-e2e.json; conventional Julia import and first solve are retained separately. No solver speedup comparison is claimed because the approximate pipeline does not deliver comparable feasibility. Conventional baseline: same original matrices, PowerModels ACP/Ipopt tol1e-9, constr_viol_tol1e-10, acceptable_tol1e-9, bound_relax_factor0, max_iter1000, max_cpu_time180, BLAS1. N4 refinement is NOT RUN because its documented implementation is absent; no other solver substituted.

Optional shifts use the existing28 spatial and30 higher-load cases, with two historical unknown spatial failures unchanged and not replaced. See shift-summary.json. Optional ridge/E+PF hybrids are labeled separately; they reuse saved controls and cannot be attributed to the newer model.

## Reproducibility and artifacts

Source: https://github.com/lukebhan/gridsfm/tree/517a07531ea55a11bd81a89a6c6879695a2ba4b4. Base checkpoint only: https://huggingface.co/lukebhan/gridsfm/resolve/970a413556fd1dc8c843cafdb03b01f9f8ef6f44/base/gridsfm_open_v2.pt . Checkpoint SHA2569e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7. Source, scripts, case/reference and config hashes in provenance.json, freeze.json, data-hashes.json. Source checkout clean; old environment and completed results preserved. New dependencies reused read-only through an isolated venv; exact installed versions in environment.json.

Executed commands (preserve this run; use a new directory/run identity for replay):
```bash
/private/tmp/gsfm006-20261021T171629Z/venv/bin/python -B /private/tmp/gsfm006-20261021T171629Z/code/gate.py
/private/tmp/gsfm006-20261021T171629Z/venv/bin/python -B /private/tmp/gsfm006-20261021T171629Z/code/run.py
/private/tmp/gsfm006-20261021T171629Z/venv/bin/python -B /private/tmp/gsfm006-20261021T171629Z/code/extra_audit.py
/private/tmp/gsfm006-20261021T171629Z/venv/bin/python -B /private/tmp/gsfm006-20261021T171629Z/code/solver_timing.py
/private/tmp/gsfm006-20261021T171629Z/venv/bin/python -B /private/tmp/gsfm006-20261021T171629Z/code/semantic_audit.py
/private/tmp/gsfm006-20261021T171629Z/venv/bin/python -B /private/tmp/gsfm006-20261021T171629Z/code/timing_e2e.py
/private/tmp/gsfm006-20261021T171629Z/venv/bin/python -B /private/tmp/gsfm006-20261021T171629Z/code/report.py
```

Working local artifacts: /private/tmp/gsfm006-20261021T171629Z/results. Permanent delivered paths recorded in delivery.json. Compact tables/checks/scripts committed; large checkpoints and full matrices are local only, indexed by SHA256. No paid compute, connected case300s, other topologies, LoRA, scratch, sweeps, email or submission.

## Five findings and next decision

1. The newer public model and differentiable SuperLU closure ran on the M5 CPU without a backend port. Strict reload, original row mappings, finite gradients and a disposable optimizer-step/reload passed. One 200-update fit completed in 107.31 seconds; selected and final are the same update 200. Native model/closure data precision and dependencies are disclosed.
2. The new equations grade references much more closely than the old clamp, but are not exact original physics. All five native oracle closures converged, yet none met the original 1e-3MW/MVAr criterion. Original-precision isolation passes only 1/5; additive epsilon alone can exceed 1e-3MW. We keep the checker and source network unchanged.
3. Adapted controls plus PF converged on 30/30 ordinary, 28/28 spatial and 30/30 higher-load cases. Full feasibility was 0 on every slice. Ordinary median maximum generator violation was 62.37MW/MVAr and voltage violation 0.009489pu: failure is not just the numerical balance floor. Frozen plus PF converged 0/30 ordinary. Raw theta/Qg are not trained as closure controls and their full-state residuals worsen; do not treat this as the intended pipeline output.
4. Small adaptation clearly helped obtain PF-solvable controls relative to the newer frozen model. It did not establish a useful foundation-model advantage: ridge plus the identical PF closure also converged 30/30, with lower median maximum generator violation 5.34MW/MVAr, voltage violation 0.000729pu and diagnostic cost error 0.00175% (versus 0.15663% for the adapted model). Both remain infeasible.
5. Do not scale up training on this evidence. First resolve whether exact-parameter completion and explicit generator/voltage-limit handling can yield useful solutions under a separately agreed protocol, with ridge+completion retained. N4 projection/refinement was unavailable in the pinned release. This pilot does not reproduce the complete paper, prove novelty or justify a speedup claim. Then STOP.

Timing: the three ordinary repeat medians were 0.11529–0.11577s/case for adapted preprocessing+inference+PF, versus 0.15003–0.16932s/case for validated conventional AC-OPF. These produce different feasibility outcomes, so the numbers are descriptive and do not establish solver acceleration. Peak sampled fit RSS 0.783GiB; available memory stayed above 37GiB during the recorded fit. Cold model and Julia startup costs are retained separately.
