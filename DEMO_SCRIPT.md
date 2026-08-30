# Demo Script

## 1. Open with the problem

"Most BI tools show what moved. Veritas KPI detects what matters, proves what changed, diagnoses likely business causes, communicates uncertainty, and returns only authorized actions."

## 2. Show the main Revenue incident

Login as `ceo` and select North / Revenue.

Expected story:

- actual Revenue is materially below its seasonal baseline,
- prediction interval is breached,
- business impact is material,
- the engine creates a Level-1 bridge for Traffic, Conversion, and AOV.

Point out that these three bridge components reconcile to the total Revenue delta.

## 3. Show Level-2 diagnosis

Expand "Why?":

- Traffic -> marketing spend reduction; lower evidence confidence because marketing is stale/contradictory.
- Conversion -> stock availability and checkout/funnel degradation.
- AOV -> product-mix/pricing shift.

Explain that Level-2 diagnoses are not added to Level-1 percentages, avoiding double counting.

## 4. Show evidence and lineage

Open the Evidence Object panel and point to:

- source tables,
- freshness,
- methods,
- prediction interval,
- bridge contributions,
- evidence confidence,
- contradictory evidence,
- lineage/query id.

## 5. Show abstention

Switch to degraded evidence mode.

The engine should still state the known Revenue and bridge movement but refuse to attribute the Traffic component confidently to marketing until the stale/contradictory feed is refreshed.

## 6. Show persona difference

Compare `ceo` with `north_mgr`.

- CEO gets enterprise impact and owner-oriented actions.
- North manager gets North-specific operational detail.

## 7. Show security

As `north_mgr`, request `South`.

The API should reject the request before any South data query is executed.

## 8. Show action engine

Actions should come from the playbook, for example:

- replenish high-impact stock-outs,
- investigate checkout degradation,
- review North marketing allocation after the marketing feed is validated.

The LLM may rephrase them but cannot invent a new action.

## 9. Show feedback and telemetry

Submit a correction. Explain it is stored for validated, scheduled recalibration rather than instantly changing model weights.

Show:

- total latency,
- SQL/analytics/LLM latency,
- model calls,
- token usage,
- estimated cost,
- fallback mode when no LLM key is configured.
