import math
import pytest
from backend.app.services.analytics import (
    shapley_bridge,
    analyze_kpi,
    compute_materiality_score,
    compute_ecs,
    compute_freshness_score,
    analyze_sparse_product,
    _derived_metrics,
)
from backend.app.services.evidence import build_evidence


def test_shapley_bridge_reconciles_revenue_delta():
    baseline = {"sessions": 1000.0, "conversion_rate": 0.04, "aov": 100.0}
    actual = {"sessions": 950.0, "conversion_rate": 0.038, "aov": 98.0}
    bridge = shapley_bridge(baseline, actual)
    total_value = sum(x["contribution_value"] for x in bridge)
    expected_delta = 950 * 0.038 * 98 - 1000 * 0.04 * 100
    assert math.isclose(total_value, expected_delta, abs_tol=0.05)


def test_bridge_reconciliation():
    """Mandatory reconciliation test: traffic_pp + conversion_pp + aov_pp == (actual_rev - base_rev) / base_rev * 100."""
    baseline = {"sessions": 12500.0, "conversion_rate": 0.035, "aov": 1250.0}
    actual = {"sessions": 11200.0, "conversion_rate": 0.031, "aov": 1280.0}
    bridge = shapley_bridge(baseline, actual)
    
    base_rev = baseline["sessions"] * baseline["conversion_rate"] * baseline["aov"]
    act_rev = actual["sessions"] * actual["conversion_rate"] * actual["aov"]
    total_pp = sum(item["contribution_pct_points_full_precision"] for item in bridge)
    expected_pp = (act_rev - base_rev) / base_rev * 100.0

    assert math.isclose(total_pp, expected_pp, abs_tol=1e-8), (
        f"Shapley bridge sum {total_pp:.6f}% does not reconcile to total delta {expected_pp:.6f}%"
    )


def test_main_scenario_calibrated_integrity():
    """Verify calibrated North main scenario meets competition integrity ranges."""
    res = analyze_kpi("North", "revenue", "main")
    
    assert -16.0 <= res["delta_pct_full_precision"] <= -10.0, f"Delta {res['delta_pct_full_precision']} out of range"
    assert res["materiality_score"] >= 0.50, f"Materiality {res['materiality_score']} too low"
    
    bridge = {item["component"]: item["contribution_pct_points_full_precision"] for item in res["bridge"]}
    assert bridge["traffic"] < 0, f"Traffic contribution {bridge['traffic']} should be negative"
    assert bridge["conversion_rate"] < 0, f"Conversion contribution {bridge['conversion_rate']} should be negative"
    assert bridge["aov"] < 0, f"AOV contribution {bridge['aov']} should be negative"
    assert bridge["conversion_rate"] < bridge["traffic"], "Conversion should be dominant negative component"
    
    sum_full = sum(bridge.values())
    assert abs(sum_full - res["delta_pct_full_precision"]) < 1e-8, "Full precision Shapley bridge does not reconcile"


def test_five_kpis_deterministic_calculation():
    """Verify deterministic calculations for Revenue, Orders, Conversion Rate, AOV, Gross Margin with zero division guards."""
    raw_sample = {
        "revenue": 500000.0,
        "orders": 2500.0,
        "sessions": 50000.0,
        "cogs": 320000.0,
        "checkout_starts": 6000.0,
        "checkout_completes": 2500.0,
    }
    derived = _derived_metrics(raw_sample)

    assert derived["revenue"] == 500000.0
    assert derived["orders"] == 2500.0
    assert derived["conversion_rate"] == 2500.0 / 50000.0  # 0.05
    assert derived["aov"] == 500000.0 / 2500.0  # 200.0
    assert derived["gross_margin"] == (500000.0 - 320000.0) / 500000.0  # 0.36

    # Test zero guards
    raw_zero = {"revenue": 0.0, "orders": 0.0, "sessions": 0.0, "cogs": 0.0}
    derived_zero = _derived_metrics(raw_zero)
    assert derived_zero["conversion_rate"] == 0.0
    assert derived_zero["aov"] == 0.0
    assert derived_zero["gross_margin"] == 0.0


def test_materiality_score_formula():
    """Verify materiality score calculation combines statistical z-score and business impact."""
    score = compute_materiality_score(z=-2.5, absolute_delta=-300000.0, z_cap=3.0, impact_cap=600000.0)
    expected = 0.4 * (2.5 / 3.0) + 0.6 * (300000.0 / 600000.0)
    assert math.isclose(score, expected, abs_tol=1e-5)


def test_ecs_thresholds():
    """Verify ECS threshold banding: HIGH >= 0.75, MEDIUM 0.50-0.749, LOW < 0.50."""
    high_ecs, high_band = compute_ecs(1.0, 1.0, 1.0, 1.0, 1.0, 0.0)
    assert high_ecs >= 0.75
    assert high_band == "HIGH"

    med_ecs, med_band = compute_ecs(0.8, 0.8, 0.6, 0.6, 0.6, 0.05)
    assert 0.50 <= med_ecs < 0.75
    assert med_band == "MEDIUM"

    low_ecs, low_band = compute_ecs(0.4, 0.3, 0.2, 0.2, 0.2, 0.30)
    assert low_ecs < 0.50
    assert low_band == "LOW"


def test_freshness_score():
    """Verify freshness score: 1.0 if age <= SLA, else max(0.0, 1.0 - (age - SLA) / SLA)."""
    assert compute_freshness_score(12.0, 24.0) == 1.0
    assert compute_freshness_score(24.0, 24.0) == 1.0
    assert compute_freshness_score(36.0, 24.0) == 0.5
    assert compute_freshness_score(60.0, 24.0) == 0.0


def test_partial_abstention():
    """Verify partial abstention in degraded scenario when marketing feed is stale/contradictory."""
    res = analyze_kpi("North", "revenue", "degraded")
    assert len(res["abstentions"]) > 0
    assert any("Traffic contributed" in abs_str and "Marketing feed is stale" in abs_str for abs_str in res["abstentions"])


def test_abstention():
    """Verify abstentions list captures low confidence drivers."""
    res = analyze_kpi("North", "revenue", "degraded")
    assert "abstentions" in res
    assert isinstance(res["abstentions"], list)


def test_sparse_history():
    """Verify sparse history product P020 bypasses normal forecast and caps ECS <= 0.60."""
    res = analyze_sparse_product("P020")
    assert res["product_id"] == "P020"
    assert res["evidence_confidence_cap"] <= 0.60
    assert "Insufficient history — cohort benchmark used." in res["message"]


def test_evidence_object_schema():
    """Verify Evidence Object output schema completeness."""
    ev = build_evidence("North", "revenue", "main")
    required_keys = [
        "insight_id", "kpi", "scope", "window", "actual_value", "expected_value",
        "delta_absolute", "delta_pct", "prediction_interval", "anomaly_score",
        "materiality_score", "kpi_bridge", "business_driver_diagnosis",
        "contradictions", "alternative_hypotheses", "evidence_confidence_score",
        "confidence_band", "lineage", "query_id", "analysis_method_version",
        "generated_at", "abstentions"
    ]
    for key in required_keys:
        assert key in ev, f"Missing key in Evidence Object: {key}"


def test_level2_not_added_to_bridge():
    """Verify Level 2 diagnosis metrics are separate and not added to Level 1 bridge percentage points."""
    res = analyze_kpi("North", "revenue", "main")
    bridge_sum = sum(item["contribution_pct_points_full_precision"] for item in res["bridge"])
    diag_conf_sum = sum(d["evidence_confidence"] for d in res["diagnoses"])
    # Level-2 evidence confidence sum must not equal Level-1 percentage points sum
    assert not math.isclose(bridge_sum, diag_conf_sum, abs_tol=1e-3)
