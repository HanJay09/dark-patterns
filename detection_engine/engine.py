"""
detection_engine/engine.py

Orchestrates rule-based heuristics + ML classifier and produces the
structured JSON response that the FastAPI endpoint returns to the frontend.

Output schema (matches what the React frontend expects):
{
  "url": str,
  "analysed_at": str (ISO 8601),
  "total_found": int,
  "overall_risk": "high" | "medium" | "low" | "none",
  "confidence": float,
  "categories_checked": int,
  "findings": [
    {
      "id": "DP-1",
      "category": str,
      "severity": "high" | "medium" | "low",
      "count": int,
      "instances": [
        { "evidence": str, "location": str }
      ],
      "explanation": str
    }
  ]
}
"""

from __future__ import annotations

from datetime import datetime, timezone
from collections import defaultdict
from typing import Any

from detection_engine.rules import run_all_rules, RuleHit
from detection_engine.classifier import get_classifier


# ── Category metadata ─────────────────────────────────────────────────────────

CATEGORY_META = {
    'DP-1': {
        'category': 'Misdirection',
        'explanation': (
            'Visual or structural tricks steer users toward one option '
            'while suppressing alternatives. Common techniques include '
            'making the decline option tiny, low-contrast, or hard to find. '
            'Research (Mathur et al., 2019) found misdirection on ~12% of '
            'surveyed shopping sites.'
        ),
    },
    'DP-2': {
        'category': 'Hidden Costs',
        'explanation': (
            'Additional fees — shipping, taxes, service charges — are '
            'disclosed only late in the purchase flow, after the user has '
            'already invested effort. This exploits sunk-cost bias to '
            'reduce abandonment despite the higher final price.'
        ),
    },
    'DP-3': {
        'category': 'Confirmshaming',
        'explanation': (
            'The opt-out choice is labelled with guilt-inducing or '
            'self-deprecating language (e.g. "No thanks, I don\'t want '
            'to save money") to make users feel foolish for declining. '
            'Identified by Gray et al. (2018) as a manipulation of '
            'social norms and self-image.'
        ),
    },
    'DP-4': {
        'category': 'Disguised Ads',
        'explanation': (
            'Advertisements are styled to visually blend in with organic '
            'content, navigation, or search results, making it difficult '
            'for users to distinguish paid promotion from genuine editorial '
            'content. Prevalence of native ad networks on a page is a '
            'strong indicator.'
        ),
    },
    'DP-5': {
        'category': 'Forced Continuity',
        'explanation': (
            'Free trials or subscriptions require payment details upfront '
            'and auto-renew without a clear, easy cancellation path. '
            'Cancellation may require a phone call, letter, or 30+ days '
            'notice — friction intentionally designed to retain unwilling '
            'subscribers.'
        ),
    },
    'DP-6': {
        'category': 'Urgency / Scarcity',
        'explanation': (
            'Artificial time pressure ("Offer ends in 2 hours") or false '
            'scarcity claims ("Only 3 left in stock") push users into '
            'hasty decisions without adequate comparison shopping. '
            'The Princeton WTAP study (2019) found urgency/scarcity '
            'patterns on over 10% of crawled e-commerce pages.'
        ),
    },
}

SEVERITY_RANK = {'high': 3, 'medium': 2, 'low': 1}

CATEGORIES_CHECKED = 6


# ── Deduplication ─────────────────────────────────────────────────────────────

def _deduplicate(hits: list[RuleHit]) -> list[RuleHit]:
    """Remove near-duplicate hits within the same category (same evidence prefix)."""
    seen: set[str] = set()
    out: list[RuleHit] = []
    for h in hits:
        key = (h.category_id, h.evidence[:60].lower().strip())
        if key not in seen:
            seen.add(key)
            out.append(h)
    return out


# ── Risk scoring ──────────────────────────────────────────────────────────────

def _overall_risk(findings: list[dict]) -> str:
    if not findings:
        return 'none'
    high_count = sum(1 for f in findings if f['severity'] == 'high')
    if high_count >= 2:
        return 'high'
    if high_count == 1 or len(findings) >= 2:
        return 'medium'
    return 'low'


def _avg_confidence(hits: list[RuleHit]) -> float:
    if not hits:
        return 0.0
    return round(sum(h.confidence for h in hits) / len(hits), 2)


# ── Main entry point ──────────────────────────────────────────────────────────

def analyse(page) -> dict[str, Any]:
    """
    Run all detection methods against a ScrapedPage and return a structured
    result dict matching the frontend's expected schema.
    """
    # 1. Rule-based detection
    rule_hits = run_all_rules(page)

    # 2. ML classifier (if model is available)
    #    Feed it button text + short text snippets from the page
    classifier = get_classifier()
    ml_hits: list[RuleHit] = []

    if classifier.available:
        # Build snippets: button text + sentences from visible text
        button_texts = [b['text'] for b in page.buttons if len(b.get('text', '')) > 5]
        sentences    = [
            s.strip() for s in page.visible_text.split('.')
            if 8 < len(s.strip()) < 200
        ]
        snippets = button_texts + sentences[:80]  # cap to avoid huge inference calls

        predictions = classifier.predict(snippets)
        for pred in predictions:
            meta = CATEGORY_META.get(pred['label'], {})
            ml_hits.append(RuleHit(
                category_id=pred['label'],
                category=meta.get('category', pred['label']),
                severity='medium',         # ML hits default to medium until calibrated
                evidence=f'"{pred["text"][:120]}"',
                location='Page text / button (ML classifier)',
                rule='ml_classifier',
                confidence=pred['confidence'],
            ))

    all_hits = _deduplicate(rule_hits + ml_hits)

    # 3. Group hits by category
    by_category: dict[str, list[RuleHit]] = defaultdict(list)
    for hit in all_hits:
        by_category[hit.category_id].append(hit)

    # 4. Build findings list
    findings = []
    for cat_id, cat_hits in by_category.items():
        meta = CATEGORY_META.get(cat_id, {})

        # Severity = highest severity among instances in this category
        severity = max(
            (h.severity for h in cat_hits),
            key=lambda s: SEVERITY_RANK.get(s, 0),
            default='low',
        )

        findings.append({
            'id':          cat_id,
            'category':    meta.get('category', cat_id),
            'severity':    severity,
            'count':       len(cat_hits),
            'instances':   [
                {'evidence': h.evidence, 'location': h.location}
                for h in cat_hits[:5]  # cap instances shown to 5
            ],
            'explanation': meta.get('explanation', ''),
        })

    # Sort: high severity first, then by count
    findings.sort(key=lambda f: (-SEVERITY_RANK.get(f['severity'], 0), -f['count']))

    return {
        'url':                page.url,
        'analysed_at':        datetime.now(timezone.utc).isoformat(),
        'total_found':        len(findings),
        'overall_risk':       _overall_risk(findings),
        'confidence':         _avg_confidence(all_hits),
        'categories_checked': CATEGORIES_CHECKED,
        'findings':           findings,
    }
