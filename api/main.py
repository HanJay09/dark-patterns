"""
api/main.py

FastAPI backend for the Dark Pattern Detection Tool.

Endpoints:
  POST /analyse        — accepts a URL, scrapes it, runs detection, returns report
  GET  /health         — liveness check
  GET  /categories     — returns the 6 supported dark pattern categories

Run locally:
  uvicorn api.main:app --reload --port 8000

The React frontend (USE_MOCK=false) will POST to http://localhost:8000/analyse
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, field_validator
import asyncio

from scraper.fetch import scrape
from detection_engine.engine import analyse

app = FastAPI(
    title="DarkDetect API",
    description="Automated dark pattern detection for websites — QMUL MSc Project",
    version="0.1.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow the React dev server (port 3000) and any production origin.
# Tighten this for deployment.
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

    @field_validator('url')
    @classmethod
    def url_must_have_scheme(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class InstanceSchema(BaseModel):
    evidence: str
    location: str


class FindingSchema(BaseModel):
    id:          str
    category:    str
    severity:    str
    count:       int
    instances:   list[InstanceSchema]
    explanation: str


class AnalyseResponse(BaseModel):
    url:                str
    analysed_at:        str
    total_found:        int
    overall_risk:       str
    confidence:         float
    categories_checked: int
    findings:           list[FindingSchema]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Liveness check — confirms the API is running."""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/categories")
async def categories():
    """Return the 6 supported dark pattern categories."""
    return {
        "categories": [
            {"id": "DP-1", "name": "Misdirection",       "description": "Visual tricks that steer users toward unintended actions"},
            {"id": "DP-2", "name": "Hidden Costs",        "description": "Fees revealed only late in a purchase flow"},
            {"id": "DP-3", "name": "Confirmshaming",      "description": "Guilt-inducing language on opt-out buttons"},
            {"id": "DP-4", "name": "Disguised Ads",       "description": "Ads styled to look like organic content"},
            {"id": "DP-5", "name": "Forced Continuity",   "description": "Hard-to-cancel subscriptions and auto-renewals"},
            {"id": "DP-6", "name": "Urgency / Scarcity",  "description": "Fake countdowns and low-stock claims"},
        ]
    }


@app.post("/analyse", response_model=AnalyseResponse)
async def analyse_url(request: AnalyseRequest):
    """
    Main endpoint. Accepts a URL, scrapes the page, runs dark pattern
    detection, and returns a structured report.

    Typical flow:
      1. Playwright scrapes the URL (headless Chromium, JS-rendered)
      2. Detection engine runs rule-based heuristics + ML classifier
      3. Structured findings JSON is returned to the React frontend
    """
    # 1. Scrape
    try:
        page = await scrape(request.url, timeout_ms=25000)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scraping failed: {str(e)}")

    if page.error:
        raise HTTPException(
            status_code=422,
            detail=f"Could not fetch the page: {page.error}. "
                   "Make sure the URL is publicly accessible."
        )

    if not page.visible_text.strip():
        raise HTTPException(
            status_code=422,
            detail="The page returned no readable content. It may require login or block automated access."
        )

    # 2. Detect
    try:
        result = analyse(page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection engine error: {str(e)}")

    return result
