"""
detection_engine/rules.py

Rule-based heuristics for detecting all 6 dark pattern categories.

Each rule function receives the ScrapedPage output and returns a list of
Finding dicts. Rules are deliberately simple and transparent — they act
as a high-recall baseline that the ML classifier then filters/scores.

Why rules first?
Per the project's design rationale, rule-based detection gives:
  1. Explainability — every finding has a traceable trigger
  2. A precision/recall baseline to compare the ML classifier against
  3. Fallback coverage for categories where labelled data is thin
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuleHit:
    """A single instance of a detected dark pattern."""
    category_id:  str
    category:     str
    severity:     str          # 'high' | 'medium' | 'low'
    evidence:     str          # the exact text / attribute that triggered the rule
    location:     str          # human-readable description of where on the page
    rule:         str          # which rule fired (for transparency / evaluation)
    confidence:   float = 0.75 # rule-based hits default to 0.75


# ── Helpers ──────────────────────────────────────────────────────────────────

def _find_all_text_matches(pattern: str, text: str, flags=re.IGNORECASE) -> list[str]:
    return re.findall(pattern, text, flags)


def _excerpt(text: str, max_len: int = 120) -> str:
    return text[:max_len].strip() + ('…' if len(text) > max_len else '')


# ── DP-1: Misdirection ───────────────────────────────────────────────────────

def detect_misdirection(page) -> list[RuleHit]:
    """
    Signals:
    - Decline/cancel buttons using visually minimising language
    - Asymmetric button pairs where one choice is buried
    """
    hits = []
    DECLINE_PATTERNS = [
        r"no[\s,]*thanks?",
        r"maybe later",
        r"skip(?: this)?",
        r"not (now|interested|today)",
        r"i('ll)? decide later",
        r"remind me later",
        r"close",
        r"dismiss",
    ]
    combined = '|'.join(DECLINE_PATTERNS)

    for btn in page.buttons:
        text = btn.get('text', '')
        if re.search(combined, text, re.IGNORECASE) and len(text) < 60:
            hits.append(RuleHit(
                category_id='DP-1',
                category='Misdirection',
                severity='medium',
                evidence=f'"{text}"',
                location=f'Button / CTA element on page',
                rule='decline_button_language',
            ))

    return hits


# ── DP-2: Hidden Costs ───────────────────────────────────────────────────────

def detect_hidden_costs(page) -> list[RuleHit]:
    """
    Signals:
    - Subscription or fee language appearing in forms or small print
    - Text patterns suggesting costs added late in a flow
    """
    hits = []
    COST_PATTERNS = [
        (r'\+\s*(?:shipping|delivery|handling|service fee|booking fee)',
         'Extra fee added to price', 'high'),
        (r'auto(?:matically)?[\s-]renew',
         'Auto-renewal language', 'high'),
        (r'cancel anytime',
         '"Cancel anytime" (potential forced continuity indicator)', 'medium'),
        (r'(?:taxes?|vat|gst)\s+(?:not included|excluded|extra|added)',
         'Tax excluded from displayed price', 'medium'),
        (r'processing fee',
         'Processing fee mentioned', 'medium'),
    ]

    for pattern, desc, severity in COST_PATTERNS:
        matches = _find_all_text_matches(pattern, page.visible_text)
        for m in matches[:3]:  # cap at 3 per pattern
            hits.append(RuleHit(
                category_id='DP-2',
                category='Hidden Costs',
                severity=severity,
                evidence=_excerpt(m),
                location='Page text',
                rule='hidden_cost_language',
            ))

    # Check form fields for hidden subscription indicators
    for form in page.forms:
        for field_info in form.get('fields', []):
            name = field_info.get('name', '').lower()
            if any(k in name for k in ['subscribe', 'recurring', 'membership']):
                hits.append(RuleHit(
                    category_id='DP-2',
                    category='Hidden Costs',
                    severity='high',
                    evidence=f'Form field name: "{field_info["name"]}"',
                    location=f'Form (action: {form.get("action", "unknown")})',
                    rule='subscription_form_field',
                ))

    return hits


# ── DP-3: Confirmshaming ─────────────────────────────────────────────────────

def detect_confirmshaming(page) -> list[RuleHit]:
    """
    Signals:
    - Opt-out button text uses guilt-inducing or self-deprecating language
    - Pattern: "No thanks, I don't want [positive thing]"
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
            hits.append(RuleHit(
                category_id='DP-3',
                category='Confirmshaming',
                severity='high',
                evidence=f'"{_excerpt(m)}"',
                location='Opt-out / decline button',
                rule='confirmshaming_button_text',
                confidence=0.85,
            ))

    # Also check visible text for modal/popup dismiss language
    MODAL_PATTERNS = [
        r"no[\s,]+thanks?,?\s+i don'?t want.{0,80}",
        r"no[\s,]+i(?:'ll)? pass on.{0,60}",
    ]
    for pattern in MODAL_PATTERNS:
        matches = re.findall(pattern, page.visible_text, re.IGNORECASE)
        for m in matches[:2]:
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


# ── DP-4: Disguised Ads ──────────────────────────────────────────────────────

def detect_disguised_ads(page) -> list[RuleHit]:
    """
    Signals:
    - Known ad-network script tags or class names in the page HTML
    - Elements labelled 'sponsored' or 'promoted' styled like organic content
    """
    hits = []

    AD_NETWORKS = [
        ('doubleclick.net',   'Google DoubleClick ad script'),
        ('googlesyndication', 'Google AdSense'),
        ('amazon-adsystem',   'Amazon Advertising'),
        ('outbrain',          'Outbrain native ads'),
        ('taboola',           'Taboola native ads'),
        ('criteo',            'Criteo retargeting ads'),
        ('adsrvr.org',        'The Trade Desk ads'),
        ('moatads',           'Moat ad measurement'),
    ]

    html_lower = page.html.lower()
    for domain, label in AD_NETWORKS:
        if domain in html_lower:
            hits.append(RuleHit(
                category_id='DP-4',
                category='Disguised Ads',
                severity='medium',
                evidence=f'Ad network script detected: {label}',
                location='Page <script> tags / external resources',
                rule='ad_network_script',
                confidence=0.65,  # presence of script ≠ definitely disguised
            ))

    # 'Sponsored' or 'promoted' labels in visible text
    SPONSOR_PATTERNS = [r'\bsponsored\b', r'\bpromoted\b', r'\badvertisement\b', r'\bad\b']
    for pattern in SPONSOR_PATTERNS:
        if re.search(pattern, page.visible_text, re.IGNORECASE):
            hits.append(RuleHit(
                category_id='DP-4',
                category='Disguised Ads',
                severity='low',
                evidence=f'Label "{pattern.strip(chr(92)+"b")}" found in page text',
                location='Page text / content area',
                rule='sponsored_label_present',
                confidence=0.55,
            ))
            break  # one hit is enough for this signal

    return hits


# ── DP-5: Forced Continuity ──────────────────────────────────────────────────

def detect_forced_continuity(page) -> list[RuleHit]:
    """
    Signals:
    - Free trial language paired with card/payment form fields
    - Cancellation difficulty language
    - Auto-renewal without prominent disclosure
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
        any(k in f.get('name', '').lower() for k in ['card', 'credit', 'payment', 'billing', 'cvv', 'expir'])
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
        (r'call (?:us )?to cancel',           'Cancellation requires a phone call', 'high'),
        (r'cancel (?:by|via) (?:mail|post|letter)', 'Cancellation requires physical mail', 'high'),
        (r'(?:30|60|90)[\s-]day(?:s)? notice',     'Long cancellation notice period required', 'high'),
        (r'non[\s-]?refundable',                    'Non-refundable charge language', 'medium'),
    ]

    for pattern, desc, severity in CANCEL_HARD_PATTERNS:
        if re.search(pattern, page.visible_text, re.IGNORECASE):
            hits.append(RuleHit(
                category_id='DP-5',
                category='Forced Continuity',
                severity=severity,
                evidence=desc,
                location='Page text / terms',
                rule='cancellation_friction',
            ))

    return hits


# ── DP-6: Urgency / Scarcity ─────────────────────────────────────────────────

def detect_urgency_scarcity(page) -> list[RuleHit]:
    """
    Signals:
    - Countdown timer language
    - Low stock claims
    - Limited-time offer language
    """
    hits = []

    URGENCY_PATTERNS = [
        (r'only\s+(\d+)\s+left(?:\s+in\s+stock)?',     'Low stock claim',          'high'),
        (r'(\d+)\s+(?:people\s+)?(?:viewing|watching)',  'Social proof urgency',     'medium'),
        (r'(?:offer\s+)?ends?\s+(?:in|at|on)',           'Offer expiry language',    'high'),
        (r'(?:deal|sale|discount)\s+ends?\s+(?:soon|today|tonight|midnight)',
                                                          'Sale ending soon',         'high'),
        (r'limited[\s-]time\s+(?:offer|deal|only)',       'Limited time offer',       'medium'),
        (r'hurry[!,.]',                                   '"Hurry" urgency language', 'medium'),
        (r'(?:selling|going)\s+fast',                     '"Selling fast" claim',     'medium'),
        (r'(\d+)\s+(?:sold|bought)\s+(?:today|this week|recently)',
                                                          'Recent sales count',       'low'),
        (r'today\s+only',                                 '"Today only" offer',       'high'),
        (r'flash\s+sale',                                 'Flash sale language',      'medium'),
    ]

    for pattern, desc, severity in URGENCY_PATTERNS:
        matches = re.findall(pattern, page.visible_text, re.IGNORECASE)
        if matches:
            # Grab the surrounding context for the first match
            m = re.search(pattern, page.visible_text, re.IGNORECASE)
            start = max(0, m.start() - 40)
            end   = min(len(page.visible_text), m.end() + 40)
            context = page.visible_text[start:end].strip()

            hits.append(RuleHit(
                category_id='DP-6',
                category='Urgency / Scarcity',
                severity=severity,
                evidence=f'"{_excerpt(context)}"',
                location='Page text / product listing',
                rule='urgency_scarcity_language',
            ))

    # Also check countdown-like elements flagged by the scraper
    for el in page.countdown_like_elements[:3]:
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
        except Exception as e:  # noqa: BLE001
            # One bad rule must never silently kill the whole engine
            print(f"[rules] Warning: {rule_fn.__name__} failed: {e}")
    return hits
