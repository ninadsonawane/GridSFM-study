1. What ran: twelve fresh pretrained full-regression fits, S/C/E/C_m × seeds11/22/33, all1000 updates, original50/10 train/validation, and fresh locked ordinary/spatial/higher-load evaluation with counts {'ordinary': {'accepted': 30, 'attempted': 30}, 'higher_load': {'accepted': 30, 'attempted': 30}, 'spatial': {'accepted': 28, 'attempted': 30}}.

2. What improved: validation-selected ordinary E-minus-C_m joint-log-balance changes by seed11/22/33 are [-0.8379895242186216, -0.3737262475734134, -0.9287331248231173]; mean -0.713483, range [-0.9287331248231173, -0.3737262475734134]. Negative favors E; separate MW/MVAr, state/cost and fixed200/500/1000 effects are in contrasts.json and matched-steps.csv.

3. What failed: every method/snapshot/slice has zero strictly feasible raw predictions. Ridge ordinary J=2.649312; compare it with every neural arm before discussing utility. No infeasible raw cost is an achievable saving.

4. What the magnitude control changed: rho=1.789784409, from20 valid first-training-case ratios, range [1.7256417824817376, 1.8278548475244945]. It was fixed before training. Seed11 E trajectory shows later gradient norms/directions differ, so this is an initial magnitude control only. All primary seed signs favor E beyond this control.

5. Next paper decision: E improves the primary joint-balance score beyond this particular initial gradient-norm control for all three training-order seeds. A sign reversal at a matched fixed endpoint shows endpoint sensitivity; uniform superiority is not established. This remains a candidate numerical-loss consistency study for professor review, not an established practical OPF replacement or novelty claim. Do not automatically expand the experiment matrix.
