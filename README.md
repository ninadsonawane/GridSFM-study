# GridSFM case300 adaptation study

Permanent research home for Ninad Sonawane's proposed steady-state AC-OPF study with Professor Surya Santoso and his postdoc. The professor's involvement and suggestions are **user-reported**; scope and review arrangements remain to be discussed.

**22 October: [GSFM-007 / Experiment 10](docs/experiments/GSFM-007.md) is READY FOR HARDWARE, not yet executed.** The user requested a five-hour practical-utility comparison of conventional AC-OPF, frozen GridSFM, full adaptation and ridge on original case300 plus independent PGLib IEEE118. [Decision 0005](docs/decisions/0005-practical-utility-benchmark.md) supersedes older active-scope/stop instructions below for this bounded task only. It adds official gated selection, three seeds, shared external OPF refinement, fresh tests and control-substitution analysis.

**GSFM-006 Experiment 9 is complete, with optional refinement not run.** See the [newer-pipeline pilot](results/pilots/GSFM-006/20261021T171629Z-m5-new-pipeline/README.md): one 200-update CPU adaptation enabled 30/30 ordinary PF completions, but 0/30 full feasibility; ridge plus the same completion remained stronger and conventional AC-OPF passed 30/30. Earlier results are preserved.

**GSFM-005 Experiments 5–8 are complete.** See the [controlled follow-up results](results/pilots/GSFM-005/20261021T120300Z-m5-seeds11-22-33/README.md): twelve full-regression fits completed 1,000 updates each across seeds11/22/33. Exact KCL beat the fixed initial-magnitude control on the selected ordinary primary score for all three seeds, but a200-update sign reversal and cost/state trade-offs prevent uniform superiority. Ridge remained stronger and all raw strict feasibility counts were zero. The [GSFM-004 pilot](results/pilots/GSFM-004/20261021T104843Z-m5-seed11/README.md) is preserved; no further study was launched.

The [publication plan after the VM experiments](docs/research/2026-10-21-publication-plan.md) is research background. The [initial research report](docs/research/2026-10-21-initial-study.md) remains the historical source/setup package; its unrun status and original scope are no longer the latest state.

Current question: **Does target-grid adaptation improve GridSFM's complete feasible AC-OPF workflow, or primarily enable power-flow completion?** See [decision 0005](docs/decisions/0005-practical-utility-benchmark.md). The earlier KCL question and [decision 0004](docs/decisions/0004-controlled-kcl-followup.md) remain historical. Constructed case300x2 and further LoRA work are deferred. These are candidate contributions, not established novelty or a publication promise.

Target: **2027 IEEE PES General Meeting, San Francisco, 25–29 July 2027**. Current [submission portal](https://submissions.mirasmart.com/PESGM2027/login.aspx) cutoff verified 21 October: **10 November 2026, 11:59 p.m. Eastern / 11 November, 10:29 a.m. IST**. Five pages **including references**. Internal ready date: 8 November. See [verified rules](docs/technical/conference-verification.md).

## Current state

The M5 Pro/64 GB worker completed GSFM-004 and the controlled GSFM-005 follow-up. GSFM-005 main fits took90.62minutes, with30 accepted ordinary,28 spatial and30 higher-load fresh cases. Two spatial local-solver failures remain unknown. All source/config/data integrity checks passed; old artifacts and the released checkpoint are unchanged. Compact results/scripts/figures are tracked; raw matrices, predictions and resumable checkpoints remain local with hashes. See the current result link above; older archives and planner descriptions are historical.

[Final verification record](results/verification/2026-10-21-package-final.json): 30 unit tests and two focused cycle/LoRA checks passed on the committed source package; JSON, CSV widths, exact imported bytes and local document links checked. This record names the exact tested code commit and dependencies. It does not certify a power-system solution or a trained model. The earlier, narrower verification record remains available in the same directory.

Important source findings: official case300 has 300 buses, 69 generators, 411 branches and **all RATE_A=0**; its external IDs are not row indices. The constructed system has 600 buses, 138 generators and 824 physical branch rows. Proposed ties have explicitly synthetic finite ratings; original interior branches remain unlimited. The newer GridSFM paper and Microsoft v1.1 are separate versioned evidence.

## Project map

| Path | Contents |
|---|---|
| [HANDOFF.md](HANDOFF.md), [AGENTS.md](AGENTS.md) | Next steps, execution limits and project instructions |
| [docs/context](docs/context), [docs/history](docs/history) | Original request, user-reported meeting, selective history and archive links |
| [docs/decisions](docs/decisions), [docs/logs](docs/logs) | Dated choices, corrections, tests and failures |
| [docs/literature](docs/literature), [paper/references.bib](paper/references.bib) | Nine primary papers, evidence/novelty and source register |
| [docs/technical](docs/technical) | MATPOWER instructions, exact source audit, GridSFM setup and conversion contract |
| [scripts/matlab](scripts/matlab), [scripts/python](scripts/python), [tests](tests) | Parameterized construction, neutral export, conversion, physical metrics and smoke checks |
| [configs](configs), [environments](environments), [manifests](manifests) | Proposed network/training settings, dependency constraints, pins/hashes and scenario designs |
| [results/templates](results/templates) | Empty result table and run-record schema; no model performance results |
| [paper/outline.md](paper/outline.md), [email](email) | Five-page plan and clearly unsent professor draft |

## Reproduction entry points

From repository root, Python 3.9+ standard library suffices for the first checks:

```sh
python -m unittest discover -s tests -v
python scripts/python/make_scenarios.py
python scripts/python/gridsfm_selfcheck.py
```

Acquire the exact MATPOWER source and reproduce construction:

```sh
git clone --branch 8.1 --depth 1 https://github.com/MATPOWER/matpower.git work/matpower-8.1
python scripts/python/matpower_case.py --git-dir work/matpower-8.1
python scripts/python/matpower_test.py
python scripts/python/matpower_case.py --construct configs/network-case300x2.json
```

Do not clone into an existing folder; reuse and verify its commit. See [MATPOWER guide](docs/technical/matpower.md) for MATLAB/Octave installation and PF/OPF commands. See [GridSFM guide](docs/technical/gridsfm-audit.md) for the separate Python 3.12 CPU/CUDA environments, checkpoint verification, supported-size control and unrun end-to-end gates. Dependency constraints are **proposed, not a resolved lock**; capture a platform lock only after a successful installation. Original-parameter evaluation uses `python scripts/python/physics_metrics.py case-input.json prediction.json --output metrics.json`.

The completed bounded runner is in [experiments/gsfm004](experiments/gsfm004/README.md). It contains seed/run defaults specific to the completed pilot; do not use it unchanged for the follow-up. Implement the separate parameterized runner specified in [GSFM-005](docs/experiments/GSFM-005.md). Its bounded hardware work is now requested; paid compute remains outside scope.

## Provenance and artifact policy

Source commits/licenses/checkpoint SHA-256 and import changes are in [manifests](manifests). Third-party code notices are retained, including the hardware runner's upstream license. MATPOWER software's license excludes case data, so source matrices and generated full matrices stay ignored; immutable source URL, checksum and retrieval instructions are tracked. The hardware worker used a checkpoint and generated labels; these large files remain local with hashes rather than in Git. No complete historical Git history is claimed.

Use main for this initially empty repository. Stage reviewed project paths, commit at meaningful milestones, push without force, then compare `git rev-parse HEAD` with `git ls-remote origin refs/heads/main`. Record each run's code commit/config/dependencies/hardware and retain unsuccessful attempts. Large future data/model artifacts require durable storage plus checksums/retrieval instructions before claiming full reproducibility.
