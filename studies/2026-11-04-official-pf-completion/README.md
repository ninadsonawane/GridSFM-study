# Official V2 power-flow completion extension

Status: ACTIVE; all planned numerical runs are saved, and analysis/manuscript work remains. The [complete current-work snapshot](publication/ALL-ARTIFACTS.md) publishes code, manifests, tables, diagnostics and every raw result. This is a new authorized extension of [the completed independent P/Q loading study](../2026-11-04-independent-pq-loading/README.md). Earlier stop instructions are historical for this explicitly requested work. No prior study file is overwritten.

Question: when P and Q demand change independently, which observed errors arise in native GridSFM output, which persist in predicted controls after the author Newton completion, and which operating limits remain unsatisfied?

## Scope and completion ledger

- [x] Read complete objective and current repository instructions; confirm main and origin/main match before work.
- [x] Verify every prior artifact hash and the full published archive; reuse existing 59 inputs and states.
- [x] Export the exact author revision from its Git object database, independent of working-tree newline changes.
- [x] Inspect primary literature sections and complete the initial prior-work distinction table.
- [ ] Map official callers, presets, preprocessing, physics and stage availability.
- [x] Validate case500goc integration, then all three networks and reference-control/perturbation gates; retain the released-graph/original-physics discrepancy.
- [x] Freeze adapter settings and provenance; expand the three nominal baseline tables.
- [x] Run all 59 matched frozen V2 + official PF inputs and 15 compatible case500goc adapted inputs, plus separately labeled exact-matrix diagnostics.
- [ ] Complete all metrics, failure/coverage records and loading figures.
- [ ] Integrate case 3 with exact electrical accounting.
- [x] Compute the final focused endpoint sensitivity and half-step checks; interpretation remains part of the analysis.
- [ ] Falsify candidate claims against matched results and closest literature.
- [ ] Compile actual IEEE source; inspect five-page PDF including references; draft unsent Dr. Li note.
- [ ] Audit every requirement and publish durable reproducibility artifacts with checksums.

The full controlling protocol is [protocol-objective.txt](protocol-objective.txt). Raw extension outputs live in `results/`, separate from native states linked through the prior archive. Installed dependencies and checkpoint binaries remain outside Git. Paid compute, long training, correspondence and submission are not authorized.

## Saved numerical coverage at publication

The coverage table contains 531 scenario/stage slots: 399 attempted records (236 reused and 163 new), 132 unavailable adapted-stage slots on case300/case300x2, and zero pending numerical slots. Frozen V2 plus official PF converges on 4/59 inputs; compatible adapted case500goc plus official PF converges on 15/15. Neither stage passes all original AC constraints. The separately labeled exact-matrix diagnostic has the same convergence/pass counts. Finite nonconverged iterates remain failed candidates, not operating responses.

The revised `paper/manuscript.tex` is still a skeleton; there is no compiled extension PDF. The earlier five-page native-study review draft remains available in the prior study. Completing loading figures, the workflow map, interpretation, claim-to-evidence audit, revised manuscript/PDF and unsent Dr. Li note remains authorized work. Publishing this snapshot does not complete the research goal.
