# Experiment16 — distinct electrical mechanisms, AC/DC and two frozen releases

COMPLETE.35 new source-selected inputs plus20 reused =55 unique inputs. Four methods are kept separate: conventional AC-OPF, audited standard DC-OPF, frozen Microsoft v1.1, frozen newer BASE v2. These are not the newer paper’s fine-tuned control+PF/projection workflow. All original matrices/results/weights are preserved; modifications are separately declared diagnostic cases.

## Overall verified outcomes

| Method | Observed outcome |
| --- | --- |
| AC-OPF | 41/55 independently verified feasible local references;14 UNKNOWN after default+one flat retry; no global certificate or infeasibility proof |
| DC-OPF | 53/55 own-law/limit passes; Qg,Vm,AC-Q/AC-thermal/joint AC validity N/A |
| Microsoft v1.1 | 0/55 native jointly feasible |
| Newer base v2 | 0/55 native jointly feasible |

UNKNOWN inputs:SHUNT50-300,GENOUT-300,VBOX80-300,SHUNT50-600,GENOUT-600,VBOX80-600,RATE80-300,RATE80-600,C300-L0.90-B0.00,C300-L1.06-B0.50,C300-L1.06-B0.00,C600-L0.90-B0.00,C600-L1.06-B0.50,C600-L1.06-B0.00. Native residual/limit checks remain valid without references; reference-dependent error cells areN/A. Failed iterates and both attempts are retained.

## Main findings, with limits on interpretation

1. PureP+10% and pureQ+10% have independently feasible localAC references on both networks. v2 PgMAE falls for both interventions, yet its maximumP imbalance rises. Reference accuracy and feasibility indicators need separate directions.
2. TighteningQg boxes by20% retains feasibleAC references and raises activeQg bounds from23→31(300),46→64(600). ModelQg clipping rises, but no native point becomes feasible. v1.1 PgMAE improves whileVm error worsens; v2 Pg/Vm/angle/active-flow MAEs worsen on both networks.
3. Halving capacitive bus shunts, removing the selected2073MW nonreference generator, or narrowingVm boxes all leaveAC outcomesUNKNOWN on both networks after the allowed retry. DC solves/ownconstraints pass; its state is identical for shunt/Q-box/V-box/R interventions because these quantities are omitted by its equations. Lower model residuals onUNKNOWN inputs are not evidence of improved accuracy.
4. One synthetic tie outage under fixedA+5%/B−5% loading has a feasibleAC reference and validDC solution. Both models overload the one remaining600MVA tie: maximumexcess803.57MVA(v1.1),752.66MVA(v2), versus146.37/31.33MVA in the two-tie baseline. Their PgMAEs and maximumP imbalances decrease, showing why an improved error component can accompany a worse operational violation. Doubling both tieX values retains feasibleAC/DC references; models still overloadboth ties, with124.54/40.52MVA maximumexcess.
5. Raising selected taps2% increases v1.1 maximumQ imbalance by1518MVAr(300) and4514MVAr(600), while v2's corresponding maximum changes little. Both have lowerPg and angleMAE; no uniform ranking follows. Cost×2 for the selected generator raises Pg and active-flowMAE for both releases on both networks.
6. PublishedRATE_A×0.8 leaves bothAC andDC solvesUNKNOWN on both rated variants. ReturnedDC points fail own-law balance/limits; they are retained, not accepted. Modeloverloadcounts rise from6→17/14→27 forv1.1 and11→25/20→52 forv2 (300/600). Reference-dependent accuracyN/A.
7. RenumberingIDs leaves both neural outputs exactly identical after mapping. Reversing rows leaves matrices AND raw converted graphs equivalent but changes both pipelines substantially: v2 maxQ imbalance7958→26242MVAr(300),9231→26120MVAr(600). AC/DC mapped outputs differ only numerically (<1e-8 in the compared state/flow quantities). This is a representation-sensitivity result, not an electrical stress. Original grid/adapter graph equivalence and output alignment pass; released feature-preparation/model internals remain an unresolved source. Do not attribute all earlier changes purely to electrical sensitivity.

All110 native states passPg/Qg/V bounds within tolerance, with measured clipping, but nonepassesjointfeasibility. DC has lowerPg and active-flowMAE than either model on all41 reference-valid inputs; eachmodel has lowerangleMAE on4/41. These55 inputs include dependent variants and physically equivalent controls, not55 independent grids.

Published rated source attribution is retained in [Experiment14](../../GSFM-014/20261023-rated-variants/README.md): [PGLib-OPF pinnedv23.07 case](https://github.com/power-grid-lib/pglib-opf/blob/dc6be4b2f85ca0e776952ec22cbd4c22396ea5a3/pglib_opf_case300_ieee.m), [CC BY4.0](https://creativecommons.org/licenses/by/4.0/), originalIEEE300 data credited in its header toRichardD.Christie/UWashington1999. Our rating reduction and two-copy derivatives are explicitly declared.

## How to read the directional table

G=active-generation MAE(MW), V=Vm MAE(pu), θ=aligned-angle MAE(degrees), F=active both-end line-flow MAE(MW). ↑ means error increased versus the stated unchanged baseline; ↓ means decreased; ≈ means numerical change below1e-6 (angles1e-4degrees). Changes compare against each input’s independently verified AC reference; neither arrow measures AC optimality. P/Q are changes in maximum nodal MW/MVAr imbalance, separately from reference errors. Clipping gives actual Pg/Qg/V clamp counts, not bound-equality counts. Thermal gives violating positive-RATE_A online branches; None means no finite ratings. Errors on offline units/branches are excluded from active-only means. Complete values/distributions/locations are in method-summary.json and CSV.

AC cells report reference feasibility, raw objective change and generators at Q bounds—not meaningless error-versus-itself zeros. Solver bound activity is not clipping. A Q-bound count can increase because of changed limits, not because a network learned enforcement. On UNKNOWN iterates, displayed Q-bound counts are diagnostic only, not feasible operating data. DC own-law passes never certify AC feasibility.

## All newly executed mechanism contrasts

| Input/condition | AC-OPF | DC-OPF | Microsoft v1.1 | Newer base v2 |
| --- | --- | --- | --- | --- |
| P10-300 | PASS; costΔ 13.9%; Q-bound 28 | own DC PASS; ΔG/θ/F ↑/↑/↑ | ΔG/V/θ/F ↑/↑/↑/↓; ΔP/Q ↓/↓; clip 20/12/45; thermal None | ΔG/V/θ/F ↓/↓/↑/↓; ΔP/Q ↑/↑; clip 52/29/286; thermal None |
| Q10-300 | PASS; costΔ 0.335%; Q-bound 29 | own DC PASS; ΔG/θ/F ↑/↓/↑ | ΔG/V/θ/F ↓/↑/↑/↓; ΔP/Q ↓/↓; clip 22/8/39; thermal None | ΔG/V/θ/F ↓/↓/↑/↑; ΔP/Q ↑/↑; clip 50/26/277; thermal None |
| ADD-concentrated-300 | PASS; costΔ 0.114%; Q-bound 23 | own DC PASS; ΔG/θ/F ↓/↑/↑ | ΔG/V/θ/F ↓/↓/↑/↓; ΔP/Q ↓/↓; clip 21/8/39; thermal None | ΔG/V/θ/F ↓/↑/↑/↑; ΔP/Q ↓/↑; clip 51/27/281; thermal None |
| ADD-distributed-300 | PASS; costΔ 0.114%; Q-bound 23 | own DC PASS; ΔG/θ/F ↑/↑/↑ | ΔG/V/θ/F ↑/↑/↑/↓; ΔP/Q ↓/↓; clip 21/8/39; thermal None | ΔG/V/θ/F ↓/↑/↑/↓; ΔP/Q ↑/↑; clip 51/27/280; thermal None |
| SHUNT50-300 | UNKNOWN; costΔ N/A; Q-bound 22 | own DC PASS; ΔG/θ/F N/A/N/A/N/A | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↑/↑; clip 21/8/38; thermal None | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↑/↑; clip 50/27/280; thermal None |
| QBOX80-300 | PASS; costΔ 0.0493%; Q-bound 31 | own DC PASS; ΔG/θ/F ↑/↓/↑ | ΔG/V/θ/F ↓/↑/↑/↓; ΔP/Q ↓/↓; clip 21/10/40; thermal None | ΔG/V/θ/F ↑/↑/↑/↑; ΔP/Q ↓/↑; clip 52/28/275; thermal None |
| GENOUT-300 | UNKNOWN; costΔ N/A; Q-bound 35 | own DC PASS; ΔG/θ/F N/A/N/A/N/A | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↓/↓; clip 22/8/51; thermal None | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↑/↑; clip 54/27/276; thermal None |
| COST2-300 | PASS; costΔ 4.86%; Q-bound 26 | own DC PASS; ΔG/θ/F ↑/↑/↑ | ΔG/V/θ/F ↑/↑/↓/↑; ΔP/Q ↓/↓; clip 22/8/39; thermal None | ΔG/V/θ/F ↑/↓/↓/↑; ΔP/Q ↓/↑; clip 51/27/278; thermal None |
| TAP102-300 | PASS; costΔ 0.0433%; Q-bound 24 | own DC PASS; ΔG/θ/F ↑/↑/↑ | ΔG/V/θ/F ↓/↑/↓/↓; ΔP/Q ↓/↑; clip 21/8/39; thermal None | ΔG/V/θ/F ↓/↓/↓/↓; ΔP/Q ↓/↓; clip 51/27/281; thermal None |
| SHIFT2-300 | PASS; costΔ -3.88e-13%; Q-bound 23 | own DC PASS; ΔG/θ/F ≈/≈/≈ | ΔG/V/θ/F ↑/↑/↓/↑; ΔP/Q ↑/↑; clip 21/8/39; thermal None | ΔG/V/θ/F ↑/↑/↓/↑; ΔP/Q ↓/↓; clip 51/27/281; thermal None |
| VBOX80-300 | UNKNOWN; costΔ N/A; Q-bound 20 | own DC PASS; ΔG/θ/F N/A/N/A/N/A | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↓/↓; clip 21/8/77; thermal None | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↓/↓; clip 51/26/285; thermal None |
| R110-300 | PASS; costΔ 0.000127%; Q-bound 23 | own DC PASS; ΔG/θ/F ↓/↑/↑ | ΔG/V/θ/F ↑/≈/↑/↑; ΔP/Q ↑/↑; clip 21/8/39; thermal None | ΔG/V/θ/F ↓/↑/↑/↓; ΔP/Q ↓/↑; clip 51/27/281; thermal None |
| X110-300 | PASS; costΔ -5.36e-06%; Q-bound 23 | own DC PASS; ΔG/θ/F ↑/↑/↓ | ΔG/V/θ/F ↓/≈/↑/↓; ΔP/Q ↓/↓; clip 21/8/39; thermal None | ΔG/V/θ/F ↑/↑/↑/↓; ΔP/Q ↓/↑; clip 51/27/281; thermal None |
| REP-renumber-300 | PASS; costΔ -6.47e-14%; Q-bound 23 | own DC PASS; ΔG/θ/F ≈/≈/≈ | ΔG/V/θ/F ≈/≈/≈/≈; ΔP/Q ≈/≈; clip 21/8/39; thermal None | ΔG/V/θ/F ≈/≈/≈/≈; ΔP/Q ≈/≈; clip 51/27/281; thermal None |
| REP-reorder-300 | PASS; costΔ 8.09e-14%; Q-bound 23 | own DC PASS; ΔG/θ/F ≈/≈/≈ | ΔG/V/θ/F ↑/↓/↑/↑; ΔP/Q ↓/↓; clip 26/11/26; thermal None | ΔG/V/θ/F ↑/↑/↑/↑; ΔP/Q ↑/↑; clip 45/27/277; thermal None |
| P10-600 | PASS; costΔ 13.9%; Q-bound 56 | own DC PASS; ΔG/θ/F ↑/↑/↑ | ΔG/V/θ/F ↓/↑/↓/↑; ΔP/Q ↓/↓; clip 37/21/78; thermal 0 | ΔG/V/θ/F ↓/↓/↑/↓; ΔP/Q ↑/↑; clip 100/54/564; thermal 0 |
| Q10-600 | PASS; costΔ 0.335%; Q-bound 58 | own DC PASS; ΔG/θ/F ↑/↓/↑ | ΔG/V/θ/F ↓/↑/↓/↑; ΔP/Q ↓/↓; clip 38/20/101; thermal 0 | ΔG/V/θ/F ↓/↓/↑/↑; ΔP/Q ↑/↓; clip 101/54/560; thermal 0 |
| ADD-concentrated-600 | PASS; costΔ 0.0568%; Q-bound 46 | own DC PASS; ΔG/θ/F ↓/↑/↑ | ΔG/V/θ/F ↓/↑/↓/↑; ΔP/Q ↓/↑; clip 39/20/98; thermal 0 | ΔG/V/θ/F ↓/↑/↓/↑; ΔP/Q ↓/↓; clip 97/54/567; thermal 0 |
| ADD-distributed-600 | PASS; costΔ 0.0571%; Q-bound 46 | own DC PASS; ΔG/θ/F ↑/↑/↑ | ΔG/V/θ/F ↓/↑/↓/↑; ΔP/Q ↓/↑; clip 39/20/98; thermal 0 | ΔG/V/θ/F ↓/↑/↑/↓; ΔP/Q ↑/↓; clip 97/54/567; thermal 0 |
| SHUNT50-600 | UNKNOWN; costΔ N/A; Q-bound 45 | own DC PASS; ΔG/θ/F N/A/N/A/N/A | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↑/↓; clip 39/20/99; thermal 0 | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↓/↓; clip 99/56/577; thermal 0 |
| QBOX80-600 | PASS; costΔ 0.0492%; Q-bound 64 | own DC PASS; ΔG/θ/F ↑/↓/↑ | ΔG/V/θ/F ↓/↑/↓/↑; ΔP/Q ↓/↓; clip 38/21/102; thermal 0 | ΔG/V/θ/F ↑/↑/↑/↑; ΔP/Q ↓/↓; clip 101/56/576; thermal 0 |
| GENOUT-600 | UNKNOWN; costΔ N/A; Q-bound 58 | own DC PASS; ΔG/θ/F N/A/N/A/N/A | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↓/↓; clip 38/20/93; thermal 0 | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↓/↓; clip 100/56/568; thermal 0 |
| COST2-600 | PASS; costΔ 2.39%; Q-bound 51 | own DC PASS; ΔG/θ/F ↑/↑/↑ | ΔG/V/θ/F ↑/↑/↓/↑; ΔP/Q ↓/↑; clip 39/20/97; thermal 0 | ΔG/V/θ/F ↑/↑/↓/↑; ΔP/Q ↓/↑; clip 99/54/566; thermal 0 |
| TAP102-600 | PASS; costΔ 0.0433%; Q-bound 48 | own DC PASS; ΔG/θ/F ↑/↑/↑ | ΔG/V/θ/F ↓/↑/↓/↓; ΔP/Q ↓/↑; clip 39/20/99; thermal 0 | ΔG/V/θ/F ↓/↓/↓/↓; ΔP/Q ↑/↓; clip 97/54/567; thermal 0 |
| SHIFT2-600 | PASS; costΔ 5.5e-13%; Q-bound 46 | own DC PASS; ΔG/θ/F ≈/≈/≈ | ΔG/V/θ/F ↓/≈/↓/↑; ΔP/Q ↑/↑; clip 39/20/99; thermal 0 | ΔG/V/θ/F ↑/↑/↓/↑; ΔP/Q ↓/↓; clip 97/54/567; thermal 0 |
| VBOX80-600 | UNKNOWN; costΔ N/A; Q-bound 46 | own DC PASS; ΔG/θ/F N/A/N/A/N/A | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↓/↓; clip 39/20/222; thermal 0 | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↓/↓; clip 97/54/570; thermal 0 |
| R110-600 | PASS; costΔ 0.000114%; Q-bound 46 | own DC PASS; ΔG/θ/F ↓/↑/↑ | ΔG/V/θ/F ↓/≈/↑/↑; ΔP/Q ↑/↑; clip 39/20/99; thermal 0 | ΔG/V/θ/F ↓/↑/↑/↓; ΔP/Q ↓/↑; clip 97/54/567; thermal 0 |
| X110-600 | PASS; costΔ -5.86e-06%; Q-bound 46 | own DC PASS; ΔG/θ/F ↑/↑/↓ | ΔG/V/θ/F ↓/↑/↑/↓; ΔP/Q ↑/↓; clip 39/20/99; thermal 0 | ΔG/V/θ/F ↑/↑/↑/↓; ΔP/Q ↓/↑; clip 97/54/567; thermal 0 |
| REP-renumber-600 | PASS; costΔ -1.94e-13%; Q-bound 46 | own DC PASS; ΔG/θ/F ≈/≈/≈ | ΔG/V/θ/F ≈/≈/≈/≈; ΔP/Q ≈/≈; clip 39/20/99; thermal 0 | ΔG/V/θ/F ≈/≈/≈/≈; ΔP/Q ≈/≈; clip 97/54/567; thermal 0 |
| REP-reorder-600 | PASS; costΔ -1.13e-13%; Q-bound 46 | own DC PASS; ΔG/θ/F ≈/≈/≈ | ΔG/V/θ/F ↑/↓/↑/↑; ΔP/Q ↑/↓; clip 34/14/89; thermal 0 | ΔG/V/θ/F ↑/↑/↑/↑; ΔP/Q ↓/↑; clip 82/54/555; thermal 0 |
| LINEOUT-300 | PASS; costΔ 0.000356%; Q-bound 23 | own DC PASS; ΔG/θ/F ↓/↑/↑ | ΔG/V/θ/F ↓/↑/↑/↓; ΔP/Q ↓/↓; clip 21/4/36; thermal None | ΔG/V/θ/F ↓/↑/↑/↓; ΔP/Q ↓/↓; clip 51/27/276; thermal None |
| TIEOUT-600 | PASS; costΔ 0.002%; Q-bound 52 | own DC PASS; ΔG/θ/F ↓/↓/↓ | ΔG/V/θ/F ↓/↓/↑/↑; ΔP/Q ↓/↑; clip 39/21/90; thermal 1 | ΔG/V/θ/F ↓/↓/↑/↑; ΔP/Q ↓/↓; clip 97/53/558; thermal 1 |
| TIEX2-600 | PASS; costΔ -0.000241%; Q-bound 52 | own DC PASS; ΔG/θ/F ↑/↑/↓ | ΔG/V/θ/F ↓/↓/↑/↓; ΔP/Q ↑/↑; clip 39/20/95; thermal 2 | ΔG/V/θ/F ↑/↓/↑/↓; ΔP/Q ↓/↑; clip 96/54/557; thermal 2 |
| RATE80-300 | UNKNOWN; costΔ N/A; Q-bound 32 | FAILED UNKNOWN, own-law FAIL; ΔG/θ/F N/A/N/A/N/A | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↓/↑; clip 29/15/28; thermal 17 | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↓/↑; clip 25/14/280; thermal 25 |
| RATE80-600 | UNKNOWN; costΔ N/A; Q-bound 64 | FAILED UNKNOWN, own-law FAIL; ΔG/θ/F N/A/N/A/N/A | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↑/↑; clip 64/25/63; thermal 27 | ΔG/V/θ/F N/A/N/A/N/A/N/A; ΔP/Q ↓/↑; clip 50/26/566; thermal 52 |

Baselines and exact interventions are frozen in scenario-manifest.json and field-differences files. The two synthetic tie tests use fixedA1.05/B0.95 loads from15 Splus, avoiding a nearly zero-transfer symmetric test. This prelaunch correction was made before either case executed, with initial planning versions retained in prelaunch-amendment.json;35-input cap unchanged.

## Reused global/local/charging screens

These20 source states are reused and revalidated, not new independent trials.18 from15 cover global90/100/106%, fixed-total location/inter-area shifts, and positive line charging50%/0 at light/heavy loading;2 are complete published PGLib rated base references/predictions from14, with4 passive new forwards only to obtain their exact clip records and require saved-output equality. See15 report for the initial directional table.

### Reused300

| Input | Method | AC ref | G/V/θ/F MAE | P max | Q max | Clipped Pg/Qg/V | Overloads |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G300-0.90 | AC-OPF | VERIFIED_LOCAL_REFERENCE | 0/0/0/0 | 2.41e-11 | 1.01e-10 | N/A | None |
| G300-0.90 | DC-OPF | VERIFIED_LOCAL_REFERENCE | 17/N/A/5.27/16.2 | 3.27e-12 | N/A | N/A | None |
| G300-0.90 | microsoft-v1.1 | VERIFIED_LOCAL_REFERENCE | 193/0.0275/63.7/95.3 | 4.99e+03 | 1.28e+04 | 27/7/37 | None |
| G300-0.90 | newer-base-v2 | VERIFIED_LOCAL_REFERENCE | 127/0.0464/47.4/110 | 7.72e+03 | 2.13e+04 | 44/26/280 | None |
| G300-1.00 | AC-OPF | VERIFIED_LOCAL_REFERENCE | 0/0/0/0 | 1.23e-10 | 1.66e-09 | N/A | None |
| G300-1.00 | DC-OPF | VERIFIED_LOCAL_REFERENCE | 26.1/N/A/7.23/21.1 | 5.12e-12 | N/A | N/A | None |
| G300-1.00 | microsoft-v1.1 | VERIFIED_LOCAL_REFERENCE | 195/0.0269/23.3/77.1 | 3.75e+03 | 8.94e+03 | 21/8/39 | None |
| G300-1.00 | newer-base-v2 | VERIFIED_LOCAL_REFERENCE | 106/0.0435/48.8/98.3 | 3.21e+03 | 7.96e+03 | 51/27/281 | None |
| G300-1.06 | AC-OPF | VERIFIED_LOCAL_REFERENCE | 0/0/0/0 | 3.17e-11 | 1.62e-10 | N/A | None |
| G300-1.06 | DC-OPF | VERIFIED_LOCAL_REFERENCE | 37.9/N/A/7.19/23.5 | 7.28e-12 | N/A | N/A | None |
| G300-1.06 | microsoft-v1.1 | VERIFIED_LOCAL_REFERENCE | 199/0.0283/29.4/72.3 | 3.15e+03 | 7.98e+03 | 21/9/42 | None |
| G300-1.06 | newer-base-v2 | VERIFIED_LOCAL_REFERENCE | 88.8/0.0422/50.7/99.5 | 3.87e+03 | 9.23e+03 | 51/27/285 | None |
| L300-weak | AC-OPF | VERIFIED_LOCAL_REFERENCE | 0/0/0/0 | 2.86e-11 | 7.82e-11 | N/A | None |
| L300-weak | DC-OPF | VERIFIED_LOCAL_REFERENCE | 25.8/N/A/6.98/20.6 | 7.74e-12 | N/A | N/A | None |
| L300-weak | microsoft-v1.1 | VERIFIED_LOCAL_REFERENCE | 195/0.0271/23.6/77 | 3.73e+03 | 8.9e+03 | 21/8/39 | None |
| L300-weak | newer-base-v2 | VERIFIED_LOCAL_REFERENCE | 107/0.0457/49.1/118 | 7.8e+03 | 2.12e+04 | 50/27/274 | None |
| L300-strong | AC-OPF | VERIFIED_LOCAL_REFERENCE | 0/0/0/0 | 2.19e-11 | 1.39e-10 | N/A | None |
| L300-strong | DC-OPF | VERIFIED_LOCAL_REFERENCE | 26.5/N/A/7.48/21.7 | 9.38e-12 | N/A | N/A | None |
| L300-strong | microsoft-v1.1 | VERIFIED_LOCAL_REFERENCE | 196/0.0267/23.2/77.5 | 3.79e+03 | 9.01e+03 | 21/8/40 | None |
| L300-strong | newer-base-v2 | VERIFIED_LOCAL_REFERENCE | 106/0.0432/48.6/95.7 | 3.24e+03 | 8.02e+03 | 52/26/283 | None |
| C300-L0.90-B0.50 | AC-OPF | VERIFIED_LOCAL_REFERENCE | 0/0/0/0 | 1.26e-11 | 1.14e-10 | N/A | None |
| C300-L0.90-B0.50 | DC-OPF | VERIFIED_LOCAL_REFERENCE | 18.2/N/A/5.52/17.2 | 3.27e-12 | N/A | N/A | None |
| C300-L0.90-B0.50 | microsoft-v1.1 | VERIFIED_LOCAL_REFERENCE | 192/0.0286/63.4/94.8 | 4.93e+03 | 1.26e+04 | 27/7/38 | None |
| C300-L0.90-B0.50 | newer-base-v2 | VERIFIED_LOCAL_REFERENCE | 127/0.0462/47.2/109 | 7.74e+03 | 2.14e+04 | 44/25/279 | None |
| C300-L0.90-B0.00 | AC-OPF | UNKNOWN | N/A | 1.52e-09 | 12.7 | N/A | None |
| C300-L0.90-B0.00 | DC-OPF | UNKNOWN | N/A | 3.27e-12 | N/A | N/A | None |
| C300-L0.90-B0.00 | microsoft-v1.1 | UNKNOWN | N/A | 4.86e+03 | 1.26e+04 | 27/7/37 | None |
| C300-L0.90-B0.00 | newer-base-v2 | UNKNOWN | N/A | 7.75e+03 | 2.14e+04 | 44/25/280 | None |
| C300-L1.06-B0.50 | AC-OPF | UNKNOWN | N/A | 1.18e-09 | 47.3 | N/A | None |
| C300-L1.06-B0.50 | DC-OPF | UNKNOWN | N/A | 7.28e-12 | N/A | N/A | None |
| C300-L1.06-B0.50 | microsoft-v1.1 | UNKNOWN | N/A | 3.13e+03 | 7.91e+03 | 20/9/43 | None |
| C300-L1.06-B0.50 | newer-base-v2 | UNKNOWN | N/A | 3.58e+03 | 9.2e+03 | 50/27/286 | None |
| C300-L1.06-B0.00 | AC-OPF | UNKNOWN | N/A | 3.34 | 465 | N/A | None |
| C300-L1.06-B0.00 | DC-OPF | UNKNOWN | N/A | 7.28e-12 | N/A | N/A | None |
| C300-L1.06-B0.00 | microsoft-v1.1 | UNKNOWN | N/A | 3.1e+03 | 7.88e+03 | 20/9/43 | None |
| C300-L1.06-B0.00 | newer-base-v2 | UNKNOWN | N/A | 3.43e+03 | 9.17e+03 | 50/28/287 | None |
| R300-base | AC-OPF | VERIFIED_LOCAL_REFERENCE | 0/0/0/0 | 3.44e-11 | 1.08e-10 | N/A | 0 |
| R300-base | DC-OPF | VERIFIED_LOCAL_REFERENCE | 69.4/N/A/17.1/65.3 | 4.92e-11 | N/A | N/A | 0 |
| R300-base | microsoft-v1.1 | VERIFIED_LOCAL_REFERENCE | 148/0.028/14.3/82.5 | 1.33e+03 | 1.38e+03 | 24/14/33 | 6 |
| R300-base | newer-base-v2 | VERIFIED_LOCAL_REFERENCE | 150/0.0484/12.9/121 | 3.09e+03 | 2.6e+04 | 28/16/286 | 11 |


### Reused600

| Input | Method | AC ref | G/V/θ/F MAE | P max | Q max | Clipped Pg/Qg/V | Overloads |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G600-0.90 | AC-OPF | VERIFIED_LOCAL_REFERENCE | 0/0/0/0 | 1.44e-11 | 8.54e-11 | N/A | 0 |
| G600-0.90 | DC-OPF | VERIFIED_LOCAL_REFERENCE | 17/N/A/5.27/16.1 | 5.02e-12 | N/A | N/A | 0 |
| G600-0.90 | microsoft-v1.1 | VERIFIED_LOCAL_REFERENCE | 135/0.0263/28/76.4 | 3.6e+03 | 1.25e+04 | 42/21/105 | 0 |
| G600-0.90 | newer-base-v2 | VERIFIED_LOCAL_REFERENCE | 126/0.0439/47/108 | 7.65e+03 | 2.14e+04 | 81/50/559 | 0 |
| G600-1.00 | AC-OPF | VERIFIED_LOCAL_REFERENCE | 0/0/0/0 | 2.03e-11 | 1.01e-10 | N/A | 0 |
| G600-1.00 | DC-OPF | VERIFIED_LOCAL_REFERENCE | 26.1/N/A/7.23/21.1 | 1.09e-11 | N/A | N/A | 0 |
| G600-1.00 | microsoft-v1.1 | VERIFIED_LOCAL_REFERENCE | 123/0.0267/30.2/71.5 | 1.14e+03 | 9.38e+03 | 39/20/99 | 0 |
| G600-1.00 | newer-base-v2 | VERIFIED_LOCAL_REFERENCE | 106/0.0422/49/94.7 | 4.92e+03 | 9.23e+03 | 97/54/567 | 0 |
| G600-1.06 | AC-OPF | VERIFIED_LOCAL_REFERENCE | 0/0/0/0 | 1.78e-11 | 1.43e-10 | N/A | 0 |
| G600-1.06 | DC-OPF | VERIFIED_LOCAL_REFERENCE | 37.9/N/A/7.2/23.4 | 9.46e-12 | N/A | N/A | 0 |
| G600-1.06 | microsoft-v1.1 | VERIFIED_LOCAL_REFERENCE | 120/0.0275/28.6/76.8 | 698 | 7.52e+03 | 37/18/87 | 0 |
| G600-1.06 | newer-base-v2 | VERIFIED_LOCAL_REFERENCE | 89.3/0.0419/51/95.6 | 5.35e+03 | 9.23e+03 | 102/54/573 | 0 |
| L600-Splus | AC-OPF | VERIFIED_LOCAL_REFERENCE | 0/0/0/0 | 2.25e-11 | 1.83e-10 | N/A | 0 |
| L600-Splus | DC-OPF | VERIFIED_LOCAL_REFERENCE | 31.6/N/A/36.5/38.6 | 6.62e-11 | N/A | N/A | 0 |
| L600-Splus | microsoft-v1.1 | VERIFIED_LOCAL_REFERENCE | 126/0.027/35.6/87.1 | 1.4e+03 | 9.34e+03 | 39/20/95 | 2 |
| L600-Splus | newer-base-v2 | VERIFIED_LOCAL_REFERENCE | 106/0.0435/34.3/103 | 5.08e+03 | 9.23e+03 | 96/54/557 | 2 |
| L600-Sminus | AC-OPF | VERIFIED_LOCAL_REFERENCE | 0/0/0/0 | 1.59e-11 | 1.22e-10 | N/A | 0 |
| L600-Sminus | DC-OPF | VERIFIED_LOCAL_REFERENCE | 31.6/N/A/36.3/38.6 | 8.1e-11 | N/A | N/A | 0 |
| L600-Sminus | microsoft-v1.1 | VERIFIED_LOCAL_REFERENCE | 120/0.0266/56/79.6 | 940 | 8.76e+03 | 38/19/92 | 0 |
| L600-Sminus | newer-base-v2 | VERIFIED_LOCAL_REFERENCE | 106/0.0435/73.7/101 | 5.02e+03 | 9.24e+03 | 96/54/557 | 0 |
| C600-L0.90-B0.50 | AC-OPF | VERIFIED_LOCAL_REFERENCE | 0/0/0/0 | 2.32e-11 | 7.27e-11 | N/A | 0 |
| C600-L0.90-B0.50 | DC-OPF | VERIFIED_LOCAL_REFERENCE | 18.2/N/A/5.52/17.2 | 5.02e-12 | N/A | N/A | 0 |
| C600-L0.90-B0.50 | microsoft-v1.1 | VERIFIED_LOCAL_REFERENCE | 134/0.0284/27.9/75.4 | 3.58e+03 | 1.25e+04 | 42/21/103 | 0 |
| C600-L0.90-B0.50 | newer-base-v2 | VERIFIED_LOCAL_REFERENCE | 125/0.0448/46.8/107 | 7.66e+03 | 2.14e+04 | 82/52/559 | 0 |
| C600-L0.90-B0.00 | AC-OPF | UNKNOWN | N/A | 1.53e-09 | 12.7 | N/A | 0 |
| C600-L0.90-B0.00 | DC-OPF | UNKNOWN | N/A | 5.02e-12 | N/A | N/A | 0 |
| C600-L0.90-B0.00 | microsoft-v1.1 | UNKNOWN | N/A | 3.56e+03 | 1.25e+04 | 42/21/102 | 0 |
| C600-L0.90-B0.00 | newer-base-v2 | UNKNOWN | N/A | 7.68e+03 | 2.14e+04 | 82/52/561 | 0 |
| C600-L1.06-B0.50 | AC-OPF | UNKNOWN | N/A | 1.18e-09 | 47.3 | N/A | 0 |
| C600-L1.06-B0.50 | DC-OPF | UNKNOWN | N/A | 9.46e-12 | N/A | N/A | 0 |
| C600-L1.06-B0.50 | microsoft-v1.1 | UNKNOWN | N/A | 680 | 7.48e+03 | 37/18/88 | 0 |
| C600-L1.06-B0.50 | newer-base-v2 | UNKNOWN | N/A | 5.21e+03 | 9.2e+03 | 101/54/573 | 0 |
| C600-L1.06-B0.00 | AC-OPF | UNKNOWN | N/A | 3.34 | 465 | N/A | 0 |
| C600-L1.06-B0.00 | DC-OPF | UNKNOWN | N/A | 9.46e-12 | N/A | N/A | 0 |
| C600-L1.06-B0.00 | microsoft-v1.1 | UNKNOWN | N/A | 656 | 7.45e+03 | 37/17/89 | 0 |
| C600-L1.06-B0.00 | newer-base-v2 | UNKNOWN | N/A | 5.16e+03 | 9.17e+03 | 98/54/571 | 0 |
| R600-base | AC-OPF | VERIFIED_LOCAL_REFERENCE | 0/0/0/0 | 2.07e-11 | 1.07e-10 | N/A | 0 |
| R600-base | DC-OPF | VERIFIED_LOCAL_REFERENCE | 69.4/N/A/17.1/65.2 | 3.51e-11 | N/A | N/A | 0 |
| R600-base | microsoft-v1.1 | VERIFIED_LOCAL_REFERENCE | 146/0.0272/40.4/102 | 615 | 3.19e+03 | 67/24/66 | 14 |
| R600-base | newer-base-v2 | VERIFIED_LOCAL_REFERENCE | 153/0.0484/13.4/114 | 2.6e+03 | 2.59e+04 | 54/30/578 | 20 |


## Representation controls: physics unchanged

Physical-equivalence checks restore all original bus/gen/branch/cost matrices exactly. Output arrays are mapped back to original buses/generators/branches, angles aligned once to the same REF. Controls distinguish ID renumbering from row-order dependence. Numerical solver output differences can arise from nonunique optima or different numerical paths; they are not automatically mapping errors. Model differences are properties of this evaluated input/preprocessing/backbone pipeline; their internal cause is not established.

| Input | Method | maxΔPg MW | maxΔQg MVAr | maxΔVm pu | max alignedΔθ deg | maxΔPflow MW |
| --- | --- | --- | --- | --- | --- | --- |
| REP-renumber-300 | AC-OPF | 4.72e-11 | 3.04e-11 | 4.24e-14 | 6.51e-12 | 7.75e-11 |
| REP-renumber-300 | DC-OPF | 0 | N/A | N/A | 0 | 0 |
| REP-renumber-300 | microsoft-v1.1 | 0 | 0 | 0 | 0 | 0 |
| REP-renumber-300 | newer-base-v2 | 0 | 0 | 0 | 0 | 0 |
| REP-reorder-300 | AC-OPF | 3.49e-11 | 6.44e-11 | 6.26e-14 | 4.09e-12 | 4.33e-11 |
| REP-reorder-300 | DC-OPF | 1.03e-10 | N/A | N/A | 1.53e-11 | 1.38e-10 |
| REP-reorder-300 | microsoft-v1.1 | 136 | 257 | 0.0714 | 146 | 3.19e+03 |
| REP-reorder-300 | newer-base-v2 | 451 | 140 | 0.12 | 12.9 | 5.33e+03 |
| REP-renumber-600 | AC-OPF | 4.77e-12 | 1.02e-10 | 5.91e-14 | 7.11e-13 | 2.44e-11 |
| REP-renumber-600 | DC-OPF | 0 | N/A | N/A | 0 | 0 |
| REP-renumber-600 | microsoft-v1.1 | 0 | 0 | 0 | 0 | 0 |
| REP-renumber-600 | newer-base-v2 | 0 | 0 | 0 | 0 | 0 |
| REP-reorder-600 | AC-OPF | 3.06e-11 | 7.45e-11 | 2.52e-14 | 7.53e-12 | 1.04e-10 |
| REP-reorder-600 | DC-OPF | 4.58e-10 | N/A | N/A | 6.85e-10 | 6.49e-09 |
| REP-reorder-600 | microsoft-v1.1 | 319 | 298 | 0.0947 | 57.2 | 1.56e+03 |
| REP-reorder-600 | newer-base-v2 | 428 | 136 | 0.12 | 11.6 | 4.57e+03 |


## Coverage, constraints and fair interpretation

Original MATPOWER300 has no finite internal ratings;600 covers only two synthetic600MVA ties. RATE80 interventions instead use complete published PGLib variants with inherited finite ratings, not ratings transplanted into original MATPOWER. Their baselines are R300/R600, not G300/G600. Branch status0 and generator status0 remain explicit source rows. Both models receive the documented active graph; only offline generator outputs are expanded to known physical zero. This is an availability mapping, not solved-label input or a repair. Active-row source mappings, source/checkpoint/default settings and actual pre/post clips are retained.

Independent FP64 Ybus and exact branch-sum agree below1e-6MW/MVAr on saved AC/model states. Every accepted reference passes original input constraints. New active-set label-poison audits pass for generator outage and tie outage,8 extra neural audit forwards. Native points are saved before evaluation. No sigmoid override, training, PF completion, OPF repair or result-driven case replacement occurred. Narrow physical parameter edits are mechanism diagnostics, not claims of physically redesigned equipment or realistic uncertainty distributions.

These are inspected bounded contrasts. Lower residuals, fewer clips, bound compliance or a feasible local reference do not individually establish a useful operating point. No universal monotonicity, training-distribution cause, stability margin, solver speedup or publication novelty is claimed. The representation finding in particular limits attributing changes entirely to electrical sensitivity.

## Reproduction and artifacts

Protocol:docs/experiments/GSFM-016.md; code:experiments/gsfm016. Existing read-only scientific Python3.11/PyTorch/PyG/PYPOWER and Julia/PowerModels/Ipopt environments. Exact checkpoint/source pins and raw counts are retained. Local-only scientific inputs/states/logs are SHA256 indexed in artifact-inventory.json; hashes alone are not remote artifact access. Original15 and earlier states remain unchanged.

```sh
PY=/Users/ninadsonawane/workspace/research-dev/GridSFM/model/.venv/bin/python
O=results/comparisons/GSFM-016/20261024-electrical-mechanisms
# Fresh output only; preparation/runner refuse overwrite.
"$PY" -B experiments/gsfm016/prepare.py
"$PY" -B experiments/gsfm016/run_cases.py "$O" 16
"$PY" -B experiments/gsfm016/capture_rated.py
"$PY" -B experiments/gsfm016/analyze.py
"$PY" -B experiments/gsfm016/report.py
```

Full numerical CSV includes Pg/Qg/Vm/angles/active-flow accuracy; P/Q balance; Pg/Qg/Vm/angle/thermal excesses; Q-bound activity, objectives and validity. Separate clipping-summary.csv and paired-contrasts.csv preserve nonmonotonic/mixed results and all UNKNOWN cases.
