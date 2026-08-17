"""
api/main.py — v3
Windows fix: ProactorEventLoop for Playwright subprocess support.
CORS updated to allow Vercel frontend deployment.
"""
from __future__ import annotations
import asyncio, sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scraper.fetch import scrape
from detection_engine.engine import analyse

app = FastAPI(
    title="Dark Pattern Detection API",
    description="Automated dark pattern detection — QMUL MSc Project",
    version="0.3.0",
)

# Allow localhost (dev) + any Vercel deployment + any custom domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to your Vercel URL after first deploy
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyseRequest(BaseModel):
    url: str

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.3.0", "platform": sys.platform}

@app.get("/categories")
async def categories():
    return {"categories": [
        {"id": "DP-1", "name": "Misdirection",      "description": "Visual tricks that steer users toward unintended actions"},
        {"id": "DP-2", "name": "Hidden Costs",       "description": "Fees revealed only late in a purchase flow"},
        {"id": "DP-3", "name": "Confirmshaming",     "description": "Guilt-inducing language on opt-out buttons"},
        {"id": "DP-4", "name": "Disguised Ads",      "description": "Ads styled to look like organic content"},
        {"id": "DP-5", "name": "Forced Continuity",  "description": "Hard-to-cancel subscriptions and auto-renewals"},
        {"id": "DP-6", "name": "Urgency / Scarcity", "description": "Fake countdowns and low-stock claims"},
    ]}

@app.post("/analyse")
async def analyse_url(request: AnalyseRequest):
    url = request.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=422, detail="URL must start with http:// or https://")
    try:
        page = await scrape(url, timeout_ms=30000)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scraping failed: {str(e)}")
    if page.error:
        raise HTTPException(status_code=422, detail=f"Could not fetch the page: {page.error}")
    if not page.visible_text.strip():
        raise HTTPException(status_code=422, detail="The page returned no readable content.")
    try:
        result = analyse(page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection engine error: {str(e)}")
    return result
