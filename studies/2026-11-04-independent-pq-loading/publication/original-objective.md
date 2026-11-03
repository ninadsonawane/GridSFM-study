**Follow this order. Start the paper’s outline and methodology early; finalize its claims after the experiments.**

1. **Fix the study scope and research question**\
   Benchmark **case300, interconnected two-copy case300, and `case500goc`**, using **AC-OPF, DC-OPF, frozen V1, and frozen V2**.\
   Working question: *How do GridSFM’s state accuracy and physical feasibility change under independent P/Q loading changes?*\
   Open a paper outline and confirm the venue, page limit, and deadline with Dr. Li.
2. **Freeze cases, models, and settings**\
   Record exact case files, checkpoint versions, solver settings, and code revision. Verify tie-line parameters, units, bus/generator mapping, and preprocessing. Confirm training exposure separately for each checkpoint.\
   **Output:** a reproducible case/model manifest.
3. **Define and implement the common evaluator**\
   Include only the selected categories:
   - **State accuracy:** Pg,Qg,V MAE/RMSE; reference-aligned angle errors.
   - **P/Q balance:** maximum absolute, mean absolute, p95 mismatch; violating-bus count.
   - **Equipment constraints:** count, maximum and mean violation for generator, voltage and branch limits.
   - **Overall feasibility:** pass/fail per scenario and percentage passing all applicable constraints.
4. Fix numerical tolerances, units, and averaging definitions beforehand. Use prescribed loads and check branch flows at both ends.
5. **Obtain baseline AC-OPF references and validate the evaluator**\
   Start with nominal loads and original limits. Independently check each AC-OPF solution using the evaluator.\
   Confirm that a known generation perturbation produces the expected mismatch and an exceeded bound registers correctly. Investigate reference failures before declaring physical infeasibility.\
   **Output:** three checked baseline references and a validated evaluator.
6. **Complete the baseline comparisons**\
   Run DC-OPF, V1, and V2 on the identical baseline inputs. Evaluate raw model outputs and save complete states alongside summary metrics.\
   Produce **one baseline table per network**. Mark unsupported native DC Q/voltage and full AC-feasibility fields as **N/A**.\
   These tables and the methodology section are the first material to review with Dr. Li.
7. **Freeze the loading scenarios**\
   For each network, use:
   - **P-only:** (PD0,QD0).
   - **Q-only:** (PD0,QD0).
   - **Combined:** (PD0,QD0).
8. Start with =1.00,1.01,1.02,1.05,1.10, keeping equipment parameters fixed.\
   **Include case 3 within this main study:** reproduce its original 93–94% operating points and controls, with nearby refinement points. Record absolute loading separately from loading relative to any adjusted baseline.
9. **Run the full main benchmark**\
   For every scenario, obtain a checked AC-OPF reference, run the other methods, and apply the same evaluator.\
   Save scenario IDs, settings, statuses, and detailed bus/generator/branch outputs. Record reference failures explicitly; state-error comparisons need valid references, while physical residuals can still be evaluated directly.
10. **Analyze the loading results, including case 3**\
    Plot the selected metrics against loading and compare V1/V2 within each network.\
    For case 3, track maximum, p95, and violating-bus count together. Identify improving/worsening buses and inspect neighboring voltages, reactive flows, and generator Q.\
    **Output:** loading plots, feasibility summaries, and an integrated case-3 explanation.
11. **Perform the final focused experimental test: sensitivity**\
    Using small adjacent P-only/Q-only increments, compare voltage and generator P/Q changes per loading increment against AC-OPF.\
    Check **direction and magnitude**, repeat with another step size, and inspect reference constraint changes near sharp responses. Separate baseline prediction offsets from response errors.
12. **Complete the paper draft**

Organize it around methodology, baseline results, loading results including case 3, focused sensitivity, and limitations. Finalize contributions and the abstract from the actual findings.