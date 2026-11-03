# All current extension artifacts

This is a publication checkpoint requested by Ninad on 4 November 2026. All saved study work is covered, including failed numerical attempts. The remaining analysis and revised paper are explicitly unfinished.

- [Current code, tables, manifests, validation and literature](../README.md)
- [Extension snapshot release](https://github.com/ninadsonawane/GridSFM-study/releases/tag/official-pf-completion-checkpoint-2026-11-04)
- [Complete extension evidence ZIP](https://github.com/ninadsonawane/GridSFM-study/releases/download/official-pf-completion-checkpoint-2026-11-04/GridSFM-official-PF-checkpoint-evidence.zip)
- [ZIP SHA-256](https://github.com/ninadsonawane/GridSFM-study/releases/download/official-pf-completion-checkpoint-2026-11-04/GridSFM-official-PF-checkpoint-evidence.zip.sha256)
- [Per-file inventory and storage coverage](artifact-inventory.json)
- [Local archive verification](archive-verification.json)
- [Prior study: five-page review draft and all reused evidence](../../2026-11-04-independent-pq-loading/publication/ALL-ARTIFACTS.md)

The ZIP contains the entire current extension tree: all 163 new stage outcomes, raw native/completed states, 148 Newton attempt traces, per-bus/generator/branch details, adapted native tensors, three baseline tables, loading metrics, case-3 electrical accounting, sensitivity tables, code, protocol, validation and manifests. All seven reference-control validation cases are separate from model results. Full per-entity tables and the `results/` tree use release storage; smaller artifacts are also browsable in Git. Every payload file has a SHA-256 entry and explicit Git/release placement. The inventory itself is inside the ZIP. Archive checksums and publication receipts are sidecars to avoid self-referential hashes.

Prior states are reused through the immutable prior release rather than duplicating its complete tree. Prior archive: `GridSFM-loading-study-evidence.zip`, SHA-256 `185cc64b3e08416c6adae56f6efb00a4781068d920457968ff9c5486ed0414c6`. The publication check revalidates every prior inventory entry.

Checkpoint binaries, installed Python/TeX runtimes, dependency caches and scratch renders are external inputs/tools. They are not scientific outputs and are not copied into Git or this archive. Exact author-source and checkpoint revisions/hashes are recorded in `manifests/execution.json`, `manifests/reuse-audit.json` and `manifests/adapted-checkpoint.json`; the checkpoint retrieval script is preserved in `session-provenance/`. No credential store or unrelated private files are included.

## Restore and inspect

1. Verify the ZIP against its `.sha256` sidecar, then extract `2026-11-04-official-pf-completion/` into `studies/` of this repository (use a separate checkout to preserve local work).
2. Download and verify the linked prior archive, then extract it into a separate evidence directory. Set `GRIDSFM_PRIOR_EVIDENCE_ROOT` to its `GridSFM-loading-study` root.
3. For code execution, retrieve `lukebhan/gridsfm` at `517a07531ea55a11bd81a89a6c6879695a2ba4b4`; set `GRIDSFM_OFFICIAL_SOURCE_ROOT` to that source root. Use the recorded dependency versions. Manifests retain the original Windows execution paths; checkpoint paths must be resolved on another machine without changing the source data or hashes.
4. Tables and raw JSON/CSV can be inspected without rerunning inference. `code/summarize.py` and `code/diagnose.py` derive summaries from the saved prior and extension states. Frozen execution files must retain their recorded hashes. This snapshot does not claim a clean-machine installation test.

## Completion boundary

All 59 frozen-stage inputs and 15 compatible adapted inputs have saved outcomes, including the separate exact-matrix diagnostics. Adapted case300/case300x2 stages remain unavailable. No completed extension operating point passes the full joint criterion. The published author Newton kernel is used with a disclosed study adapter; the referenced standalone author evaluation exporter is absent from the pinned release, so this is not a full author-workflow reproduction.

`paper/manuscript.tex` is a working skeleton. The revised extension PDF, final plots, workflow diagram, claim-to-evidence synthesis and unsent Dr. Li note remain pending. The previous five-page paper concerns the earlier native-only study. This release does not establish novelty, publication readiness or completion of the active research goal.
