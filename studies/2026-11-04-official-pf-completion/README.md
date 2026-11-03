# Official V2 power-flow completion extension

Status: bounded numerical study, analysis and five-page review draft COMPLETE. See the [final artifacts](publication/FINAL-ARTIFACTS.md), [requirements audit](publication/requirements-audit.md) and release verification receipt for delivery. Authorship, scientific review and unavailable adaptation/exporter boundaries remain explicit. The [complete current-work snapshot](publication/ALL-ARTIFACTS.md) publishes code, manifests, tables, diagnostics and every raw result. This is a new authorized extension of [the completed independent P/Q loading study](../2026-11-04-independent-pq-loading/README.md). Earlier stop instructions are historical for this explicitly requested work. No prior study file is overwritten.

Question: when P and Q demand change independently, which observed errors arise in native GridSFM output, which persist in predicted controls after the author Newton completion, and which operating limits remain unsatisfied?

## Scope and completion ledger

- [x] Read complete objective and current repository instructions; confirm main and origin/main match before work.
- [x] Verify every prior artifact hash and the full published archive; reuse existing 59 inputs and states.
- [x] Export the exact author revision from its Git object database, independent of working-tree newline changes.
- [x] Inspect primary literature sections and complete the initial prior-work distinction table.
- [x] Map official callers, presets, preprocessing, physics and stage availability.
- [x] Validate case500goc integration, then all three networks and reference-control/perturbation gates; retain the released-graph/original-physics discrepancy.
- [x] Freeze adapter settings and provenance; expand the three nominal baseline tables.
- [x] Run all 59 matched frozen V2 + official PF inputs and 15 compatible case500goc adapted inputs, plus separately labeled exact-matrix diagnostics.
- [x] Complete all metrics, failure/coverage records and loading figures.
- [x] Integrate case 3 with exact electrical accounting.
- [x] Compute the final focused endpoint sensitivity and half-step checks; interpretation remains part of the analysis.
- [x] Falsify candidate claims against matched results and closest literature.
- [x] Compile actual IEEE source; inspect five-page PDF including references; draft unsent Dr. Li note.
- [x] Audit every requirement and publish durable reproducibility artifacts with checksums.

The full controlling protocol is [protocol-objective.txt](protocol-objective.txt). Raw extension outputs live in `results/`, separate from native states linked through the prior archive. Installed dependencies and checkpoint binaries remain outside Git. Paid compute, long training, correspondence and submission are not authorized.

## Saved numerical coverage at publication

The coverage table contains 531 scenario/stage slots: 399 attempted records (236 reused and 163 new), 132 unavailable adapted-stage slots on case300/case300x2, and zero pending numerical slots. Frozen V2 plus official PF converges on 4/59 inputs; compatible adapted case500goc plus official PF converges on 15/15. Neither stage passes all original AC constraints. The separately labeled exact-matrix diagnostic has the same convergence/pass counts. Finite nonconverged iterates remain failed candidates, not operating responses.

The revised [actual IEEE source](paper/manuscript.tex) compiles to the [five-page PDF](paper/manuscript.pdf), including references. Every page was inspected, all fonts are embedded, and the abstract has 137 words. The full [results](RESULTS.md), [workflow](WORKFLOW.md), [claims audit](CLAIMS.md), [literature comparison](literature/comparison.md) and [unsent Dr. Li note](paper/dr-li-note-unsent.md) are complete. This is a review draft, not a submitted paper or a guarantee of novelty. The earlier checkpoint and native-study releases remain unchanged.
