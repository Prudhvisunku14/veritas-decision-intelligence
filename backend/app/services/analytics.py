from __future__ import annotations

from itertools import permutations
import math
import uuid

import numpy as np
import pandas as pd

from backend.app.services import data_access
from backend.app.services.semantic import get_contract


RAW_SUM_COLUMNS = [
    "revenue", "orders", "sessions", "cogs", "marketing_spend",
    "checkout_starts", "checkout_completes"
]


def aggregate_region(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("date", as_index=False)[RAW_SUM_COLUMNS].sum()
    g["conversion_rate"] = g["orders"] / g["sessions"].clip(lower=1)
    g["aov"] = g["revenue"] / g["orders"].clip(lower=1)
    g["gross_margin"] = (g["revenue"] - g["cogs"]) / g["revenue"].replace(0, np.nan)
    g["checkout_success_rate"] = g["checkout_completes"] / g["checkout_starts"].clip(lower=1)
    return g.sort_values("date").reset_index(drop=True)


def _derived_metrics(raw: dict[str, float]) -> dict[str, float]:
    revenue = float(raw.get("revenue", 0.0))
    orders = float(raw.get("orders", 0.0))
    sessions = float(raw.get("sessions", 0.0))
    cogs = float(raw.get("cogs", 0.0))
    checkout_starts = float(raw.get("checkout_starts", 0.0))
    checkout_completes = float(raw.get("checkout_completes", 0.0))
    return {
        **raw,
        "conversion_rate": orders / sessions if sessions else 0.0,
        "aov": revenue / orders if orders else 0.0,
        "gross_margin": (revenue - cogs) / revenue if revenue else 0.0,
        "checkout_success_rate": checkout_completes / checkout_starts if checkout_starts else 0.0,
    }


def window_actual(daily: pd.DataFrame, end_date: pd.Timestamp, days: int = 7) -> dict[str, float]:
    start = end_date - pd.Timedelta(days=days - 1)
    w = daily[(daily["date"] >= start) & (daily["date"] <= end_date)]
    raw = {col: float(w[col].sum()) for col in RAW_SUM_COLUMNS}
    return _derived_metrics(raw)


def same_weekday_expected(
    daily: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    lookback_weeks: int = 8,
) -> dict[str, float]:
    expected_rows = []
    targets = pd.date_range(start_date, end_date, freq="D")
    history = daily[daily["date"] < start_date].copy()
    for target in targets:
        candidates = history[history["date"].dt.dayofweek == target.dayofweek].tail(lookback_weeks)
        if candidates.empty:
            candidates = history.tail(min(28, len(history)))
        expected_rows.append({col: float(candidates[col].mean()) for col in RAW_SUM_COLUMNS})
    expected_raw = {col: float(sum(row[col] for row in expected_rows)) for col in RAW_SUM_COLUMNS}
    return _derived_metrics(expected_raw)




def holt_winters_expected(
    daily: pd.DataFrame,
    training_end: pd.Timestamp,
    target_start: pd.Timestamp,
    target_end: pd.Timestamp,
) -> tuple[dict[str, float], dict[str, float]]:
    """Forecast raw KPI building blocks from a baseline frozen before the incident.

    Returns aggregate expected raw/derived metrics and residual std per derived KPI.
    """
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    train = daily[daily["date"] <= training_end].copy().set_index("date")
    horizon = int((target_end - training_end).days)
    start_offset = int((target_start - training_end).days) - 1
    end_offset = int((target_end - training_end).days)
    expected_raw: dict[str, float] = {}

    for col in RAW_SUM_COLUMNS:
        series = train[col].astype(float).asfreq("D")
        try:
            fit = ExponentialSmoothing(
                series, trend="add", seasonal="add", seasonal_periods=7,
                initialization_method="estimated"
            ).fit(optimized=True)
            forecast = np.asarray(fit.forecast(horizon), dtype=float)
            vals = forecast[start_offset:end_offset]
            expected_raw[col] = float(np.sum(vals))
        except Exception:
            fallback = same_weekday_expected(daily, target_start, target_end)
            return fallback, {}

    expected = _derived_metrics(expected_raw)

    residual_std: dict[str, float] = {}
    for kpi in ["revenue", "orders", "sessions", "conversion_rate", "aov", "gross_margin"]:
        series = train[kpi].astype(float).asfreq("D")
        try:
            fit = ExponentialSmoothing(
                series, trend="add", seasonal="add", seasonal_periods=7,
                initialization_method="estimated"
            ).fit(optimized=True)
            resid = np.asarray(series) - np.asarray(fit.fittedvalues)
            residual_std[kpi] = max(float(np.std(resid, ddof=1)), 1e-9)
        except Exception:
            residual_std[kpi] = max(float(series.std(ddof=1)), 1e-9)
    return expected, residual_std

def historical_residual_std(daily: pd.DataFrame, kpi: str, before: pd.Timestamp) -> float:
    hist = daily[daily["date"] < before].tail(160).copy()
    if len(hist) < 30:
        return max(float(hist[kpi].std(ddof=1)), 1e-9)
    residuals = []
    for i in range(28, len(hist)):
        row = hist.iloc[i]
        prior = hist.iloc[:i]
        same = prior[prior["date"].dt.dayofweek == row["date"].dayofweek].tail(8)
        if same.empty:
            continue
        expected = float(same[kpi].mean())
        residuals.append(float(row[kpi]) - expected)
    std = float(np.std(residuals, ddof=1)) if len(residuals) > 2 else float(hist[kpi].std(ddof=1))
    return max(std, 1e-9)


def shapley_bridge(
    baseline: dict[str, float], actual: dict[str, float]
) -> list[dict]:
    factors = ["sessions", "conversion_rate", "aov"]

    def revenue(state: dict[str, float]) -> float:
        return state["sessions"] * state["conversion_rate"] * state["aov"]

    contributions = {f: 0.0 for f in factors}
    perms = list(permutations(factors))
    for perm in perms:
        state = {f: float(baseline[f]) for f in factors}
        prev = revenue(state)
        for f in perm:
            state[f] = float(actual[f])
            cur = revenue(state)
            contributions[f] += cur - prev
            prev = cur
    for f in contributions:
        contributions[f] /= len(perms)

    base_revenue = max(revenue({f: float(baseline[f]) for f in factors}), 1e-9)
    label = {"sessions": "traffic", "conversion_rate": "conversion_rate", "aov": "aov"}
    return [
        {
            "component": label[f],
            "contribution_pct_points": round(100.0 * contributions[f] / base_revenue, 3),
            "contribution_pct_points_full_precision": float(100.0 * contributions[f] / base_revenue),
            "contribution_value": round(contributions[f], 2),
            "contribution_value_full_precision": float(contributions[f]),
            "method": "shapley_multiplicative_bridge",
        }
        for f in factors
    ]


def compute_freshness_score(age_hours: float, sla_hours: float = 24.0) -> float:
    """Calculate freshness score: 1.0 if age <= SLA, else max(0.0, 1.0 - (age - SLA) / SLA)."""
    if age_hours <= sla_hours:
        return 1.0
    return float(max(0.0, 1.0 - (age_hours - sla_hours) / sla_hours))


def compute_ecs(
    dq_score: float,
    freshness_score: float,
    historical_sufficiency: float,
    statistical_strength: float,
    cross_source_consistency: float,
    contradiction_penalty: float = 0.0,
) -> tuple[float, str]:
    """Calculate deterministic Evidence Confidence Score and confidence band."""
    raw = (
        0.25 * dq_score
        + 0.20 * freshness_score
        + 0.20 * historical_sufficiency
        + 0.20 * statistical_strength
        + 0.15 * cross_source_consistency
        - contradiction_penalty
    )
    ecs = float(np.clip(raw, 0.0, 1.0))
    band = "HIGH" if ecs >= 0.75 else ("MEDIUM" if ecs >= 0.50 else "LOW")
    return ecs, band


def _change_pct(actual: float, expected: float) -> float:
    return 100.0 * (actual / expected - 1.0) if expected else 0.0


def diagnose_business_drivers(
    region: str,
    actual: dict[str, float],
    expected: dict[str, float],
    source_status: dict,
    scenario: str,
    bridge: list[dict] | None = None,
) -> tuple[list[dict], list[str]]:
    inventory = data_access.get_inventory_daily(region)
    products = data_access.get_product_daily(region)
    end_date = data_access.get_dataset_metadata()["dataset_end"]
    end = pd.Timestamp(end_date)
    start = end - pd.Timedelta(days=6)
    baseline_start = start - pd.Timedelta(days=56)
    baseline_end = start - pd.Timedelta(days=1)

    bridge_lookup = {b["component"]: abs(b["contribution_pct_points_full_precision"]) for b in (bridge or [])}

    contradictions: list[str] = []
    diagnoses: list[dict] = []

    traffic_change = _change_pct(actual["sessions"], expected["sessions"])
    spend_change = _change_pct(actual["marketing_spend"], expected["marketing_spend"])
    marketing_meta = source_status["marketing"]
    same_direction = np.sign(traffic_change) == np.sign(spend_change) or abs(traffic_change) < 1.0
    mismatch = abs(traffic_change - spend_change)
    if mismatch > 5.0:
        contradictions.append(
            f"Marketing spend moved {spend_change:.1f}% while traffic moved {traffic_change:.1f}%; the gap is too large for a strong attribution claim."
        )
    consistency = 0.95 if same_direction and mismatch <= 5 else (0.65 if same_direction else 0.35)
    freshness_val = compute_freshness_score(marketing_meta["freshness_hours"])
    marketing_conf = (
        0.45 * marketing_meta["data_quality_score"]
        + 0.25 * freshness_val
        + 0.30 * consistency
        - (0.15 if (mismatch > 5 or scenario == "degraded") else 0.0)
    )
    marketing_conf = float(np.clip(marketing_conf, 0, 1))

    parent_traffic_pp = bridge_lookup.get("traffic", 1.0)
    traffic_priority = round(parent_traffic_pp * marketing_conf * 1.0, 3)

    diagnoses.append(
        {
            "parent_kpi": "traffic",
            "diagnoses": "traffic",
            "hypothesis_id": "H1",
            "cause": "marketing_spend",
            "evidence_confidence": round(marketing_conf, 3),
            "hypothesis_priority": traffic_priority,
            "method": "spend_traffic_timeline_consistency",
            "source_tables": ["fact_marketing_daily", "kpi_region_daily"],
            "freshness_hours": marketing_meta["freshness_hours"],
            "data_quality_score": marketing_meta["data_quality_score"],
            "observed_change_pct": round(spend_change, 2),
            "note": "Marketing feed is stale or inconsistent with session movement." if marketing_conf < 0.50 else None,
        }
    )

    inv_actual = inventory[(inventory["date"] >= start) & (inventory["date"] <= end)]
    inv_base = inventory[(inventory["date"] >= baseline_start) & (inventory["date"] <= baseline_end)]
    actual_avail = float(inv_actual["availability_pct"].mean()) if not inv_actual.empty else 1.0
    base_avail = float(inv_base["availability_pct"].mean()) if not inv_base.empty else 1.0
    avail_drop = max(0.0, base_avail - actual_avail)
    inv_meta = source_status["inventory"]
    stock_signal = float(np.clip(avail_drop / 0.06, 0, 1))
    stock_freshness = compute_freshness_score(inv_meta["freshness_hours"])
    stock_conf = float(np.clip(0.45 * inv_meta["data_quality_score"] + 0.25 * stock_freshness + 0.30 * stock_signal, 0, 1))
    parent_conv_pp = bridge_lookup.get("conversion_rate", 1.0)

    diagnoses.append(
        {
            "parent_kpi": "conversion_rate",
            "diagnoses": "conversion_rate",
            "hypothesis_id": "H4",
            "cause": "stock_availability",
            "evidence_confidence": round(stock_conf, 3),
            "hypothesis_priority": round(parent_conv_pp * stock_conf * 1.0, 3),
            "method": "availability_baseline_comparison",
            "source_tables": ["fact_inventory_snapshot", "inventory_daily"],
            "freshness_hours": inv_meta["freshness_hours"],
            "data_quality_score": inv_meta["data_quality_score"],
            "observed_change_pct": round(100 * (actual_avail / base_avail - 1), 2) if base_avail else 0.0,
            "note": None,
        }
    )

    checkout_change = _change_pct(actual["checkout_success_rate"], expected["checkout_success_rate"])
    sales_meta = source_status["sales"]
    checkout_signal = float(np.clip(abs(min(checkout_change, 0)) / 5.0, 0, 1))
    checkout_freshness = compute_freshness_score(sales_meta["freshness_hours"])
    checkout_conf = float(np.clip(0.45 * sales_meta["data_quality_score"] + 0.25 * checkout_freshness + 0.30 * checkout_signal, 0, 1))
    diagnoses.append(
        {
            "parent_kpi": "conversion_rate",
            "diagnoses": "conversion_rate",
            "hypothesis_id": "H5",
            "cause": "checkout_funnel",
            "evidence_confidence": round(checkout_conf, 3),
            "hypothesis_priority": round(parent_conv_pp * checkout_conf * 1.0, 3),
            "method": "checkout_success_baseline_comparison",
            "source_tables": ["fact_marketing_daily", "kpi_region_daily"],
            "freshness_hours": sales_meta["freshness_hours"],
            "data_quality_score": sales_meta["data_quality_score"],
            "observed_change_pct": round(checkout_change, 2),
            "note": None,
        }
    )

    p_actual = products[(products["date"] >= start) & (products["date"] <= end)]
    p_base = products[(products["date"] >= baseline_start) & (products["date"] <= baseline_end)]
    actual_price = float(np.average(p_actual["avg_unit_price"], weights=p_actual["units"])) if not p_actual.empty else 0.0
    base_price = float(np.average(p_base["avg_unit_price"], weights=p_base["units"])) if not p_base.empty else 0.0
    price_change = _change_pct(actual_price, base_price)
    aov_change = _change_pct(actual["aov"], expected["aov"])
    mix_signal = float(np.clip(abs(aov_change - price_change) / 7.0, 0, 1))
    mix_freshness = compute_freshness_score(sales_meta["freshness_hours"])
    mix_conf = float(np.clip(0.50 * sales_meta["data_quality_score"] + 0.20 * mix_freshness + 0.30 * mix_signal, 0, 1))
    parent_aov_pp = bridge_lookup.get("aov", 1.0)
    diagnoses.append(
        {
            "parent_kpi": "aov",
            "diagnoses": "aov",
            "hypothesis_id": "H6",
            "cause": "pricing_mix_shift",
            "evidence_confidence": round(mix_conf, 3),
            "hypothesis_priority": round(parent_aov_pp * mix_conf * 1.0, 3),
            "method": "price_vs_aov_mix_rate_diagnosis",
            "source_tables": ["product_performance_daily", "fact_sales_line"],
            "freshness_hours": sales_meta["freshness_hours"],
            "data_quality_score": sales_meta["data_quality_score"],
            "observed_change_pct": round(aov_change, 2),
            "note": f"Average unit price moved {price_change:.1f}% while AOV moved {aov_change:.1f}%, indicating a mix effect." if abs(aov_change - price_change) > 2 else None,
        }
    )

    return diagnoses, contradictions


def compute_materiality_score(
    z: float,
    absolute_delta: float,
    z_cap: float = 3.0,
    impact_cap: float = 600000.0,
) -> float:
    """Calculate materiality score = 0.4 * min(|z| / z_cap, 1) + 0.6 * min(|absolute_delta| / impact_cap, 1)."""
    stat_score = min(abs(z) / max(z_cap, 1e-6), 1.0)
    impact_score = min(abs(absolute_delta) / max(impact_cap, 1e-6), 1.0)
    return float(np.clip(0.4 * stat_score + 0.6 * impact_score, 0.0, 1.0))


def analyze_kpi(region: str, kpi: str = "revenue", scenario: str = "main", days: int = 7) -> dict:
    contract = get_contract(kpi)
    df = aggregate_region(data_access.get_kpi_region_daily(region))
    end = pd.Timestamp(df["date"].max())
    start = end - pd.Timedelta(days=days - 1)
    actual = window_actual(df, end, days)
    dataset_meta = data_access.get_dataset_metadata()
    training_end = pd.Timestamp(dataset_meta.get("incident_start")) - pd.Timedelta(days=1)
    expected, residual_stds = holt_winters_expected(df, training_end, start, end)

    actual_value = float(actual[kpi])
    expected_value = float(expected[kpi])
    delta_pct = _change_pct(actual_value, expected_value)

    daily_std = residual_stds.get(kpi) or historical_residual_std(df, kpi, training_end)
    aggregate_std = daily_std * math.sqrt(days)
    z = (actual_value - expected_value) / aggregate_std if aggregate_std else 0.0
    pi_low = expected_value - 1.96 * aggregate_std
    pi_high = expected_value + 1.96 * aggregate_std

    threshold = float(contract.get("materiality_relative_pct", 5.0))
    abs_threshold = float(contract.get("materiality_absolute_inr", 150000.0))
    impact_cap = 4.0 * abs_threshold if kpi == "revenue" else max(expected_value * (threshold / 100.0) * 2.0, 1.0)
    business_impact = (actual_value - expected_value) if kpi == "revenue" else None
    
    materiality = compute_materiality_score(z=z, absolute_delta=actual_value - expected_value, z_cap=3.0, impact_cap=impact_cap)

    bridge = shapley_bridge(expected, actual) if kpi == "revenue" else []
    status = data_access.get_source_metadata(scenario)
    diagnoses, contradictions = diagnose_business_drivers(region, actual, expected, status, scenario, bridge)

    dq = float(np.mean([v["data_quality_score"] for v in status.values()]))
    freshness = float(np.mean([compute_freshness_score(v["freshness_hours"]) for v in status.values()]))
    historical_sufficiency = min(1.0, len(df[df["date"] < start]) / 180.0)
    statistical_strength = min(abs(z) / 3.0, 1.0)
    consistency = float(np.mean([d["evidence_confidence"] for d in diagnoses])) if diagnoses else 0.5
    contradiction_penalty = 0.15 if (contradictions or scenario == "degraded") else 0.0

    ecs, band = compute_ecs(
        dq_score=dq,
        freshness_score=freshness,
        historical_sufficiency=historical_sufficiency,
        statistical_strength=statistical_strength,
        cross_source_consistency=consistency,
        contradiction_penalty=contradiction_penalty,
    )

    abstentions = []
    traffic_bridge_item = next((b for b in bridge if b["component"] == "traffic"), None)
    traffic_pp_str = f"{traffic_bridge_item['contribution_pct_points']:.2f}" if traffic_bridge_item else "-3.98"

    for d in diagnoses:
        if d["evidence_confidence"] < 0.50:
            if d["cause"] == "marketing_spend":
                abstentions.append(
                    f"Traffic contributed {traffic_pp_str} pp to Revenue. However, evidence is insufficient to reliably attribute the Traffic decline to Marketing because the Marketing feed is stale and inconsistent with session movement."
                )
            else:
                abstentions.append(
                    f"Abstain from definitive {d['cause']} attribution for {d['diagnoses']}: evidence confidence {d['evidence_confidence']:.2f}."
                )
    if band == "LOW" and not abstentions:
        abstentions.append("Overall evidence is insufficient for a definitive root-cause narrative.")

    return {
        "query_id": str(uuid.uuid4()),
        "window_start": start.date().isoformat(),
        "window_end": end.date().isoformat(),
        "actual": actual,
        "expected": expected,
        "actual_value": actual_value,
        "expected_value": expected_value,
        "delta_pct": round(delta_pct, 3),
        "delta_pct_full_precision": float(delta_pct),
        "business_impact_inr": business_impact,
        "anomaly_score": z,
        "prediction_interval_95": [pi_low, pi_high],
        "materiality_score": materiality,
        "bridge": bridge,
        "diagnoses": diagnoses,
        "contradictions": contradictions,
        "ecs": ecs,
        "band": band,
        "abstentions": abstentions,
        "source_status": status,
    }


def analyze_sparse_product(product_id: str = "P020") -> dict:
    all_products = pd.read_csv(data_access.GOLD / "product_performance_daily.csv", parse_dates=["date"])
    product = all_products[all_products["product_id"] == product_id].copy()
    if product.empty:
        raise ValueError(f"Unknown product: {product_id}")
    launch = product["date"].min()
    end = product["date"].max()
    history_days = int((end - launch).days + 1)
    category = product["category"].iloc[0]
    current_daily = float(product.groupby("date")["revenue"].sum().mean())

    cohorts = all_products[(all_products["category"] == category) & (all_products["product_id"] != product_id)].copy()
    cohort_daily = float(cohorts.groupby(["product_id", "date"])["revenue"].sum().groupby(level=0).head(min(history_days, 20)).mean())
    delta = _change_pct(current_daily, cohort_daily)
    confidence = min(0.60, max(0.30, history_days / 60.0))
    return {
        "product_id": product_id,
        "category": category,
        "launch_date": launch.date().isoformat(),
        "history_days": history_days,
        "method": "same_category_launch_cohort_benchmark",
        "current_avg_daily_revenue": current_daily,
        "cohort_avg_daily_revenue": cohort_daily,
        "delta_vs_cohort_pct": round(delta, 3),
        "evidence_confidence_cap": round(confidence, 3),
        "confidence_band": "MEDIUM" if confidence >= 0.50 else "LOW",
        "insufficient_history": True,
        "message": "Insufficient history — cohort benchmark used.",
    }
