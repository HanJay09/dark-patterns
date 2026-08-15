"""
api/main.py

FastAPI backend for the Automated Dark Pattern Detection Tool.

Windows fix (v2):
  Playwright on Windows requires the ProactorEventLoop, but uvicorn
  uses SelectorEventLoop by default. Setting WindowsProactorEventLoopPolicy
  at module load fixes the NotImplementedError when launching Chromium.

Endpoints:
  POST /analyse   — scrape a URL and run dark pattern detection
  GET  /health    — liveness check
  GET  /categories — list of supported dark pattern categories
"""

from __future__ import annotations

import asyncio
import sys
import traceback

# ── Windows event loop fix ────────────────────────────────────────────────────
# Playwright's subprocess launch requires ProactorEventLoop on Windows.
# This must be set before uvicorn starts the event loop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scraper.fetch import scrape
from detection_engine.engine import analyse

app = FastAPI(
    title="Dark Pattern Detection API",
    description="Automated dark pattern detection for websites — QMUL MSc Project",
    version="0.2.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response schemas ────────────────────────────────────────────────

class AnalyseRequest(BaseModel):
    url: str

    model_config = {"json_schema_extra": {"example": {"url": "https://www.mirror.co.uk"}}}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0", "platform": sys.platform}


@app.get("/categories")
async def categories():
    return {
        "categories": [
            {"id": "DP-1", "name": "Misdirection",      "description": "Visual tricks that steer users toward unintended actions"},
            {"id": "DP-2", "name": "Hidden Costs",       "description": "Fees revealed only late in a purchase flow"},
            {"id": "DP-3", "name": "Confirmshaming",     "description": "Guilt-inducing language on opt-out buttons"},
            {"id": "DP-4", "name": "Disguised Ads",      "description": "Ads styled to look like organic content"},
            {"id": "DP-5", "name": "Forced Continuity",  "description": "Hard-to-cancel subscriptions and auto-renewals"},
            {"id": "DP-6", "name": "Urgency / Scarcity", "description": "Fake countdowns and low-stock claims"},
        ]
    }


@app.post("/analyse")
async def analyse_url(request: AnalyseRequest):
    """
    Scrape a URL and return a dark pattern detection report.
    """
    url = request.url.strip()

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=422,
            detail="URL must start with http:// or https://"
        )

    # Scrape
    try:
        page = await scrape(url, timeout_ms=30000)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Scraping failed"
        )

    if page.error:
        raise HTTPException(
            status_code=422,
            detail=f"Could not fetch the page: {page.error}. "
                   "Make sure the URL is publicly accessible and does not require login."
        )

    if not page.visible_text.strip():
        raise HTTPException(
            status_code=422,
            detail="The page returned no readable content. "
                   "It may require login or block automated access."
        )

    # Detect
    try:
        result = analyse(page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection engine error: {str(e)}")

    return result
