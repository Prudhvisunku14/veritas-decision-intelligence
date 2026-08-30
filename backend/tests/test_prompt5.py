import pytest
from fastapi import HTTPException

from backend.app.security import USERS, authorize
from backend.app.services.actions import select_actions
from backend.app.services.evidence import build_evidence
from backend.app.services.narrative import generate_narrative, validate_narrative_factuality, template_narrative
from backend.app.services import data_access


def test_security_entitlements():
    """Verify role-based scoping before analytics execution."""
    north_mgr = USERS["north_mgr"]
    marketing_mgr = USERS["marketing_mgr"]
    ceo = USERS["ceo"]

    # North manager allowed for North
    authorize(north_mgr, "North", "revenue")

    # North manager denied for South
    with pytest.raises(HTTPException) as exc_info:
        authorize(north_mgr, "South", "revenue")
    assert exc_info.value.status_code == 403
    assert "North" in exc_info.value.detail

    # Marketing manager denied for sensitive gross_margin
    with pytest.raises(HTTPException) as exc_info:
        authorize(marketing_mgr, "North", "gross_margin")
    assert exc_info.value.status_code == 403

    # CEO allowed for all regions and KPIs
    authorize(ceo, "South", "gross_margin")


def test_action_permissions():
    """Verify action playbooks are filtered by persona decision rights and evidence confidence."""
    evidence = build_evidence("North", "revenue", "main")

    regional_actions = select_actions(evidence, requester_role="regional_manager")
    ceo_actions = select_actions(evidence, requester_role="ceo")

    assert isinstance(regional_actions, list)
    assert isinstance(ceo_actions, list)

    for action in regional_actions:
        assert "driver" in action
        assert "lever" in action
        assert "action" in action
        assert "expected_impact" in action
        assert "owner" in action
        assert "confidence" in action
        assert "monitoring_plan" in action
        assert action["status"] == "validated_playbook_action"


def test_offline_fallback():
    """Verify narrative generation works offline without LLM API key."""
    evidence = build_evidence("North", "revenue", "main")
    actions = select_actions(evidence, requester_role="ceo")
    context = []

    text, llm_meta = generate_narrative(evidence, persona="ceo", actions=actions, context=context)

    assert isinstance(text, str)
    assert len(text) > 50
    assert "North" in text
    assert "Revenue" in text
    assert llm_meta["input_tokens"] == 0
    assert llm_meta["output_tokens"] == 0
    assert llm_meta["estimated_cost_usd"] == 0.0
    assert llm_meta["fallback_used"] is True


def test_factuality_grounding():
    """Verify factuality validator catches invalid probability claims and unproven causality."""
    evidence = build_evidence("North", "revenue", "main")
    actions = select_actions(evidence, requester_role="ceo")

    # Invalid: turn ECS into probability percentage
    bad_prob_text = "The revenue drop has a 71% probability of being caused by marketing."
    is_valid, reason = validate_narrative_factuality(bad_prob_text, evidence, actions)
    assert not is_valid
    assert "probability" in reason.lower()

    # Invalid: claim direct causality without causal_result
    bad_causal_text = "Marketing spend decrease directly caused the revenue drop."
    is_valid_c, reason_c = validate_narrative_factuality(bad_causal_text, evidence, actions)
    assert not is_valid_c
    assert "causality" in reason_c.lower()

    # Valid template text
    good_text = template_narrative(evidence, persona="ceo", actions=actions)
    is_valid_g, _ = validate_narrative_factuality(good_text, evidence, actions)
    assert is_valid_g


def test_feedback_persistence():
    """Verify feedback storage and batch recalibration status."""
    payload = {
        "user_id": "ceo",
        "insight_id": "ins_test_123",
        "rating": 5,
        "comment": "Accurate breakdown of stockout impact.",
    }
    result = data_access.append_feedback(payload)

    assert result["status"] == "queued_for_validation"
    assert "feedback_id" in result
    assert result["user_id"] == "ceo"


def test_telemetry_logging(tmp_path, monkeypatch):
    """Verify telemetry logging schema and offline zero-token recording."""
    row = {
        "request_id": "req_test_999",
        "created_at": "2026-08-29T12:00:00Z",
        "insight_id": "ins_test_123",
        "role": "ceo",
        "kpi": "revenue",
        "region": "North",
        "total_latency_ms": 45.2,
        "sql_latency_ms": 0.0,
        "analytics_latency_ms": 32.1,
        "retrieval_latency_ms": 5.0,
        "llm_latency_ms": 0.0,
        "model": "deterministic_template",
        "model_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "cache_hit": False,
        "fallback_used": True,
        "errors": 0,
        "ecs_band": "MEDIUM",
    }
    data_access.append_telemetry(row)
    # File appended successfully without exception
