# Proposed five-page paper outline

Status: outline only, no results paper, 21 October 2026.

Title: **Matched Low-Rank Adaptation of GridSFM Under Inter-Area Transfer Stress**

Question: can fixed-rank FFN LoRA recover matched full-FT accuracy and physical-feasibility gains at 100/500 target examples on one validated constructed interconnection, including load shift and a withheld circuit outage?

Hypothesis contribution statements:

1. We test whether target adaptation improves accuracy and original-equipment feasibility under controlled area-load shifts.
2. We quantify the trade-off between FFN LoRA and full FT with a shared checkpoint, splits and evaluation, without inferring memory savings from parameter counts.
3. We test whether improvements persist for one withheld parallel-circuit outage and release the provenance, conversion checks and unsuccessful cases.

Allocation: title/abstract/introduction0.65page; problem/construction0.90; protocol1.05; results1.35; limitations/conclusion0.35; references0.70. Total5.00including references. Max150word abstract. No speculative numerical abstract or synthetic placeholder findings.

Visual assets (two figures, one table):

- Fig.1 (~0.3page): AreaA andB boxes, original231↔231 terminals345kV, two labeled circuits, one reference; below it source→neutral input/labels→model→independent evaluator. Mermaid source is in the initial report; final vector drawing must retain IDs/units and say constructed.
- TableI (~0.45page): frozen, LoRA100/500, FT100/500. Group by nominal/load stress/outage. Columns: n accepted/attempted, cost median/p95, residual p95, joint pass fraction, trainable parameters, peak memory. All entries currently blank. Show3seed range or interval, not a single best seed. Limit table width by reporting only primary endpoints and put full metrics in repository.
- Fig.2 (~0.5page): left, physical P/Q residual distribution against realized area exchange, with nominal/outage distinction; right, method differences across seeds/budgets, raw joint pass fraction. Use fixed axes and include failed/nonfinite predictions as counts. No fabricated lines.

Figure/table sources: results/templates/summary.csv is an empty schema, manifests/scenarios/proposed-v1.json is a design only, and results/templates/run-record.json defines provenance. Each eventual plotting script must consume a committed summary derived from per-scenario outputs and refuse missing values; never fill blank cells with zeros. Figure rendering is deferred until actual data exist, so no numerical figures are claimed reproducible yet.

References: use paper/references.bib; select6–9closest items that fit the page budget and actual final claims. Cite official MATPOWER/code versions in methods, possibly footnote/reproducibility link. Defer author order/affiliations to the team.

Fallback title: **Physical Feasibility of Frozen GridSFM Predictions on a Constructed Two-Area System**. Remove adaptation hypotheses/table rows; explain the narrow robustness gap and integration findings honestly. Scientific merit must be reassessed with the professor; no acceptance forecast.
