"""
tests/e2e/test_live_urls.py

End-to-end test script for the dark pattern detection pipeline.

This script:
1. Scrapes each URL in the test list using the Playwright scraper
2. Passes the extracted content through the detection engine
3. Prints a detailed per-URL report to the console
4. Saves all results to data/results/e2e_results.json

Run from the project root:
    python -m tests.e2e.test_live_urls

Requirements:
    - pip install -r requirements.txt
    - playwright install chromium
    - Internet access

The test URLs below are deliberately chosen to represent a range of
site types: e-commerce (likely dark patterns), news (possible ads),
and a clean reference site (should return few/no findings).
Add or remove URLs to suit your evaluation needs.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path so modules resolve correctly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scraper.fetch import scrape
from detection_engine.engine import analyse

# ── Test URL list ─────────────────────────────────────────────────────────────
# Format: (url, notes)
# Add your own URLs here — aim for at least 10 before the evaluation phase
TEST_URLS = [
    # E-commerce — high likelihood of dark patterns
    ("https://www.amazon.co.uk",          "Major e-commerce — likely DP-6, DP-4"),
    ("https://www.booking.com",           "Travel booking — likely DP-6, DP-5"),
    ("https://www.trainline.com",         "Travel ticketing — likely DP-2, DP-6"),

    # Subscription services — likely forced continuity / hidden costs
    ("https://www.netflix.com",           "Subscription — likely DP-5, DP-2"),
    ("https://www.linkedin.com/premium",  "Premium upsell — likely DP-5, DP-3"),

    # News / media — likely disguised ads
    ("https://www.dailymail.co.uk",       "News site — likely DP-4, DP-6"),
    ("https://www.mirror.co.uk",          "News site — likely DP-4"),

    # Should be clean — use as negative/baseline controls
    ("https://www.bbc.co.uk",             "Public broadcaster — expect few findings"),
    ("https://www.gov.uk",                "UK Government — expect no findings"),
    ("https://example.com",               "Minimal test page — expect no findings"),
]

# ── Output paths ──────────────────────────────────────────────────────────────
RESULTS_DIR  = Path(__file__).parent.parent.parent / "data" / "results"
RESULTS_FILE = RESULTS_DIR / "e2e_results.json"


# ── Formatting helpers ────────────────────────────────────────────────────────

SEV_COLOUR = {
    "high":   "\033[91m",  # red
    "medium": "\033[93m",  # yellow
    "low":    "\033[92m",  # green
}
RESET = "\033[0m"
BOLD  = "\033[1m"


def print_separator(char="─", width=70):
    print(char * width)


def print_result(url: str, notes: str, result: dict, elapsed: float):
    print_separator()
    print(f"{BOLD}URL:{RESET}   {url}")
    print(f"Notes: {notes}")
    print(f"Time:  {elapsed:.1f}s")

    if result.get("error"):
        print(f"\033[91mERROR: {result['error']}{RESET}")
        return

    risk_colour = SEV_COLOUR.get(result.get("overall_risk", "low"), "")
    print(f"Risk:  {risk_colour}{result['overall_risk'].upper()}{RESET}  |  "
          f"Found: {result['total_found']}  |  "
          f"Confidence: {result.get('confidence', 0):.0%}")

    findings = result.get("findings", [])
    if not findings:
        print("  \033[92mNo dark patterns detected\033[0m")
    else:
        print()
        for f in findings:
            sev_col = SEV_COLOUR.get(f["severity"], "")
            print(f"  {sev_col}[{f['severity'].upper():6}]{RESET} "
                  f"{f['id']} — {f['category']}  ({f['count']} instance(s))")
            for inst in f["instances"][:2]:  # show max 2 instances per category
                evidence = inst["evidence"][:80].replace("\n", " ")
                print(f"           {evidence}")


# ── Core test runner ──────────────────────────────────────────────────────────

async def run_single(url: str, notes: str) -> dict:
    """Scrape and analyse a single URL. Returns result dict."""
    t0 = time.monotonic()

    try:
        page = await scrape(url, timeout_ms=30000)
    except Exception as e:
        return {
            "url":     url,
            "notes":   notes,
            "error":   f"Scraper exception: {str(e)}",
            "elapsed": round(time.monotonic() - t0, 2),
        }

    if page.error:
        return {
            "url":     url,
            "notes":   notes,
            "error":   page.error,
            "elapsed": round(time.monotonic() - t0, 2),
        }

    if not page.visible_text.strip():
        return {
            "url":     url,
            "notes":   notes,
            "error":   "Page returned no readable content (may require login or block scrapers)",
            "elapsed": round(time.monotonic() - t0, 2),
        }

    try:
        result = analyse(page)
    except Exception as e:
        return {
            "url":     url,
            "notes":   notes,
            "error":   f"Detection engine exception: {str(e)}",
            "elapsed": round(time.monotonic() - t0, 2),
        }

    result["notes"]   = notes
    result["elapsed"] = round(time.monotonic() - t0, 2)
    return result


async def run_all(urls: list[tuple[str, str]]) -> list[dict]:
    """Run all URLs sequentially (not parallel — avoids rate limiting)."""
    results = []
    print(f"\n{BOLD}DarkDetect — End-to-End Live URL Test{RESET}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing {len(urls)} URLs\n")

    for i, (url, notes) in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Fetching {url} ...")
        result = await run_single(url, notes)
        elapsed = result.get("elapsed", 0)
        print_result(url, notes, result, elapsed)
        results.append(result)

        # Small delay between requests to be polite to servers
        if i < len(urls):
            await asyncio.sleep(2)

    return results


# ── Summary statistics ────────────────────────────────────────────────────────

def print_summary(results: list[dict]):
    print_separator("═")
    print(f"{BOLD}SUMMARY{RESET}")
    print_separator("═")

    total       = len(results)
    errors      = [r for r in results if r.get("error")]
    successes   = [r for r in results if not r.get("error")]
    with_findings = [r for r in successes if r.get("total_found", 0) > 0]
    high_risk   = [r for r in successes if r.get("overall_risk") == "high"]

    print(f"URLs tested:          {total}")
    print(f"Successfully scraped: {len(successes)}")
    print(f"Errors:               {len(errors)}")
    print(f"Pages with findings:  {len(with_findings)} / {len(successes)}")
    print(f"High risk pages:      {len(high_risk)}")

    if successes:
        avg_found = sum(r.get("total_found", 0) for r in successes) / len(successes)
        avg_time  = sum(r.get("elapsed", 0)     for r in results)   / len(results)
        print(f"Avg patterns found:   {avg_found:.1f}")
        print(f"Avg time per URL:     {avg_time:.1f}s")

    # Category frequency across all results
    cat_counts: dict[str, int] = {}
    for r in successes:
        for f in r.get("findings", []):
            cat_counts[f["category"]] = cat_counts.get(f["category"], 0) + 1

    if cat_counts:
        print(f"\n{BOLD}Category frequency across all pages:{RESET}")
        for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
            bar = "█" * count
            print(f"  {cat:<25} {bar} ({count})")

    if errors:
        print(f"\n{BOLD}Failed URLs:{RESET}")
        for r in errors:
            print(f"  {r['url']}")
            print(f"    {r['error']}")


# ── Save results ──────────────────────────────────────────────────────────────

def save_results(results: list[dict]):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "run_at":  datetime.now(timezone.utc).isoformat(),
        "total":   len(results),
        "results": results,
    }
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {RESULTS_FILE}")


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    results = await run_all(TEST_URLS)
    print_summary(results)
    save_results(results)


if __name__ == "__main__":
    asyncio.run(main())