"""
scraper/fetch.py

Prototype content-extraction pipeline for the Dark Pattern Detection Tool.

Given a URL, this module:
1. Loads the page with a real browser engine (via Playwright), so JS-rendered
   content (React/Vue apps) is captured — not just raw static HTML.
2. Extracts the rendered DOM, visible text, and key styling signals.
3. Returns a structured dict ready to be passed into the detection engine.

Why Playwright over plain requests/BeautifulSoup-only:
Per the project's risk assessment, many target sites are JS-heavy and won't
render with a simple HTTP GET. Playwright runs a real headless browser so we
get the DOM *after* JavaScript has executed.

Usage:
    python -m scraper.fetch https://example.com
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup


@dataclass
class ScrapedPage:
    url: str
    fetched_at: str
    html: str                      # full rendered HTML
    visible_text: str              # text actually visible to a user
    title: str
    links: list[str]
    forms: list[dict[str, Any]]    # form fields — relevant for hidden-cost / forced-continuity patterns
    buttons: list[dict[str, str]]  # button/CTA text + visibility — relevant for misdirection
    countdown_like_elements: list[str]  # elements that look like urgency timers
    error: str | None = None


async def _extract(page: Page, url: str) -> ScrapedPage:
    html = await page.content()
    title = await page.title()

    soup = BeautifulSoup(html, "lxml")

    # Strip script/style for clean visible-text extraction
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    visible_text = " ".join(soup.get_text(separator=" ").split())

    links = [a.get("href") for a in soup.find_all("a", href=True)]

    forms = []
    for form in soup.find_all("form"):
        fields = [
            {"name": inp.get("name", ""), "type": inp.get("type", "text")}
            for inp in form.find_all(["input", "select", "textarea"])
        ]
        forms.append({"action": form.get("action", ""), "fields": fields})

    buttons = []
    for btn in soup.find_all(["button"]) + soup.find_all("a", attrs={"role": "button"}):
        text = btn.get_text(strip=True)
        if text:
            buttons.append({"text": text, "tag": btn.name})

    # crude heuristic flag for urgency/countdown-style dark patterns —
    # refine this in detection_engine once taxonomy is finalised
    countdown_keywords = ["left in stock", "only", "offer ends", "expires in", "time left", "hurry"]
    countdown_like = [
        text for text in [b["text"] for b in buttons] + [visible_text]
        if any(k in text.lower() for k in countdown_keywords)
    ]

    return ScrapedPage(
        url=url,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        html=html,
        visible_text=visible_text,
        title=title,
        links=links,
        forms=forms,
        buttons=buttons,
        countdown_like_elements=countdown_like[:10],  # cap for sanity
    )


async def scrape(url: str, timeout_ms: int = 20000) -> ScrapedPage:
    """Fetch and extract content from a single URL."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=timeout_ms, wait_until="networkidle")
            result = await _extract(page, url)
        except Exception as e:  # noqa: BLE001 — prototype-stage broad catch is intentional
            result = ScrapedPage(
                url=url,
                fetched_at=datetime.now(timezone.utc).isoformat(),
                html="",
                visible_text="",
                title="",
                links=[],
                forms=[],
                buttons=[],
                countdown_like_elements=[],
                error=str(e),
            )
        finally:
            await browser.close()
        return result


def scrape_sync(url: str, timeout_ms: int = 20000) -> ScrapedPage:
    """Convenience sync wrapper (handy for quick scripts/tests/notebooks)."""
    return asyncio.run(scrape(url, timeout_ms))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scraper.fetch <url>")
        sys.exit(1)

    target_url = sys.argv[1]
    page_data = scrape_sync(target_url)

    # Don't dump full HTML to console — just the useful summary
    summary = asdict(page_data)
    summary.pop("html")
    print(json.dumps(summary, indent=2))
