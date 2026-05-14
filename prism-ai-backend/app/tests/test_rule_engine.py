from __future__ import annotations

from app.services.extraction_service import extract_internship_details
from app.services.rule_engine import evaluate_rules
from app.services.scoring_service import calculate_trust_score


def test_application_fee_reduces_score_heavily() -> None:
    text = "Frontend Developer Internship at Nova Labs. Apply fee ₹299. Remote. 2 months."
    extracted = extract_internship_details(text)
    rules = evaluate_rules(text, extracted)
    score = calculate_trust_score(extracted, rules)
    assert score <= 40
    assert rules.red_flags


def test_clear_stipend_increases_score() -> None:
    strong_text = "Frontend Developer Internship at Nova Labs. Remote. ₹12k/month stipend. 2 months. Official website application."
    weak_text = "Frontend Developer Internship. Remote. 2 months."
    strong_score = calculate_trust_score(extract_internship_details(strong_text), evaluate_rules(strong_text, extract_internship_details(strong_text)))
    weak_score = calculate_trust_score(extract_internship_details(weak_text), evaluate_rules(weak_text, extract_internship_details(weak_text)))
    assert strong_score > weak_score


def test_whatsapp_only_contact_adds_medium_red_flag() -> None:
    text = "Frontend Developer Internship at Nova Labs. Send resume on WhatsApp only. Remote. ₹12k/month."
    extracted = extract_internship_details(text)
    rules = evaluate_rules(text, extracted)
    labels = [flag["label"].lower() for flag in rules.red_flags]
    assert any("whatsapp" in label or "telegram" in label for label in labels)


def test_missing_company_name_reduces_score() -> None:
    missing_company = "Frontend Developer Internship. Remote. ₹12k/month. 2 months."
    with_company = "Frontend Developer Internship at Nova Labs. Remote. ₹12k/month. 2 months."
    missing_score = calculate_trust_score(extract_internship_details(missing_company), evaluate_rules(missing_company, extract_internship_details(missing_company)))
    with_company_score = calculate_trust_score(extract_internship_details(with_company), evaluate_rules(with_company, extract_internship_details(with_company)))
    assert with_company_score > missing_score


def test_score_is_always_between_zero_and_100() -> None:
    text = "Application fee. Training fee. Pay to get internship. WhatsApp only. Telegram only. Guaranteed selection. No interview required."
    extracted = extract_internship_details(text)
    rules = evaluate_rules(text, extracted)
    score = calculate_trust_score(extracted, rules)
    assert 0 <= score <= 100
