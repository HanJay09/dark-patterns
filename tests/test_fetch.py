"""
tests/test_fetch.py

Basic smoke tests for scraper.fetch. These don't require network access for
the dataclass/structure checks; the live-fetch test is marked separately so
you can skip it in CI or offline environments.
"""

import pytest

from scraper.fetch import ScrapedPage, scrape_sync


def test_scraped_page_dataclass_defaults():
    page = ScrapedPage(
        url="https://example.com",
        fetched_at="2026-06-26T00:00:00+00:00",
        html="<html></html>",
        visible_text="",
        title="",
        links=[],
        forms=[],
        buttons=[],
        countdown_like_elements=[],
    )
    assert page.error is None
    assert page.url == "https://example.com"


@pytest.mark.network
def test_scrape_live_example_site():
    """Requires internet + Playwright browser binaries installed."""
    result = scrape_sync("https://example.com")
    assert result.error is None
    assert "Example Domain" in result.title or result.title != ""
    assert len(result.html) > 0
