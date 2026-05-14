from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import Settings


@dataclass
class SearchOutcome:
    status: str
    results: list[dict]
    notes: list[str]


class SearchService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def search_company(self, company: str, title: str | None = None, deep_scan: bool = False) -> SearchOutcome:
        if not self.settings.enable_web_search:
            return SearchOutcome(status="skipped", results=[], notes=["Web search is disabled."])
        if self.settings.search_provider.lower() != "tavily" or not self.settings.tavily_api_key:
            return SearchOutcome(status="skipped", results=[], notes=["Search provider is unavailable."])

        queries = [
            f"{company} official website",
            f"{company} internship",
            f"{company} LinkedIn",
            f"{company} reviews",
        ]
        if title:
            queries.append(title)
        if deep_scan:
            queries.extend(
                [
                    f"{company} careers page",
                    f"{company} hiring team",
                    f"{company} recruiter",
                    f"{company} company profile",
                ]
            )

        all_results: list[dict] = []
        notes: list[str] = []
        headers = {"Authorization": f"Bearer {self.settings.tavily_api_key}", "Content-Type": "application/json"}

        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                for query in queries:
                    response = client.post(
                        "https://api.tavily.com/search",
                        headers=headers,
                        json={"query": query, "max_results": 8 if deep_scan else 5, "search_depth": "advanced", "include_answer": False},
                    )
                    response.raise_for_status()
                    payload = response.json()
                    for result in payload.get("results", []):
                        all_results.append(
                            {
                                "title": result.get("title") or query,
                                "url": result.get("url"),
                                "snippet": result.get("content") or result.get("snippet"),
                                "source_type": "search",
                            }
                        )
            return SearchOutcome(status="completed", results=all_results, notes=notes)
        except Exception as exc:
            notes.append(str(exc))
            return SearchOutcome(status="failed", results=[], notes=notes)
