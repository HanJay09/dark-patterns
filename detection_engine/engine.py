from __future__ import annotations
from datetime import datetime, timezone
from collections import defaultdict
from detection_engine.rules import run_all_rules, RuleHit

# Per-instance evidence explanations — shown beneath each finding in the UI
EVIDENCE_EXPLANATIONS = {
    'decline_button_language':        'This button uses language designed to make declining feel like the harder or less acceptable option, while the primary action (subscribe, purchase) is made more prominent.',
    'weak_decline_button':            'A dismiss or close button is present that may be intentionally less prominent than the main call-to-action, nudging users toward the preferred commercial action.',
    'hidden_cost_language':           'Additional charges (delivery fees, taxes, service fees) are mentioned in the page text but may not be included in the headline price, meaning users discover the true cost only later in the checkout flow.',
    'subscription_form_field':        'A form field related to subscriptions or recurring billing was found. This may indicate payment details are collected as part of a free trial that auto-converts to a paid plan.',
    'confirmshaming_button_text':     'The opt-out button uses guilt-inducing language (e.g. "No thanks, I don\'t want to save money") to make users feel foolish for declining, rather than offering a neutral choice.',
    'confirmshaming_modal_text':      'A pop-up on this page uses shame-based language to discourage dismissal, manipulating users into accepting offers they may not want.',
    'native_ad_network_script':       'This page loads content from a native advertising network such as Taboola or Outbrain. These networks serve paid promotional content styled to look like genuine editorial articles or recommendations, making it hard to distinguish ads from real content.',
    'ad_network_script':              'This page includes scripts from an advertising network. These scripts serve targeted ads that may be styled to blend in with the page\'s organic content, making them harder to identify as paid promotion.',
    'sponsored_label_present':        'The word "sponsored" or "advertisement" appears on this page. Research shows users frequently overlook these labels, especially when ads are styled to match editorial content.',
    'free_trial_with_payment_form':   'This page offers a free trial but requires payment details upfront. This frequently leads to users being charged after the trial ends without realising, particularly when cancellation is difficult or the renewal date is not clearly communicated.',
    'cancellation_friction':          'The page contains language suggesting cancellation requires extra effort — such as calling a phone number, writing a letter, or giving 30+ days notice. This deliberate friction is designed to retain unwilling subscribers.',
    'urgency_scarcity_language':      'This page uses time pressure or scarcity language to rush purchasing decisions. Research (Mathur et al., 2019) found such claims on over 10% of e-commerce sites, and they are frequently exaggerated or false.',
    'countdown_element':              'A countdown timer or "X left" indicator was detected. On many sites these timers reset when the page is refreshed, indicating they are artificial rather than reflecting genuine stock or time constraints.',
    'ml_classifier':                  'Detected by the machine learning text classifier, which analyses visible text and button labels for patterns associated with dark pattern language.',
}

CATEGORY_META = {
    'DP-1': {'category': 'Misdirection',      'explanation': 'Visual or structural design choices steer users toward one option while suppressing alternatives. Common techniques include making the decline option tiny, low-contrast, or hard to find. Research (Mathur et al., 2019) found misdirection on around 12% of surveyed shopping sites.'},
    'DP-2': {'category': 'Hidden Costs',      'explanation': 'Additional fees such as shipping, taxes, or service charges are disclosed only late in the purchase flow, after the user has already invested effort. This exploits sunk-cost bias to reduce abandonment despite the higher final price.'},
    'DP-3': {'category': 'Confirmshaming',    'explanation': 'The opt-out choice is labelled with guilt-inducing or self-deprecating language to make users feel foolish for declining. Identified by Gray et al. (2018) as a manipulation of social norms and self-image.'},
    'DP-4': {'category': 'Disguised Ads',     'explanation': 'Advertisements are styled to visually blend in with organic content, navigation, or search results, making it difficult for users to distinguish paid promotion from genuine editorial content. Native ad networks such as Taboola and Outbrain specialise in this type of content.'},
    'DP-5': {'category': 'Forced Continuity', 'explanation': 'Free trials or subscriptions require payment details upfront and auto-renew without a clear, easy cancellation path. Cancellation may require a phone call, letter, or 30+ days notice — friction intentionally designed to retain unwilling subscribers.'},
    'DP-6': {'category': 'Urgency / Scarcity','explanation': 'Artificial time pressure or false scarcity claims push users into hasty decisions without adequate comparison shopping. The Princeton WTAP study (2019) found urgency and scarcity patterns on over 10% of crawled e-commerce pages.'},
}

SEVERITY_RANK = {'high': 3, 'medium': 2, 'low': 1}
CATEGORIES_CHECKED = 6

def _deduplicate(hits):
    seen = set(); out = []
    for h in hits:
        k = (h.category_id, h.evidence[:60].lower().strip())
        if k not in seen:
            seen.add(k); out.append(h)
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
        clf = get_classifier()
        if clf.available:
            snippets = [b['text'] for b in page.buttons if len(b.get('text','')) > 5] + \
                       [s.strip() for s in page.visible_text.split('.') if 8 < len(s.strip()) < 200][:80]
            for pred in clf.predict(snippets):
                label = str(pred['label'])
                meta  = CATEGORY_META.get(label, {})
                ml_hits.append(RuleHit(
                    category_id=label, category=meta.get('category', label),
                    severity='medium', evidence=f'"{str(pred["text"])[:120]}"',
                    location='ML classifier', rule='ml_classifier',
                    confidence=float(pred['confidence'])
                ))
    except Exception:
        pass

    all_hits = _deduplicate(rule_hits + ml_hits)
    by_category = defaultdict(list)
    for h in all_hits:
        by_category[str(h.category_id)].append(h)

    findings = []
    for cat_id, hits in by_category.items():
        meta     = CATEGORY_META.get(cat_id, {})
        severity = max((h.severity for h in hits), key=lambda s: SEVERITY_RANK.get(s, 0), default='low')
        findings.append({
            'id':          str(cat_id),
            'category':    meta.get('category', cat_id),
            'severity':    severity,
            'count':       len(hits),
            'instances':   [{
                'evidence':            str(h.evidence),
                'location':            str(h.location),
                'rule':                str(h.rule),
                'confidence':          round(float(h.confidence), 2),
                'severity':            str(h.severity),
                'evidence_explanation': EVIDENCE_EXPLANATIONS.get(h.rule, ''),
            } for h in hits[:5]],
            'explanation': meta.get('explanation', ''),
        })

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
