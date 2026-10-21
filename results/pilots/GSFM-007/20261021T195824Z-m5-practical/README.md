# GSFM-007 — Experiment10 practical AC-OPF value

Three optimizer seeds per network, one fixed50/10 split each; bounded1500-update adaptation, released source-defined objective and selection. Fresh fixed candidates follow a frozen protocol; original physical parameters and strict checker unchanged.

## Outcome — COMPLETE, 22 October 2026

All six sequential fits reached 1,500 updates (9,000 total) within 60.23 fit-minutes. All 180 fixed confirmation candidates were retained; 179 have independently verified local references. Evaluation completed 4,860 timed requests plus 18 excluded warm-ups, three interleaved timing repeats and 240 prespecified control substitutions. Verification re-scored 12,960 saved states and passed. No extra training followed.

| Network | Method | Native PF convergence | Native PF full feasibility | Final quality / all requests | Median / p95 online ms | Fallbacks |
|---|---|---:|---:|---:|---:|---:|
| case300 | conventional | N/A | N/A | 267/270 | 158.68 / 184.53 | 0 |
| case300 | frozen | 0/270 | 0/270 | 267/270 | 305.67 / 337.54 | 270 |
| case300 | ridge | 270/270 | 0/270 | 267/270 | 163.06 / 184.86 | 3 |
| case300 | FT-s11-selected | 270/270 | 0/270 | 267/270 | 262.50 / 285.59 | 3 |
| case300 | FT-s22-selected | 270/270 | 0/270 | 267/270 | 261.88 / 285.49 | 3 |
| case300 | FT-s33-selected | 270/270 | 0/270 | 267/270 | 264.06 / 292.17 | 3 |
| pglib118 | conventional | N/A | N/A | 270/270 | 83.64 / 95.45 | 0 |
| pglib118 | frozen | 270/270 | 0/270 | 270/270 | 154.64 / 169.68 | 0 |
| pglib118 | ridge | 270/270 | 0/270 | 270/270 | 84.95 / 99.86 | 0 |
| pglib118 | FT-s11-selected | 270/270 | 0/270 | 270/270 | 148.93 / 161.92 | 0 |
| pglib118 | FT-s22-selected | 270/270 | 0/270 | 270/270 | 149.87 / 164.17 | 0 |
| pglib118 | FT-s33-selected | 270/270 | 0/270 | 270/270 | 147.60 / 161.35 | 0 |

Quality requires original-parameter feasibility, completion within the common 30-second deadline and signed verified-local-reference cost gap <=0.1%. Per method, 270 requests represent 90 unique scenarios with three timing repeats. Counts are not 270 independent scenarios. All methods reached 89/90 unique-case quality on case300 and 90/90 on PGLib118. The common unresolved case300 input is `spatial-027`, SHA256 `20ab94cbe4f027eed38a926c78f1dd0dde77adbe274dca5c9c17090f76078ceb`. Its reference solver returned `LOCALLY_INFEASIBLE`; this is a local numerical status, not a proof of physical infeasibility. All nine online arms failed on it in all three repeats. It remains in the denominator, with reference-dependent costs N/A. [Failed requests](failed-requests.json).

## Five findings

1. **SUPPORTED — Adaptation enabled case300 PF completion, but this gain was network dependent.** Frozen case300 completed 0/90 unique inputs versus 90/90 for every selected FT seed and ridge. On PGLib118, frozen already completed 90/90, so adaptation added no convergence coverage. See [pooled rows](pooled-summary.csv), [all slice/stage rows](stage-summary.csv) and [learning curves](figures/01-learning-curves.png).
2. **CONTRADICTED — PF convergence did not establish operating feasibility.** Every native PF method had 0/90 fully feasible outputs on both networks. For case300 selected FT, median scenario-wise maximum Qg excess was 34.60/41.60/44.08 MVAr (seeds11/22/33), versus ridge16.68 MVAr. On PGLib118 it was 28.35/28.43/50.15 MVAr, versus ridge7.83 MVAr. Slack recovery, reactive limits, voltage limits and rated branches must still be checked. Case300 thermal feasibility is N/A because all original ratings are unlimited. [Physical distributions](summary.json), [original-ID locations](worst-locations.json).
3. **CONTRADICTED — Adaptation did not improve complete-solve speed or reliability in this CPU setup.** Final quality coverage was identical across all methods. At joint comparable quality, selected FT added mean102.23–104.75 ms on case300 and62.64–64.38 ms on PGLib118 versus conventional initialization; every corresponding paired95% interval excluded zero saving. Ridge also added3.82 ms and2.34 ms respectively. Thus no pooled measured amortization benefit exists, even before charging offline adaptation. Some slice-conditional ridge estimates are positive and are labeled conditional in the detailed file; they do not establish overall utility. [Paired intervals and denominators](paired-runtime.json), [online stage times](figures/03-online-stages.png).
4. **SUPPORTED, bounded intervention — Control-voltage substitution changes Q violations, with a voltage trade-off.** On the fixed first10 ordinary IDs per network ×3 seeds, replacing FT voltage controls with ridge controls changed maximum Qg excess by a median−4.868 MVAr on case300 and−17.847 MVAr on PGLib118. PGLib118 maximum voltage excess increased by median0.000889 pu. Dispatch-only substitution had much smaller pooled Q effect (−0.241/−0.000392 MVAr), while branch effects and seed effects varied. These are medians of paired changes, not differences of medians; the experiment holds PQ initial magnitudes at1pu. It supports a control-level trade-off, not a universal representation-level cause or uniform ridge superiority. [Paired interventions](factorial-paired-effects.json), [summary](factorial-summary.json), [figure](figures/02-control-substitutions.png).
5. **SUPPORTED locally; broader transfer INCONCLUSIVE — Redistribution at fixed demand totals stressed completed controls.** Spatial variants moved399.82–704.66 MW and138.17–225.61 MVAr on case300;73.97–97.48 MW and24.17–36.21 MVAr on PGLib118 (half the sum of absolute nodal changes, so source/sink transfer is counted once). Median paired Q-excess increases for selected FT seeds were50.86–56.09 MVAr and3.55–6.39 MVAr respectively. Final solver quality lost only the common unresolved case300 variant, for every method. This isolates load redistribution under unchanged topology/totals, not geographical/topological generalization. [Input manifest](confirmation/manifest.json), [paired spatial records](spatial-pairs.json).

These findings support the paper question “Does adaptation improve the complete AC-OPF workflow, or mainly enable PF completion?” They provide a reproducible limitation under a declared budget; they do not establish novel architecture, global optimality, universal transfer failure or a publication guarantee. Only two fixed topologies, one50/10 split per network and three optimizer seeds were tested. Neither network is proven unseen in pretraining. The30-epoch CPU/batch1 run is not the published400-epoch training budget. Experiment9 used a different selection score and remains development evidence.

## Final common-solver stage (all online requests)

| Network | Method | Slice | Feasible / requests | Quality / all requests | Median / p95 total seconds | Fallbacks |
|---|---|---|---|---|---|---|
| case300 | FT-s11-final | higher_load | 90/90 | 90/90 | 0.2691/0.2836 | 0 |
| case300 | FT-s11-final | ordinary | 90/90 | 90/90 | 0.2557/0.2810 | 0 |
| case300 | FT-s11-final | spatial | 87/90 | 87/90 | 0.2590/0.3246 | 3 |
| case300 | FT-s11-selected | higher_load | 90/90 | 90/90 | 0.2680/0.2872 | 0 |
| case300 | FT-s11-selected | ordinary | 90/90 | 90/90 | 0.2589/0.2835 | 0 |
| case300 | FT-s11-selected | spatial | 87/90 | 87/90 | 0.2611/0.2819 | 3 |
| case300 | FT-s22-final | higher_load | 90/90 | 90/90 | 0.2641/0.2789 | 0 |
| case300 | FT-s22-final | ordinary | 90/90 | 90/90 | 0.2591/0.2889 | 0 |
| case300 | FT-s22-final | spatial | 87/90 | 87/90 | 0.2699/0.3230 | 3 |
| case300 | FT-s22-selected | higher_load | 90/90 | 90/90 | 0.2661/0.2823 | 0 |
| case300 | FT-s22-selected | ordinary | 90/90 | 90/90 | 0.2566/0.2874 | 0 |
| case300 | FT-s22-selected | spatial | 87/90 | 87/90 | 0.2627/0.2912 | 3 |
| case300 | FT-s33-final | higher_load | 90/90 | 90/90 | 0.2675/0.2811 | 0 |
| case300 | FT-s33-final | ordinary | 90/90 | 90/90 | 0.2589/0.2794 | 0 |
| case300 | FT-s33-final | spatial | 87/90 | 87/90 | 0.2651/0.2868 | 3 |
| case300 | FT-s33-selected | higher_load | 90/90 | 90/90 | 0.2692/0.2838 | 0 |
| case300 | FT-s33-selected | ordinary | 90/90 | 90/90 | 0.2576/0.2820 | 0 |
| case300 | FT-s33-selected | spatial | 87/90 | 87/90 | 0.2617/0.3093 | 3 |
| case300 | conventional | higher_load | 90/90 | 90/90 | 0.1661/0.1872 | 0 |
| case300 | conventional | ordinary | 90/90 | 90/90 | 0.1525/0.1694 | 0 |
| case300 | conventional | spatial | 87/90 | 87/90 | 0.1562/0.1913 | 0 |
| case300 | frozen | higher_load | 90/90 | 90/90 | 0.3135/0.3349 | 90 |
| case300 | frozen | ordinary | 90/90 | 90/90 | 0.3014/0.3228 | 90 |
| case300 | frozen | spatial | 87/90 | 87/90 | 0.3039/0.3398 | 90 |
| case300 | ridge | higher_load | 90/90 | 90/90 | 0.1660/0.1798 | 0 |
| case300 | ridge | ordinary | 90/90 | 90/90 | 0.1579/0.1840 | 0 |
| case300 | ridge | spatial | 87/90 | 87/90 | 0.1637/0.1922 | 3 |
| pglib118 | FT-s11-final | higher_load | 90/90 | 90/90 | 0.1511/0.1640 | 0 |
| pglib118 | FT-s11-final | ordinary | 90/90 | 90/90 | 0.1446/0.1579 | 0 |
| pglib118 | FT-s11-final | spatial | 90/90 | 90/90 | 0.1508/0.1641 | 0 |
| pglib118 | FT-s11-selected | higher_load | 90/90 | 90/90 | 0.1460/0.1562 | 0 |
| pglib118 | FT-s11-selected | ordinary | 90/90 | 90/90 | 0.1441/0.1567 | 0 |
| pglib118 | FT-s11-selected | spatial | 90/90 | 90/90 | 0.1508/0.1659 | 0 |
| pglib118 | FT-s22-final | higher_load | 90/90 | 90/90 | 0.1459/0.1649 | 0 |
| pglib118 | FT-s22-final | ordinary | 90/90 | 90/90 | 0.1493/0.1590 | 0 |
| pglib118 | FT-s22-final | spatial | 90/90 | 90/90 | 0.1478/0.1651 | 0 |
| pglib118 | FT-s22-selected | higher_load | 90/90 | 90/90 | 0.1486/0.1658 | 0 |
| pglib118 | FT-s22-selected | ordinary | 90/90 | 90/90 | 0.1455/0.1570 | 0 |
| pglib118 | FT-s22-selected | spatial | 90/90 | 90/90 | 0.1505/0.1666 | 0 |
| pglib118 | FT-s33-final | higher_load | 90/90 | 90/90 | 0.1466/0.1649 | 0 |
| pglib118 | FT-s33-final | ordinary | 90/90 | 90/90 | 0.1458/0.1571 | 0 |
| pglib118 | FT-s33-final | spatial | 90/90 | 90/90 | 0.1508/0.1638 | 0 |
| pglib118 | FT-s33-selected | higher_load | 90/90 | 90/90 | 0.1498/0.1624 | 0 |
| pglib118 | FT-s33-selected | ordinary | 90/90 | 90/90 | 0.1444/0.1570 | 0 |
| pglib118 | FT-s33-selected | spatial | 90/90 | 90/90 | 0.1488/0.1642 | 0 |
| pglib118 | conventional | higher_load | 90/90 | 90/90 | 0.0855/0.0948 | 0 |
| pglib118 | conventional | ordinary | 90/90 | 90/90 | 0.0820/0.0948 | 0 |
| pglib118 | conventional | spatial | 90/90 | 90/90 | 0.0837/0.0956 | 0 |
| pglib118 | frozen | higher_load | 90/90 | 90/90 | 0.1554/0.1671 | 0 |
| pglib118 | frozen | ordinary | 90/90 | 90/90 | 0.1507/0.1649 | 0 |
| pglib118 | frozen | spatial | 90/90 | 90/90 | 0.1575/0.1732 | 0 |
| pglib118 | ridge | higher_load | 90/90 | 90/90 | 0.0834/0.0988 | 0 |
| pglib118 | ridge | ordinary | 90/90 | 90/90 | 0.0845/0.1034 | 0 |
| pglib118 | ridge | spatial | 90/90 | 90/90 | 0.0874/0.0994 | 0 |

Full raw/PF/final-stage distributions including separate P/Q bounds, voltage/thermal/angle violations, signed feasible cost gaps and control errors: summary.json. All per-request metrics and failures are in per-request-metrics.csv and failed-requests.json; full local records remain in online-rows.jsonl; each repeat is paired and method order interleaved. Three repeats are timing measurements, not independent scenarios.

## Protocol and interpretation

The actual closed_forward function is extracted from pinned train_elastic.py and executed with the study store adapter. Training weights: elastic rho_g=rho_h10, control32, merit170; selection uses mean elastic diagnostic loss +32×mean control loss, excluding merit as in released eval_elastic/vsel. Ten cold validation closures must all converge. Source-defined reductions/top-k/masks/cost scale are retained; CPU/batch1 and serial closure are declared accommodations. LR horizon400epochs; PF tolerance reaches1e-8 at epoch25 of30. No LR/penalty search or accuracy-based duration selection. Experiment9 used a different selection rule and remains historical development evidence.

Ridge predicts all online Pg, including slack, and control-bus Vm. Fixed columns and intercept/scalers use training only. Three alpha candidates are selected using the same score and PF-convergence eligibility gate. Controls remain unclipped. Ridge has no raw full-state prediction; PQ magnitudes1pu and angles/Qg placeholders are only initialization scaffolding and are not reported as raw physical predictions. Native neural completion starts from its full predicted voltage profile; this additional PQ initialization information is disclosed. The2×2 factorial diagnostic holds PQ initial magnitudes at1pu for all four swaps, isolating dispatch/control-voltage substitutions within that diagnostic.

PF completion uses the native +1e-12 admittance and native stored coefficient precision, max40 Newton steps, backtracking and DC cold angles. It does not enforce Q-limit PV/PQ switching. Slack P and generator Q are recovered without clipping; raw/PF/refined outputs remain separate. The reference-control gate is an ORACLE diagnostic only.

External refinement is our common original-parameter PowerModels ACP/Ipopt solve, not unavailable upstream N4. Every ordinary primal OPF variable is free; controls are starts only. Fresh model instances use identical default dual initialization, no reference duals. Same tol1e-9/constr_viol_tol1e-10/acceptable_tol1e-9/bound_relax_factor0/max_iter1000. One30s online alarm/watchdog covers preprocessing, inference, native PF, solver, feasibility validation and fallback. Failed PF invokes default; failed warm OPF gets at most one default retry within remaining time. Default starts and actual internal Ipopt iteration-zero points were verified on10 pilot scenarios with deliberate distinct label-free starts. Physical thermal/angle limits on PGLib118 are independently checked and logged in the numerical model.

All fixed nonexcluded candidates are retained, including missing references; solver failure is UNKNOWN. Cases with no verified reference can still count as feasible but not reference-dependent quality. Primary quality is independent feasibility within30s and signed local-reference cost gap<=0.1%. Local optima are not global certificates. Negative feasible gaps may improve the reference.

Fresh input JSON/schema/graph preparation is included in each predictor request; models and topology caches are resident. Reference data never enter features or starts. Label generation, training/tuning, initial graph setup, model loading and Julia startup are offline/cold costs reported separately. Paired-runtime intervals bootstrap scenario families after collapsing timing repeats, retaining ordinary/spatial pairing. Break-even is computed only for positive mean saving at jointly successful quality and is conditional on that subset. No forward-only speedup claim.

## Reproducibility

Source protocol: docs/experiments/GSFM-007.md at4fb28fc. Model code517a07531ea55a11bd81a89a6c6879695a2ba4b4; base checkpoint9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7. PGLib118 source b1af0833849040c04babc3700631cff0d9afa66b79c5d3e13ae79bdf516cec78;35fixed-P synchronous condensers retained. Original case300 RATE_A=0 means thermal N/A. Neither benchmark is proven unseen during pretraining.

Run: /Users/ninadsonawane/workspace/research-dev/GridSFM-study/results/pilots/GSFM-007/20261021T195824Z-m5-practical. Scripts: experiments/gsfm007/. Execute with GSFM007_RUN set to a NEW durable run directory and GSFM007_START_UTC set to actual UTC start; never overwrite this completed run. Frozen scripts/config/data/checkpoint hashes are in freeze.json; all local states/checkpoints have SHA256 inventory and paths. Old Results and environment remain untouched.

Commands executed (existing isolated Python environment):
```bash
GSFM007_RUN=/Users/ninadsonawane/workspace/research-dev/GridSFM-study/results/pilots/GSFM-007/20261021T195824Z-m5-practical /private/tmp/gsfm007-20261021T195824Z/venv/bin/python -B experiments/gsfm007/train.py
GSFM007_RUN=/Users/ninadsonawane/workspace/research-dev/GridSFM-study/results/pilots/GSFM-007/20261021T195824Z-m5-practical /private/tmp/gsfm007-20261021T195824Z/venv/bin/python -B experiments/gsfm007/confirm.py
GSFM007_RUN=/Users/ninadsonawane/workspace/research-dev/GridSFM-study/results/pilots/GSFM-007/20261021T195824Z-m5-practical /private/tmp/gsfm007-20261021T195824Z/venv/bin/python -B experiments/gsfm007/analyze.py
```

Five findings, figures and verification are complete. No LoRA, scratch, paid compute, MPS port, case300x2, submission or additional experiment.

## Offline, startup and selection audit

[Fit status](fit-status.csv) and [all180 validation decisions](selection-audit.csv) retain each seed. Selected updates case300:1250/1400/1450; PGLib118:1050/1350/1000 (seeds11/22/33). All selected endpoints passed the10/10 cold validation gate. All fixed-final1500-update diagnostics were evaluated separately. Ridge selected alpha100 on both networks. Its three-candidate tuning took0.226 seconds on case300 and0.136 seconds on PGLib118 (full values in ridge summaries).

Six fits including validation/checkpoints took3614.03seconds (60.23min), with sampled process-tree RSS below1GiB and minimum sampled available memory above33GiB; these are sampled readings, not a continuous OS peak bound. All15,146,823 model parameters have requires_grad=True; the feasibility head had no gradient under this regression objective, as retained in parameter-audit.json. No classifier training or LoRA.

PGLib train/validation generation accepted60/60 attempts, label solve time9.51seconds and total preparation12.07seconds. Case300's existing labels are reused sunk work, not free data; original label records are included by path/hash in freeze.json. Fresh confirmation reference generation is evaluation-only cost. Resident neural checkpoint loads cost0.219–0.365seconds per model; Julia process ready1.381seconds including1.039seconds imports. The first reference solve took3.604seconds on case300, including cold solver compilation; it is excluded from resident online timing. These components are separate cold costs, not a single measured fresh-machine cold end-to-end benchmark. See model-loading.json, solver-startup.json, confirmation/manifest.json and confirmation/case300-cache-cost.json and confirmation/pglib118-cache-cost.json. Setup included a retained namespace-binding failure before the passing gate (gate-attempt1-namespace.log); all six scientific fits completed without restart. [Phase timing](post-training-phases.json), [environment](environment.json), [delivery and retrieval map](delivery.json).

## Artifact access

Tracked compact outputs include per-request metrics, all162 stage rows, selection audit, seed status, frozen provenance, solver-start consumption checks, original-ID localization, failures and three PNG/PDF figures. Large input matrices, full states and resumable model/optimizer checkpoints remain ONLY at the durable local run path above. [Artifact inventory](artifact-inventory.json) gives relative paths, byte sizes and SHA256 for every retained run file; it excludes itself and mutable delivery metadata. No cloud backup of large artifacts is implied. Base/model sources and old labels are external dependencies explicitly hashed in freeze.json.

To reproduce from source, verify the pinned sources/base checkpoint and dependencies first, set GSFM007_RUN to a new directory and GSFM007_START_UTC to the actual UTC start, then run prepare.py, gate.py, train.py, confirm.py, analyze.py, verify.py in that order with the isolated Python environment; render figures.py with the separate plotting runtime. Never rerun into this completed directory. The gate/wrapper proof and freeze are mandatory before confirmation. The execution fit code was5447c790e40291ad1e28f4c252049cd91b3e584f; confirmation/analysis code2603c7fc909c86a58123dd0f8126ddf1ffca5468. Hashes of actual executed frozen files are authoritative; delivery-only tables/formatting were added afterward.
