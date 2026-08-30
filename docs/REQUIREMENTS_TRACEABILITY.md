# Round 2 Requirements Traceability

| Challenge expectation | Prototype implementation | Demo surface |
|---|---|---|
| 3-5 connected KPIs | Revenue, Orders, Conversion Rate, AOV, Gross Margin | `/api/kpis`, UI KPI selector |
| 2-3 heterogeneous sources | Sales order lines, marketing/campaign daily data, inventory 4-hour snapshots | `data/bronze/` and data dictionary |
| Different grains/cadences | Native grains preserved; Gold tables reconcile only at valid grains | `docs/DATA_DICTIONARY.md` |
| Semantic/KPI contract | Versioned YAML definitions, formulas, owners, thresholds, bridge/driver hierarchy | `backend/app/knowledge/kpi_contracts.yaml` |
| Material KPI detection | Holt-Winters expected baseline + residual + business-impact materiality | Evidence Object |
| Multi-factor movement | North Revenue incident with Traffic, Conversion, AOV bridge | Main demo |
| Driver ranking | Level-2 evidence diagnosis for marketing, stock, checkout, pricing/mix | UI Level 2 panel |
| Traceable evidence | Source freshness, DQ, methods, query id, lineage, contradiction list | Evidence Object |
| Uncertainty/abstention | Deterministic Evidence Confidence Score and LOW-confidence abstention | `scenario=degraded` |
| Two personas | CEO and North Regional Manager (plus Analyst/Marketing Manager) | `X-Demo-User` header / UI |
| Sparse-history scenario | P020 launched 20 days before dataset end; cohort benchmark + confidence cap | `/api/sparse-history` |
| Role-based security | Authorization before scoped data query; North manager denied South | HTTP 403 demo |
| Practical actions | Controlled YAML playbooks with owner, lever, expected impact, monitoring | Governed Actions panel |
| Feedback learning | Corrections stored immediately, queued for validation/batch recalibration | `/api/feedback` |
| LLM vs non-LLM breakdown | Quantitative tasks deterministic; LLM only narrative/persona/action phrasing | `ARCHITECTURE.md` |
| Runtime telemetry | Total/analytics/LLM latency, calls, tokens, model, cost field | Telemetry panel |
| Ground-truth validation | Counterfactual/Shapley synthetic driver table isolated from live engine | `/api/evaluation/ground-truth` |
