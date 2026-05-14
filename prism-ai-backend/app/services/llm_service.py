from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.schemas.common import ConfidenceLevel, FlagItem


class LLMAnalysisResult(BaseModel):
    extracted_details: dict[str, Any] = Field(default_factory=dict)
    green_flags: list[FlagItem] = Field(default_factory=list)
    red_flags: list[FlagItem] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    summary: str = ""
    recommended_action: str = ""
    safe_message: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.medium


@dataclass
class LLMOutcome:
    status: str
    result: LLMAnalysisResult | None = None
    raw_output: dict[str, Any] | None = None
    notes: list[str] | None = None


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def analyze(self, combined_text: str, extracted_details: dict[str, Any], search_summary: dict[str, Any] | None = None) -> LLMOutcome:
        if not self.settings.enable_llm_analysis:
            return LLMOutcome(status="skipped", notes=["LLM analysis disabled."])
        if self.settings.llm_provider.lower() != "gemini" or not self.settings.gemini_api_key:
            return LLMOutcome(status="skipped", notes=["LLM provider unavailable."])

        prompt = {
            "instruction": "Return only JSON. Do not invent facts. Separate evidence from assumptions. Mark uncertain details as unknown. Do not say confirmed scam unless fee/payment/fraud evidence is explicit.",
            "input_text": combined_text[:12000],
            "current_extraction": extracted_details,
            "search_summary": search_summary or {},
            "required_schema": {
                "extracted_details": {},
                "green_flags": [],
                "red_flags": [],
                "missing_information": [],
                "summary": "",
                "recommended_action": "",
                "safe_message": "",
                "confidence": "Low|Medium|High",
            },
        }

        payload = {
            "system_instruction": {
                "parts": [
                    {
                        "text": "You are Prism AI, an internship trust verification assistant. Analyze only the provided post and verification sources. Return cautious structured JSON. Do not claim something is definitely a scam unless explicit evidence exists.",
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": json.dumps(prompt)}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds * 2) as client:
                response = client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.gemini_model}:generateContent?key={self.settings.gemini_api_key}",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                response_payload = response.json()
                content = _extract_gemini_text(response_payload)
                raw = _extract_json_object(content)
                result = LLMAnalysisResult.model_validate(raw)
                return LLMOutcome(status="completed", result=result, raw_output=raw)
        except Exception as exc:
            return LLMOutcome(status="failed", notes=[str(exc)])


def _extract_gemini_text(response_payload: dict[str, Any]) -> str:
    candidates = response_payload.get("candidates") or []
    if candidates:
        content = candidates[0].get("content") or {}
        parts = content.get("parts") or []
        text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        if text:
            return text
    text = response_payload.get("text")
    if text:
        return str(text)
    raise ValueError("Gemini response did not contain text content")


def _extract_json_object(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
        candidate = re.sub(r"\s*```$", "", candidate)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise
