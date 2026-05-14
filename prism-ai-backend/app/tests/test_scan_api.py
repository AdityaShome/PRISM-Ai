from __future__ import annotations


def _low_risk_payload() -> dict[str, str]:
    return {
        "text": (
            "Frontend Developer Internship at Nova Labs. Apply through the official website. "
            "Email hr@novalabs.com. Remote. ₹12k/month stipend. 2 months."
        ),
        "category": "internship",
    }


def _risk_payload() -> dict[str, str]:
    return {
        "text": (
            "Data Analyst Internship. Certificate only. Pay ₹999 registration fee. Guaranteed selection. "
            "Apply on WhatsApp."
        ),
        "category": "internship",
    }


def test_low_risk_internship_completes_without_human_review(client) -> None:
    response = client.post("/api/scans", json=_low_risk_payload())
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_status"] == "completed"
    assert payload["requires_human_review"] is False
    assert payload["trust_score"] >= 75
    assert payload["agent_trace"]


def test_whatsapp_only_internship_triggers_human_review(client) -> None:
    response = client.post(
        "/api/scans",
        json={
            "text": "Backend Developer Internship at Nova Labs. Apply on WhatsApp only. Remote. ₹12k/month stipend.",
            "category": "internship",
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["workflow_status"] == "awaiting_human_review"
    assert payload["requires_human_review"] is True
    assert any("whatsapp" in reason.lower() for reason in payload["human_review_reason"])
    assert payload["human_review"]["options"]


def test_application_fee_triggers_human_review_and_high_risk_scoring(client) -> None:
    response = client.post("/api/scans", json=_risk_payload())
    payload = response.json()
    assert response.status_code == 200
    assert payload["workflow_status"] == "awaiting_human_review"
    assert payload["requires_human_review"] is True
    assert payload["trust_score"] < 50
    assert any("fee" in reason.lower() or "payment" in reason.lower() for reason in payload["human_review_reason"])


def test_missing_company_name_triggers_human_review(client) -> None:
    response = client.post(
        "/api/scans",
        json={
            "text": "Frontend Developer Internship. Remote. ₹12k/month stipend. 2 months. Apply through the official website.",
            "category": "internship",
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["requires_human_review"] is True
    assert any("company" in reason.lower() for reason in payload["human_review_reason"])


def test_mark_suspicious_resume_completes_scan_with_suspicious_status(client) -> None:
    initial = client.post("/api/scans", json=_risk_payload()).json()
    scan_id = initial["scan_id"]
    resumed = client.post(
        f"/api/scans/{scan_id}/review",
        json={"decision": "mark_suspicious", "notes": "Fee request and guaranteed selection look unsafe."},
    )
    payload = resumed.json()
    assert resumed.status_code == 200
    assert payload["workflow_status"] == "completed"
    assert payload["requires_human_review"] is False
    assert payload["risk_level"] in {"High Risk", "High Caution"}
    assert "avoid" in payload["recommended_action"].lower()


def test_continue_anyway_resume_completes_with_caution(client) -> None:
    initial = client.post("/api/scans", json=_risk_payload()).json()
    scan_id = initial["scan_id"]
    resumed = client.post(
        f"/api/scans/{scan_id}/review",
        json={"decision": "continue_anyway", "notes": "I want to verify manually."},
    )
    payload = resumed.json()
    assert resumed.status_code == 200
    assert payload["workflow_status"] == "completed"
    assert payload["requires_human_review"] is False
    assert "verify through official company channels" in payload["recommended_action"].lower()


def test_run_deeper_scan_updates_trace(client) -> None:
    initial = client.post("/api/scans", json=_risk_payload()).json()
    scan_id = initial["scan_id"]
    resumed = client.post(
        f"/api/scans/{scan_id}/review",
        json={"decision": "run_deeper_scan", "notes": "Search more sources."},
    )
    payload = resumed.json()
    assert resumed.status_code == 200
    assert any(step["step"] == "deeper_scan" for step in payload["agent_trace"])
    assert payload["workflow_status"] in {"completed", "awaiting_human_review"}


def test_llm_failure_does_not_break_workflow(client, prism_agent, monkeypatch) -> None:
    def raise_llm(*args, **kwargs):
        raise RuntimeError("LLM provider failed")

    monkeypatch.setattr(prism_agent.llm_service, "analyze", raise_llm)
    response = client.post("/api/scans", json=_low_risk_payload())
    payload = response.json()
    assert response.status_code == 200
    assert payload["workflow_status"] in {"completed", "awaiting_human_review"}
    assert payload["trust_score"] is not None


def test_search_failure_does_not_break_workflow(client, prism_agent, monkeypatch) -> None:
    monkeypatch.setattr(
        prism_agent.search_service,
        "search_company",
        lambda company, title=None, deep_scan=False: type(
            "SearchOutcomeStub",
            (),
            {"status": "failed", "results": [], "notes": ["search failed"]},
        )(),
    )
    response = client.post("/api/scans", json=_low_risk_payload())
    payload = response.json()
    assert response.status_code == 200
    assert payload["workflow_status"] in {"completed", "awaiting_human_review"}
    assert payload["trust_score"] is not None


def test_agent_trace_contains_all_major_steps(client) -> None:
    response = client.post("/api/scans", json=_low_risk_payload())
    payload = response.json()
    trace_steps = {step["step"] for step in payload["agent_trace"]}
    assert {"receive_input", "fetch_url_content", "extract_details", "run_rule_checks", "run_web_verification", "run_llm_analysis", "calculate_score", "risk_gate", "generate_recommendation", "save_result"}.issubset(trace_steps)


def test_paused_workflow_can_be_resumed(client) -> None:
    initial = client.post("/api/scans", json=_risk_payload()).json()
    assert initial["workflow_status"] == "awaiting_human_review"
    resumed = client.post(
        f"/api/scans/{initial['scan_id']}/review",
        json={"decision": "reject_opportunity", "notes": "This is unsafe."},
    )
    payload = resumed.json()
    assert resumed.status_code == 200
    assert payload["human_decision"] == "reject_opportunity"
    assert payload["workflow_status"] in {"completed", "rejected"}
