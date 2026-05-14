from __future__ import annotations

from urllib.parse import urlparse

from app.schemas.common import SearchSource, VerificationSignals


def _domain_from_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    return (parsed.hostname or "").lower() or None


def verify_company(company: str | None, source_results: dict | None) -> tuple[VerificationSignals, list[SearchSource]]:
    if not company or not source_results:
        return VerificationSignals(company_website_found=None, official_domain_match=None, company_footprint="unknown", duplicate_post_risk="unknown", search_results_checked=0, suspicious_source_notes=["Search verification was skipped or unavailable." ]), []

    results = source_results.get("results") or []
    sources: list[SearchSource] = []
    company_tokens = [token for token in company.lower().split() if len(token) > 2]
    official_website_found = False
    official_domain_match = False
    review_mentions = 0
    linkedin_mentions = 0
    website_mentions = 0
    suspicious_notes: list[str] = []

    for item in results:
        title = item.get("title") or ""
        url = item.get("url")
        snippet = item.get("snippet")
        source_type = item.get("source_type")
        sources.append(SearchSource(title=title, url=url, snippet=snippet, source_type=source_type))
        domain = _domain_from_url(url)
        if domain and any(token in domain for token in company_tokens):
            official_domain_match = True
        if domain and domain not in {"linkedin.com", "www.linkedin.com"} and any(token in title.lower() for token in ["official", "about", "careers", "company"]):
            official_website_found = True
        if "linkedin" in (url or "").lower() or "linkedin" in title.lower():
            linkedin_mentions += 1
        if any(term in (title + " " + (snippet or "")).lower() for term in ["review", "glassdoor", "ambitionbox", "reddit"]):
            review_mentions += 1
        if any(term in (title + " " + (snippet or "")).lower() for term in ["website", "official", "careers", "apply"]):
            website_mentions += 1

    footprint_score = len(results)
    if official_website_found and website_mentions >= 2:
        company_footprint = "strong"
    elif footprint_score >= 3 or linkedin_mentions >= 1:
        company_footprint = "medium"
    else:
        company_footprint = "weak"

    duplicate_post_risk = "high" if review_mentions >= 2 else "medium" if review_mentions == 1 else "low"
    if not official_website_found:
        suspicious_notes.append("No clear official website result was found in the search set.")
    if official_domain_match is False:
        suspicious_notes.append("The result domains did not strongly match the company name.")

    signals = VerificationSignals(
        company_website_found=official_website_found,
        official_domain_match=official_domain_match,
        company_footprint=company_footprint,
        duplicate_post_risk=duplicate_post_risk,
        search_results_checked=len(results),
        suspicious_source_notes=suspicious_notes,
    )
    return signals, sources
