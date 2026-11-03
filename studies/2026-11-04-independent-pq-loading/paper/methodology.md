# Methodology and fixed scope

Question: How do frozen GridSFM state accuracy and physical feasibility change under independent active and reactive loading changes?

The study uses original MATPOWER 8.1 case300, the existing interconnected two-copy case300, and PGLib v23.07 pglib_opf_case500_goc. The latter is the exact case denoted case500goc in this package. Methods are AC-OPF, DC-OPF, Microsoft frozen V1.1, and the newer frozen base V2. No training, checkpoint selection, external output clipping, PF completion, or OPF repair is applied. Native release clipping remains enabled and its inputs and outputs are retained. These results evaluate native frozen inference, not the complete adapted/projection workflow in the newer paper.

## Frozen identities and construction

`manifest.json` records exact case hashes, checkpoint hashes, source revisions, mappings, settings and tolerances. The imported research source is commit acd3986c5858696e238bf7628ac0980a90a42043. The executed files have SHA-256 records in each phase completion record; the final artifact inventory identifies the final source and every result. Baseline acceptance uses the code frozen before baseline execution. Later additions implement orchestration, plots and analysis without changing the evaluator equations or tolerances.

case300 has 300 buses, 69 generators and 411 branches. All RATE_A values are zero, meaning no applicable thermal rating. The two-copy system has 600 buses, 138 generators and 824 branches, with two parallel synthetic ties at original bus 231 in each copy. Each tie has r=0.002 pu, x=0.019 pu, b=1.127 pu, rating 600 MVA, zero phase shift and unity effective tap on the 100-MVA base. Impedance and charging copy source branch 45; the rating is a disclosed study-design value. Original internal branches remain unrated. The second reference bus becomes a voltage-controlled bus, leaving one angle reference. This constructed network is not a standard IEEE 600-bus benchmark.

case500goc has 500 buses, 224 generator rows (171 online), and 733 branch rows (728 online and rated). Its original reference bus 311 hosts an offline generator. An OPF phase reference need not host online generation; the old PF-specific validation assertion was removed without changing the input case or its reference bus. Offline generator rows are retained with zero output. Online rows alone enter generation-accuracy averages.

## Evaluator

Reconstruct V_i = v_i exp(j theta_i). Use the prescribed scenario demand, not a demand inferred from the predicted state. Evaluate complex bus mismatch as r = Cg(Pg+jQg) - (Pd+jQd) - baseMVA V conj(Ybus V). Independently stamp both ends of each branch, including transformer taps, shifts, line charging, status and bus shunts; require agreement with PYPOWER Ybus/Yf/Yt within 1e-6 MVA.

State errors are equally weighted MAE and RMSE of online-generator Pg (MW), Qg (MVAr), all-bus voltage magnitude (pu), and bus angle (degrees). Subtract the original reference-bus angle from each state, then wrap prediction-minus-reference differences into [-180,180). Valid checked AC references are required for state errors. They are local optima, not certified global optima.

For P and Q mismatches separately, report maximum absolute, mean absolute, p95 and violating-bus count over all buses. p95 uses NumPy linear interpolation. The balance tolerance is 1e-3 MW/MVAr per bus. Equipment excess is the nonnegative amount outside each original bound. Count an item when its excess exceeds tolerance. Report maximum, mean over all eligible items including zeros, and an additional mean over violating items. Generator and finite thermal tolerances are 1e-3 MW/MVAr and 1e-3 MVA; voltage is 1e-4 pu; applicable branch angle difference is 1e-3 degrees. Thermal excess uses the larger apparent flow magnitude at either end. Branch angle bounds are part of equipment checking. Both zero angle bounds mean no angle constraint; +/-360 indicate unbounded sides.

Joint AC feasibility requires every applicable balance and equipment check. Unrated thermal constraints are N/A, not passed finite ratings. Native DC uses its own linear active-power equations, including phase shifts, taps and fixed conductance demand. Native DC Q, voltage, apparent thermal limits and full AC feasibility are N/A. DC Pg and reference-aligned angle error remain comparable against valid AC references.

## Reference and evaluator validation

AC-OPF uses PowerModels ACP and Ipopt, tol=1e-9, constraint violation tolerance=1e-10, acceptable tolerance=1e-9, bound relaxation=0, maximum 3000 iterations and 120 seconds per attempt. Use the deterministic default start and one flat retry if needed. Preserve every failed attempt. Accept a reference only if the solver reports local success and the common evaluator independently passes. The MATPOWER-to-PowerModels parser is checked against original loads, shunts, branches, limits and costs.

DC-OPF uses PYPOWER PIPS 200 with 150 iterations, feasibility tolerance=1e-10 and gradient/complementarity tolerances=1e-9. Optional missing generator columns are zero-extended at the PYPOWER boundary to preserve MATPOWER v2 semantics. This does not change original case matrices.

All three baseline references pass. A +10 MW / +7 MVAr generator perturbation changes only the expected signed bus mismatch. Deliberate +5 MW generation and +0.01 pu voltage exceedances register; shifting every angle by 35 degrees leaves aligned error unchanged. A one-MVA both-end thermal exceedance registers correctly. `evaluator-validation.json` records the checks.

## Scenarios and sensitivity

The main grid is P-only (lambda PD0,QD0), Q-only (PD0,lambda QD0), and combined (lambda PD0,lambda QD0), with lambda = 1, 1.01, 1.02, 1.05 and 1.10. The repeated nominal point is computed once per network, giving 13 unique inputs per network and 39 total. Signed loads retain their original sign; equipment remains fixed.

The integrated case-3 study reproduces original case300 absolute combined factors 0.92, 0.93, 0.9301, 0.9303, 0.935, 0.94, 0.945 and 0.95, plus P-only and Q-only controls at 0.935, 0.94 and 0.95 while the other component remains 0.93. These are 14 additional inputs. The relative baseline is 0.93, so absolute 0.94 is relative 0.94/0.93 = 1.010752688. Original controls come from GSFM-020; this run uses fresh inference and solves, with historical files preserved.

The final sensitivity test adds P-only and Q-only factor 1.005 in each network (six inputs). Compare (x(1+h)-x(1))/h at h=0.005 and h=0.01, and the adjacent 1.01-to-1.02 interval, for V, Pg and Qg. Report response MAE/RMSE, direction agreement and the model/reference response L2 magnitude ratio. Keep baseline prediction offsets separate. Direction counts exclude reference changes <=1e-6 pu for V or <=1e-3 MW/MVAr for generation; flat model responses are disagreements when the reference is material. Inspect active reference constraints at both endpoints using the frozen equipment tolerances. These are finite differences, not an exact derivative claim at active-set changes.

All 59 unique inputs and all four method slots are retained. Reference failures remain UNKNOWN. Feasibility percentages use attempted-input denominators and separately report accepted references and returned outputs. No inference about universal feasibility or population accuracy follows from this finite deterministic grid.
