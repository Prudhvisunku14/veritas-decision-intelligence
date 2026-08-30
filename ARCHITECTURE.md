# Architecture

```text
Sales / Marketing / Inventory
            |
         Ingestion
            |
       Data quality
            |
     Reconciliation
            |
 Bronze -> Silver -> Gold
            |
      Semantic contracts
            |
 Authentication + authorization
            |
       Scoped SQL query
            |
       KPI computation
            |
  Expected baseline / forecast
            |
 Materiality + anomaly gate
            |
    Level 1 KPI bridge
 Revenue = Sessions x Conversion x AOV
            |
 Interaction-aware Shapley bridge
            |
   Level 2 business diagnosis
 Marketing / Stock / Funnel / Mix / Price
            |
       Hypothesis ranking
            |
       Evidence assembly
            |
 Evidence Confidence Score
       /            \
 adequate          low
    |               |
Evidence Object   Abstain
    |
Structured lookup + limited RAG
    |
Persona-aware narrative layer
    |
LLM or deterministic fallback
    |
Controlled action playbook
    |
Decision-right validation
    |
User workspace
    |
Feedback + outcome tracking
```

Security, lineage, freshness, auditability, latency, token usage, cost, and model version are horizontal concerns.

## Level 1 vs Level 2

Level 1 answers **what mathematically produced the KPI movement**. For Revenue:

`Revenue = Sessions x Conversion Rate x AOV`

The bridge uses Shapley allocation across the three multiplicative factors so interaction effects are distributed fairly and all contributions reconcile exactly to the observed Revenue delta.

Level 2 answers **why each bridge component likely moved**. It does not create a second set of additive Revenue contributions.

- Traffic: marketing spend, campaign performance, seasonality.
- Conversion: stock availability, checkout/funnel degradation, pricing friction.
- AOV: product/category mix, pricing, discounting.

## Evidence Confidence Score

The ECS is a composite evidence-quality score, not a posterior probability:

```text
ECS =
    0.25 * data_quality
  + 0.20 * freshness
  + 0.20 * historical_sufficiency
  + 0.20 * statistical_strength
  + 0.15 * cross_source_consistency
  - contradiction_penalty
```

Bands:

- HIGH: ECS >= 0.75
- MEDIUM: 0.50 <= ECS < 0.75
- LOW: ECS < 0.50 -> abstain on the unsupported claim

## LLM boundary

LLM allowed:

- natural-language intent parsing,
- persona-specific explanation,
- summarizing already-validated evidence,
- phrasing already-approved actions.

LLM prohibited:

- KPI arithmetic,
- anomaly scoring,
- contribution calculation,
- confidence scoring,
- security decisions,
- free-form action invention,
- expected-impact estimation.
