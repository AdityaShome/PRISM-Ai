from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.schemas.common import FlagItem, Severity

HIGH_RISK_PATTERNS = {
    "application_fee": [r"application fee", r"registration fee", r"training fee", r"security deposit", r"pay to get internship", r"pay.*fee", r"limited seats.*pay now"],
    "guaranteed_selection": [r"guaranteed selection", r"100% placement guaranteed", r"no interview required"],
    "contact_risk": [r"whatsapp[-\s]?only", r"telegram[-\s]?only", r"send resume on whatsapp", r"message only on whatsapp"],
    "personal_docs": [r"aadhaar", r"pan", r"bank details", r"upi", r"card details"],
    "fake_certificate": [r"certificate[-\s]?only", r"guaranteed certificate"],
}

MEDIUM_RISK_PATTERNS = {
    "vague_role": [r"responsibilities?:?\s*$", r"work from home internship", r"join our growing team"],
    "buzzwords": [r"dynamic opportunity", r"mass hiring", r"limited time opportunity"],
    "grammar": [r"apply now\s+kindly", r"urgent hiring", r"work hard grow faster"],
}

GREEN_PATTERNS = {
    "clear_stipend": [r"₹", r"stipend", r"salary", r"paid internship"],
    "clear_duration": [r"\b\d+\s*(months?|weeks?|days?)\b"],
    "official_link": [r"official website", r"career page", r"apply here"],
    "no_fee": [r"no fee", r"no application fee", r"free application"],
}


@dataclass
class RuleEngineResult:
    green_flags: list[dict[str, Any]] = field(default_factory=list)
    red_flags: list[dict[str, Any]] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    duplicate_copy_paste_signals: dict[str, Any] = field(default_factory=dict)
    fee_payment_risk_signals: dict[str, Any] = field(default_factory=dict)
    unrealistic_claim_signals: dict[str, Any] = field(default_factory=dict)
    recruiter_contact_risk_signals: dict[str, Any] = field(default_factory=dict)


def _matches(patterns: list[str], text: str) -> list[str]:
    matches: list[str] = []
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            matches.append(pattern)
    return matches


def _has(text: str, pattern: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE) is not None


def evaluate_rules(text: str, extracted: dict[str, Any], verification_signals: dict[str, Any] | None = None) -> RuleEngineResult:
    combined_text = text or ""
    company = extracted.get("company")
    stipend = extracted.get("stipend")
    duration = extracted.get("duration")
    mode = extracted.get("mode")
    contact_method = extracted.get("contact_method")
    application_channel = extracted.get("application_channel")
    application_fee = bool(extracted.get("application_fee"))
    skills = extracted.get("skills") or []
    suspicious_phrases = extracted.get("suspicious_phrases") or []

    result = RuleEngineResult()

    for label, patterns in GREEN_PATTERNS.items():
        matched = _matches(patterns, combined_text)
        if matched:
            evidence = {
                "clear_stipend": "Clear stipend mentioned in the post.",
                "clear_duration": "Duration is stated clearly.",
                "official_link": "The post references an official application path.",
                "no_fee": "No application fee language found.",
            }.get(label, "Positive signal detected.")
            result.green_flags.append({"label": evidence, "evidence": matched[0]})

    if company:
        result.green_flags.append({"label": "Company name provided", "evidence": f"The post mentions {company}."})
    else:
        result.red_flags.append({"label": "Missing company name", "severity": Severity.high, "evidence": "No company name was found in the provided text."})
        result.missing_information.append("Company name")

    if stipend:
        result.green_flags.append({"label": "Clear stipend mentioned", "evidence": f"{stipend} was provided."})
    else:
        result.missing_information.append("Stipend details")

    if duration:
        result.green_flags.append({"label": "Clear duration mentioned", "evidence": f"{duration} was provided."})
    else:
        result.missing_information.append("Duration")

    if application_fee or _matches(HIGH_RISK_PATTERNS["application_fee"], combined_text) or re.search(r"\bapply\s+fee\b", combined_text, re.IGNORECASE):
        result.red_flags.append({
            "label": "Payment-related request detected",
            "severity": Severity.high,
            "evidence": "The post contains application fee, training fee, or pay-to-apply language.",
        })
    else:
        result.green_flags.append({"label": "No application fee request", "evidence": "No fee or deposit request was found."})

    if _matches(HIGH_RISK_PATTERNS["guaranteed_selection"], combined_text):
        result.red_flags.append({
            "label": "Guaranteed selection language",
            "severity": Severity.high,
            "evidence": "The post makes a guaranteed selection or placement claim.",
        })

    if _matches(HIGH_RISK_PATTERNS["contact_risk"], combined_text):
        result.red_flags.append({
            "label": "WhatsApp-only or Telegram-only application",
            "severity": Severity.medium,
            "evidence": "The application path relies on a private chat channel.",
        })
        result.recruiter_contact_risk_signals["private_channel_only"] = True
    elif contact_method:
        result.recruiter_contact_risk_signals["private_channel_only"] = False

    if _matches(HIGH_RISK_PATTERNS["personal_docs"], combined_text):
        result.red_flags.append({
            "label": "Early request for sensitive personal documents",
            "severity": Severity.high,
            "evidence": "The post asks for Aadhaar, PAN, bank details, or similar sensitive data too early.",
        })

    if _matches(HIGH_RISK_PATTERNS["fake_certificate"], combined_text):
        result.red_flags.append({
            "label": "Certificate-selling language",
            "severity": Severity.medium,
            "evidence": "The post uses certificate-only or guaranteed certificate language.",
        })

    if not mode:
        result.red_flags.append({
            "label": "Unclear work mode",
            "severity": Severity.medium,
            "evidence": "The post does not clearly state whether the role is remote, hybrid, or on-site.",
        })
        result.missing_information.append("Work mode")

    if not extracted.get("contact_method"):
        result.red_flags.append({
            "label": "Unclear recruiter contact method",
            "severity": Severity.medium,
            "evidence": "No recruiter contact method or application channel was clearly identified.",
        })
        result.missing_information.append("Recruiter contact method")

    if not extracted.get("recruiter_email"):
        result.missing_information.append("Recruiter email")

    if not extracted.get("application_channel"):
        result.missing_information.append("Official application link")

    if not skills:
        result.missing_information.append("Skills required")

    if not suspicious_phrases:
        result.green_flags.append({"label": "No explicit scam keywords", "evidence": "No direct fee or scam wording was detected."})

    if stipend and re.search(r"certificate only|unpaid", stipend, re.IGNORECASE):
        result.red_flags.append({
            "label": "Certificate-only or unpaid role",
            "severity": Severity.medium,
            "evidence": f"Stipend field indicates: {stipend}.",
        })

    if re.search(r"unrealistic|too good to be true|lakh|1\s?lakh|2\s?lakh", combined_text, re.IGNORECASE):
        result.unrealistic_claim_signals["unrealistic_claim_detected"] = True
        result.red_flags.append({
            "label": "Potentially unrealistic claim",
            "severity": Severity.medium,
            "evidence": "The post contains language that may overstate compensation or outcomes.",
        })
    else:
        result.unrealistic_claim_signals["unrealistic_claim_detected"] = False

    copy_paste = _has(combined_text, r"limited seats|apply fast|urgent hiring")
    result.duplicate_copy_paste_signals = {
        "copy_paste_risk": "medium" if copy_paste else "low",
        "repeated_template_language": copy_paste,
        "notes": "Template-like language detected." if copy_paste else "No strong copy-paste pattern detected.",
    }

    result.fee_payment_risk_signals = {
        "application_fee_mentioned": application_fee or bool(_matches(HIGH_RISK_PATTERNS["application_fee"], combined_text)) or bool(re.search(r"\bapply\s+fee\b", combined_text, re.IGNORECASE)),
        "payment_language_detected": bool(_matches(HIGH_RISK_PATTERNS["application_fee"], combined_text)) or bool(re.search(r"\bapply\s+fee\b", combined_text, re.IGNORECASE)),
        "notes": "Fee or payment request was detected." if (application_fee or bool(re.search(r"\bapply\s+fee\b", combined_text, re.IGNORECASE))) else "No fee request detected.",
    }

    result.recruiter_contact_risk_signals.update(
        {
            "contact_method": contact_method,
            "application_channel": application_channel,
            "gmail_only_risk": bool(re.search(r"@(gmail|yahoo|outlook)\.com", combined_text, re.IGNORECASE)),
        }
    )

    if verification_signals and verification_signals.get("company_footprint") == "weak":
        result.red_flags.append({
            "label": "Weak public company footprint",
            "severity": Severity.medium,
            "evidence": "Search verification found limited public company presence.",
        })

    return result
