from __future__ import annotations
from datetime import datetime, timezone
from collections import defaultdict
from typing import Any
from detection_engine.rules import run_all_rules, RuleHit

CATEGORY_META = {
    'DP-1': {'category': 'Misdirection', 'explanation': 'Visual tricks steer users toward unintended actions.'},
    'DP-2': {'category': 'Hidden Costs', 'explanation': 'Fees disclosed only late in a purchase flow.'},
    'DP-3': {'category': 'Confirmshaming', 'explanation': 'Guilt-inducing language on opt-out buttons.'},
    'DP-4': {'category': 'Disguised Ads', 'explanation': 'Ads styled to look like organic content.'},
    'DP-5': {'category': 'Forced Continuity', 'explanation': 'Hard-to-cancel subscriptions and auto-renewals.'},
    'DP-6': {'category': 'Urgency / Scarcity', 'explanation': 'Fake countdowns and low-stock claims.'},
}
SEVERITY_RANK = {'high': 3, 'medium': 2, 'low': 1}
CATEGORIES_CHECKED = 6

def _deduplicate(hits):
    seen = set(); out = []
    for h in hits:
        key = (h.category_id, h.evidence[:60].lower().strip())
        if key not in seen:
            seen.add(key); out.append(h)
    return out

def _overall_risk(findings):
    if not findings: return 'none'
    high_count = sum(1 for f in findings if f['severity'] == 'high')
    if high_count >= 2: return 'high'
    if high_count == 1 or len(findings) >= 2: return 'medium'
    return 'low'

def _avg_confidence(hits):
    if not hits: return 0.0
    return round(sum(h.confidence for h in hits) / len(hits), 2)

def analyse(page):
    rule_hits = run_all_rules(page)
    ml_hits = []
    try:
        from detection_engine.classifier import get_classifier
        classifier = get_classifier()
        if classifier.available:
            button_texts = [b['text'] for b in page.buttons if len(b.get('text','')) > 5]
            sentences = [s.strip() for s in page.visible_text.split('.') if 8 < len(s.strip()) < 200]
            snippets = button_texts + sentences[:80]
            for pred in classifier.predict(snippets):
                meta = CATEGORY_META.get(pred['label'], {})
                # Fix: ensure label is plain str, not np.str_
                label = str(pred['label'])
                ml_hits.append(RuleHit(
                    category_id=label,
                    category=meta.get('category', label),
                    severity='medium',
                    evidence=f'"{str(pred["text"])[:120]}"',
                    location='ML classifier',
                    rule='ml_classifier',
                    confidence=float(pred['confidence'])
                ))
    except Exception as e:
        pass
    all_hits = _deduplicate(rule_hits + ml_hits)
    by_category = defaultdict(list)
    for hit in all_hits:
        by_category[str(hit.category_id)].append(hit)
    findings = []
    for cat_id, cat_hits in by_category.items():
        meta = CATEGORY_META.get(cat_id, {})
        severity = max((h.severity for h in cat_hits), key=lambda s: SEVERITY_RANK.get(s,0), default='low')
        findings.append({
            'id': str(cat_id),
            'category': meta.get('category', cat_id),
            'severity': severity,
            'count': len(cat_hits),
            'instances': [{'evidence': str(h.evidence), 'location': str(h.location)} for h in cat_hits[:5]],
            'explanation': meta.get('explanation', '')
        })
    findings.sort(key=lambda f: (-SEVERITY_RANK.get(f['severity'],0), -f['count']))
    return {
        'url': page.url,
        'analysed_at': datetime.now(timezone.utc).isoformat(),
        'total_found': len(findings),
        'overall_risk': _overall_risk(findings),
        'confidence': _avg_confidence(all_hits),
        'categories_checked': CATEGORIES_CHECKED,
        'findings': findings
    }
