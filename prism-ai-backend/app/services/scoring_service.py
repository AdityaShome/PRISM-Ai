from __future__ import annotations

from typing import Any

from app.schemas.common import ConfidenceLevel, RiskLevel


def _clamp_score(value: int) -> int:
    return max(0, min(100, value))


def _signal_value(signals, key: str, default=None):
    if signals is None:
        return default
    if isinstance(signals, dict):
        return signals.get(key, default)
    return getattr(signals, key, default)


def calculate_trust_score(
    extracted_details: dict[str, Any],
    rule_result,
    verification_signals: dict[str, Any] | None = None,
    llm_result: dict[str, Any] | None = None,
) -> int:
    score = 70

    if verification_signals:
        if _signal_value(verification_signals, "company_website_found") is True:
            score += 10
        if _signal_value(verification_signals, "official_domain_match") is True:
            score += 8
        if _signal_value(verification_signals, "company_footprint") == "strong":
            score += 5
        elif _signal_value(verification_signals, "company_footprint") == "medium":
            score += 3
        if _signal_value(verification_signals, "duplicate_post_risk") == "low":
            score += 4

    if extracted_details.get("stipend"):
        score += 8
    if extracted_details.get("duration"):
        score += 6
    if extracted_details.get("application_fee") is False:
        score += 5
    if extracted_details.get("company"):
        score += 5
    if extracted_details.get("skills"):
        score += 4

    if not extracted_details.get("company"):
        score -= 18
    if not extracted_details.get("stipend"):
        score -= 8
    if not extracted_details.get("duration"):
        score -= 5
    if not extracted_details.get("application_channel"):
        score -= 5

    if rule_result.fee_payment_risk_signals.get("application_fee_mentioned") or rule_result.fee_payment_risk_signals.get("payment_language_detected"):
        score -= 50
    if rule_result.red_flags:
        for flag in rule_result.red_flags:
            label = flag.get("label", "").lower()
            severity = str(flag.get("severity", "")).lower()
            if "personal" in label or "financial" in label:
                score -= 25
            elif "guaranteed" in label:
                score -= 20
            elif "whatsapp" in label or "telegram" in label:
                score -= 20
            elif "missing company" in label:
                score -= 18
            elif "official website" in label:
                score -= 15
            elif "role" in label and severity == "medium":
                score -= 12
            elif "copy" in label:
                score -= 12
            elif "unrealistic" in label:
                score -= 10
            elif "stipend" in label:
                score -= 8
            elif "contact" in label:
                score -= 8
            elif "duration" in label:
                score -= 5

    if llm_result and llm_result.get("confidence") == "High":
        score += 2

    return _clamp_score(score)


def determine_risk_level(trust_score: int, evidence_strength: str = "medium") -> str:
    if evidence_strength == "low":
        return RiskLevel.needs_manual_verification.value
    if trust_score >= 80:
        return RiskLevel.low_risk.value
    if trust_score >= 60:
        return RiskLevel.medium_risk.value
    if trust_score >= 40:
        return RiskLevel.high_caution.value
    return RiskLevel.high_risk.value


def determine_confidence(extracted_details: dict[str, Any], verification_signals: dict[str, Any] | None, llm_available: bool, text_length: int) -> ConfidenceLevel:
    evidence_count = sum(1 for key in ["company", "stipend", "duration", "application_channel", "contact_method"] if extracted_details.get(key))
    verification_count = int(_signal_value(verification_signals, "search_results_checked", 0) or 0)

    if evidence_count >= 4 and verification_count >= 3 and text_length >= 100:
        return ConfidenceLevel.high
    if evidence_count >= 2 and text_length >= 60:
        return ConfidenceLevel.medium
    if llm_available and text_length >= 80:
        return ConfidenceLevel.medium
    return ConfidenceLevel.low


def scam_likelihood_from_score(trust_score: int) -> int:
    return _clamp_score(100 - trust_score)
