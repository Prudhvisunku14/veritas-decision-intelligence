# Verification Snapshot & Evaluation Report

**Verified in Environment:** 2026-08-29
**Test Suite Status:** **35 Passed / 0 Failed** (`python -m pytest backend/tests -q`)

---

### Measured Verification Results (`scripts/evaluate_system.py`)

1. **Main North Revenue Scenario (`2026-07-10` to `2026-08-20`):**
   - **Expected Baseline Revenue:** `3,144,866.96 INR`
   - **Actual Revenue:** `2,707,979.70 INR`
   - **Revenue Delta (%):** `-13.892%` (Full Precision: `-13.892074514748831%`)
   - **Absolute Revenue Impact:** `-436,887.26 INR`
   - **95% Prediction Interval:** `[2,713,621.57, 3,576,112.36] INR`
   - **Residual Z-Score:** `-1.986` ($\approx -2.0$)
   - **Materiality Score:** `0.702` ($\ge 0.60$ threshold)
   - **Overall Evidence Confidence Score (ECS):** `0.714` (`MEDIUM` confidence band)

2. **Level-1 Shapley Revenue Bridge ($f(S,C,A) = S \times C \times A$):**
   - **Traffic Contribution:** `-3.976%` (`-125,042.45 INR`)
   - **Conversion Rate Contribution:** `-9.263%` (`-291,313.25 INR`, dominant negative component)
   - **AOV Contribution:** `-0.653%` (`-20,531.56 INR`, net negative mix effect)
   - **Bridge Reconciliation Error:** `3.55e-15` (Exact float reconciliation, error $< 10^{-8}$)

3. **Degraded Marketing Scenario & Partial Abstention:**
   - Marketing feed SLA: 24h, Age: ~30h, Freshness: 0.75, Spend/Traffic mismatch: 15%
   - Marketing Diagnosis Confidence: `0.216` ($< 0.50$)
   - **Partial Abstention Output:**
     > *"Traffic contributed -3.98 pp to Revenue. However, evidence is insufficient to reliably attribute the Traffic decline to Marketing because the Marketing feed is stale and inconsistent with session movement."*

4. **Security Entitlements Test:**
   - `north_mgr` requesting `South` Revenue receives HTTP **403** Access Denied *before* any South analytics or database queries run. South data is never passed to Evidence Objects or LLM prompts.

5. **Sparse-History SKU (`P020`):**
   - History Days: `20`
   - Strategy: Seasonal Holt-Winters forecast bypassed; same-category launch cohort benchmark used.
   - Confidence Ceiling: `0.333` ($\le 0.60$ ceiling enforced).
   - Output Notice: `"Insufficient history — cohort benchmark used."`

6. **System Benchmark Performance Metrics:**
   - **Anomaly Precision / Recall / F1:** `1.0 / 1.0 / 1.0`
   - **Top-1 & Top-2 Driver Recovery Rate:** `100%`
   - **Abstention Correctness Rate:** `100%`
   - **Security Entitlement Pass Rate:** `100%`
   - **Sparse-History Pass Rate:** `100%`
   - **Numeric Grounding Rate:** `100%`
   - **Analytics Processing Latency:** `~1.89s`

---

### Environment & Run Instructions

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Bootstrap data and DuckDB database
python scripts/bootstrap.py

# 3. Run test suite & evaluation benchmark
python -m pytest backend/tests -q
python scripts/evaluate_system.py

# 4. Start FastAPI server
python -m uvicorn backend.app.main:app --reload --port 8000

# 5. Start Streamlit UI
python -m streamlit run frontend/streamlit_app.py
```
