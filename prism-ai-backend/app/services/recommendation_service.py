from __future__ import annotations

from typing import Any


def build_recommendation(
    extracted_details: dict[str, Any],
    trust_score: int,
    risk_level: str,
    green_flags: list[dict[str, Any]],
    red_flags: list[dict[str, Any]],
    verification_signals: dict[str, Any] | None = None,
) -> tuple[str, str, str]:
    company = extracted_details.get("company") or "this internship"
    title = extracted_details.get("title") or "the role"

    if trust_score >= 80:
        action = "Apply through the official company website or verified recruiter email. Keep payment and personal document sharing off until you confirm selection steps."
    elif trust_score >= 60:
        action = "Request the official application link, recruiter email, and stipend confirmation before sharing documents."
    elif trust_score >= 40:
        action = "Do not apply yet. Verify the company name, recruiter identity, and payment terms through official sources first."
    else:
        action = "High-risk pattern detected. Avoid applying until you can verify the company and remove any payment or private-channel request."

    safe_message = (
        f"Hi, I’m interested in the {title} at {company}. Could you please confirm the official application process, stipend, expected responsibilities, and whether any fee is required?"
    )

    if risk_level == "Needs Manual Verification":
        summary = "Evidence is incomplete. Prism recommends manual verification before you proceed."
    elif trust_score >= 80:
        summary = "This internship looks mostly genuine, but apply only through official channels and verify the recruiter before sharing documents."
    elif trust_score >= 60:
        summary = "Some strong signals are present, but a few details still need verification before you apply."
    elif trust_score >= 40:
        summary = "Several caution signals were detected. Treat this listing carefully and verify independently."
    else:
        summary = "This listing has strong scam-risk indicators and should not be treated as reliable without further verification."

    if red_flags and not green_flags:
        summary = "The post lacks enough positive evidence to offset the risk signals, so manual verification is recommended."

    return action, safe_message, summary
