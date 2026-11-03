# GridSFM loading study paper outline and methodology Draft

Source: https://chatgpt.com/space/page_4fce14d686308191b7fc35b61f4a5952

Working question: How do GridSFM state accuracy and physical feasibility change under independent active and reactive loading changes?

Scope: original case300, the existing interconnected two-copy case300 construction, and PGLib v23.07 case500goc; AC-OPF, DC-OPF, frozen V1 and frozen V2. Ninad specified the five-page IEEE PES San Francisco venue. The official [PES GM 2027 call for papers](https://pes-gm.org/wp-content/uploads/2026/06/6.8.26-Flyer_2027-IEEE-PES-GM-CFP.pdf) identifies a five-page maximum and 10 November 2026 submission deadline. Direct confirmation from Dr. Li was not obtained.

# Paper outline

1. Introduction: question, motivation, and contributions finalized from the experiments.

2. Methodology: frozen cases and checkpoints, loading scenarios, common evaluator, numerical tolerances and reference acceptance.

3. Baseline results: one comparison table per network at nominal loads and original limits.

4. Loading results: independent P-only, Q-only and combined changes, with the original case-3 controls and the 93–94% region integrated into this analysis.

5. Focused sensitivity: adjacent loading increments, direction and magnitude versus AC-OPF, step-size checks, and reference constraint changes.

6. Limitations and conclusion: checkpoint training exposure, network and representation scope, reference failures, and applicable constraints.

# Methodology draft

For each network, preserve the case ordering, bus and generator mapping, equipment parameters and native preprocessing. Record exact case and checkpoint hashes, source revisions and solver settings in a reproducibility manifest. Evaluate frozen model outputs as returned by each release, without external clipping, power-flow completion or OPF repair.

Apply the same prescribed demand vectors to all methods. Interpret P-only loading as (lambda PD0, QD0), Q-only loading as (PD0, lambda QD0), and combined loading as (lambda PD0, lambda QD0), with initial factors 1.00, 1.01, 1.02, 1.05 and 1.10. Record absolute factors separately from factors relative to an adjusted case-3 baseline.

Independently evaluate nominal AC-OPF solutions before using them as references. A solver failure is an UNKNOWN reference outcome and does not prove physical infeasibility. State-error metrics require an accepted reference; physical residuals use the scenario demand directly and remain available without one.

Report generator Pg and Qg, voltage-magnitude and reference-aligned angle MAE/RMSE. For P and Q bus mismatches, report maximum absolute, mean absolute, p95 and violating-bus count. For generator, voltage and branch constraints, report violation count, maximum and mean. Check branch power at both ends. Report joint pass/fail per scenario and the fraction passing every applicable constraint.

Frozen tolerances are 1e-3 MW/MVAr for balance and generator bounds, 1e-4 pu for voltage, 1e-3 MVA for thermal excess, and 1e-3 degrees for applicable branch angle bounds. Equipment means include zeros over eligible items; p95 uses linear interpolation over all buses. Three nominal AC references and known perturbation, bound, angle-alignment and both-end thermal checks passed. Native DC Q, voltage, apparent thermal and joint AC feasibility remain N/A.

# Results and claims

The benchmark and five-page review draft are complete. Across 59 unique inputs, 57 AC references independently pass and two remain UNKNOWN; all 59 native DC solutions pass their own constraints. All 118 frozen model states fail joint AC feasibility. In case 3, V2 maximum Q mismatch falls from 21,320.45 to 12,413.00 MVAr while p95 rises from 1,282.38 to 1,429.64 MVAr and violating buses increase from 299 to 300. Final sensitivity includes 0.5% and 1% increments with 108 model-variable comparisons. Exact checkpoint training-scenario exposure remains unverified and is explicitly separated from source-reported topology exposure.

# Five page working allocation

The saved review PDF has five pages including references: motivation and design; evaluator and three baseline tables; loading results; integrated case-3 analysis; sensitivity, limitations and references. The accompanying local evidence package contains source, manifests, raw states, failed attempts, full tables and figures. Authorship, affiliations, Dr. Li’s review and final IEEE template checks remain publication tasks.
