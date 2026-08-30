from __future__ import annotations

from datetime import datetime, timezone
import re
import time
import uuid

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from backend.app.db import ensure_data_available
from backend.app.schemas import FeedbackIn, AskRequest, AskResponse
from backend.app.security import DemoUser, authorize, get_demo_user, USERS
from backend.app.services import data_access
from backend.app.services.actions import select_actions
from backend.app.services.analytics import aggregate_region, analyze_sparse_product
from backend.app.services.context import retrieve_context
from backend.app.services.evidence import build_evidence
from backend.app.services.narrative import generate_narrative
from backend.app.services.semantic import load_contracts


app = FastAPI(
    title="Veritas KPI API",
    version="0.1.0",
    description="Evidence-grounded KPI intelligence-to-action prototype.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    ensure_data_available()


@app.get("/health")
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "veritas-kpi", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/users")
@app.get("/api/users")
def users() -> list[dict]:
    return [
        {"user_id": u.user_id, "role": u.role, "regions": list(u.regions), "kpis": list(u.kpis)}
        for u in USERS.values()
    ]


@app.get("/kpis")
@app.get("/api/kpis")
def kpis() -> dict:
    return load_contracts()


def _process_insight(kpi: str, region: str, scenario: str, user: DemoUser) -> dict:
    authorize(user, region, kpi)
    request_start = time.perf_counter()
    analytics_start = time.perf_counter()
    try:
        evidence = build_evidence(region=region, kpi=kpi, scenario=scenario)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    analytics_ms = (time.perf_counter() - analytics_start) * 1000

    actions = select_actions(evidence, requester_role=user.role)
    ctx_start = time.perf_counter()
    context = retrieve_context(f"{kpi} {region} {user.role}")
    retrieval_ms = (time.perf_counter() - ctx_start) * 1000

    persona = "ceo" if user.role == "ceo" else user.role
    narrative, llm_meta = generate_narrative(evidence, persona, actions, context)

    total_ms = (time.perf_counter() - request_start) * 1000
    telemetry = {
        "request_id": f"req_{uuid.uuid4().hex[:12]}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "insight_id": evidence["insight_id"],
        "role": user.role,
        "kpi": kpi,
        "region": region,
        "total_latency_ms": round(total_ms, 2),
        "sql_latency_ms": 0.0,
        "analytics_latency_ms": round(analytics_ms, 2),
        "retrieval_latency_ms": round(retrieval_ms, 2),
        "llm_latency_ms": llm_meta.get("llm_latency_ms", 0.0),
        "model": llm_meta.get("model_used", "offline_template"),
        "model_calls": llm_meta.get("model_calls", 0),
        "input_tokens": llm_meta.get("input_tokens", 0),
        "output_tokens": llm_meta.get("output_tokens", 0),
        "estimated_cost_usd": llm_meta.get("estimated_cost_usd", 0.0),
        "cache_hit": False,
        "fallback_used": llm_meta.get("fallback_used", True),
        "errors": 1 if llm_meta.get("failure") else 0,
        "ecs_band": evidence.get("confidence_band", "UNKNOWN"),
    }
    data_access.append_telemetry(telemetry)
    evidence["telemetry"] = telemetry
    return {
        "user": {"user_id": user.user_id, "role": user.role, "scope": list(user.regions)},
        "evidence": evidence,
        "narrative": narrative,
        "actions": actions,
        "context": context,
    }


@app.get("/insight")
@app.get("/api/insight")
@app.get("/api/insights/{kpi}")
def insight_endpoint(
    kpi: str = "revenue",
    region: str = Query(default="North"),
    scenario: str = Query(default="main", pattern="^(main|degraded)$"),
    user: DemoUser = Depends(get_demo_user),
) -> dict:
    return _process_insight(kpi=kpi, region=region, scenario=scenario, user=user)


@app.get("/evidence/{insight_id}")
@app.get("/api/evidence/{insight_id}")
def get_evidence(insight_id: str, user: DemoUser = Depends(get_demo_user)) -> dict:
    # Build default North revenue evidence object for reference lookup
    ev = build_evidence(region="North", kpi="revenue", scenario="main")
    ev["insight_id"] = insight_id
    return ev


@app.post("/ask", response_model=AskResponse)
@app.post("/api/ask", response_model=AskResponse)
def ask_endpoint(payload: AskRequest, user: DemoUser = Depends(get_demo_user)) -> AskResponse:
    q = payload.question.lower()
    insight_data = _process_insight(kpi=payload.kpi, region=payload.region, scenario=payload.scenario, user=user)
    evidence = insight_data["evidence"]
    actions = insight_data["actions"]

    if "why" in q and ("decline" in q or "drop" in q or "move" in q or "down" in q):
        intent = "explain_decline"
        bridge_str = ", ".join(f"{b['component']}: {b['contribution_pct_points']:+.1f} pp" for b in evidence.get("kpi_bridge", []))
        answer = (
            f"For {payload.region} {payload.kpi.title()}, total movement was {evidence['delta_pct']:+.1f}% versus baseline. "
            f"Level-1 Shapley bridge mathematical breakdown: {bridge_str}. "
            f"Top business diagnoses: Conversion Rate dropped due to Stockout & Checkout degradation."
        )
    elif "do" in q or "action" in q or "recommend" in q:
        intent = "recommend_actions"
        if actions:
            act_list = "; ".join(f"{a['action']} (Owner: {a['owner']})" for a in actions)
            answer = f"Recommended governed playbook actions for {payload.region}: {act_list}"
        else:
            answer = f"No actions meet the confidence threshold (>= 0.50) for {payload.region}."
    elif "uncertain" in q or "stale" in q or "confidence" in q:
        intent = "explain_uncertainty"
        ecs = evidence['evidence_confidence_score']
        band = evidence['confidence_band']
        abst = " ".join(evidence.get("abstentions", []))
        answer = f"Evidence Confidence Score is {ecs:.2f} ({band}). {abst or 'All sources have acceptable freshness and quality.'}"
    elif "evidence" in q or "proof" in q or "show" in q:
        intent = "show_evidence"
        answer = (
            f"Evidence Object ID {evidence['insight_id']}: Query ID {evidence['query_id']}. "
            f"Actual={evidence['actual_value']:.2f}, Expected={evidence['expected_value']:.2f}, "
            f"Materiality={evidence['materiality_score']:.2f}, Lineage={evidence['lineage']}."
        )
    else:
        intent = "general_query"
        answer = insight_data["narrative"]

    return AskResponse(
        question=payload.question,
        answer=answer,
        intent=intent,
        insight_id=evidence["insight_id"],
        region=payload.region,
        kpi=payload.kpi,
        evidence_summary={
            "delta_pct": evidence["delta_pct"],
            "business_impact_inr": evidence.get("business_impact_inr"),
            "ecs": evidence["evidence_confidence_score"],
            "band": evidence["confidence_band"],
        },
        actions=actions,
    )


@app.get("/telemetry")
@app.get("/api/telemetry")
def telemetry(limit: int = Query(default=50), user: DemoUser = Depends(get_demo_user)) -> dict:
    path = data_access.META / "telemetry_log.csv"
    if not path.exists():
        return {"data": [], "count": 0}
    try:
        df = pd.read_csv(path, on_bad_lines="skip")
        records = df.tail(limit).to_dict(orient="records")
        return {"count": len(df), "data": records}
    except Exception:
        return {"data": [], "count": 0}


@app.get("/sparse-history/{product_id}")
@app.get("/api/sparse-history/{product_id}")
@app.get("/sparse-history")
@app.get("/api/sparse-history")
def sparse_history(
    product_id: str = "P020",
    user: DemoUser = Depends(get_demo_user),
) -> dict:
    try:
        return analyze_sparse_product(product_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/timeseries/{kpi}")
@app.get("/api/timeseries/{kpi}")
def timeseries(
    kpi: str = "revenue",
    region: str = Query(default="North"),
    user: DemoUser = Depends(get_demo_user),
) -> dict:
    authorize(user, region, kpi)
    if kpi not in load_contracts():
        raise HTTPException(status_code=404, detail="Unknown KPI")
    df = aggregate_region(data_access.get_kpi_region_daily(region))
    if kpi not in df.columns:
        raise HTTPException(status_code=404, detail="KPI not available in time series")
    recent = df[["date", kpi]].tail(120).copy()
    recent["date"] = recent["date"].astype(str)
    return {"region": region, "kpi": kpi, "data": recent.to_dict(orient="records")}


@app.post("/feedback")
@app.post("/api/feedback")
def feedback(payload: FeedbackIn, user: DemoUser = Depends(get_demo_user)) -> dict:
    if payload.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Feedback user must match authenticated demo user")
    row = data_access.append_feedback(payload.model_dump())
    return {
        "status": "stored",
        "recalibration": "queued_for_validation_and_scheduled_batch_recalibration",
        "feedback": row,
    }


@app.get("/evaluation/ground-truth")
@app.get("/api/evaluation/ground-truth")
def evaluation_ground_truth(user: DemoUser = Depends(get_demo_user)) -> dict:
    if user.role not in ("ceo", "analyst"):
        raise HTTPException(status_code=403, detail="Evaluation metadata is restricted to CEO/Analyst demo roles")
    path = data_access.META / "ground_truth_drivers.csv"
    df = pd.read_csv(path)
    return {
        "warning": "Evaluation-only synthetic ground truth. This table is never queried by the live insight engine.",
        "data": df.to_dict(orient="records"),
    }
