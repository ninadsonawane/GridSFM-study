# Handoff after the initial research package

## Current instruction: GSFM-005, Experiments 5–8

21 October 2026: the user requested the next experiments in Exchange's To-do. Read **[GSFM-005](docs/experiments/GSFM-005.md)** and [decision 0004](docs/decisions/0004-controlled-kcl-followup.md). This section supersedes the older operational instructions below; preserve them as history. Status: READY FOR HARDWARE, not executed by the Windows planner.

GSFM-004 completed six 200-update fits. All raw feasibility counts were zero; ridge beat neural methods on balance, and exact KCL had selected-checkpoint benefits but state/fixed-endpoint trade-offs. The next bounded run tests S/C/E plus a training-only gradient-magnitude-matched stock control, 1,000 updates each for seeds 11/22/33 (12 fits). Keep the same 50 training/10 validation cases; then evaluate the frozen recipe on fresh ordinary/spatial/higher-load cases. Five-hour inclusive cap, compute cutoff 4h40m, 15 minutes per fit, mandatory ridge/nearest/frozen controls. No automatic expansion to LoRA, new networks or a final large study.

Start a NEW GSFM-005 run directory and clock; mark ownership/RUNNING in Exchange. Parameterize the old runner's hard-coded seed11 and GSFM-004 paths rather than relabeling runs. Preserve existing Results, large local artifacts, source/checkpoint bytes and all failures. Normal reviewed commits/pushes remain authorized. No paid compute, email or conference submission is authorized. Append the report and stop when the specified work finishes, even before five hours.

## Current amendment: bounded discovery pilot, 21 October 2026

**Budget revision2 now controls:** the user asked for4-5hours. GSFM-004 is reduced to a five-hour inclusive cap, compute stops at4h40m, six fits/one seed11, <=200updates and25minutes per fit,50train plus10each validation/ordinary/spatial/high-load. Second seed, cross-case audit and MPS probe are deferred. Preserve any work already started; the clock runs from the original start and no duplicate or automatic restart is permitted. The earlier eight-hour paragraph below is historical.

The user explicitly requested a new hardware To-do with multiple hypothesis-screening experiments for M5 Pro/64GB. Read **`docs/experiments/GSFM-004.md`** and decision0003 first. This supersedes003's smoke-only operational stop, while retaining its uncompleted correctness checks. The latest live Exchange read still contained only frozen/diagnostic results; no new adaptation result was reported.

New scope: one50-label dataset, nearest-example/ridge/frozen baselines, six neural variants (full no/stock/exact KCL, heads, rank2 FFN-LoRA+heads, scratch), at most two balanced seeds, <=400common updates and30minutes per fit, <=8hours total including implementation/data/reporting. CPU FP32 model + CPU float64 original-parameter physics, sequential execution. Ordinary, paired spatial-demand and higher-load evaluation slices are all development data. Optional small cross-case operator audit only within the cap. No automatic final-study training, paid compute, publication submission or correspondence. Existing publication-plan sections below are historical proposals until this pilot chooses a hypothesis.

The hardware worker must mark task ownership/status, preserve prior Results, implement/validate a bounded runner, and return actual traces and failures. The planner has written instructions, not run these experiments. Use the commit-pinned protocol link in Exchange and synchronize without overwriting local VM artifacts.

## Latest amendment: post-experiment publication research, 21 October 2026

**This amendment supersedes the operational next steps below; the original handoff is preserved as history.** Start with `docs/research/2026-10-21-publication-plan.md`, decision0002 and `docs/experiments/GSFM-003.md`.

The user asked to read the latest Exchange results and deeply assess a tangible novel experiment for PESGM. The document now reports completed frozen inference, exact-reference checks, source-physics mismatch diagnostics and a negative solver-initialization pilot. Its research content is archived in `docs/context/2026-10-21-exchange-results.txt`. VM hardware is Apple M5 Pro/64 GB; no GPU-training claim is established. Raw experiment artifacts remain on that Mac and are not included in this research commit. Treat document numbers as VM-reported, not independently rerun here.

New primary research includes October2026 error-geometry work, LUMINA/LUMINA-Bench, HydraGNN adaptation and UNION. Plain OOD failure, physical violation reporting, full FT and LoRA are already close prior art. Recommended primary experiment: frozen/no-KCL/stock-clamped-KCL/exact-KCL adaptation on original case300, with identical settings, followed by original-physics scoring. The initial task is bounded to operator/gradient checks and20 updates/120seconds per arm. Main training remains a proposed separately authorized stage. LoRA, extra interconnections and warm-start acceleration are not requirements of this study.

Important: released `loss.py` is documented for fine-tuning; its mismatch does not establish the cause of frozen errors or original pretraining. Disable feasibility/stress auxiliaries equally, retain context and other losses, account for empty branch-supervision masks, and match precision. Detailed controls/gates are in the new plan. If there is no meaningful adaptation effect, reassess publication rather than claim a novel solver.

Official CFP/portal were reverified:10Nov2026 23:59Eastern =11Nov10:29IST; five pages including references; internal ready8Nov. No submission, external message, paid compute or main training was performed. Research files are committed/pushed at the milestone reported in chat; verify current Git state rather than relying on this amendment for the final hash.

---

Prepared 21 October 2026, Asia/Kolkata. Read README and docs/research/2026-10-21-initial-study.md first. The user authorized normal commits and pushes of this project to `ninadsonawane/GridSFM-study`; original remote was empty, branch is **main**. Final delivered commit and remote comparison are given in the delivery message; use `git log -2 --oneline` and `git ls-remote origin refs/heads/main` to inspect the current state.

## What actually happened

- Read the supplied request and saved it byte-for-byte, SHA-256 `1e60656cbe9a42de50d530ac28174c4826ae551f6e5960f02f2fe927994e08d7`.
- Read historical instructions/handoff/source metadata and selected audit/code files at research-learning commit `5b00e71e136e400445aab3a7a93bb8459cdd8a7c`. Archive unchanged.
- Inspected nine primary papers and official conference/MATPOWER/GridSFM sources. Verified public MIRA deadline by browser without signing in. Initial static-web timezone gap was resolved: 10 November 23:59 Eastern = 11 November 10:29 IST.
- Pinned/fetched actual MATPOWER source, computed matrix audit and constructed unsolved 600-bus JSON. Executed structural tests; see manifests/matpower-execution.json.
- Compared archive/upstream code hashes and HF revision/file metadata. Executed toy conversion tests, actual extracted upstream cycle function and a small FFN-wrapper gradient check; precise scope is in manifests/gridsfm-checks.json.
- Authored/tested a stdlib original-parameter physics checker and deterministic scenario split designs. All-check verification log is generated after the source commit so it can name an exact commit.
- Completed [final commit-linked package verification](results/verification/2026-10-21-package-final.json) against clean source commit `f1718fccaf93afee286eacbe9547ab554944edf9`: 30 tests plus two focused cycle/LoRA checks passed, JSON/CSV and local document links checked, and committed imported bytes verified. Earlier verification is retained. Initial push succeeded after resolving a restricted-process Git credential-helper error; final push is verified separately in the delivery message.

No MATLAB/Octave script, PF/OPF solve, full PyG pipeline, released-checkpoint inference, training study, memory/runtime benchmark, paper submission or external message was executed. Model/table result fields are empty. The initial network, code and adapter are prototypes until numerical gates pass.

## Environment and artifacts

Current host: Windows; default Python 3.9.10, Python 3.13 also listed. Existing torch/NumPy/SciPy supported a narrowly extracted-cycle/tiny-NN check, but do not constitute a supported GridSFM installation. The project specifies an isolated Python 3.12 Linux/WSL path; no WSL distro/CUDA readiness is established. `matlab`, `octave`, `nvidia-smi` were not on PATH; hardware CIM queries were denied. Do not infer that no GPU exists or reuse an unrelated PF/OPF environment.

Local-only, deliberately ignored: official `data/source/matpower-8.1/case300.m`, unsolved `data/generated/` matrices/conversions, Python caches and scratch/source checkouts. Case source is recoverable from immutable MATPOWER commit and SHA via the provided acquisition script; generated matrices are deterministically reconstructible. No solved labels/checkpoints/performance data exist. The archive and temporary upstream clones are references, not essential unpushed project changes. See manifests/source-repositories.json and source-specific manifests.

The MATPOWER data license exception prevents treating case300 as BSD software; keep retrieval instructions instead of silently republishing. No credentials/account databases or unrelated research/admissions/visa files were copied. New original project code has no separately selected public license yet; third-party notices are retained. Do not infer permission to relicense the user's work.

## Exact next steps

1. Ninad reviews `email/professor-santoso-unsent.md`; ask scientific questions about same-pair ties, ratings/focus, review windows and compute. Sending is not authorized. Provisional scope is decision 0001; update it by dated amendment after discussion.
2. Establish MATLAB or Octave with pinned MATPOWER 8.1 using docs/technical/matpower.md; run `test_matpower`, then `run_matpower_smoke(repo_root, unique_run_dir)`. Check original and constructed network with independent residual/limit gates. Supplied case initial VM violates some bounds and is not a solved label.
3. Execute the24-scenario pilot manifest, with seeds/loads regenerated by scripts/python/make_scenarios.py. A driver applying each manifest row and saving every solve remains to implement. The constructor already applies area factors; apply per-bus factors exactly once using the Python RNG's stored factors, not MATLAB's different RNG stream. Save actual factor arrays for every run.
4. Create isolated GridSFM environment; resolve and commit dependency lock; retrieve exact v1.1 checkpoint and verify both whole-file SHA and loader metadata. Run supported-size control and `gridsfm_selfcheck.py --upstream <pinned-clone> --model --lora`.
5. Pass accepted-label numerical round trip, original-parameter evaluation, feature/label-invariance, parallel-edge promotion/batch/loss and one backward pass. `gridsfm_adapter.py` is an unexecuted proposed tensor bridge; do not describe it as training-ready until these pass.
6. Implement one matched runner with frozen/LoRA/FT using same labels/losses/splits/evaluator. Disable synthetic-negative feasibility augmentation/classifier training. Run only tiny pilots when authorized; long training requires a subsequent instruction. By25 October decide retain adaptation or frozen fallback.
7. Freeze protocol before unsealing tests. Final plans allow4 tuning + 12 full fits (+ 2 tiny pilots), or cut to 6 final100-label fits if time/compute tight. Keep all failures and count test families, not paired outage cases as independent.
8. Reproduce figures/tables from actual records, write the five-page results paper and seek postdoc/professor review. Internal ready8 November; actual submission requires separate authorization.

## Blocking questions and scientific risks

No required user input blocks the delivered package. Further execution needs actual solver/ML setup and compute, but no purchase is authorized. Checkpoint-specific training-topology exposure remains unknown; exact case300 may be absent from documented bases but is not proven unseen. The two-copy interconnection's AC feasibility and useful transfer range are unverified. Reference optima are local. Native JSON silently ignores labels, and default PowerModels corrections can alter original angle bounds; use the audited direct conversion. Source unlimited ratings restrict thermal claims to the two ties. Performance benefits and novelty remain hypotheses.

Preserve dates, superseded configurations and failures. Read the original brief for full requirements; do not infer that this package already completed the proposed experiment.
