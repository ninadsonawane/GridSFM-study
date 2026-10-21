# GridSFM case300 adaptation study

Permanent research home for Ninad Sonawane's proposed steady-state AC-OPF study with Professor Surya Santoso and his postdoc. The professor's involvement and suggestions are **user-reported**; scope and review arrangements remain to be discussed.

**GSFM-004 revision 2 is complete; GSFM-005 is ready for the hardware worker.** See the [bounded pilot results](results/pilots/GSFM-004/20261021T104843Z-m5-seed11/README.md): six seed-11 fits completed 200 updates each, all checks passed, and all raw feasibility counts were zero. Ridge outperformed every neural arm on physical imbalance. Exact-KCL showed selected-checkpoint improvement with state/cost and fixed-endpoint trade-offs; no uniform dominance or useful adaptation claim is established. The user requested [Experiments 5–8](docs/experiments/GSFM-005.md): a KCL-magnitude control, longer training across three seeds, fresh locked evaluation and a paper decision, within five hours. These follow-up experiments have not been run by the planner.

The [publication plan after the VM experiments](docs/research/2026-10-21-publication-plan.md) is research background. The [initial research report](docs/research/2026-10-21-initial-study.md) remains the historical source/setup package; its unrun status and original scope are no longer the latest state.

Current question: **Does correcting the KCL operator improve learning beyond increasing its penalty strength, and does that effect repeat after longer training?** See [decision 0004](docs/decisions/0004-controlled-kcl-followup.md). Constructed case300x2 and further LoRA work are deferred. These are candidate contributions, not established novelty or a publication promise.

Target: **2027 IEEE PES General Meeting, San Francisco, 25–29 July 2027**. Current [submission portal](https://submissions.mirasmart.com/PESGM2027/login.aspx) cutoff verified 21 October: **10 November 2026, 11:59 p.m. Eastern / 11 November, 10:29 a.m. IST**. Five pages **including references**. Internal ready date: 8 November. See [verified rules](docs/technical/conference-verification.md).

## Current state

The separate M5 Pro/64 GB worker completed reference solves, frozen inference, conversion/physics diagnostics, a solver-initialization pilot and **six case300 adaptation fits in GSFM-004**. The six main fits took 472.64 seconds including validation/checkpointing, using CPU FP32 model computation and FP64 physics. Compact scripts and results are committed; large raw data and checkpoints remain on that Mac with a hash inventory. This Windows planner has read those artifacts but has not independently rerun the scientific experiments. The [older Exchange archive](docs/context/2026-10-21-exchange-results.txt) is historical; use the completed pilot linked above for current performance evidence.

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
