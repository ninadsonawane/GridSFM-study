# Experiment 20: local operating-condition investigation

The user explicitly authorized local testing on 26 October 2026. This supersedes the prior Mac-access blocker. No previous results, checkpoints or source files will be overwritten. Study baseline: `2aa8778e0cc97cc39e748b40fdb8b36a475e4d0f`. No publication, correspondence, training, checkpoint selection, PF completion or OPF repair.

## Clock and budget

- Retain the preceding continuation's clock: 2026-10-26 16:45:13 UTC. Deadline: 21:45:13 UTC / 27 October 03:15:13 IST. Stop new computation by 21:15 UTC for reporting.
- At most 24 attempted discovery inputs plus six attempted confirmation inputs. Four to six new inputs per batch. Failed inputs count. Existing conditions used for installation/repeatability are separately recorded; do not silently count them as new discovery or confirmation.
- At most 20 diagnostic forwards. Bounded diagnosis: 45 minutes of diagnostic work, inside the overall cap. Local setup is inside the total clock. Native output mediation may remain unresolved; proceed only with verified fixed-order mapping, repeatability and independent physics.
- Record each input before execution, save outcomes after each input and select each next batch before viewing its outcomes. All four methods are attempted for every new condition unless a correctness gate requires stopping dependent work.

## Local recreation and correctness

Acquire exact checkpoint bytes and pinned model source. Verify SHA-256 and strict loading, seed 0, CPU FP32, four torch threads, shipped default clipping. Save native returned dictionaries before conversion/scoring. Observe exact existing clamp calls without changing their returns. Save prepared tensors for diagnostic comparisons. Separate altered-feature forwards from shipped defaults.

Preserve original external IDs and original bus/generator/branch order. Recreate only original MATPOWER case300 and the already specified two-copy system with its two existing parallel ties. Verify reconstructed matrices against historical input hashes when available. No additional network construction. Never supply solved values as features.

Use the audited AC PowerModels ACP/Ipopt settings and DC PYPOWER PIPS settings. Record dependency differences from the historical Mac. AC must pass original FP64 balance, limits, objective and parser round trips before it is a reference. Solver failures remain UNKNOWN. One deterministic flat AC retry is permitted. Do not tune settings on outcomes.

Fixed tolerances: balance and generator excess 1e-3 MW/MVAr; Vm excess 1e-4 pu; active angle excess 1e-3 degrees; thermal excess 1e-3 MVA. Independent branch/Ybus discrepancy must be below 1e-6 MVA. Original case300 thermal results N/A; connected-system thermal coverage only the existing finite 600-MVA ties. DC uses its own equations; Qg/Vm/joint AC feasibility N/A.

## First discovery batch (fixed before new outcomes)

Earlier evidence: v2 maximum Q imbalance drops 21,338.70 to 7,380.67 MVAr from 90% to 95% global loading. Original bus235 Vm moves from 0.94 to 1.04786 pu while bus238 remains 1.06; branch321 dominates the local change. Cause and nearby repeatability remain unverified.

Hypothesis: the four intervening global load levels expose whether this is a repeatable clipping/voltage transition or an isolated sampled difference. All signed Pd/Qd scale together; other fields and ordering remain fixed. Paired historical controls: 0.90 and 0.95. Reuse matching saved states if verified; report unavailable raw returns explicitly.

| ID | Pd and Qd scale | Expected conventional response |
|---|---:|---|
| G300-0.91 | 0.91 | More active demand generally increases AC generation and losses; local voltage/Q active sets need not be monotone. DC tracks P demand under its own equations. |
| G300-0.92 | 0.92 | Same |
| G300-0.93 | 0.93 | Same |
| G300-0.94 | 0.94 | Same |

Inspect global residual distributions, severity bands with unchanged acceptance, hotspots, exact branch321 flows, actual clamps, and separate native/reference motion. After this batch, select the next isolated intervention by the uncertainty it resolves. Include both allowed networks in the eventual comparison. Do not exhaust the budget automatically.

## Confirmation and report

Reserve six inputs. Select nearby settings and relevant controls before their outcomes, after discovery establishes the claim. Preserve every failure and negative result. Report five state/flow accuracy measures against accepted references; P/Q mean, median, p95, max and counts; generator/voltage/angle/thermal count, severity and locations; joint native feasibility; actual clipping versus bound activity. Finish with the three strongest supported findings, confirmation evidence, feasibility outcome, expected physics versus possible novelty, commands/hashes/artifacts and a bounded central claim.
