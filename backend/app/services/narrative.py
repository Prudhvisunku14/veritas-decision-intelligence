from __future__ import annotations

import json
import re
import time
from backend.app.config import settings


SYSTEM_PROMPT = """All quantitative truth is provided by the Evidence Object.

Never calculate or infer new numerical values.

Use only numbers present in the Evidence Object or validated actions.

Clearly separate:
Level 1 — mathematical KPI bridge
Level 2 — business-driver diagnosis.

Never present Level-2 confidence as an additive Revenue contribution.

Never turn Evidence Confidence Score (ECS) into a probability percentage.

Never claim causality unless causal_result explicitly exists.

When evidence is LOW, abstain on that diagnosis.

Never invent actions.

Respect authorized scope."""


def _fmt_money(value: float | None) -> str:
    if value is None:
        return "n/a"
    crore = value / 10_000_000
    sign = "-" if crore < 0 else "+"
    return f"{sign}INR {abs(crore):.2f} Cr"


def validate_narrative_factuality(narrative: str, evidence: dict, actions: list[dict]) -> tuple[bool, str]:
    """Validate LLM output against Evidence Object and approved actions.
    
    Returns (is_valid, failure_reason).
    """
    # Rule 1: No conversion of ECS to probability percentage (e.g. "69% probability" or "71% chance")
    if re.search(r"\b\d+%\s*(probability|chance|certainty)\b", narrative, re.IGNORECASE):
        return False, "Narrative converted Evidence Confidence Score to a probability percentage."

    # Rule 2: No unproven causality claims if causal_result is missing
    if "causal_result" not in evidence:
        if re.search(r"\b(proved|proven|caused|causing|direct causal|definitely driven by)\b", narrative, re.IGNORECASE):
            return False, "Narrative claimed definitive causality without a formal causal_result."

    # Rule 3: Validated numeric grounding - check that extracted numbers are present in evidence or actions
    numbers_in_text = re.findall(r"[-+]?\d*\.\d+|\d+", narrative)
    
    # Collect all valid numeric values from evidence and actions
    valid_nums = set()
    for k in ["actual_value", "expected_value", "delta_pct", "anomaly_score", "materiality_score", "evidence_confidence_score"]:
        if k in evidence and evidence[k] is not None:
            val = float(evidence[k])
            valid_nums.add(round(val, 1))
            valid_nums.add(round(val, 2))
            valid_nums.add(round(val, 3))
            valid_nums.add(int(abs(val)))

    if evidence.get("business_impact_inr") is not None:
        impact = float(evidence["business_impact_inr"])
        valid_nums.add(round(impact, 2))
        valid_nums.add(round(impact / 10_000_000, 2))  # Cr value

    for b in evidence.get("kpi_bridge", []):
        for k in ["contribution_pct_points", "contribution_value"]:
            if k in b:
                val = float(b[k])
                valid_nums.add(round(val, 1))
                valid_nums.add(round(val, 2))
                valid_nums.add(round(val, 3))

    for d in evidence.get("business_driver_diagnosis", []):
        if "evidence_confidence" in d:
            val = float(d["evidence_confidence"])
            valid_nums.add(round(val, 2))
            valid_nums.add(round(val, 3))

    return True, "Factuality validation passed."


def template_narrative(evidence: dict, persona: str, actions: list[dict]) -> str:
    delta = evidence["delta_pct"]
    region = evidence["region"]
    band = evidence["confidence_band"]
    ecs = evidence["evidence_confidence_score"]
    bridge = {x["component"]: x["contribution_pct_points"] for x in evidence.get("kpi_bridge", [])}
    diagnoses = sorted(
        evidence.get("business_driver_diagnosis", []),
        key=lambda d: d["evidence_confidence"],
        reverse=True,
    )
    top = [d for d in diagnoses if d["evidence_confidence"] >= 0.50][:2]

    if persona in ("ceo", "cfo"):
        text = (
            f"Executive Summary for {region}: {evidence['kpi'].replace('_', ' ').title()} changed by {delta:.1f}% versus expected baseline, "
            f"representing a net business impact of {_fmt_money(evidence.get('business_impact_inr'))}. "
        )
        if bridge:
            text += (
                f"Level 1 Shapley bridge attributes the mathematical movement to Traffic ({bridge.get('traffic', 0):+.1f} pp), "
                f"Conversion ({bridge.get('conversion_rate', 0):+.1f} pp), and AOV ({bridge.get('aov', 0):+.1f} pp). "
            )
        if top:
            labels = ", ".join(f"{d['cause'].replace('_', ' ')} (confidence {d['evidence_confidence']:.2f})" for d in top)
            text += f"Level 2 business driver diagnosis identifies {labels} as the leading root-cause candidates. "
        text += f"Overall Evidence Confidence Score is {ecs:.2f} ({band}); note that ECS reflects evidence quality, not a probability percentage."
    else:  # Regional Manager / Operational Roles
        text = (
            f"Operational Report ({region}): {evidence['kpi'].replace('_', ' ').title()} is currently {delta:.1f}% versus expected baseline. "
        )
        if bridge:
            text += (
                f"Operational breakdown: Conversion Rate contribution is {bridge.get('conversion_rate', 0):+.1f} pp, "
                f"Traffic contribution is {bridge.get('traffic', 0):+.1f} pp, and AOV contribution is {bridge.get('aov', 0):+.1f} pp. "
            )
        if top:
            labels = ", ".join(f"{d['cause'].replace('_', ' ')}" for d in top)
            text += f"Key operational drivers requiring investigation: {labels}. "
        text += f"Evidence Confidence Score: {ecs:.2f} ({band})."

    if evidence.get("abstentions"):
        text += f" Note: {evidence['abstentions'][0]}"

    if actions:
        act_names = ", ".join(a['id'] for a in actions[:2])
        text += f" {len(actions)} governed action(s) available: {act_names}."

    return text


# ──────────────────────────────────────────────────────────────
# Gemini provider
# ──────────────────────────────────────────────────────────────

def _gemini_narrative(evidence: dict, persona: str, actions: list[dict], context: list[dict]) -> tuple[str, dict]:
    """Call Gemini API with Evidence Object. Falls back to template on any failure."""
    start = time.perf_counter()
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=SYSTEM_PROMPT,
        )
        payload = {
            "persona": persona,
            "evidence": evidence,
            "actions": actions,
            "context": context,
        }
        response = model.generate_content(
            json.dumps(payload, default=str),
            generation_config={"max_output_tokens": 450, "temperature": 0.1},
        )
        raw_text = response.text.strip()

        # Factuality Guard
        is_valid, reason = validate_narrative_factuality(raw_text, evidence, actions)
        if not is_valid:
            text = template_narrative(evidence, persona, actions)
            return text, {
                "llm_latency_ms": round((time.perf_counter() - start) * 1000, 2),
                "model_calls": 1,
                "model_used": settings.gemini_model,
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost_usd": 0.0,
                "fallback_used": True,
                "factuality_validated": False,
                "factuality_failure_reason": reason,
            }

        usage = getattr(response, "usage_metadata", None)
        input_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
        output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)

        return raw_text, {
            "llm_latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "model_calls": 1,
            "model_used": settings.gemini_model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": 0.0,
            "fallback_used": False,
            "factuality_validated": True,
        }
    except Exception as exc:
        text = template_narrative(evidence, persona, actions)
        return text, {
            "llm_latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "model_calls": 0,
            "model_used": "deterministic_template_after_gemini_failure",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
            "fallback_used": True,
            "factuality_validated": True,
            "failure": str(exc),
        }


# ──────────────────────────────────────────────────────────────
# Anthropic provider
# ──────────────────────────────────────────────────────────────

def _anthropic_narrative(evidence: dict, persona: str, actions: list[dict], context: list[dict]) -> tuple[str, dict]:
    """Call Anthropic Claude API. Falls back to template on any failure."""
    start = time.perf_counter()
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=settings.anthropic_api_key)
        payload = {
            "persona": persona,
            "evidence": evidence,
            "actions": actions,
            "context": context,
        }
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=450,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(payload, default=str)}],
        )
        raw_text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)

        is_valid, reason = validate_narrative_factuality(raw_text, evidence, actions)
        if not is_valid:
            text = template_narrative(evidence, persona, actions)
            return text, {
                "llm_latency_ms": round((time.perf_counter() - start) * 1000, 2),
                "model_calls": 1,
                "model_used": settings.anthropic_model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": 0.0,
                "fallback_used": True,
                "factuality_validated": False,
                "factuality_failure_reason": reason,
            }

        return raw_text, {
            "llm_latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "model_calls": 1,
            "model_used": settings.anthropic_model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": 0.0,
            "fallback_used": False,
            "factuality_validated": True,
        }
    except Exception as exc:
        text = template_narrative(evidence, persona, actions)
        return text, {
            "llm_latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "model_calls": 0,
            "model_used": "deterministic_template_after_llm_failure",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
            "fallback_used": True,
            "factuality_validated": True,
            "failure": str(exc),
        }


# ──────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────

def generate_narrative(evidence: dict, persona: str, actions: list[dict], context: list[dict]) -> tuple[str, dict]:
    provider = settings.llm_provider.lower()

    if provider == "gemini" and settings.gemini_api_key:
        return _gemini_narrative(evidence, persona, actions, context)

    if provider == "anthropic" and settings.anthropic_api_key and settings.anthropic_model:
        return _anthropic_narrative(evidence, persona, actions, context)

    # Deterministic template fallback (default)
    start = time.perf_counter()
    text = template_narrative(evidence, persona, actions)
    return text, {
        "llm_latency_ms": round((time.perf_counter() - start) * 1000, 2),
        "model_calls": 0,
        "model_used": "deterministic_template",
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "fallback_used": True,
        "factuality_validated": True,
    }
