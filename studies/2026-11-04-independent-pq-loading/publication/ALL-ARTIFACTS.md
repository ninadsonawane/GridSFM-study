# Complete paper and evidence access

Published on explicit instruction to push **ALL** study material. Repository files provide browsable paper sources, PDF, every summary table and plot, evaluator and runner code, cases, manifests, provenance, environment specifications and original objective. The complete raw evidence is delivered as an immutable GitHub release asset, including all successful and failed solver attempts, model tensors, native states, detailed bus/generator/branch outputs, prepared features and logs.

- [Five-page review paper](../paper/GridSFM-five-page-draft.pdf)
- [Full release](https://github.com/ninadsonawane/GridSFM-study/releases/tag/independent-pq-loading-2026-11-04)
- [Complete evidence ZIP](https://github.com/ninadsonawane/GridSFM-study/releases/download/independent-pq-loading-2026-11-04/GridSFM-loading-study-evidence.zip)
- [Archive SHA-256](https://github.com/ninadsonawane/GridSFM-study/releases/download/independent-pq-loading-2026-11-04/GridSFM-loading-study-evidence.zip.sha256)
- [Baseline tables](../paper/baseline-tables.md)
- [Reproduction and limitations](../README.md)

Archive: **67,810,352 bytes**, SHA-256 `185cc64b3e08416c6adae56f6efb00a4781068d920457968ff9c5486ed0414c6`. Its root is `GridSFM-loading-study/`. Extract it to a separate directory for the exact evidence layout; the code in that directory locates the raw `results/` beside `paper/`. The Git copy intentionally uses GitHub release storage for large raw files. The archive contains all 3,082 original package files, including its 3,081-file SHA-256 inventory. The coverage manifest identifies the Git-versus-release placement of each file.

All 59 scenarios are retained: 57 checked AC references, two UNKNOWN references, 59/59 native DC own-constraint passes, and 0/118 frozen-model AC joint passes. Publication adds access only: it does not rerun experiments, submit a paper, establish training exposure, or change the research conclusions. Checkpoint binaries and installed runtime caches were inputs, not study outputs; their exact versions and hashes are recorded rather than duplicated here.

The original outline Page is exported in this publication folder for access independently of ChatGPT. Page UI metadata and private account identifiers are not exported. Authorship/affiliations and Dr. Li review remain pending; the PDF is a review draft and the generated LaTeX source was not compiled on the execution host.
