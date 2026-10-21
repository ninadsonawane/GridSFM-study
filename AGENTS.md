# GridSFM study instructions

Read README.md, HANDOFF.md, docs/decisions/0001-study-scope.md and the dated research report before continuing. The permanent project is https://github.com/ninadsonawane/GridSFM-study. Use main until a later workflow is agreed; never force-push or discard work. Normal project commits and pushes are authorized; deliberately stage reviewed project files and verify the remote commit after each push.

- This project concerns steady-state AC-OPF on official MATPOWER case300 and our constructed two-copy system. Historical sequential PF/OPF, LFAC/DC and GTG/storage are separate work; do not import their scope or results.
- Treat the professor's meeting feedback as user-reported. The two-parallel-circuit interpretation is provisional. New evidence may change the question; record superseded decisions with dates.
- Separate verified source facts, proposed hypotheses, new runs, historical reported results and unresolved claims. Never invent results, globally certified optima, generalization, feasibility, runtime or memory savings.
- Preserve original case/checkpoint bytes and SHA-256 manifests. No silent rating inference, feasibility relaxation, dropped shunts, reordered labels or leakage of solutions into features. Preserve parallel branch IDs.
- Keep raw infeasible predictions separate from repaired outputs. Numerical failure is not proof of infeasibility. Compare LoRA and full FT only with a matched checkpoint, splits and evaluation.
- Record every run's code commit, config hashes, seeds, environment, hardware, status and artifacts. Retain failures. Test labels cannot guide construction, tuning or model selection.
- The archive research-learning is read-only historical reference. Nested archived repos are flattened, not complete Git histories. Do not change baselines or copy unrelated material. Recheck third-party licenses before importing anything.
- Long training jobs, paid compute, submission and external messages need further authorization. Email in email/ is an UNSENT draft. This research-package request authorizes lightweight code checks only.
- Use concise prose. Explain power assumptions from first principles. Repository Markdown is the requested format; do not create unrelated Pages.
- Keep credentials, account databases, personal/admissions/visa records, environments, caches and large model/data binaries out of Git. Large outputs require an agreed durable artifact location plus checksums; report local-only artifacts.
- Oracle environments remain read-only by default. Any mutation there requires explaining the exact action and receiving explicit user approval. Never infer permission from testing/investigation requests.
