from __future__ import annotations

from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

try:
    import trafilatura
except Exception:  # pragma: no cover - optional dependency
    trafilatura = None

from app.core.config import Settings

PRIVATE_DOMAINS = ("linkedin.com", "facebook.com", "instagram.com", "x.com", "twitter.com")


def sanitize_text(text: str) -> str:
    return " ".join(text.replace("\u200b", " ").split())


def extract_text_from_html(html: str) -> str:
    if trafilatura is not None:
        extracted = trafilatura.extract(html, include_links=False, include_comments=False, favor_precision=True)
        if extracted:
            return sanitize_text(extracted)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    return sanitize_text(text)


def fetch_and_extract_url_text(url: str, settings: Settings) -> tuple[str | None, dict[str, str]]:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if any(domain in hostname for domain in PRIVATE_DOMAINS):
        return None, {"status": "skipped", "detail": "Private platform URLs are not fetched directly."}

    headers = {"User-Agent": "PrismAI/1.0 (+https://prism.ai)"}
    try:
        with httpx.Client(timeout=settings.request_timeout_seconds, follow_redirects=True, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()
            html = response.text[: settings.max_url_bytes]
            extracted = extract_text_from_html(html)
            if settings.max_fetched_chars > 0:
                extracted = extracted[: settings.max_fetched_chars]
            return extracted, {"status": "completed", "detail": f"Fetched {len(extracted)} characters from page text."}
    except Exception as exc:
        return None, {"status": "failed", "detail": str(exc)}
