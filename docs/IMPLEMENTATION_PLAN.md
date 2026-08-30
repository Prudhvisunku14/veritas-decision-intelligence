# Implementation Plan

## Phase 1 - Synthetic data

Generate realistic multi-source history with seasonality, weekend effects, promotions, source-specific native grains, sparse-history SKU, and an injected North-region incident.

## Phase 2 - Data layer

Load Bronze CSVs into DuckDB and build Gold views:

- `kpi_region_daily`
- `product_performance_daily`
- `inventory_daily`

## Phase 3 - Semantic layer

Load five versioned KPI contracts from YAML.

## Phase 4 - Analytics

Implement expected baseline, prediction interval, materiality, Shapley KPI bridge, and Level-2 evidence diagnostics.

## Phase 5 - Evidence and abstention

Create the Evidence Object and Evidence Confidence Score.

## Phase 6 - Security and actions

Enforce role/region access before querying data and return actions only from playbooks.

## Phase 7 - Narrative and UX

Use a deterministic fallback first; optionally connect an external LLM.

## Phase 8 - Feedback and telemetry

Record corrections, action acceptance, timing, model usage, and cost metadata.
