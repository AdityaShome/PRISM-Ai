from __future__ import annotations

import re
from collections import Counter
from typing import Any

from app.schemas.common import ExtractedDetails

STIPEND_PATTERNS = [
    r"₹\s?\d+(?:[.,]\d+)?(?:\s?(?:k|K))?(?:/\s?(?:month|mo|week|wk))?",
    r"\$\s?\d+(?:[.,]\d+)?(?:\s?(?:k|K))?(?:/\s?(?:month|mo|week|wk))?",
    r"\b(?:stipend|salary|pay|compensation)\b[^\n]{0,80}",
    r"certificate\s*only",
    r"unpaid",
]

SKILL_KEYWORDS = [
    "react",
    "typescript",
    "javascript",
    "python",
    "ml",
    "machine learning",
    "node.js",
    "nodejs",
    "api",
    "postgresql",
    "sql",
    "figma",
    "excel",
    "seo",
    "content",
    "research",
    "dashboard",
    "ui",
    "ux",
]

SUSPICIOUS_PATTERNS = [
    r"application fee",
    r"training fee",
    r"security deposit",
    r"pay to get internship",
    r"guaranteed selection",
    r"guaranteed certificate",
    r"no interview required",
    r"limited seats",
    r"100% placement guaranteed",
    r"certificate[-\s]?only",
    r"whatsapp[-\s]?only",
    r"telegram[-\s]?only",
]

CONTACT_PATTERNS = {
    "WhatsApp": r"whatsapp|wa\.me|chat on whatsapp",
    "Telegram": r"telegram|t\.me",
    "Email": r"mailto:|email us|send.*email|gmail\.com|yahoo\.com|outlook\.com",
    "Official Website": r"apply on (?:our )?website|official website|career page|apply here",
}


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"\s+", " ", text.replace("\u200b", " ")).strip()
    return cleaned


def find_first(patterns: list[str], text: str, flags: int = re.IGNORECASE) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(0).strip()
    return None


def extract_company(text: str) -> str | None:
    company_patterns = [
        r"(?:at|for|from)\s+([A-Z][A-Za-z0-9&.,'\- ]{2,60})",
        r"company[:\-]\s*([A-Z][A-Za-z0-9&.,'\- ]{2,60})",
        r"(?:company|startup|organization)[:\-]\s*([A-Z][A-Za-z0-9&.,'\- ]{2,60})",
    ]
    for pattern in company_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip().rstrip(".,")
            candidate = re.sub(r"\b(?:remote|hybrid|on[- ]site|stipend|salary|apply|internship)\b.*", "", candidate, flags=re.IGNORECASE).strip()
            if candidate:
                return candidate
    return None


def extract_title(text: str) -> str | None:
    title_patterns = [
        r"([A-Z][A-Za-z0-9+/&\- ]{3,80}Internship)",
        r"([A-Z][A-Za-z0-9+/&\- ]{3,80}Intern)",
        r"([A-Z][A-Za-z0-9+/&\- ]{3,80}Role)",
    ]
    for pattern in title_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    if "internship" in text.lower():
        first_clause = re.split(r"[.\n|]", text)[0]
        if len(first_clause) <= 120:
            return first_clause.strip()
    return None


def extract_skills(text: str) -> list[str]:
    lower_text = text.lower()
    found = []
    for skill in SKILL_KEYWORDS:
        if skill in lower_text:
            normalized = "Node.js" if skill in {"node.js", "nodejs"} else skill.replace("ml", "ML") if skill == "ml" else skill.title() if skill not in {"ui", "ux", "sql"} else skill.upper()
            if normalized not in found:
                found.append(normalized)
    return found


def detect_contact_method(text: str) -> str | None:
    for label, pattern in CONTACT_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return None


def extract_recruiter_email(text: str) -> str | None:
    match = re.search(r"[A-Za-z0-9._%+-]+@(?!example\.com)[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    if match:
        return match.group(0)
    return None


def extract_internship_details(text: str, llm_details: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = normalize_text(text)
    lower = normalized.lower()
    suspicious_phrases = []
    for pattern in SUSPICIOUS_PATTERNS:
        match = re.search(pattern, lower, re.IGNORECASE)
        if match:
            suspicious_phrases.append(match.group(0))

    company = extract_company(normalized)
    title = extract_title(normalized)
    stipend = find_first(STIPEND_PATTERNS, normalized)
    duration_match = re.search(r"\b\d+\s*(?:months?|weeks?|days?)\b", lower, re.IGNORECASE)
    mode_match = re.search(r"\b(remote|hybrid|on[- ]site)\b", lower, re.IGNORECASE)
    location_match = re.search(r"location[:\-]\s*([A-Za-z0-9, ]{2,40})", normalized, re.IGNORECASE)
    deadline_match = re.search(r"(?:deadline|apply by|last date)[:\-]?\s*([A-Za-z0-9,./ -]{4,40})", normalized, re.IGNORECASE)

    application_fee = any(re.search(pattern, lower, re.IGNORECASE) for pattern in [r"application fee", r"registration fee", r"training fee", r"security deposit", r"pay to get internship", r"pay.*fee", r"limited seats.*pay now"])
    contact_method = detect_contact_method(normalized)
    recruiter_email = extract_recruiter_email(normalized)
    application_channel = "Official Website" if re.search(r"apply here|career page|official website|website", lower) else contact_method or ("Email" if recruiter_email else None)

    extracted = ExtractedDetails(
        title=title,
        company=company,
        role_type=llm_details.get("role_type") if llm_details else None,
        stipend=stipend,
        mode=mode_match.group(1).title() if mode_match else None,
        duration=duration_match.group(0) if duration_match else None,
        location=location_match.group(1).strip() if location_match else None,
        skills=extract_skills(normalized),
        contact_method=contact_method,
        application_channel=application_channel,
        application_fee=application_fee,
        deadline=deadline_match.group(1).strip() if deadline_match else None,
        suspicious_phrases=suspicious_phrases,
        recruiter_email=recruiter_email,
    )

    if llm_details:
        for key in ["title", "company", "role_type", "stipend", "mode", "duration", "location", "contact_method", "application_channel", "deadline", "recruiter_email"]:
            value = llm_details.get(key)
            if value and not getattr(extracted, key):
                setattr(extracted, key, value)
        if llm_details.get("skills"):
            merged_skills = list(dict.fromkeys(extracted.skills + [str(skill) for skill in llm_details["skills"]]))
            extracted.skills = merged_skills
        if llm_details.get("application_fee") is not None:
            extracted.application_fee = bool(llm_details["application_fee"])
        if llm_details.get("suspicious_phrases"):
            extracted.suspicious_phrases = list(dict.fromkeys(extracted.suspicious_phrases + [str(item) for item in llm_details["suspicious_phrases"]]))

    return extracted.model_dump()


def detect_copy_paste_signals(text: str) -> dict[str, Any]:
    normalized = normalize_text(text)
    sentences = [sentence.strip().lower() for sentence in re.split(r"[.\n]+", normalized) if sentence.strip()]
    duplicate_sentences = [sentence for sentence, count in Counter(sentences).items() if count > 1]
    repeated_template_phrases = [phrase for phrase in ["limited seats", "100% placement guaranteed", "pay now", "certificate only"] if phrase in normalized.lower()]
    return {
        "duplicate_sentence_count": len(duplicate_sentences),
        "repeated_template_phrases": repeated_template_phrases,
        "duplicate_post_risk": "high" if len(duplicate_sentences) >= 2 or len(repeated_template_phrases) >= 2 else "medium" if duplicate_sentences or repeated_template_phrases else "low",
    }
