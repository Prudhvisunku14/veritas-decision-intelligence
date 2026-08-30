from typing import Any
from pydantic import BaseModel, Field


class KPIBridgeItem(BaseModel):
    component: str
    contribution_pct_points: float
    contribution_pct_points_full_precision: float | None = None
    contribution_value: float | None = None
    contribution_value_full_precision: float | None = None
    method: str


class DiagnosisItem(BaseModel):
    parent_kpi: str | None = None
    diagnoses: str
    hypothesis_id: str | None = None
    cause: str
    evidence_confidence: float = Field(ge=0.0, le=1.0)
    hypothesis_priority: float | None = None
    method: str
    source_tables: list[str]
    freshness_hours: float
    data_quality_score: float
    observed_change_pct: float | None = None
    note: str | None = None


class EvidenceObject(BaseModel):
    insight_id: str
    kpi: str
    scope: str | None = None
    region: str
    window: dict[str, str]
    actual_value: float
    expected_value: float
    delta_absolute: float | None = None
    delta_pct: float
    delta_pct_full_precision: float | None = None
    business_impact_inr: float | None = None
    anomaly_score: float
    prediction_interval: list[float] | None = None
    prediction_interval_95: list[float]
    materiality_score: float
    kpi_bridge: list[KPIBridgeItem]
    business_driver_diagnosis: list[DiagnosisItem]
    contradictions: list[str] | None = None
    contradictory_evidence: list[str] | None = None
    alternative_hypotheses: list[str] | None = None
    alternative_hypotheses_considered: list[str] | None = None
    evidence_confidence_score: float
    confidence_band: str
    abstentions: list[str]
    analysis_method_version: str
    query_id: str
    lineage: str
    generated_at: str
    source_freshness: dict[str, float]
    data_quality: dict[str, float]
    telemetry: dict[str, Any] | None = None


class FeedbackIn(BaseModel):
    insight_id: str
    user_id: str
    rating: Any
    corrected_driver: str | None = None
    free_text: str | None = None
    comment: str | None = None
    action_taken: bool | None = None


class AskRequest(BaseModel):
    question: str
    region: str = "North"
    kpi: str = "revenue"
    scenario: str = "main"


class AskResponse(BaseModel):
    question: str
    answer: str
    intent: str
    insight_id: str
    region: str
    kpi: str
    evidence_summary: dict
    actions: list[dict]
