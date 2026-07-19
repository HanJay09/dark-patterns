"""
detection_engine/rules.py

Rule-based heuristics for detecting all 6 dark pattern categories.

v2 — improved after live URL testing (July 2026):
  - DP-6: Added cookie banner exclusion filters to reduce false positives
           on gov.uk, BBC, Netflix, Trainline
  - DP-1: Tightened misdirection to exclude standard cookie consent
           close/dismiss buttons — these are legitimate UI, not misdirection
  - DP-4: Improved confidence scoring — script presence alone is low signal
  - General: Added minimum text length guards to avoid title-text false positives
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuleHit:
    """A single instance of a detected dark pattern."""
    category_id: str
    category:    str
    severity:    str          # 'high' | 'medium' | 'low'
    evidence:    str
    location:    str
    rule:        str
    confidence:  float = 0.75


# ── Helpers ───────────────────────────────────────────────────────────────────

def _excerpt(text: str, max_len: int = 120) -> str:
    return text[:max_len].strip() + ('…' if len(text) > max_len else '')


# Cookie consent text patterns — used to filter out false positives across rules.
# These are legitimate UI elements, not dark patterns.
COOKIE_CONSENT_PATTERNS = [
    r'we use (?:cookies|essential cookies)',
    r'cookie (?:settings|preferences|policy|banner|consent|notice)',
    r'accept (?:all )?cookies',
    r'necessary (?:cookies )?only',
    r'manage (?:cookie )?preferences',
    r'privacy (?:settings|preferences|policy)',
    r'gdpr',
    r'our use of cookies',
    r'cookies on (?:gov\.uk|this site|our site)',
]

def _is_cookie_context(text: str) -> bool:
    """Return True if the text is likely from a cookie consent banner."""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in COOKIE_CONSENT_PATTERNS)


def _strip_cookie_sentences(text: str) -> str:
    """
    Remove sentences that are clearly about cookie consent from visible text
    before running urgency/scarcity detection.
    This prevents cookie banners from triggering false DP-6 hits.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    filtered = [s for s in sentences if not _is_cookie_context(s)]
    return ' '.join(filtered)


# ── DP-1: Misdirection ────────────────────────────────────────────────────────

def detect_misdirection(page) -> list[RuleHit]:
    """
    Detects asymmetric button pairs where a decline option uses
    guilt-inducing, minimising, or hidden language.

    v2 fix: exclude standard cookie consent close/dismiss buttons —
    these are legitimate UI elements, not misdirection. A "Close"
    button on a cookie banner is expected; a "Close" button that is
    the ONLY way to decline a subscription is a dark pattern.
    We now require the button text to appear alongside non-cookie context.
    """
    hits = []

    DECLINE_PATTERNS = [
        r"no[\s,]*thanks?",
        r"maybe later",
        r"skip(?: this)?",
        r"not (now|interested|today)",
        r"i('ll)? decide later",
        r"remind me later",
    ]

    # Excluded alone — only flag close/dismiss if NOT in a cookie context
    WEAK_DECLINE_PATTERNS = [
        r"\bclose\b",
        r"\bdismiss\b",
        r"\bskip\b",
    ]

    combined_strong = '|'.join(DECLINE_PATTERNS)
    combined_weak   = '|'.join(WEAK_DECLINE_PATTERNS)

    for btn in page.buttons:
        text = btn.get('text', '').strip()
        if not text or len(text) > 60:
            continue

        # Strong decline patterns always flag
        if re.search(combined_strong, text, re.IGNORECASE):
            hits.append(RuleHit(
                category_id='DP-1',
                category='Misdirection',
                severity='medium',
                evidence=f'"{text}"',
                location='Button / CTA element',
                rule='decline_button_language',
            ))

        # Weak patterns (close/dismiss/skip) only flag if surrounding
        # page context is NOT a cookie consent banner
        elif re.search(combined_weak, text, re.IGNORECASE):
            if not _is_cookie_context(page.visible_text[:2000]):
                hits.append(RuleHit(
                    category_id='DP-1',
                    category='Misdirection',
                    severity='low',
                    evidence=f'"{text}"',
                    location='Button / CTA element (possible dismiss misdirection)',
                    rule='weak_decline_button',
                    confidence=0.55,
                ))

    return hits


# ── DP-2: Hidden Costs ────────────────────────────────────────────────────────

def detect_hidden_costs(page) -> list[RuleHit]:
    """
    Signals: subscription/fee language in text or form fields.
    Requires minimum surrounding context length to avoid matching
    page titles or navigation fragments.
    """
    hits = []

    COST_PATTERNS = [
        (r'\+\s*(?:shipping|delivery|handling|service fee|booking fee)',
         'Extra fee added to price', 'high'),
        (r'auto(?:matically)?[\s-]renew(?:s|al)?',
         'Auto-renewal language', 'high'),
        (r'(?:taxes?|vat|gst)\s+(?:not included|excluded|extra|added at checkout)',
         'Tax excluded from displayed price', 'medium'),
        (r'processing fee',
         'Processing fee mentioned', 'medium'),
        (r'resort fee|destination fee|facility fee',
         'Hidden resort/facility fee', 'high'),
        (r'price (?:shown )?(?:does not|doesn\'t) include',
         'Price exclusion disclosed late', 'high'),
    ]

    # Only check text that is at least 40 chars to avoid title fragments
    text_to_check = page.visible_text
    if len(text_to_check) < 40:
        return hits

    for pattern, desc, severity in COST_PATTERNS:
        matches = list(re.finditer(pattern, text_to_check, re.IGNORECASE))
        for m in matches[:3]:
            start = max(0, m.start() - 40)
            end   = min(len(text_to_check), m.end() + 60)
            context = text_to_check[start:end].strip()

            # Skip if this is clearly cookie consent context
            if _is_cookie_context(context):
                continue

            hits.append(RuleHit(
                category_id='DP-2',
                category='Hidden Costs',
                severity=severity,
                evidence=f'"{_excerpt(context)}"',
                location='Page text',
                rule='hidden_cost_language',
            ))

    # Check form fields for subscription indicators
    for form in page.forms:
        for field_info in form.get('fields', []):
            name = field_info.get('name', '').lower()
            if any(k in name for k in ['subscribe', 'recurring', 'membership']):
                hits.append(RuleHit(
                    category_id='DP-2',
                    category='Hidden Costs',
                    severity='high',
                    evidence=f'Form field: "{field_info["name"]}"',
                    location=f'Form (action: {form.get("action", "unknown")})',
                    rule='subscription_form_field',
                ))

    return hits


# ── DP-3: Confirmshaming ──────────────────────────────────────────────────────

def detect_confirmshaming(page) -> list[RuleHit]:
    """
    Guilt-inducing opt-out language.
    Requires full sentence context to avoid matching fragments.
    """
    hits = []

    SHAME_PATTERNS = [
        r"no[\s,]+thanks?,?\s+i(?:'m| am| don't| do not).{0,60}",
        r"i(?:'m| am) (?:not |un)?interested in saving",
        r"i don'?t want (?:to )?(?:save|get|receive|learn|improve|grow|earn)",
        r"i(?:'ll)? (?:miss out|stay (?:broke|behind|ignorant|unhealthy))",
        r"no[\s,]+i(?:'ll)? pay full price",
        r"i(?:'m| am) (?:already|not) (?:smart|successful|rich|healthy|informed) enough",
    ]

    all_button_text = ' | '.join(b.get('text', '') for b in page.buttons)

    for pattern in SHAME_PATTERNS:
        matches = re.findall(pattern, all_button_text, re.IGNORECASE)
        for m in matches:
            if len(m) < 10:
                continue
            hits.append(RuleHit(
                category_id='DP-3',
                category='Confirmshaming',
                severity='high',
                evidence=f'"{_excerpt(m)}"',
                location='Opt-out / decline button',
                rule='confirmshaming_button_text',
                confidence=0.85,
            ))

    # Check visible text for modal dismiss language
    MODAL_PATTERNS = [
        r"no[\s,]+thanks?,?\s+i don'?t want.{0,80}",
        r"no[\s,]+i(?:'ll)? pass on.{0,60}",
    ]
    for pattern in MODAL_PATTERNS:
        matches = re.findall(pattern, page.visible_text, re.IGNORECASE)
        for m in matches[:2]:
            if len(m) < 10 or _is_cookie_context(m):
                continue
            hits.append(RuleHit(
                category_id='DP-3',
                category='Confirmshaming',
                severity='high',
                evidence=f'"{_excerpt(m)}"',
                location='Modal / pop-up dismiss option',
                rule='confirmshaming_modal_text',
                confidence=0.80,
            ))

    return hits


# ── DP-4: Disguised Ads ───────────────────────────────────────────────────────

def detect_disguised_ads(page) -> list[RuleHit]:
    """
    Known ad-network script signatures in page HTML.

    v2: Split into two tiers.
    - Native ad networks (Taboola, Outbrain) are higher confidence
      as they specifically serve content-style ads.
    - General ad networks (DoubleClick, AdSense) are lower confidence
      as they may serve standard display ads that are clearly labelled.
    """
    hits = []

    NATIVE_AD_NETWORKS = [
        ('outbrain',        'Outbrain native ads'),
        ('taboola',         'Taboola native ads'),
        ('revcontent',      'Revcontent native ads'),
        ('mgid',            'MGID native ads'),
    ]

    GENERAL_AD_NETWORKS = [
        ('doubleclick.net', 'Google DoubleClick ad script'),
        ('googlesyndication','Google AdSense'),
        ('amazon-adsystem', 'Amazon Advertising'),
        ('criteo',          'Criteo retargeting'),
        ('adsrvr.org',      'The Trade Desk'),
    ]

    html_lower = page.html.lower()

    for domain, label in NATIVE_AD_NETWORKS:
        if domain in html_lower:
            hits.append(RuleHit(
                category_id='DP-4',
                category='Disguised Ads',
                severity='high',
                evidence=f'Native ad network detected: {label}',
                location='Page <script> / external resources',
                rule='native_ad_network_script',
                confidence=0.75,
            ))

    for domain, label in GENERAL_AD_NETWORKS:
        if domain in html_lower:
            hits.append(RuleHit(
                category_id='DP-4',
                category='Disguised Ads',
                severity='medium',
                evidence=f'Ad network script detected: {label}',
                location='Page <script> / external resources',
                rule='ad_network_script',
                confidence=0.55,
            ))

    return hits


# ── DP-5: Forced Continuity ───────────────────────────────────────────────────

def detect_forced_continuity(page) -> list[RuleHit]:
    """
    Free trials with auto-renewal and difficult cancellation.
    """
    hits = []

    FREE_TRIAL_PATTERNS = [
        r'free\s+trial',
        r'try\s+(?:it\s+)?free',
        r'(\d+)[\s-]day\s+free',
        r'first\s+(?:month|year|30\s+days)\s+free',
    ]

    has_trial = any(
        re.search(p, page.visible_text, re.IGNORECASE)
        for p in FREE_TRIAL_PATTERNS
    )
    has_payment_field = any(
        any(k in f.get('name', '').lower()
            for k in ['card', 'credit', 'payment', 'billing', 'cvv', 'expir'])
        for form in page.forms
        for f in form.get('fields', [])
    )

    if has_trial and has_payment_field:
        hits.append(RuleHit(
            category_id='DP-5',
            category='Forced Continuity',
            severity='high',
            evidence='Free trial offer present alongside payment/card form fields',
            location='Page text + form fields',
            rule='free_trial_with_payment_form',
            confidence=0.82,
        ))

    CANCEL_HARD_PATTERNS = [
        (r'call (?:us )?to cancel',              'Cancellation requires a phone call', 'high'),
        (r'cancel (?:by|via) (?:mail|post|letter)', 'Cancellation requires physical mail', 'high'),
        (r'(?:30|60|90)[\s-]day(?:s)? notice',  'Long cancellation notice period', 'high'),
        (r'non[\s-]?refundable',                 'Non-refundable charge', 'medium'),
        (r'cancel anytime',                      'Cancel anytime (verify flow depth)', 'low'),
    ]

    for pattern, desc, severity in CANCEL_HARD_PATTERNS:
        if re.search(pattern, page.visible_text, re.IGNORECASE):
            if not _is_cookie_context(page.visible_text[:500]):
                hits.append(RuleHit(
                    category_id='DP-5',
                    category='Forced Continuity',
                    severity=severity,
                    evidence=desc,
                    location='Page text / terms',
                    rule='cancellation_friction',
                ))

    return hits


# ── DP-6: Urgency / Scarcity ──────────────────────────────────────────────────

def detect_urgency_scarcity(page) -> list[RuleHit]:
    """
    Artificial time pressure and false scarcity claims.

    v2 fixes:
    - Strip cookie consent sentences before matching — prevents "necessary only"
      and cookie banner text from triggering false positives on gov.uk, BBC etc.
    - Added minimum match length guard (>8 chars of context)
    - Added page-title exclusion — do not match against the first 200 chars
      if they appear to be navigation/title text
    - "only" pattern now requires numeric context to fire
    """
    hits = []

    # Pre-filter: remove cookie consent sentences
    clean_text = _strip_cookie_sentences(page.visible_text)

    # Also skip the first 150 chars which is often page title/nav
    clean_text = clean_text[150:] if len(clean_text) > 150 else clean_text

    if len(clean_text) < 20:
        return hits

    URGENCY_PATTERNS = [
        # Must include a number to reduce false positives on "only"
        (r'only\s+(\d+)\s+left(?:\s+in\s+stock)?',     'Low stock claim',          'high'),
        (r'(\d+)\s+(?:people\s+)?(?:viewing|watching)',  'Social proof urgency',     'medium'),
        (r'(?:offer|deal|sale|discount)\s+ends?\s+(?:in|at|on|soon|today|tonight|midnight)',
                                                          'Offer expiry language',    'high'),
        (r'limited[\s-]time\s+(?:offer|deal|only)',       'Limited time offer',       'medium'),
        (r'hurry[!,.]',                                   '"Hurry" urgency language', 'medium'),
        (r'(?:selling|going)\s+fast',                     '"Selling fast" claim',     'medium'),
        (r'(\d+)\s+(?:sold|bought)\s+(?:today|this week|recently)',
                                                          'Recent sales count',       'low'),
        (r'today\s+only',                                 '"Today only" offer',       'high'),
        (r'flash\s+sale',                                 'Flash sale language',      'medium'),
        (r'(\d+)\s+hours?\s+(?:left|only|remaining)',     'Countdown hours',          'high'),
        (r'(?:expires?|expiring)\s+(?:soon|today|tonight|in \d+)',
                                                          'Expiry imminent',          'high'),
    ]

    for pattern, desc, severity in URGENCY_PATTERNS:
        m = re.search(pattern, clean_text, re.IGNORECASE)
        if m:
            start   = max(0, m.start() - 40)
            end     = min(len(clean_text), m.end() + 60)
            context = clean_text[start:end].strip()

            # Skip very short or cookie-context matches
            if len(context) < 8 or _is_cookie_context(context):
                continue

            hits.append(RuleHit(
                category_id='DP-6',
                category='Urgency / Scarcity',
                severity=severity,
                evidence=f'"{_excerpt(context)}"',
                location='Page text / product listing',
                rule='urgency_scarcity_language',
            ))

    # Countdown-like elements flagged by the scraper
    for el in page.countdown_like_elements[:3]:
        if _is_cookie_context(el) or len(el) < 8:
            continue
        hits.append(RuleHit(
            category_id='DP-6',
            category='Urgency / Scarcity',
            severity='high',
            evidence=f'"{_excerpt(el)}"',
            location='Countdown / timer element',
            rule='countdown_element',
            confidence=0.80,
        ))

    return hits


# ── Public API ────────────────────────────────────────────────────────────────

ALL_RULES = [
    detect_misdirection,
    detect_hidden_costs,
    detect_confirmshaming,
    detect_disguised_ads,
    detect_forced_continuity,
    detect_urgency_scarcity,
]


def run_all_rules(page) -> list[RuleHit]:
    """Run every rule against the scraped page and return all hits."""
    hits = []
    for rule_fn in ALL_RULES:
        try:
            hits.extend(rule_fn(page))
        except Exception as e:
            print(f"[rules] Warning: {rule_fn.__name__} failed: {e}")
    return hits
