from functools import lru_cache
import yaml
from backend.app.config import settings


@lru_cache(maxsize=1)
def _playbooks() -> list[dict]:
    path = settings.root_dir / "backend" / "app" / "knowledge" / "action_playbooks.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["actions"]


def select_actions(evidence: dict, requester_role: str) -> list[dict]:
    confident_causes = {
        d["cause"]: d for d in evidence.get("business_driver_diagnosis", [])
        if d.get("evidence_confidence", 0) >= 0.50
    }
    cause_aliases = {
        "stock_availability": "stock_availability",
        "checkout_funnel": "checkout_funnel",
        "marketing_spend": "marketing_spend",
        "pricing_mix_shift": "pricing_mix_shift",
    }
    out = []
    for play in _playbooks():
        allowed_roles = play.get("allowed_requester_roles", [])
        if requester_role not in allowed_roles:
            continue
        diagnosis = play.get("diagnosis") or play.get("driver")
        if diagnosis not in cause_aliases:
            continue
        if diagnosis not in confident_causes:
            continue
        item = {
            "id": play["id"],
            "driver": play["driver"],
            "lever": play["lever"],
            "action": play["action"],
            "owner": play["owner"],
            "confidence": play["confidence"],
            "expected_impact": play["expected_impact"],
            "monitoring_plan": play["monitoring_plan"],
            "evidence_confidence": confident_causes[diagnosis]["evidence_confidence"],
            "status": "validated_playbook_action",
        }
        out.append(item)
    return out
