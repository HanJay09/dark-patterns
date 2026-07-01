// src/utils/api.js
// All communication with the FastAPI backend lives here.
// Base URL reads from the env var; falls back to localhost for dev.

const BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * POST /analyse
 * Sends a URL to the backend and returns the detection report.
 *
 * @param {string} url - The target website URL to analyse
 * @returns {Promise<AnalysisResult>}
 */
export async function analyseUrl(url) {
  const res = await fetch(`${BASE}/analyse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `Server error ${res.status}`);
  }

  return res.json();
}

/**
 * Mock response — used during frontend development before the backend is ready.
 * Call mockAnalyse(url) instead of analyseUrl(url) while building the UI.
 */
export async function mockAnalyse(url) {
  await new Promise(r => setTimeout(r, 2800)); // simulate network delay
  return {
    url,
    analysed_at: new Date().toISOString(),
    total_found: 3,
    overall_risk: 'high',
    confidence: 0.87,
    categories_checked: 6,
    findings: [
      {
        id: 'DP-6',
        category: 'Urgency / Scarcity',
        severity: 'high',
        count: 2,
        instances: [
          {
            evidence: '"Only 3 left in stock — order soon"',
            location: 'Product listing — above add-to-basket button',
          },
          {
            evidence: '"Deal ends in 02:14:33"',
            location: 'Banner — top of page',
          },
        ],
        explanation:
          'These messages create artificial time or stock pressure. Research shows ' +
          'that fake scarcity claims are among the most commonly deployed dark patterns ' +
          'on e-commerce sites (Mathur et al., 2019). The goal is to prevent comparison ' +
          'shopping and force impulsive decisions.',
      },
      {
        id: 'DP-1',
        category: 'Misdirection',
        severity: 'high',
        count: 1,
        instances: [
          {
            evidence:
              'Primary CTA: "Add to basket" (48px, #FF9900, high contrast). ' +
              'Decline: "No thanks" (11px, #767676, below fold).',
            location: 'Product page — action area',
          },
        ],
        explanation:
          'The visual hierarchy strongly favours the commercially beneficial action. ' +
          'The decline option is rendered in a colour that fails WCAG AA contrast ' +
          'requirements and is positioned outside the normal reading flow.',
      },
      {
        id: 'DP-3',
        category: 'Confirmshaming',
        severity: 'medium',
        count: 1,
        instances: [
          {
            evidence: '"No thanks, I don\'t want to save money"',
            location: 'Newsletter sign-up modal — dismiss button',
          },
        ],
        explanation:
          'The opt-out label is framed to make users feel foolish for declining, ' +
          'rather than offering a neutral choice. This exploits social norms around ' +
          'rationality to coerce consent.',
      },
    ],
  };
}
