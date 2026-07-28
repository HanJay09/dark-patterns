"""
scraper/fetch.py — v2

Changes from v1:
- Extra 2s post-load wait for JS frameworks to render dynamic content
- Page scroll to trigger lazy-loaded elements (urgency banners, stock alerts)
- domcontentloaded fallback for sites that never reach networkidle
- Realistic user-agent and viewport to reduce bot detection
- Expanded countdown_keywords list
"""
from __future__ import annotations
import asyncio, json, sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

@dataclass
class ScrapedPage:
    url: str; fetched_at: str; html: str; visible_text: str; title: str
    links: list; forms: list; buttons: list; countdown_like_elements: list
    error: str | None = None

async def _extract(page, url: str) -> ScrapedPage:
    from bs4 import BeautifulSoup
    html = await page.content(); title = await page.title()
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script","style","noscript"]): tag.decompose()
    visible_text = " ".join(soup.get_text(separator=" ").split())
    links = [a.get("href") for a in soup.find_all("a", href=True)]
    forms = [{"action": f.get("action",""), "fields": [{"name": i.get("name",""),"type": i.get("type","text")} for i in f.find_all(["input","select","textarea"])]} for f in soup.find_all("form")]
    buttons = [{"text": b.get_text(strip=True), "tag": b.name} for b in soup.find_all(["button"]) + soup.find_all("a", attrs={"role":"button"}) if b.get_text(strip=True)]
    kw = ["left in stock","only","offer ends","expires in","time left","hurry","limited-time","deal ends","selling fast","hours left","today only","flash sale"]
    countdown_like = [t for t in [b["text"] for b in buttons]+[visible_text] if any(k in t.lower() for k in kw)]
    return ScrapedPage(url=url, fetched_at=datetime.now(timezone.utc).isoformat(), html=html, visible_text=visible_text, title=title, links=links, forms=forms, buttons=buttons, countdown_like_elements=countdown_like[:10])

async def scrape(url: str, timeout_ms: int = 30000) -> ScrapedPage:
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        try:
            try:
                await page.goto(url, timeout=timeout_ms, wait_until="networkidle")
            except Exception:
                await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            # Extra wait for JS frameworks to render dynamic content
            await asyncio.sleep(2)
            # Scroll to trigger lazy-loaded content (urgency banners, stock alerts)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3);")
            await asyncio.sleep(1)
            await page.evaluate("window.scrollTo(0, 0);")
            await asyncio.sleep(0.5)
            result = await _extract(page, url)
        except Exception as e:
            result = ScrapedPage(url=url, fetched_at=datetime.now(timezone.utc).isoformat(), html="", visible_text="", title="", links=[], forms=[], buttons=[], countdown_like_elements=[], error=str(e))
        finally:
            await browser.close()
    return result

def scrape_sync(url: str, timeout_ms: int = 30000) -> ScrapedPage:
    return asyncio.run(scrape(url, timeout_ms))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scraper.fetch <url>"); sys.exit(1)
    page_data = scrape_sync(sys.argv[1])
    summary = asdict(page_data); summary.pop("html")
    print(json.dumps(summary, indent=2))
