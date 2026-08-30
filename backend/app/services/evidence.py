from __future__ import annotations

from datetime import datetime, timezone
import uuid

from backend.app.services.analytics import analyze_kpi


def build_evidence(region: str, kpi: str, scenario: str = "main") -> dict:
    a = analyze_kpi(region=region, kpi=kpi, scenario=scenario)
    freshness = {k: float(v["freshness_hours"]) for k, v in a["source_status"].items()}
    dq = {k: float(v["data_quality_score"]) for k, v in a["source_status"].items()}
    
    delta_abs = round(a["business_impact_inr"], 2) if a["business_impact_inr"] is not None else round(a["actual_value"] - a["expected_value"], 2)
    
    return {
        "insight_id": f"ins_{uuid.uuid4().hex[:12]}",
        "kpi": kpi,
        "scope": region,
        "region": region,
        "window": {"start": a["window_start"], "end": a["window_end"]},
        "actual_value": round(a["actual_value"], 4),
        "expected_value": round(a["expected_value"], 4),
        "delta_absolute": delta_abs,
        "business_impact_inr": delta_abs if kpi == "revenue" else None,
        "delta_pct": round(a["delta_pct"], 3),
        "delta_pct_full_precision": a["delta_pct_full_precision"],
        "anomaly_score": round(a["anomaly_score"], 3),
        "prediction_interval": [round(x, 4) for x in a["prediction_interval_95"]],
        "prediction_interval_95": [round(x, 4) for x in a["prediction_interval_95"]],
        "materiality_score": round(a["materiality_score"], 3),
        "kpi_bridge": a["bridge"],
        "business_driver_diagnosis": a["diagnoses"],
        "contradictions": a["contradictions"],
        "contradictory_evidence": a["contradictions"],
        "alternative_hypotheses": ["seasonality", "campaign_performance", "pricing_only"],
        "alternative_hypotheses_considered": ["seasonality", "campaign_performance", "pricing_only"],
        "evidence_confidence_score": round(a["ecs"], 3),
        "confidence_band": a["band"],
        "abstentions": a["abstentions"],
        "lineage": "raw sources -> reconciled Gold tables -> scoped KPI analysis -> Evidence Object",
        "query_id": a["query_id"],
        "analysis_method_version": "bridge_v1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_freshness": freshness,
        "data_quality": dq,
    }
