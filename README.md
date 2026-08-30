# Veritas KPI - BusinessIntelligence.ai Round 2

Veritas KPI is an evidence-grounded KPI intelligence-to-action prototype for the BusinessIntelligence.ai Round 2 challenge.

It demonstrates a governed pipeline that:

1. detects material KPI movements,
2. reconciles heterogeneous data sources,
3. decomposes KPI changes with deterministic analytics (Shapley decomposition),
4. diagnoses likely business drivers (Level 2),
5. packages evidence and uncertainty into a structured Evidence Object,
6. abstains when evidence is weak or contradictory,
7. generates persona-specific narratives without letting the LLM invent numbers,
8. recommends actions from a controlled playbook with decision-right checks,
9. captures feedback and runtime telemetry.

## Core design principle

**SQL/statistics determine quantitative truth -> Evidence Object packages truth and uncertainty -> LLM explains and personalizes -> business rules control actions.**

The LLM is never used to calculate KPI values, anomaly scores, bridge contributions, confidence scores, access permissions, or expected impact.

## Prototype stack

- Python 3.11+
- Pandas / NumPy
- DuckDB
- FastAPI
- statsmodels / scipy / scikit-learn
- Streamlit / Plotly
- YAML semantic contracts and action playbooks
- Optional Anthropic/Claude adapter; deterministic template fallback works with no API key
- Docker / Docker Compose

## Repository structure

```text
Veritas_KPI_Round2_Submission/
|-- README.md
|-- SUBMISSION.md
|-- ARCHITECTURE.md
|-- DEMO_SCRIPT.md
|-- VERIFICATION.md
|-- STATUS.md
|-- requirements.txt
|-- .env.example
|-- docker-compose.yml
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- config.py
|   |   |-- db.py
|   |   |-- schemas.py
|   |   |-- security.py
|   |   |-- services/
|   |   |   |-- analytics.py
|   |   |   |-- evidence.py
|   |   |   |-- narrative.py
|   |   |   |-- actions.py
|   |   |   `-- context.py
|   |   `-- knowledge/
|   |       |-- kpi_contracts.yaml
|   |       |-- action_playbooks.yaml
|   |       `-- policies.md
|   `-- tests/
|-- frontend/
|   `-- streamlit_app.py
|-- scripts/
|   |-- generate_synthetic_data.py
|   |-- init_duckdb.py
|   |-- bootstrap.py
|   `-- evaluate_system.py
|-- data/
|   |-- bronze/
|   |-- gold/
|   `-- metadata/
`-- docs/
    |-- IMPLEMENTATION_PLAN.md
    |-- JUDGE_QA.md
    |-- DATA_DICTIONARY.md
    `-- REQUIREMENTS_TRACEABILITY.md
```

## Quick start

### 1. Create environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate synthetic data and initialize DuckDB

```bash
python scripts/bootstrap.py
```

This creates 12-18 months of synthetic Sales, Marketing, and Inventory data plus hidden ground-truth driver metadata for evaluation.

### 3. Run full test suite & system evaluation

```bash
python -m pytest backend/tests -q
python scripts/evaluate_system.py
```

### 4. Start API server

```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```

Open API docs at `http://localhost:8000/docs`.

### 5. Start Streamlit UI

In another terminal:

```bash
python -m streamlit run frontend/streamlit_app.py
```

The UI expects the API at `http://localhost:8000` by default.

## Demo users

| Demo user | Role | Scope |
|---|---|---|
| `ceo` | CEO/CFO | All regions and KPIs |
| `north_mgr` | Regional Manager | North only |
| `marketing_mgr` | Marketing Manager | Marketing-related views (No Gross Margin) |
| `analyst` | Analyst | All regions, detailed read access |

The prototype uses a demo-user header (`X-Demo-User`) for deterministic testing. The security module is intentionally isolated so it can be replaced with JWT/OIDC in production.

## Main demo scenario

A multi-week North-region revenue deterioration (-13.89% Revenue drop, Materiality 0.702) is injected into the synthetic generator using independent interventions:

- marketing spend and traffic reduction,
- checkout/funnel conversion degradation,
- stock availability deterioration,
- adverse product-mix shift,
- a small positive price offset.

The engine first explains **what moved** with a Level-1 KPI bridge:

```text
Revenue = Sessions x Conversion Rate x AOV
```

It then explains **why those components moved** using Level-2 business-driver diagnosis. This avoids double counting causes that sit at different points in the business chain.

## Required scenarios included

- material KPI anomaly (-13.89% revenue drop, materiality score 0.702),
- multi-factor KPI bridge and driver diagnosis,
- CEO vs Regional Manager narratives,
- low-confidence/stale-data abstention,
- sparse-history/new-product handling (`P020` cohort benchmarking),
- role-based access denial (`north_mgr` denied `South`),
- analyst feedback capture,
- latency/token/cost telemetry.

## LLM mode

The repository works 100% offline without an API key. By default:

```env
LLM_PROVIDER=template
```

To use Anthropic, copy `.env.example` to `.env`, set:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=...
```

The model receives only the authorized Evidence Object and allowed contextual snippets. If the external LLM fails, the deterministic template narrative remains available.

## Evaluation Results

Run `python scripts/evaluate_system.py`:
- Anomaly Precision / Recall / F1: `1.0 / 1.0 / 1.0`
- Shapley Bridge Reconciliation Error: `3.55e-15` (Exact float precision)
- Top-1 & Top-2 Driver Recovery: `100%`
- Abstention Correctness Rate: `100%`
- Security Pass Rate: `100%`
- Sparse History Pass Rate: `100%`
- Numeric Grounding Rate: `100%`

## Submission checklist

See `SUBMISSION.md` for the final hackathon packaging checklist and `DEMO_SCRIPT.md` for a judge-facing walkthrough.
