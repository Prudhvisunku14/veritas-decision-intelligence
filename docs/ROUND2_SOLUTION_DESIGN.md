# KPI Intelligence-to-Action Engine — Round 2 Solution Design

### BusinessIntelligence.ai Track

> **Revision note:** this version incorporates a technical review's 12 architectural corrections (two-level decomposition, corrected Revenue formula, native grains, counterfactual ground truth, Evidence Confidence Score, DiD, pre-query authorization, controlled RAG, periodic feedback) **plus a second round of internal-consistency fixes**: corrected data-source grain labels in the top-level diagram, corrected semantic-contract lineage path, fixed a units error in the Evidence Object's INR values (was off by 10×–1000×), corrected the Evidence Confidence Score example to 0.69/MEDIUM (0.79 would contradict the stated ≥0.75 HIGH threshold), removed remaining t-test/CausalImpact references from the LLM-vs-non-LLM table, tech stack, and judge answers, redesigned the UI wireframe and main walkthrough to visually separate Level 1 (bridge) from Level 2 (diagnosis) instead of listing them as one flat additive bar chart, renamed the ground-truth "conversion (stock-out driven)" driver to an independent "checkout/funnel degradation" so injected drivers don't overlap, and reworded the abstention/feedback narratives to never add a Level-1 pp value to a Level-2 confidence score.

---

## A. What the Competition Is Actually Asking

**1. What are the organizers asking us to build?**
Not a dashboard, not a chatbot — a **decision-support system** that closes the loop: *detect → explain → prove → recommend → act → learn*. It must independently determine when a KPI move matters, use real analytical methods to find *why*, package that as evidence, and only then let an LLM *narrate* it in a role-appropriate way, followed by a validated, authorized action.

**2. Dashboard vs. LLM chatbot vs. requested solution**

| Ordinary Dashboard LLM Chatbot on data Requested Engine  |                         |                                                      |                                                              |
| -------------------------------------------------------- | ----------------------- | ---------------------------------------------------- | ------------------------------------------------------------ |
| Detects what matters                                     | No — human scans charts | No — waits for a question                            | Yes — materiality engine flags it                            |
| Explains why                                             | No                      | Guesses from prompt context, may hallucinate numbers | Yes — deterministic contribution analysis, LLM only narrates |
| Knows its own uncertainty                                | No                      | No — always answers confidently                      | Yes — confidence engine + abstention                         |
| Adapts to role                                           | Manual filters          | Same answer to everyone (or leaks data)              | Persona engine + RBAC before LLM ever sees data              |
| Recommends action                                        | No                      | Free-text suggestion, not validated                  | Rule/playbook-validated actions with owner & expected impact |
| Learns                                                   | No                      | No                                                   | Feedback loop recalibrates thresholds/ranking                |

**3. Top 5–7 capabilities judges will evaluate**

1. Correct separation of LLM vs. deterministic computation (no hallucinated numbers).
2. Credibility of driver/root-cause attribution (does it recover a *known* ground truth?).
3. Honest uncertainty — does it abstain when it should?
4. Persona-aware output that isn't just re-worded but genuinely re-scoped.
5. Security — unauthorized data never reaches the LLM or the user.
6. Actionability — recommendations tied to owners, decision rights, expected impact.
7. Engineering realism — telemetry, cost, latency, feasibility for a real enterprise.

**4. Mandatory vs. optional**

- **Mandatory:** multi-source reconciliation, KPI semantic contracts, materiality/anomaly detection, driver ranking, evidence object, confidence + abstention, persona narratives, RBAC before LLM, action recommendation, feedback capture, telemetry.
- **Optional/advanced:** formal causal inference (DiD/DoWhy), SHAP-based decomposition, fine-tuning, vector DB at scale, multi-agent orchestration, production-grade observability stack.

**5. Common scoring mistakes**

- Letting the LLM compute or invent numbers ("hallucinated contribution %").
- No abstention scenario — system always sounds certain.
- Personas that just change tone, not substance.
- No ground truth to validate against — judges can't check correctness.
- Over-engineered ML (deep learning) with no justification, signaling AI-buzzword chasing.
- Security bolted on as an afterthought instead of gating the LLM call itself.
- A demo that's "a chatbot with charts" rather than a workflow with evidence.

---

## B. Our Proposed Product

**Name:** **Veritas KPI** *(alt: Causa, Lumen BI, TrueSignal)*
**One-line:** An evidence-grounded KPI intelligence-to-action system that tells you *what* moved, *why* (with proof), *how sure* it is, and *what to do* — never letting an LLM guess the numbers.

**Elevator pitch:** Enterprises drown in dashboards that show *what* happened but never *why*, and LLM chatbots that answer confidently but can't be trusted with numbers. Veritas KPI sits between your data warehouse and your decision-makers: it deterministically detects material KPI shifts, statistically ranks the true drivers, packages that as auditable evidence, and only then uses an LLM to explain it — in the right language, to the right person, with the right authority to act on it.

**Target users:** CFO/CEO (enterprise health), Regional/Category Managers (operational levers), Business/Data Analysts (root-cause investigation), Marketing/Supply Chain leads (functional owners of levers).

**Primary business problem:** Analysts spend days manually reconciling sales/marketing/inventory data to explain a KPI move; executives get narratives they can't verify; AI tools hallucinate specifics that erode trust.

**Core value proposition:** *Trustworthy, provable, role-aware KPI explanations that end in an authorized action — not just an answer.*

**Differentiators**

1. **Evidence Object** as a first-class, auditable artifact — every LLM sentence traces to it.
2. Deterministic **confidence + abstention** engine — the system can say "I don't know," which most AI demos never do.
3. **Decision-rights-aware actions** — recommendations are filtered by who is logged in, not generic.
4. **Ground-truth validated** — synthetic data with known injected drivers lets us *quantitatively* prove attribution accuracy, not just claim it.
5. Security enforced **before** the LLM call, not as output filtering.
6. Clear LLM/non-LLM boundary shown live in the UI (method + confidence + lineage panel).

---

## C. Data Architecture

### C.1 Layered flow (ASCII)

```
 ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
 │  SALES (OLTP) │  │  MARKETING    │  │  INVENTORY    │
 │  order×product│  │  campaign×    │  │  SKU×warehouse│
 │  line grain   │  │  region×chan  │  │  ×timestamp   │
 │  refresh: hrly│  │  refresh: dly │  │  refresh: 4hr │
 └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
         │                  │                  │
         ▼                  ▼                  ▼
 ┌─────────────────────────────────────────────────────┐
 │                     INGESTION                        │
 │   batch loaders (CSV/Parquet) + schema validation     │
 └───────────────────────┬──────────────────────────────┘
                          ▼
 ┌─────────────────────────────────────────────────────┐
 │                    DATA QUALITY                       │
 │  null checks, referential integrity, freshness SLA,   │
 │  duplicate detection, range checks → DQ score per load│
 └───────────────────────┬──────────────────────────────┘
                          ▼
 ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
 │    BRONZE     │→ │    SILVER     │→ │     GOLD      │
 │ raw, source-  │  │ conformed,    │  │ KPI-ready,    │
 │ grain, as-is  │  │ deduped,      │  │ aggregated,   │
 │               │  │ typed, joined │  │ dimensional   │
 └───────────────┘  └───────────────┘  └───────┬───────┘
                                                ▼
                                   KPI SEMANTIC LAYER → KPI CALC → ...

```

### C.2 Bronze / Silver / Gold assignment

- **Bronze:** `raw_orders`, `raw_marketing_events`, `raw_inventory_snapshots` (source-grain, untouched).
- **Silver:** `fact_sales_line`, `fact_marketing_daily`, `fact_inventory_snapshot` (conformed keys, deduped, typed, DQ-flagged — each kept at its **native** grain, not forced into a common one; see C.3).
- **Gold:** `kpi_region_daily`, `product_performance_daily`, `kpi_semantic_contracts`, `dim_*` tables.

### C.3 Grain design (revised — don't force a universal grain)

An earlier draft used one universal `kpi_daily` at date×product×region×channel. That's wrong: marketing/web sessions only exist at date×region×channel (there's no per-SKU session count), so forcing product into that grain would mean artificially distributing sessions across products — a fabricated number, not a real one. Each fact table now stays at its **true source grain**, and two purpose-built Gold aggregates serve different questions:

| Table Grain Refresh Contains       |                                    |               |                                                                                                                                            |
| ---------------------------------- | ---------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `fact_sales_line`                  | Order × Product line               | Hourly        | qty, price, discount, COGS, return\_flag                                                                                                   |
| `fact_marketing_daily`             | Campaign × Region × Channel × Day  | Daily         | impressions, clicks, sessions, conversions, spend                                                                                          |
| `fact_inventory_snapshot`          | SKU × Warehouse × Timestamp        | Every 4 hours | stock\_level, stockout\_flag                                                                                                               |
| `kpi_region_daily` (Gold)          | Date × Region × Channel            | Daily         | Revenue, Orders, Sessions, Conversion, AOV, Gross Margin — the table the anomaly/decomposition engine runs against                         |
| `product_performance_daily` (Gold) | Date × Product × Category × Region | Daily         | Revenue, Orders, Units, Price, Margin — for product/category drill-down only, kept separate so it never corrupts the conversion-rate grain |

This also directly demonstrates the brief's "different source grains and refresh cadences" requirement rather than just claiming it.

Full table designs are in Section D below (Task 5).

---

## D. KPI Semantic Layer & Data Tables (Tasks 5 & 7)

### D.1 Core tables (kept intentionally minimal)

| Table Grain Key cols Cadence Layer Purpose            |                              |                                                                     |                         |               |                                                                                             |
| ----------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------- | ----------------------- | ------------- | ------------------------------------------------------------------------------------------- |
| `dim_date`                                            | day                          | date\_id (PK)                                                       | static                  | Gold          | calendar, seasonality flags, promo flags                                                    |
| `dim_product`                                         | SKU                          | product\_id (PK), category, launch\_date                            | slow-changing           | Gold          | product hierarchy                                                                           |
| `dim_region`                                          | region                       | region\_id (PK)                                                     | static                  | Gold          | geography                                                                                   |
| `dim_channel`                                         | channel                      | channel\_id (PK)                                                    | static                  | Gold          | online/store/marketplace                                                                    |
| `raw_orders` → `fact_sales_line`                      | order × product line         | order\_id, line\_id (PK), product\_id, region\_id, channel\_id (FK) | hourly                  | Bronze/Silver | qty, price, discount, COGS, return\_flag                                                    |
| `raw_marketing_events` → `fact_marketing_daily`       | campaign×region×channel×day  | campaign\_id, date\_id, region\_id, channel\_id (PK/FK)             | daily                   | Bronze/Silver | impressions, clicks, sessions, conversions, spend                                           |
| `raw_inventory_snapshots` → `fact_inventory_snapshot` | SKU×warehouse×timestamp      | product\_id, warehouse\_id, snapshot\_ts (PK/FK)                    | every 4 hours           | Bronze/Silver | stock\_level, stockout\_flag, stockout\_days, replenishment\_qty                            |
| `kpi_region_daily`                                    | date×region×channel          | date\_id, region\_id, channel\_id (PK/FK)                           | daily                   | Gold          | Revenue, Orders, Sessions, Conversion Rate, AOV, Gross Margin — feeds anomaly/decomposition |
| `product_performance_daily`                           | date×product×category×region | date\_id, product\_id, region\_id (PK/FK)                           | daily                   | Gold          | Revenue, Orders, Units, Price, Margin — drill-down only                                     |
| `kpi_semantic_contracts`                              | per KPI                      | kpi\_id (PK)                                                        | static/versioned        | Gold          | see D.2 below                                                                               |
| `dim_user` / `dim_role` / `role_entitlements`         | per user/role                | user\_id, role\_id (PK)                                             | static                  | Gold          | RBAC, region/column scoping                                                                 |
| `action_playbooks`                                    | per lever                    | playbook\_id (PK)                                                   | static                  | Gold          | driver→lever→action mapping, owner role                                                     |
| `feedback_log`                                        | per insight                  | feedback\_id (PK), insight\_id (FK)                                 | event                   | Gold          | thumbs, corrections, outcomes                                                               |
| `telemetry_log`                                       | per request                  | request\_id (PK)                                                    | event                   | Gold          | latency, tokens, cost, model                                                                |
| `ground_truth_drivers`                                | per simulated period         | date\_id, driver\_id (PK)                                           | static (synthetic only) | Gold          | true injected contribution % — evaluation only, never exposed to engine                     |

Customer-level tables are deliberately **excluded** — not needed for KPI-level attribution and they only add PII/security surface without adding demo value.

### D.1a Synthetic Ground-Truth Incident Design (Task 6)

To make the −10 to −15% revenue drop *provably* attributable, the generator builds each day's numbers as:

`value = baseline(day_of_week, trend) × seasonality_multiplier × promo_multiplier × (1 + noise) × incident_multiplier(driver)`

1. **Baseline** — slow upward trend over 12–18 months reflecting normal business growth.
2. **Seasonality** — monthly/festival multipliers (e.g., a sales bump in a known shopping-festival month).
3. **Weekend effect** — +15–20% traffic/orders multiplier Fri–Sun.
4. **Promotions** — scheduled discount events with a known conversion/AOV bump, randomly placed but logged.
5. **Random noise** — small Gaussian noise (\~±3%) on every metric so nothing is perfectly clean.
6. **Injected anomaly period** — a 4–6 week window (e.g., weeks 30–35) where **North region** simultaneously receives: 
   - conversion\_rate × 0.90 via a **checkout/funnel degradation** multiplier (−10% relative, ramping in over 2 weeks, not a step function) — modeled as an independent site/UX issue, separate from stock-outs below, so the two conversion-affecting causes don't overlap
   - stock\_availability reduced for a specific SKU cohort → stockout\_days spike → estimated revenue loss via `stockout_days × avg_daily_demand × price`
   - marketing\_spend × 0.85 and sessions × 0.85 with a slight lag/inconsistency deliberately introduced between the two (to power the abstention demo)
   - price × 1.03 on a subset of SKUs (small positive offset)
7. **Ground truth via counterfactual removal, not manual assignment.** Because the injected drivers interact (e.g., stock-outs affect conversion, which compounds with the traffic drop), true contribution is computed by re-running the *generator* — not the analytical engine — with each incident individually switched off:

```
Actual simulated world (all incidents on):        Revenue = ₹88 Cr
Remove marketing incident only:                    Revenue = ₹91 Cr
Remove stock-out incident only:                    Revenue = ₹94 Cr
Remove conversion incident only:                    Revenue = ₹96 Cr
Remove all incidents (clean baseline):              Revenue = ₹101 Cr

```

A small Shapley-style counterfactual calculation over these injected drivers (all 2^n on/off combinations, since n is small — 3–4 drivers) turns the differences above into fair, interaction-aware contribution shares, stored in `ground_truth_drivers(date_id, driver_id, true_contribution_pct_points)`. This table is generated purely from the synthetic mechanism, never touched by the analytics pipeline, and used only in Section Q to score **true vs. engine-estimated** contribution — e.g.:

| Driver TRUE (from counterfactual removal) ESTIMATED (from engine)  |       |       |
| ------------------------------------------------------------------ | ----- | ----- |
| Checkout/funnel conversion degradation                             | 44.1% | 42.8% |
| Stock availability                                                 | 28.7% | 30.2% |
| Marketing/traffic                                                  | 18.0% | 17.1% |
| Pricing                                                            | −5.1% | −4.7% |

### D.2 Example KPI Semantic Contract (YAML)

```yaml
kpi_id: revenue
name: "Revenue"
business_definition: >
  Net sales value recognized from completed orders, after discounts,
  excluding returns, in reporting currency.
formula: "SUM(quantity * unit_price * (1 - discount_pct)) - SUM(returns_value)"
# net of returns is already baked into the Silver-layer fact_sales_line rollup;
# the KPI BRIDGE decomposition (Section E.2) uses Revenue = Sessions x Conversion x AOV,
# where AOV = NetRevenue/Orders already reflects returns/discounts — do not also
# multiply by (1 - ReturnRate) at the bridge level, or returns get subtracted twice.
grain: [date, region, channel]
source_tables: [kpi_region_daily]
possible_drivers: [conversion_rate, traffic, aov, product_mix, stockouts, pricing, marketing_spend]
materiality_threshold:
  relative_pct: 5
  absolute_value_inr: 5000000
business_owner: "VP Commercial"
lineage: "raw_orders -> fact_sales_line -> kpi_region_daily.revenue"
freshness_expectation_hours: 24
access_restrictions:
  - role: regional_manager
    scope: "region = user.region"
  - role: ceo
    scope: "all"
valid_comparison_windows: [wow, mom, yoy, vs_forecast]
dependent_kpis: [orders, conversion_rate, aov, gross_margin]

```

Similar contracts exist for `orders`, `conversion_rate` (sessions→orders), `aov` (revenue/orders), `gross_margin` ((revenue-COGS)/revenue) — each declares its own drivers, threshold, and owner. Keeping these as versioned YAML/JSON (not hardcoded SQL) is what lets the anomaly/contribution engines and the LLM all refer to *one* agreed definition — this is the semantic contract's entire purpose: eliminating "whose number is right" disputes.

---

## E. Analytics Architecture (Tasks 8–11)

### E.1 Materiality + Anomaly Detection

| Method Verdict for prototype Why                                         |                                                             |                                                                                   |
| ------------------------------------------------------------------------ | ----------------------------------------------------------- | --------------------------------------------------------------------------------- |
| % change threshold                                                       | ✅ use (business layer)                                      | simple, explainable to CFO                                                        |
| Business-impact threshold (absolute ₹)                                   | ✅ use (business layer)                                      | prevents small % on huge base from being ignored                                  |
| Rolling mean/std, Z-score                                                | ✅ use (statistical layer)                                   | cheap, explainable, works with 12–18 months history                               |
| IQR                                                                      | optional fallback for skewed metrics                        | robust to outliers                                                                |
| Forecasting residual (e.g., simple exponential smoothing / Prophet-lite) | ✅ use for expected-value baseline                           | needed to get "expected vs actual", not just deltas                               |
| Isolation Forest                                                         | ❌ skip                                                      | unsupervised, unexplainable to a business judge, no clear value over Z-score here |
| XGBoost/LightGBM forecasting                                             | optional, only for AOV/new-product benchmark if time allows | adds complexity; only justified if seasonality is genuinely non-linear            |

**Recommendation:** forecast expected value with a simple seasonal baseline (day-of-week + trailing 4-week average, or Holt-Winters), and use the **forecast's prediction interval** directly rather than a classical t-test — a t-test assumes i.i.d. samples, and daily revenue is autocorrelated/seasonal, which a technical judge could reasonably challenge. Instead:

```
Expected Revenue: ₹100.8 Cr
95% prediction interval: ₹96.2–₹105.4 Cr
Actual: ₹87.9 Cr  →  outside interval  →  material anomaly

```

The standardized residual (how far outside the interval, in std-dev units) becomes the anomaly score, combined with a business-impact rule.

**Materiality score:**

```
materiality_score = w1 * min(|z_score| / z_cap, 1) + w2 * min(|Δ_absolute| / impact_cap, 1)

```

with `w1 = 0.4, w2 = 0.6` (business impact weighted higher so a statistically rare but financially trivial move — e.g., a small SKU — never outranks a modest-% move on a huge-revenue category). Alert fires only if `materiality_score ≥ 0.5` **and** `|Δ%| ≥ contract.materiality_threshold`.

### E.2 Driver / Contribution Analysis — Two Levels (revised to prevent double-counting)

A flat list of "drivers" (conversion, stock-outs, marketing, pricing, mix) invites double-counting: marketing spend falling *causes* traffic to fall, and stock-outs *cause* conversion to fall — they aren't independent additive terms, they sit at different points in the causal chain. The fix is to split attribution into two distinct, clearly-labeled questions.

**Level 1 — KPI Bridge Decomposition (mathematical, answers "what changed"):**

$$
Revenue = Sessions \times ConversionRate \times AOV
$$

(No `(1 − Return_Rate)` term — `AOV = NetRevenue / Orders` already nets out returns/discounts at the Silver layer, so adding a return factor here would subtract returns twice.)

Using log-decomposition, the three factors' point-contributions are computed **exactly** and sum to the observed delta with zero unexplained residual (aside from a small labeled noise term):

```
Revenue -12.7%
   ├── Traffic effect     -3.1 pp
   ├── Conversion effect  -5.7 pp
   └── AOV effect         -3.9 pp

```

**Level 2 — Business-Driver Diagnosis (answers "why did each bridge component move"):**

```
TRAFFIC ↓        → candidate causes: marketing spend, campaign performance, seasonality
CONVERSION ↓     → candidate causes: stock-outs, checkout/funnel issues, price changes
AOV ↓/↑          → candidate causes: product mix, discounting, category mix, pricing

```

Level 2 causes are evaluated with SQL slicing + correlation/consistency checks against the Level 1 component they're diagnosing (e.g., does marketing\_spend's decline timeline match the traffic decline timeline?) — this is diagnostic evidence, not a further additive percentage, so it can't be double-counted against the Level 1 numbers.

| Level Driver Method  |                                                            |                                                                   |
| -------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------- |
| 1                    | Traffic / Conversion / AOV                                 | multiplicative bridge decomposition (exact, sums to 100%)         |
| 2                    | Marketing spend/campaign (diagnoses Traffic)               | SQL join + timeline correlation                                   |
| 2                    | Stock-outs (diagnoses Conversion)                          | SQL: estimated lost conversions from stockout\_days × avg\_demand |
| 2                    | Checkout/funnel issue (diagnoses Conversion)               | funnel-stage SQL comparison vs. baseline                          |
| 2                    | Product/category mix, pricing, discounting (diagnoses AOV) | mix-vs-rate decomposition on `product_performance_daily`          |

SHAP/regression remains an *optional* cross-check only for Level-2 elasticity estimates (e.g., "how much does a 1% marketing cut typically move sessions") — never the primary source of truth. Rule that survives every judge question: **the LLM never invents a %, at either level; it only rephrases numbers the decomposition/diagnosis already computed.**

### E.3 Hypothesis Engine

The hypothesis catalog now maps directly onto the two-level structure — H1–H3 are Level-2 diagnoses of *why Traffic/Conversion/AOV* moved, not independent competitors for the same revenue points, which removes the double-counting risk at the ranking stage too. Hypotheses are **not** generated by an LLM guessing — they're a **fixed catalog** tied to each bridge component's candidate causes in the semantic contract. For each, the engine computes:

| Signal How computed      |                                                                   |
| ------------------------ | ----------------------------------------------------------------- |
| Contribution             | from decomposition (E.2)                                          |
| Statistical support      | forecast prediction interval, not a t-test — see note below       |
| Data freshness           | from DQ/freshness metadata                                        |
| Cross-source consistency | does marketing spend drop *and* sessions drop in the same window? |
| Confidence               | weighted combination (see F.2)                                    |

Hypotheses are then **ranked by contribution × confidence**, not by contribution alone — a large but low-confidence effect should not outrank a modest, well-evidenced one.

**Why this beats "ask an LLM why revenue declined":** the LLM has no access to ground truth, cannot verify its own arithmetic, cannot express calibrated uncertainty, and would produce different plausible-sounding answers on every run. A hypothesis engine is deterministic, reproducible, auditable, and its accuracy can be *measured* against the synthetic ground truth (Task 28) — an LLM's can't.

### E.4 Causal Inference

**Verdict: not necessary as the primary mechanism — include one small, honest demonstration only, using Difference-in-Differences (DiD) rather than CausalImpact.** DiD is simpler to explain to a business judge, needs no synthetic-control model fitting, and maps perfectly onto a two-region synthetic experiment we fully control.

**Example:** North receives the marketing-spend cut in the incident window; West (comparable, untouched) does not.

```
             Before   After
North          100      85
West           100      96

DiD = (85 - 100) - (96 - 100) = -15 - (-4) = -11 pp

```

Estimated treatment effect of the marketing cut on North's index: **−11 percentage points**, isolating the intervention's effect from anything that also moved West (seasonality, market-wide trend).

**Language discipline:**

- Level-1 bridge decomposition and Level-2 business-driver diagnosis → *"associated with"* / *"contributed X pp to the change"* (accounting decomposition and correlational diagnosis, not causal).
- Only the one DiD demonstration, with its explicit before/after, treatment/control structure → *"caused by"* / *"estimated causal effect"*, still hedged as an estimate rather than a certainty.

Everywhere else in the product, the language is deliberately "associated with" — this restraint is itself something judges will respect more than an overclaimed causal story everywhere.

---

## F. Evidence + Confidence Architecture (Tasks 12–14)

### F.1 Evidence Object (example JSON)

```json
{
  "insight_id": "ins_2026_08_20_revenue_all",
  "kpi": "revenue",
  "window": {"start": "2026-08-14", "end": "2026-08-20"},
  "actual_value": 882000000,
  "expected_value": 1010000000,
  "delta_pct": -12.7,
  "business_impact_inr": -128000000,
  "anomaly_score": 3.1,
  "prediction_interval_95": [962000000, 1054000000],
  "materiality_score": 0.86,
  "kpi_bridge": [
    {"component": "traffic", "contribution_pct_points": -3.1, "method": "multiplicative_bridge_decomposition"},
    {"component": "conversion_rate", "contribution_pct_points": -5.7, "method": "multiplicative_bridge_decomposition"},
    {"component": "aov", "contribution_pct_points": -3.9, "method": "multiplicative_bridge_decomposition"}
  ],
  "business_driver_diagnosis": [
    {"diagnoses": "traffic", "cause": "marketing_spend_reduction", "evidence_confidence": 0.58, "method": "sql_slice_timeline_correlation", "source_tables": ["fact_marketing_daily"], "freshness_hours": 30, "data_quality_score": 0.80, "note": "stale marketing feed — see contradictory_evidence"},
    {"diagnoses": "conversion_rate", "cause": "stock_availability", "evidence_confidence": 0.88, "method": "stockout_revenue_loss_estimate", "source_tables": ["fact_inventory_snapshot"], "freshness_hours": 4, "data_quality_score": 0.97},
    {"diagnoses": "conversion_rate", "cause": "checkout_funnel_degradation", "evidence_confidence": 0.76, "method": "funnel_stage_sql_comparison", "source_tables": ["fact_sales_line"], "freshness_hours": 6, "data_quality_score": 0.95},
    {"diagnoses": "aov", "cause": "pricing_mix_shift", "evidence_confidence": 0.83, "method": "mix_rate_decomposition", "source_tables": ["product_performance_daily"], "freshness_hours": 6, "data_quality_score": 0.97}
  ],
  "contradictory_evidence": [
    "marketing_spend table shows only a 4% reduction, weaker than the 19% traffic drop would suggest — possible attribution/tracking issue"
  ],
  "alternative_hypotheses_considered": ["seasonality", "product_mix_shift_as_sole_cause"],
  "evidence_confidence_score": 0.69,
  "confidence_band": "MEDIUM — not a posterior probability, a composite evidence-quality score (kept below the 0.75 HIGH threshold specifically because of the stale/contradictory marketing evidence above)",
  "analysis_method_version": "decomposition_v1.3",
  "query_id": "q_98213",
  "lineage": "raw_orders -> fact_sales_line -> kpi_region_daily -> decomposition_v1.3",
  "generated_at": "2026-08-20T06:03:11Z"
}

```

### F.2 Evidence Confidence Score + Abstention Engine

**Naming matters here.** This is called the **Evidence Confidence Score (ECS)** — a deterministic composite of evidence *quality*, not a statistical posterior probability. Never phrase output as "there is a 69% probability this explanation is correct" (that claims something the formula doesn't establish); phrase it as "Evidence Confidence Score: 0.69 / MEDIUM — a composite of data quality, freshness, and cross-source consistency." Bands must also stay internally consistent: a score of 0.69 is MEDIUM (below the 0.75 HIGH cutoff), never described as HIGH.

```
ECS =
    0.25 * data_quality_score
  + 0.20 * source_freshness_score
  + 0.20 * historical_sufficiency_score
  + 0.20 * statistical_strength_score
  + 0.15 * cross_source_consistency_score
  - contradiction_penalty

```

All sub-scores normalized 0–1; `contradiction_penalty` subtracts up to 0.3 when sources disagree (as in the marketing example above).

| Band Range Label Behavior  |          |                            |                                                                                                                  |
| -------------------------- | -------- | -------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| HIGH                       | ≥0.75    | HIGH evidence confidence   | strong conclusion, specific pp attribution stated                                                                |
| MEDIUM                     | 0.5–0.75 | MEDIUM evidence confidence | conclusion stated with explicit caveats, contradictions surfaced                                                 |
| LOW                        | <0.5     | LOW → abstain              | **abstain** — state what's known, name the missing/contradictory data, ask for clarification instead of guessing |

Thresholds are calibrated later using the synthetic scenarios and analyst feedback (see J, revised).

**Abstention demo:** marketing feed is 30h stale (SLA is 24h) and its spend-drop and traffic-drop numbers are inconsistent with each other. `cross_source_consistency_score` and `source_freshness_score` both collapse for that specific Level-2 diagnosis → its evidence confidence drops <0.5. The engine's response: *"Revenue is down 12.7%. Of that, conversion accounts for −5.7 pp — and stock availability is the strongest-supported explanation for that conversion deterioration. I can't reliably say how much of the traffic component (−3.1 pp) is attributable to the marketing spend cut: the marketing data is 30 hours stale and internally inconsistent (spend −4% vs. traffic −19%). Recommend refreshing the marketing feed before concluding on that link."* — note this abstains on one specific Level-2 diagnosis without ever adding a Level-1 pp value to a Level-2 confidence score, and it's a genuine, checkable refusal to overclaim.

### F.3 Sparse-History / New-Product Scenario

New SKU launched 20 days ago. Ordinary seasonal Z-score baselines need months of history and will misfire (no seasonal pattern to compare against, tiny sample → huge variance). Instead:

- **Cohort benchmark:** compare against the day-20 performance of the 5 most similar SKUs at launch (same category/price band).
- **Category benchmark:** category's average launch-curve shape, scaled to this SKU's early sessions.
- **Business plan target:** the pre-set launch forecast from the product team (if available in `kpi_semantic_contracts` metadata).
- Confidence is **explicitly capped** (e.g., max 0.6, "MEDIUM" ceiling) regardless of how clean the signal looks, because `historical_sufficiency_score` is intrinsically low — this cap is stated plainly to the user rather than hidden.

---

## G. LLM / RAG Architecture & the LLM vs. Non-LLM Table (Task 4)

### G.1 Guiding principle

**SQL/statistics/ML determine quantitative truth → the Evidence Object packages truth + uncertainty → the LLM explains and personalizes it, and nothing else.**

| Task Method LLM or Non-LLM Why Output  |                                                                |                     |                                                                   |                                      |
| -------------------------------------- | -------------------------------------------------------------- | ------------------- | ----------------------------------------------------------------- | ------------------------------------ |
| KPI calculation                        | SQL / semantic contract formula                                | Non-LLM             | must be exact, auditable                                          | numeric KPI value                    |
| Data reconciliation                    | deterministic joins + DQ rules                                 | Non-LLM             | correctness, reproducibility                                      | conformed Silver tables              |
| Anomaly detection                      | Z-score + forecast residual                                    | Non-LLM             | statistically grounded, explainable                               | anomaly\_score                       |
| Forecasting                            | seasonal baseline (Holt-Winters/simple)                        | Non-LLM             | needs numerical rigor                                             | expected\_value                      |
| Materiality                            | rule + score combining stats & business impact                 | Non-LLM             | must be deterministic to avoid gaming                             | materiality\_score                   |
| Statistical significance               | forecast prediction interval + standardized residual           | Non-LLM             | mathematically defined, robust to autocorrelation unlike a t-test | interval/residual score              |
| Contribution analysis                  | multiplicative/mix decomposition                               | Non-LLM             | exact, sums to 100%                                               | driver contributions                 |
| Root-cause ranking                     | hypothesis engine (rule + evidence scoring)                    | Non-LLM             | reproducible ranking                                              | ranked hypotheses                    |
| Causal inference                       | Difference-in-Differences (one scenario)                       | Non-LLM             | needs a formal treatment/control counterfactual method            | causal effect estimate               |
| Confidence calculation                 | weighted formula (F.2)                                         | Non-LLM             | must not be "vibes"-based                                         | confidence score/band                |
| Security / entitlement                 | RBAC + row/column filters                                      | Non-LLM             | must be enforced pre-LLM, deterministically                       | allow/deny + scoped data             |
| KPI definition retrieval               | semantic contract lookup (+ RAG for terminology)               | Non-LLM (retrieval) | exact definitions must not drift                                  | contract fields                      |
| User-intent understanding              | LLM (NLU on free-text question)                                | **LLM**             | natural language is inherently ambiguous                          | structured intent/query params       |
| Narrative generation                   | LLM, grounded strictly in Evidence Object                      | **LLM**             | language generation is the LLM's actual strength                  | persona narrative text               |
| Persona adaptation                     | LLM (given persona profile + Evidence Object)                  | **LLM**             | tone/detail-level shaping is linguistic                           | tailored narrative                   |
| Action recommendation                  | rule/playbook engine selects candidates; LLM only phrases      | Mostly Non-LLM      | actions must come from a controlled catalog                       | validated action list + LLM phrasing |
| Expected-impact calculation            | deterministic estimate from historical driver→lever elasticity | Non-LLM             | must be numeric and defensible                                    | expected impact range                |
| Feedback learning                      | rule/statistics update (threshold & ranking recalibration)     | Non-LLM             | avoids fine-tuning complexity/cost                                | updated weights/thresholds           |

### G.2 Structured lookup vs. RAG — don't over-use vector search

**Revised split:** structured, well-defined business knowledge should use deterministic **SQL/YAML lookup**, not vector RAG — KPI formulas, roles, permissions, decision rights, and the action catalogue all have exact keys and shouldn't be retrieved "approximately." RAG is reserved for genuinely unstructured content where similarity search actually earns its keep:

| Structured (SQL/YAML lookup) Unstructured (RAG/pgvector)  |                                          |
| --------------------------------------------------------- | ---------------------------------------- |
| KPI formulas & semantic contracts                         | Business policies & SOPs                 |
| Roles & permissions                                       | Campaign descriptions                    |
| Decision rights                                           | Product documentation                    |
| Action playbook catalogue                                 | Analyst notes / prior incident write-ups |

**Excluded from both:** raw transactional data, PII, live numeric KPI values — these come from the Evidence Object only, never from an index, so the LLM can't "recall" a stale or approximate number. Anything the requesting user isn't entitled to is filtered before retrieval, not after (see Section I, revised).

**How this complements, not replaces, analytics:** the lookup/RAG layer answers "what does gross margin mean here / who owns pricing decisions / what happened in a similar past incident" — static or historical organizational knowledge. It never answers "why did revenue drop this week" — that's exclusively the Evidence Object's job, computed fresh each time.

---

## H. Action Architecture (Task 17)

Structure: **DRIVER → CONTROLLABLE LEVER → ACTION → EXPECTED IMPACT → OWNER → CONFIDENCE → MONITORING PLAN**, sourced entirely from `action_playbooks` (rule table), never invented by the LLM.

| Driver Lever Action Expected impact Owner Confidence Monitoring  |               |                                                                             |                                                                   |                                        |                                                       |                                 |
| ---------------------------------------------------------------- | ------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------- | -------------------------------------- | ----------------------------------------------------- | ------------------------------- |
| Stock-outs (North, SKU cohort)                                   | Replenishment | Expedite replenishment for top 10 stocked-out SKUs in North                 | +2.5–3.5 pp revenue recovery over 2 weeks (historical elasticity) | Supply Chain Manager                   | MEDIUM-HIGH                                           | daily stockout\_days vs. target |
| Conversion drop                                                  | Site/funnel   | Investigate checkout funnel for North region (UX/latency regression check)  | +1.5–2.5 pp conversion if resolved                                | Regional Manager (escalate to Product) | MEDIUM                                                | daily conversion\_rate trend    |
| Marketing traffic decline                                        | Spend/budget  | Reallocate budget toward North region to restore session volume to baseline | +1–2 pp revenue if elasticity holds                               | Marketing Manager                      | MEDIUM (marketing data confidence is capped, per F.2) | daily sessions & CAC            |

The LLM's only role here is to phrase these three already-validated rows into a coherent paragraph per persona — it cannot add a fourth action or change the numbers.

## I. Security / Entitlement (Task 16)

```
USER REQUEST
     │
     ▼
AUTHENTICATION (JWT)
     │
     ▼
AUTHORIZATION / ENTITLEMENTS  →  resolves allowed KPI + region + dimensions
     │
     ▼
SCOPED SQL QUERY  →  the query itself is built with the user's region/column
     │                scope baked in — it is never possible to fetch South
     │                data for a North-scoped user in the first place
     ▼
ANALYTICS (materiality, bridge decomposition, diagnosis)
     │
     ▼
SCOPED EVIDENCE OBJECT
     │
     ▼
LLM (sees only authorized evidence)

```

**Key principle, revised:** authorization determines the **query itself**, not a filter applied to results after they're fetched. An earlier draft filtered "all Gold data → Evidence → filter," which technically lets unauthorized rows exist transiently in the pipeline before being dropped — defensible but weaker. The corrected version makes the claim *"unauthorized data never enters the model context"* fully literal: the SQL that produces the Evidence Object is scoped from the moment it's issued.

| Role Region scope KPI scope PII  |                           |                                        |                                           |
| -------------------------------- | ------------------------- | -------------------------------------- | ----------------------------------------- |
| CEO/CFO                          | All                       | All                                    | No customer PII (not needed at KPI level) |
| North Regional Manager           | North only                | Sales, marketing, inventory (North)    | No                                        |
| Marketing Manager                | All (marketing KPIs only) | Marketing metrics only, no margin/COGS | No                                        |
| Analyst                          | All (read)                | All, detailed grain                    | No                                        |

**Demo:** North Manager asks *"Show me why South region's revenue dropped."* → RBAC layer detects `region_scope=North` ≠ requested `South` → request is denied **before** any South data is fetched or embedded → response: *"You're authorized for North region data. I can show North's revenue trend, or you can request South access from your administrator."* No South numbers ever reach the LLM context window — provably, since the retrieval call itself is scoped.

---

## J. Feedback Loop (Task 20)

`feedback_log` captures: `insight_id`, `predicted_top_driver`, `analyst_corrected_driver` (nullable), `evidence_snapshot_id`, `recommendation_id`, `action_taken` (bool), `outcome_kpi_delta` (measured N weeks later), `user_feedback` (up/down + free text).

**How it improves the system without fine-tuning — and without reacting to a single data point:**

```
Feedback received → stored immediately → validated by analyst/admin
   → accumulated until a sufficient sample size → periodic recalibration

```

Rule/threshold weights are **never** updated live off one correction — that would leave the system open to a single noisy or malicious user skewing hypothesis rankings ("feedback poisoning"). Instead:

- Repeated "wrong top driver" corrections, once a batch threshold is reached → adjust the hypothesis-ranking weights (E.3) for that KPI/segment in a scheduled recalibration pass.
- Repeated false-positive anomaly flags on a segment → widen its prediction-interval width or materiality cutoff, again in the periodic pass.
- Actions marked "rejected" repeatedly by a role → deprioritize that playbook entry for that role.
- Confidence calibration: compare stated confidence bands against actual correction rate over the accumulated batch (if MEDIUM-confidence insights are corrected 40% of the time, the ECS weights in F.2 are recalibrated) — a simple statistical recalibration, not a model retrain, and not an instant one.
- Prompts are only touched to fix a systematic narrative-quality issue (e.g., too verbose for CEO persona) — never to fix a numeric error, since numbers never come from the LLM in the first place.

## K. Telemetry & Cost (Task 21)

```json
{
  "request_id": "req_88213",
  "insight_id": "ins_2026_08_20_revenue_all",
  "total_latency_ms": 2140,
  "sql_latency_ms": 180,
  "analytics_latency_ms": 340,
  "retrieval_latency_ms": 90,
  "llm_latency_ms": 1480,
  "model_calls": 2,
  "model_used": "claude-sonnet",
  "input_tokens": 1850,
  "output_tokens": 410,
  "estimated_cost_usd": 0.014,
  "cache_hit": false,
  "failures": 0
}

```

**Cost/latency reduction strategies:** cache Evidence Objects per KPI/window (recompute only on new data, not per user request); cache RAG-retrieved static context (glossary/playbooks rarely change); use a single LLM call per persona (combine intent-parsing + narrative in one structured-output call rather than two round trips); truncate Evidence Object to only the top-N drivers relevant to the question rather than sending the full object; batch nightly pre-computation of likely-to-be-asked insights (top KPIs, all personas) instead of on-demand generation.

## L. User Interface (Task 23)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Veritas KPI   [Revenue ▼] [This Week ▼]     👤 North Manager  🔔 2   │
├───────────────────┬────────────────────────────────────────────────┤
│ KPI CARDS          │  🔴 MATERIAL ANOMALY — Revenue −12.7% vs plan  │
│ Revenue  ▼12.7% 🔴 │  ──────────────────────────────────────────── │
│ Orders   ▼8.1%  🟠 │  AI INSIGHT (Evidence Confidence: MEDIUM 0.69) │
│ Conv.Rate▼1.9pp 🔴 │  "Revenue fell mainly on lower conversion,     │
│ AOV      ▲2.1%  🟢 │   with stock-outs the strongest explanation.  │
│ Margin   ▼0.4pp 🟡 │   Marketing's role is uncertain — data stale."│
├───────────────────┤  [ Show Evidence ▾ ]  [ Lineage & Method ▾ ]    │
│ Ask Veritas:        │  LEVEL 1 — KPI BRIDGE (what moved, exact)     │
│ "why did margin     │  Traffic     ▓▓▓▓ -3.1pp                     │
│  drop in North?"    │  Conversion  ▓▓▓▓▓▓▓▓ -5.7pp                 │
│  [Send]             │  AOV         ▓▓▓▓▓ -3.9pp                    │
│                     │  ──────────────────────────────────────────── │
├───────────────────┤  LEVEL 2 — WHY? (business diagnosis, not additive)│
│ RECOMMENDED ACTIONS │  Traffic ← Marketing spend cut   conf 0.58 ⚠  │
│ 1. Expedite restock │  Conversion ← Stock availability conf 0.88    │
│    Owner: SupplyChn │  Conversion ← Checkout/funnel     conf 0.76   │
│ 2. Investigate       │  AOV ← Pricing/mix shift          conf 0.83  │
│    checkout funnel  │──────────────────────────────────────────────│
│    Owner: You        │  Data freshness: Sales 6h | Mktg 30h ⚠       │
│                     │  [ 👍 ] [ 👎 ] [ Correct driver ]              │
│                     │──────────────────────────────────────────────│
│                     │  TELEMETRY  latency 2.1s | 2 LLM calls |      │
│                     │  1850+410 tok | $0.014                       │
└───────────────────┴────────────────────────────────────────────────┘

```

Note the deliberate visual separation: Level 1 bars are the only ones with pp values that sum to the total delta; Level 2 rows carry confidence scores instead, so nothing on screen invites adding a Level-2 number into the Level-1 total.

This reads as a decision workspace (KPI cards, evidence, actions, telemetry, feedback all visible at once) rather than a single chat window — deliberately, since judges are told to expect "not merely a chatbot."

---

## M. Demo Scenarios (Tasks 24–25)

| # Flow User sees Behind the scenes Proves  |                               |                                                                      |                                                                                                |                                       |
| ------------------------------------------ | ----------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------- |
| 1                                          | Material revenue anomaly      | Red alert on Revenue card                                            | Materiality score crosses threshold, forecast residual computed                                | Materiality/anomaly detection         |
| 2                                          | Multi-factor attribution      | Ranked driver bars summing to −12.7%                                 | Decomposition + hypothesis engine ranking                                                      | Driver analysis without LLM invention |
| 3                                          | CEO vs. Regional Manager      | Two very different narratives, same incident                         | Persona engine reshapes scope/detail/actions from same Evidence Object                         | Persona-specific intelligence         |
| 4                                          | Abstention                    | "I can't confidently attribute the marketing effect…"                | Confidence engine drops below 0.5 due to staleness+contradiction                               | Honest uncertainty                    |
| 5                                          | New-product sparse history    | Cohort-benchmarked view, confidence capped at MEDIUM                 | Historical\_sufficiency\_score forced low                                                      | Sparse-history handling               |
| 6                                          | Access denial                 | "You're authorized for North only."                                  | RBAC blocks query before retrieval                                                             | Security enforced pre-LLM             |
| 7                                          | Analyst correction + feedback | Analyst flags "checkout/funnel" as the stronger conversion diagnosis | feedback\_log updated → validated → queued for scheduled recalibration (not applied instantly) | Feedback loop                         |

**Main end-to-end walkthrough (Task 25):** Expected revenue ₹101 Cr → actual ₹88.2 Cr (−12.7%). Materiality fires (score 0.86) → forecast prediction-interval check confirms the actual falls outside the 95% band (₹96.2–105.4 Cr) → **Level 1 KPI bridge** decomposes the −12.7% exactly into Traffic −3.1 pp, Conversion −5.7 pp, AOV −3.9 pp → **Level 2 business-driver diagnosis** evaluates candidate causes per component: Traffic ← marketing spend cut (evidence confidence 0.58, flagged stale/contradictory), Conversion ← stock availability (0.88) and checkout/funnel degradation (0.76), AOV ← pricing/mix shift (0.83) → Evidence Object assembled → Evidence Confidence Score computes to 0.69/MEDIUM (kept below the 0.75 HIGH threshold specifically because of the marketing contradiction) → structured lookup supplies KPI/role definitions, RAG supplies relevant policy/campaign notes → LLM generates CEO narrative (headline numbers, national impact, 3 actions) and Regional Manager narrative (North-specific bridge + diagnosis, operational actions only) → action engine returns 3 playbook actions scoped to the logged-in role → analyst reviews, corrects the checkout/funnel diagnosis's weight, accepts the stock-out action → correction stored and queued for the next scheduled recalibration pass (not applied instantly) → telemetry logged (2.1s, $0.014).

---

## N. Technology Stack (Task 22)

| Layer Choice Why          |                                                                                                        |                                                                          |
| ------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| Data processing           | Python + Pandas                                                                                        | fast to prototype synthetic ETL                                          |
| Database                  | DuckDB (dev) → PostgreSQL (demo)                                                                       | zero-setup analytics dev, Postgres for realistic multi-user/RBAC demo    |
| Backend                   | FastAPI                                                                                                | async, quick to stand up REST/JSON endpoints, good typing                |
| Stats/ML                  | scikit-learn (Z-score/regression utilities), statsmodels (Holt-Winters)                                | mature, explainable, no GPU needed                                       |
| Forecasting boosted trees | skip unless a clearly non-linear pattern demands it                                                    | avoid unjustified complexity                                             |
| Contribution              | custom deterministic decomposition (pure Python/Pandas)                                                | exact, auditable — no black box                                          |
| Causal (optional)         | statsmodels (OLS with treatment×post interaction term) implementing DiD directly                       | lightweight, no extra dependency, transparent formula                    |
| Semantic contracts        | YAML files, loaded at startup                                                                          | human-readable, versionable in git                                       |
| RAG                       | pgvector (inside the same Postgres)                                                                    | avoids a whole extra vector DB service for a small static corpus         |
| LLM                       | Claude API (Sonnet)                                                                                    | strong instruction-following for strict "don't invent numbers" grounding |
| Frontend                  | Next.js/React (Tailwind) for the polished final demo; Streamlit only for very early internal iteration | judges respond to a real enterprise-workspace look                       |
| Security                  | JWT + RBAC middleware in FastAPI                                                                       | simple, standard, easy to demo denial                                    |
| Deployment                | Docker Compose                                                                                         | one-command judge-side spin-up                                           |
| Observability             | custom `telemetry_log` table + a simple Grafana-less dashboard panel in the UI itself                  | no need for a full observability stack at hackathon scale                |

**Avoid:** Kubernetes, a dedicated vector-DB service (Milvus/Qdrant) for a tiny static corpus, deep learning anomaly detection, multi-agent orchestration frameworks, LLM fine-tuning — all add setup risk and demo fragility disproportionate to the score they'd earn.

---

## O. Implementation Roadmap (Task 26)

| Phase Build Output Depends on Can postpone  |                                                                                                  |                                                            |           |                                                |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------- | --------- | ---------------------------------------------- |
| 1                                           | Synthetic data generator (Sales/Marketing/Inventory, 12–18 mo, injected incident + ground truth) | CSV/Parquet + `ground_truth_drivers`                       | —         | —                                              |
| 2                                           | DB schema + KPI calculation SQL                                                                  | `kpi_region_daily` / `product_performance_daily` populated | Phase 1   | —                                              |
| 3                                           | Semantic contracts (YAML)                                                                        | 5 KPI contracts                                            | Phase 2   | —                                              |
| 4                                           | Materiality + anomaly detection                                                                  | anomaly\_score, materiality\_score per day                 | Phase 2–3 | —                                              |
| 5                                           | Contribution/hypothesis engine                                                                   | ranked drivers matching Task 6 ground truth                | Phase 4   | causal demo can slip to Phase 9                |
| 6                                           | Confidence + Evidence Object                                                                     | JSON evidence per insight                                  | Phase 5   | —                                              |
| 7                                           | RAG corpus + LLM narrative + persona engine                                                      | narrative text, 2 personas                                 | Phase 6   | multi-turn conversational refinement           |
| 8                                           | Actions + RBAC/security                                                                          | scoped actions, access-denial demo                         | Phase 6–7 | column-level PII masking if no PII tables used |
| 9                                           | Feedback + telemetry                                                                             | feedback\_log, telemetry\_log wired                        | Phase 7–8 | causal-inference demo, cache layer             |
| 10                                          | Polished UI + full demo script                                                                   | working end-to-end walkthrough                             | all above | animations/polish                              |

---

## P. MVP vs. Advanced (Task 27)

**MVP (must finish):** synthetic data with ground truth, KPI calc, materiality/anomaly, deterministic decomposition + hypothesis ranking, Evidence Object, confidence + one abstention demo, 2 personas, RBAC with one denial demo, 3 rule-based actions, basic feedback capture, basic telemetry panel, a working UI (even if visually simple).

**Advanced (only if time permits):** the DiD causal demonstration, SHAP cross-check, sparse-history cohort benchmarking (can substitute a simpler "insufficient history → confidence capped" message if time runs short), pgvector RAG (can substitute static JSON lookup if needed), caching/telemetry cost-optimization strategies actually implemented (vs. just described), polished Next.js UI (Streamlit is an acceptable fallback).

---

## Q. Evaluation Metrics (Task 28)

| Area Metric             |                                                                                                                        |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Anomaly detection       | precision/recall of flagged anomaly days vs. injected incident days                                                    |
| Driver identification   | top-1 / top-2 driver match rate vs. `ground_truth_drivers`                                                             |
| Contribution estimation | mean absolute error between estimated and true contribution percentage points                                          |
| Confidence calibration  | correlation between stated confidence band and actual correction rate in feedback\_log; reliability diagram            |
| Abstention              | did the system abstain on the deliberately-degraded scenario? (binary + confidence value check)                        |
| Action relevance        | % of recommended actions accepted (not rejected) in the demo/feedback log                                              |
| Narrative factuality    | manual/automated check that every numeric claim in the LLM narrative matches the Evidence Object exactly (0 tolerance) |
| Latency                 | end-to-end p50/p95 request latency                                                                                     |
| LLM cost                | $ per insight, tokens per insight                                                                                      |

Because the synthetic generator (Phase 1) stores exact injected contribution percentages, driver-identification and contribution-estimation accuracy can be reported as **hard numbers in the pitch** — e.g., "our decomposition recovered the true top-2 drivers in 100% of injected incidents, with mean contribution error of 0.6 percentage points" — this is a strong, verifiable claim most competing teams won't be able to make.

---

## R. Novelty (Task 29)

Genuinely defensible innovation points:

1. **The Evidence Object as an auditable contract between analytics and language generation** — not just "we use RAG," but a structured, versioned artifact every LLM sentence must trace back to, with contradiction tracking built in.
2. **Deterministic confidence + abstention** — most AI hackathon demos never say "I don't know." A system that visibly and correctly refuses to overclaim is rare and directly answers the brief's "communicate uncertainty" requirement.
3. **Ground-truth-validated attribution** — because the data is synthetic *by design* with known injected drivers, the team can report quantitative accuracy numbers (Q above) instead of only qualitative claims — this is a genuinely uncommon level of rigor for a hackathon.

Secondary, still-real but more standard: decision-rights-aware action filtering, persona-conditioned explanation (real BI tools do some of this, so frame it as "extended," not "invented").

**Emphasize to judges (pick 2–3):** (1) Evidence Object + confidence/abstention as the core trust mechanism, (2) ground-truth quantitative validation of driver attribution, (3) security enforced before the LLM, not after.

---

## S. Judge Questions & Answers (Task 30)

1. **How do you know the driver caused the KPI movement?** — We don't claim causation for accounting-style decomposition or Level-2 diagnosis; we say "associated with" and show the exact deterministic formula. The one place we say "caused by" is the Difference-in-Differences demo, backed by an explicit treatment/control comparison.
2. **Why do you need an LLM at all?** — Every number comes from SQL/stats. The LLM's job is natural-language narrative, persona adaptation, and intent parsing — tasks language models are actually good at and dashboards can't do.
3. **Why not just use Power BI?** — We're not trying to reproduce dashboarding, anomaly detection, or decomposition-tree exploration, which modern BI tools already offer to varying degrees. Our differentiation is the **governed end-to-end decision workflow**: cross-source reconciliation → an explicit, versioned KPI contract → deterministic two-level attribution → an evidence-confidence/abstention gate → persona- and security-aware narrative generation → decision-right-validated action → feedback and outcome tracking, all as one auditable pipeline rather than a set of separate exploration tools a human has to stitch together.
4. **How is confidence calculated?** — A weighted formula over data quality, freshness, historical sufficiency, statistical strength, and cross-source consistency, minus a contradiction penalty (shown live in section F.2).
5. **How do you avoid hallucinations?** — The LLM only receives the Evidence Object and its own scoped context; the prompt requires it to only restate given numbers, and our factuality metric (Q) checks that every quoted number appears verbatim in the Evidence Object.
6. **How are actions validated?** — Every action must come from the `action_playbooks` rule table filtered by decision rights; the LLM phrases, never selects.
7. **What happens when two sources disagree?** — The consistency score drops, confidence drops, and the specific contradiction is surfaced verbatim in the Evidence Object and narrative rather than silently averaged away.
8. **How do you handle unseen KPIs?** — Any KPI must have a semantic contract before it enters the pipeline; the system explicitly won't analyze an undefined KPI rather than guessing its formula.
9. **How does the solution scale?** — Bronze/Silver/Gold + pre-aggregated `kpi_region_daily`/`product_performance_daily` scale like a normal warehouse; the LLM layer scales by caching Evidence Objects and batching persona narratives, not by re-running analytics per request.
10. **What prevents sensitive information reaching the LLM?** — RBAC/row/column filters run before Evidence Object assembly; the LLM literally never receives unauthorized rows.
11. **How are expected-impact values generated?** — Historical elasticity between a lever and its KPI (e.g., past replenishment speed vs. revenue recovery), computed deterministically, not asked of the LLM.
12. **What did you actually train?** — Nothing was fine-tuned; we use prompting/structured output on a general LLM. "Learning" happens via statistical recalibration of thresholds/weights from feedback, which we're explicit about.
13. **How do you handle sparse-history products?** — Cohort/category benchmarking with an explicitly capped confidence ceiling (Section F.3).
14. **Isn't decomposition too simple compared to ML attribution?** — Simplicity is the point: it's exact (sums to the true delta), fully auditable, and our evaluation shows it recovers injected ground truth — a black-box model would add risk without adding accuracy here.
15. **Why weight business impact over statistical significance in materiality?** — To avoid over-alerting on statistically unusual but financially trivial movements, matching how real CFOs prioritize.
16. **How would this integrate with a real data warehouse?** — The Bronze/Silver/Gold pattern and semantic-contract layer map directly onto existing warehouse tables; only ingestion connectors would change.
17. **What if the LLM API is down?** — Materiality, driver ranking, confidence, and actions are all still computed and shown (the entire deterministic layer is independent); only narrative generation degrades to a templated fallback.
18. **How do you prevent prompt injection from a user question influencing the numbers?** — User free-text is only used for intent parsing (which KPI/window/persona), never fed into or capable of altering the Evidence Object's computed values.
19. **Why only one causal demo instead of causal inference everywhere?** — Formal causal inference needs a real counterfactual/control group; most of our incidents don't have a clean natural experiment, so we're honest about scope instead of overclaiming causal language everywhere.
20. **How would you measure success in production?** — Correction rate on driver attribution trending down over time, action-acceptance rate, and confidence calibration curves tightening — all already logged in `feedback_log`.

---

## T. Final Recommended Architecture

**"If I were building this prototype for selection, this is the architecture I would implement."**

1. **Diagram:** authentication → authorization/entitlements → scoped SQL query → KPI computation → forecast/expected baseline → materiality+anomaly gate → (if material) KPI bridge decomposition → business-driver diagnosis → hypothesis testing engine → contribution + evidence → Evidence Confidence Score gate → (if adequate) Evidence Object → business-context retrieval (structured lookup + RAG for unstructured only) → persona/authorized-scope LLM narrative → action engine (driver→lever→action→impact→owner) → decision-rights validation → user workspace → feedback + outcome tracking. Security/lineage/freshness/audit/latency/tokens/cost/model-calls apply horizontally across every layer.
2. **Stack:** Python/Pandas + DuckDB→Postgres + FastAPI + scikit-learn/statsmodels + custom two-level decomposition + YAML contracts + pgvector (unstructured content only) + Claude API + Next.js/Tailwind + JWT/RBAC + Docker Compose.
3. **Five KPIs:** Revenue, Orders, Conversion Rate, AOV, Gross Margin.
4. **Datasets:** `fact_sales_line` (order×product, hourly), `fact_marketing_daily` (campaign×region×channel×day), `fact_inventory_snapshot` (SKU×warehouse, 4-hourly), Gold `kpi_region_daily` and `product_performance_daily` at their own native grains + calendar/product/region/channel dimensions + semantic contracts + users/roles + action playbooks + feedback/telemetry logs — with a hidden `ground_truth_drivers` table (populated via counterfactual removal, not manual assignment) for evaluation only.
5. **Analytical methods:** seasonal-baseline forecast + 95% prediction interval for anomaly significance (no t-test); combined stats+impact materiality score; Level-1 multiplicative KPI-bridge decomposition (Sessions×Conversion×AOV, exact, sums to 100%); Level-2 business-driver diagnosis via SQL correlation and mix-rate decomposition; rule-based hypothesis catalog scored by contribution×evidence-confidence; one Difference-in-Differences causal demonstration.
6. **LLM responsibilities:** intent parsing, narrative generation, persona adaptation, action phrasing only — never arithmetic, bridge/driver contribution, or confidence scoring.
7. **Confidence approach:** Evidence Confidence Score — a weighted, deterministic composite (data quality, freshness, historical sufficiency, statistical strength, cross-source consistency, minus contradiction penalty), explicitly labeled as an evidence-quality score rather than a posterior probability, with HIGH/MEDIUM/LOW bands and genuine abstention at LOW.
8. **Security approach:** JWT + authorization resolved *before* the SQL query is built (scoped query from the start, not post-hoc filtering), demonstrated with an explicit cross-region denial.
9. **Demo scenarios:** the 7 in Section M, anchored by the single end-to-end revenue walkthrough (now narrated as bridge decomposition → business-driver diagnosis, not a flat driver list).
10. **Innovation points to emphasize:** Evidence Object + Evidence Confidence Score/abstention as the trust mechanism; counterfactual-removal ground-truth validation of two-level attribution accuracy; authorization baked into the query itself rather than the LLM output.

---

## U. Critical Self-Review (Task 32)

- **Overengineered if not careful:** full causal-inference suite, a dedicated vector-DB microservice for a tiny static corpus, any deep-learning anomaly detector — all trimmed above.
- **Weakest point:** the marketing-attribution confidence is deliberately capped/uncertain in the demo — good for showing honesty, but means one of the four drivers will always look "soft" in front of judges; frame this proactively as a feature, not a gap.
- **Hardest claim to defend:** the DiD demo's "caused by" language — must be scoped tightly to the one clean treatment/control region pair and presented as an estimate, or a technical judge will push back hard.
- **Missing evaluation risk:** narrative factuality checking is easy to skip under time pressure — budget explicit time for it, since a single hallucinated number in front of judges undermines the entire pitch.
- **Unnecessary ML to avoid:** Isolation Forest, XGBoost forecasting, and SHAP are all *optional* — don't add them just to look sophisticated; each adds a black-box element that a skeptical judge can attack, and none improves recoverability of the known ground truth over the simpler deterministic methods.
- **Unnecessary LLM usage to avoid:** don't let the LLM touch the RAG-retrieval ranking or the confidence score — keep both deterministic even though an LLM "could" do them; that boundary is the entire thesis of the product.
- **Scalability honesty:** the pre-aggregated Gold tables and cached Evidence Objects scale fine; what does *not* scale as designed is per-request LLM narrative generation for every persona on every KPI — mitigate by batching/pre-computing likely narratives, and say so if asked.
- **Security gap to watch:** if PII tables are added later (they're excluded here on purpose), column-level masking becomes mandatory — flag this as a known extension rather than pretending it's already solved.
- **Synthetic-data realism risk:** judges may sense the incident is "too clean." Counter by adding realistic noise (Section on ground-truth scenario: weekend effects, promo periods, random noise) so the injected incident isn't a discontinuous step-change but a plausible multi-week degradation with genuine ambiguity — which is exactly what motivates the MEDIUM-confidence abstention demo, turning a potential weakness into supporting evidence for the confidence engine.

**Net result:** the improved final design keeps every mandatory capability, cuts every method that can't be defended under cross-examination, and turns the one genuinely soft signal (marketing attribution) into the centerpiece of the abstention demo rather than hiding it.