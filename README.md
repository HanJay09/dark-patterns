# Automated Dark Pattern Detection Tool for Websites

MSc Project — Han Jay Tan | Supervisor: Jinhua Liang | QMUL 2025–26

## What this is

A tool that accepts a website URL, crawls the page, and detects dark
patterns (deceptive UI/UX techniques) using a combination of rule-based
heuristics and machine learning text/structure classification.

## Repo structure

```
dark-pattern-detector/
├── scraper/            # Web scraping & content extraction (Playwright/Selenium)
├── detection_engine/    # Rule-based heuristics + ML classifier
├── frontend/            # React interface for submitting URLs & viewing reports
├── data/
│   ├── raw/              # Raw scraped pages (HTML/DOM dumps) — not committed
│   └── labelled/         # Labelled dark pattern examples for training/eval
├── docs/                 # Literature review, taxonomy, wireframes, write-up notes
└── tests/                # Unit/integration tests
```

## Current status

- [ ] Phase 1: Literature review & taxonomy definition
- [ ] Phase 2: Requirements & system design
- [ ] Phase 3: Implementation (scraper, detection engine, frontend)
- [ ] Phase 4: Evaluation (accuracy + usability testing)
- [ ] Phase 5: Write-up

## Setup

```bash
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
playwright install         # downloads browser binaries for scraping
```

## Dark pattern categories (initial scope — narrow this in Phase 1/2)

Per the project's own risk assessment, trying to cover too many categories
is the single biggest scope risk. Starting shortlist (refine after lit review):

1. Misdirection
2. Hidden costs
3. Confirmshaming
4. Disguised ads
5. Urgency/scarcity claims (e.g. fake countdown timers)
6. Forced continuity (hard-to-cancel subscriptions)

## License

TBD (academic project — check QMUL submission requirements before
choosing a license if open-sourcing later).
