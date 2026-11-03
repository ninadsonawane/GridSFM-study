# GridSFM independent loading study

Completed local benchmark and research draft, 4 November 2026 IST. Start with [the five-page paper](paper/GridSFM-five-page-draft.pdf), [the full baseline tables](paper/baseline-tables.md), and [the methodology](paper/methodology.md).

## Verified outcome

- 59 unique inputs: 39 main loading inputs, 14 integrated case-3 inputs, six final sensitivity inputs.
- 57 independently checked AC references and two UNKNOWN references. The combined 110% case300 and two-copy points remain UNKNOWN after default and flat starts; no global infeasibility claim.
- 59/59 DC own-law passes. Native DC Q, voltage, apparent thermal and full AC feasibility are N/A.
- 0/118 native frozen model states jointly AC-feasible.
- Evaluator perturbation tests and independent saved-state crosschecks passed. Maximum accepted-reference balance residual: 6.253e-9 MW/MVAr.
- V2 case-3 maximum Q residual falls 41.8%, while p95 and the violating-bus count worsen. Local voltage-gap accounting explains the dominant branch-flow change.
- Sensitivity covers V, Pg and Qg direction and magnitude, two step sizes, adjacent increments, separate baseline offsets and reference constraint changes.

## Paper and review

The PDF is a visually inspected five-page **review draft**, including references. [Markdown](paper/manuscript.md) and [IEEEtran LaTeX source](paper/manuscript.tex) are editable. The LaTeX source was generated but not compiled on this host; its eventual page count is not claimed. Final authorship, affiliations, Dr. Li review, IEEE template compliance and submission remain publication tasks. No paper or message was submitted or sent.

Ninad specified IEEE PES, five pages, San Francisco. The [official PES GM 2027 call](https://pes-gm.org/wp-content/uploads/2026/06/6.8.26-Flyer_2027-IEEE-PES-GM-CFP.pdf) identifies the 10 November 2026 deadline. This run verified the date, not the portal cutoff time. Direct confirmation from Dr. Li was not obtained. The [outline Page](https://chatgpt.com/space/page_4fce14d686308191b7fc35b61f4a5952) records the original outline and updated outcome; its text was read back, but its UI preview was not visually inspected.

Exact training exposure remains limited by source evidence: [checkpoint-specific audit](paper/training-exposure.json). V2's associated paper identifies case500_goc as a pretraining topology; neither downloaded checkpoint exposes exact training or split membership. V1's public card does not establish a roster tied to the tested hash. The paper does not claim exact scenario novelty or attribute performance differences causally to training exposure.

## Evidence map

| File | Purpose |
|---|---|
| `manifest.json` | Original pre-run case/model freeze, code hashes, mappings and settings |
| `manifest-addendum.json` | Post-run provenance notes, hardware, training-audit link and reproduction-only path adjustment |
| `scenario-plan.json` | Frozen absolute and relative loading factors, IDs and input hashes |
| `evaluator-validation.json` | Three baseline acceptance and intentional-perturbation checks |
| `final-verification.json` | Independent saved-state audit and exact counts |
| `artifact-sha256.json` | SHA-256 inventory of all package files except itself |
| `results/<scenario>/input.json` | Exact prescribed problem |
| `results/<scenario>/*-returned.pt/json` | Native model returns, saved before scoring |
| `results/<scenario>/*-native.json` | Full physical-unit state in original row order |
| `results/<scenario>/*-metadata.json` | Exact model pins, raw-to-physical mapping, environment and features |
| `results/<scenario>/ac-attempt*` | Both successful and failed AC attempts, starts and solver traces |
| `results/<scenario>/*-bus/generator/branch.csv` | Detailed states, residuals and both-end flows |
| `paper/all-metrics.csv` | 236 method slots; no replacement of missing values by zero |
| `paper/feasibility-summary.csv` | Main-grid passes, attempted denominators and reference coverage |
| `paper/figures/` | Selected MAE/RMSE, balance and equipment plots in PNG/PDF |
| `paper/case3/` | Improving/worsening buses, nearby voltages, reactive flows, generator Q and exact branch decomposition |
| `paper/sensitivity-*.csv/json` | 108 finite-difference comparisons and per-variable details |
| `paper/step-size-check.json` | Matched 0.5%/1% comparison |
| `paper/reference-constraint-changes.json` | Active reference bounds at adjacent endpoints |
| `paper/reference-failure-investigation.json` | Retained UNKNOWN diagnostics |

## Reproduce saved-state analysis

No inference or optimization is needed to inspect or regenerate these outputs. On the original Windows host, from this package directory:

```powershell
$studyPython = 'C:\Users\Ninad\Documents\Codex\2026-10-26\don-t-wait-for-max-anything\work\runtime\python\Scripts\python.exe'
& $studyPython -B experiments/loading/analyze.py loading
& $studyPython -B experiments/loading/focused.py case3
& $studyPython -B experiments/loading/focused.py sensitivity
& $studyPython -B experiments/loading/verify.py
```

These commands rewrite derived analysis/verification files. Use a separate extracted copy to preserve the delivered artifact hashes. Numerical packages are listed in `python-environment.txt`; source and Julia environment pins are included. The `verify.py` command crosschecks the saved states with a second evaluator and verifies model mappings and DC Q-only invariance.

## Reproduce fresh experiments

Preserve this package as evidence. Create a separate destination containing `sources`, `scripts`, `experiments` and an empty `paper` directory, with no old manifest, plan or results. Restore the pinned model-source checkouts, checkpoint bytes and local runtime according to `manifest.json`. Set `GRIDSFM_RUNTIME_ROOT` if they are not in the original location. Its layout is `runtime/sources/{microsoft,newer}`, `runtime/checkpoints`, `julia/julia-1.11.9/bin/julia.exe`, `julia/depot`, and the original `GridSFM-study` checkout for source-revision recording during initialization. The final runner uses the bundled `experiments/loading/julia` Project and Manifest; they are byte-identical to the environment used in the run.

Then execute, in order:

```powershell
& $studyPython -B experiments/loading/study.py init
& $studyPython -B experiments/loading/study.py baseline-ac
& $studyPython -B experiments/loading/run.py baseline
& $studyPython -B experiments/loading/analyze.py
& $studyPython -B experiments/loading/run.py freeze
& $studyPython -B experiments/loading/run.py loading
& $studyPython -B experiments/loading/analyze.py loading
& $studyPython -B experiments/loading/focused.py case3
& $studyPython -B experiments/loading/run.py sensitivity
& $studyPython -B experiments/loading/focused.py sensitivity
& $studyPython -B experiments/loading/verify.py
```

`init` refuses to replace an existing frozen manifest. Phase runners retain attempts and skip saved completed states; they do not silently rerun inference. Model caches are stored outside this package under the task's `work/cache`. No checkpoints, installed runtimes or credentials are included in the archive. CPU/platform replay is not claimed to be bit-identical on a different machine.

## Boundaries and deviations

- The input objective's loading equations lost their multipliers. The interpretation was stated before execution and frozen as P-only, Q-only and combined scaling.
- Case 3 was resolved to the matching GSFM-020 93-94% experiment and its controls. All required points were freshly run; old artifacts were not overwritten.
- The case500 OPF reference-bus validator was generalized before any new solve: an online generator is required in the connected island, not specifically at the angle-reference bus. Original case matrices are unchanged.
- An initial case-3 analysis assertion incorrectly assumed branch 321 had zero resistance. It failed before emitting a completed mechanism summary. The corrected decomposition uses the actual r=0.0002 pu, x=0.0006 pu and charging; exact reconstructed flow agreement was checked. This affected analysis only, not states or the evaluator.
- Sensitivity execution overlapped the correction of that saved-state analysis assertion. No experimental point or tolerance was selected from this correction; the complete sensitivity plan was already frozen before loading results.
- The final runner accepts a runtime-root environment override and a bundled Julia-project path. These path-only portability changes occurred after execution; the archived phase code hashes identify the actual executed code. The numerical evaluator is unchanged.
- Raw inference is fixed to original row order and shipped feature handling. No permutation robustness, global optimum, certified infeasibility or submission readiness is claimed.

Original MATPOWER and PGLib source attribution is retained in `sources/`. The case500 source is CC BY 4.0 with the requested synthetic-network citation in the manuscript. Model source and checkpoints retain their own upstream terms.
