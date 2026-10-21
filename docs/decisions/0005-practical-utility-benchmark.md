# Decision 0005: practical utility under bounded target-grid adaptation

22 October 2026. User-authorized hardware follow-up: [GSFM-007 / Experiment 10](../experiments/GSFM-007.md). READY, not yet run by the planner.

The user requested adaptation, simple baselines, explanatory tests and additional networks to support a five-page empirical conference paper, and delegated the second-network choice. Keep original MATPOWER case300 primary and add pinned PGLib IEEE118 as an independent, thermally rated second network. This supersedes the older restriction to case300 plus a constructed duplicate. case300x2 remains preserved and deferred; it is not independent replication. Selection of IEEE118 is based on topology diversity, available ratings, verified structural conversion and compute budget, not model performance.

Compare conventional AC-OPF, frozen newer GridSFM, full-regression adaptation and ridge. Use released native PF completion followed by an explicitly labeled common external OPF refinement. Separate prediction, PF convergence, operating limits and final feasible-solve utility. Three seeds per grid at 1,500 updates, fixed source schedules and official gated validation, then fresh fixed candidates and control substitutions, fit a single bounded five-hour task subject to runtime gates.

The earlier post-Experiment-9 note's proposed no-training Experiment 10 / separate Experiment 11 split is superseded by this integrated task. Older KCL and LoRA studies remain historical evidence, not the new main comparison. Training within this task is explicitly requested; no paid compute, external messages or submission are authorized. Results and publication value remain unknown until execution and review.
