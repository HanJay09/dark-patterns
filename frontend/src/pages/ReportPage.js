// src/pages/ReportPage.js
import React, { useState } from 'react';

const SEV_STYLES = {
  high:   { bg: 'var(--red-bg)',   border: 'var(--red-border)',   text: 'var(--red-text)',   dot: 'var(--red-dot)',   label: 'High' },
  medium: { bg: 'var(--amber-bg)', border: 'var(--amber-border)', text: 'var(--amber-text)', dot: 'var(--amber-dot)', label: 'Medium' },
  low:    { bg: 'var(--green-bg)', border: 'var(--green-border)', text: 'var(--green-text)', dot: 'var(--green-dot)', label: 'Low' },
};

const RISK_STYLES = {
  high:   { label: 'High risk',   color: 'var(--red-text)',   bg: 'var(--red-bg)',   border: 'var(--red-border)' },
  medium: { label: 'Medium risk', color: 'var(--amber-text)', bg: 'var(--amber-bg)', border: 'var(--amber-border)' },
  low:    { label: 'Low risk',    color: 'var(--green-text)', bg: 'var(--green-bg)', border: 'var(--green-border)' },
  none:   { label: 'No patterns', color: 'var(--green-text)', bg: 'var(--green-bg)', border: 'var(--green-border)' },
};

const RULE_LABELS = {
  urgency_scarcity_language: 'Urgency/scarcity language detected',
  countdown_element:         'Countdown or timer element detected',
  confirmshaming_button_text:'Guilt-inducing opt-out button text',
  confirmshaming_modal_text: 'Guilt-inducing modal dismiss text',
  decline_button_language:   'Misdirecting decline button',
  weak_decline_button:       'Possible misdirection on dismiss button',
  hidden_cost_language:      'Hidden or additional cost language',
  subscription_form_field:   'Subscription-related form field',
  native_ad_network_script:  'Native ad network script (e.g. Taboola)',
  ad_network_script:         'General ad network script detected',
  free_trial_with_payment_form: 'Free trial with payment form (forced continuity)',
  cancellation_friction:     'Cancellation friction language',
  ml_classifier:             'Detected by ML text classifier',
};

function ConfidenceBar({ value }) {
  const pct = Math.round(value * 100);
  const color = value >= 0.8 ? 'var(--green-dot)' : value >= 0.6 ? 'var(--amber-dot)' : 'var(--red-dot)';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ flex: 1, height: 4, background: 'var(--grey-100)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 2 }} />
      </div>
      <span style={{ fontSize: 10, color: 'var(--grey-400)', minWidth: 28 }}>{pct}%</span>
    </div>
  );
}

function InstanceCard({ inst, borderColor }) {
  const [showExplain, setShowExplain] = useState(false);

  return (
    <div style={{
      background: 'var(--grey-50)', border: '1px solid var(--grey-100)',
      borderLeft: `3px solid ${borderColor}`,
      borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
      padding: '10px 12px', marginBottom: 8,
    }}>
      {/* Evidence text */}
      <div style={{
        fontFamily: 'var(--font-mono)', fontSize: 12,
        color: 'var(--navy-900)', lineHeight: 1.6, marginBottom: 8,
        wordBreak: 'break-word',
      }}>
        {inst.evidence}
      </div>

      {/* Metadata row */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
        {/* Location */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
            <path d="M5.5 1C3.57 1 2 2.57 2 4.5C2 7 5.5 10 5.5 10C5.5 10 9 7 9 4.5C9 2.57 7.43 1 5.5 1Z"
              stroke="var(--grey-400)" strokeWidth="1" fill="none" />
            <circle cx="5.5" cy="4.5" r="1.2" stroke="var(--grey-400)" strokeWidth="1" />
          </svg>
          <span style={{ fontSize: 11, color: 'var(--grey-400)' }}>{inst.location}</span>
        </div>

        {/* Rule that fired + explain toggle */}
        {inst.rule && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
              <circle cx="5.5" cy="5.5" r="4.5" stroke="var(--grey-400)" strokeWidth="1" />
              <path d="M5.5 3.5V6M5.5 7.5V8" stroke="var(--grey-400)" strokeWidth="1.2" strokeLinecap="round" />
            </svg>
            <span style={{ fontSize: 11, color: 'var(--grey-400)' }}>
              {RULE_LABELS[inst.rule] || inst.rule}
            </span>
            {inst.evidence_explanation && (
              <button onClick={() => setShowExplain(e => !e)} style={{
                fontSize: 10, padding: '1px 7px', borderRadius: 20, cursor: 'pointer',
                border: '1px solid var(--accent-border)', background: showExplain ? 'var(--accent-light)' : 'transparent',
                color: 'var(--accent)', marginLeft: 4,
              }}>
                {showExplain ? 'Hide' : 'What does this mean?'}
              </button>
            )}
          </div>
        )}

        {/* Confidence bar */}
        {inst.confidence !== undefined && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 'auto' }}>
            <span style={{ fontSize: 10, color: 'var(--grey-400)' }}>Confidence</span>
            <div style={{ width: 64 }}>
              <ConfidenceBar value={inst.confidence} />
            </div>
          </div>
        )}
      </div>

      {/* Evidence explanation — shown when toggled */}
      {showExplain && inst.evidence_explanation && (
        <div style={{
          marginTop: 10, padding: '10px 12px',
          background: 'var(--accent-light)', border: '1px solid var(--accent-border)',
          borderRadius: 'var(--radius-sm)', fontSize: 12,
          color: 'var(--navy-900)', lineHeight: 1.7,
        }}>
          <strong style={{ color: 'var(--accent)', display: 'block', marginBottom: 4, fontSize: 11 }}>
            What this means:
          </strong>
          {inst.evidence_explanation}
        </div>
      )}
    </div>
  );
}

function FindingCard({ finding }) {
  const [open, setOpen] = useState(true);
  const sev = SEV_STYLES[finding.severity] || SEV_STYLES.low;

  return (
    <div style={{
      background: 'var(--white)', border: '1px solid var(--grey-100)',
      borderRadius: 'var(--radius-md)', overflow: 'hidden', marginBottom: 12,
    }}>
      {/* Header */}
      <button onClick={() => setOpen(o => !o)} style={{
        width: '100%', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', padding: '14px 16px',
        background: 'none', border: 'none', cursor: 'pointer',
        textAlign: 'left', gap: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 'var(--radius-sm)',
            background: sev.bg, border: `1px solid ${sev.border}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 11, fontWeight: 700, color: sev.text,
            fontFamily: 'var(--font-mono)', flexShrink: 0,
          }}>
            {finding.id}
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--navy-900)' }}>
              {finding.category}
            </div>
            <div style={{ fontSize: 12, color: 'var(--grey-400)' }}>
              {finding.count} {finding.count === 1 ? 'instance' : 'instances'} detected
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
          <span style={{
            fontSize: 11, fontWeight: 500, padding: '3px 10px', borderRadius: 20,
            background: sev.bg, border: `1px solid ${sev.border}`, color: sev.text,
          }}>
            {sev.label}
          </span>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"
            style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform .2s', color: 'var(--grey-400)' }}>
            <path d="M2 5L7 10L12 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </button>

      {/* Body */}
      {open && (
        <div style={{ padding: '0 16px 16px', borderTop: '1px solid var(--grey-100)' }}>

          {/* Evidence instances */}
          <div style={{ marginTop: 14, marginBottom: 12 }}>
            <div style={{
              fontSize: 11, fontWeight: 600, color: 'var(--grey-400)',
              letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 8,
            }}>
              Evidence
            </div>
            {finding.instances.map((inst, i) => (
              <InstanceCard key={i} inst={inst} borderColor={sev.dot} />
            ))}
          </div>

          {/* Explanation */}
          <div style={{ background: 'var(--grey-50)', borderRadius: 'var(--radius-sm)', padding: '12px 14px' }}>
            <div style={{
              fontSize: 11, fontWeight: 600, color: 'var(--grey-400)',
              letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 6,
            }}>
              Why this matters
            </div>
            <p style={{ fontSize: 13, color: 'var(--grey-600)', lineHeight: 1.7 }}>
              {finding.explanation}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ReportPage({ result, onReset }) {
  const risk       = RISK_STYLES[result.overall_risk] || RISK_STYLES.none;
  const displayUrl = result.url.replace(/^https?:\/\//, '');

  function exportJson() {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const a    = document.createElement('a');
    a.href     = URL.createObjectURL(blob);
    a.download = `darkdetect-${displayUrl.split('/')[0]}-${Date.now()}.json`;
    a.click();
  }

  return (
    <main style={{ maxWidth: 680, margin: '0 auto', padding: '32px 32px 64px' }}>

      {/* Back button + timestamp */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <button onClick={onReset} style={{
          display: 'flex', alignItems: 'center', gap: 6, fontSize: 12,
          color: 'var(--grey-400)', background: 'none', border: 'none', cursor: 'pointer',
        }}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M9 11L4 7L9 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Analyse another URL
        </button>
        <span style={{ fontSize: 11, color: 'var(--grey-400)' }}>
          {new Date(result.analysed_at).toLocaleTimeString()}
        </span>
      </div>

      {/* Report header card */}
      <div style={{
        background: 'var(--white)', border: '1px solid var(--grey-100)',
        borderRadius: 'var(--radius-lg)', padding: '20px 24px',
        display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
        gap: 16, marginBottom: 16,
      }}>
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--grey-400)', marginBottom: 4 }}>
            {displayUrl}
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 600, color: 'var(--navy-900)', letterSpacing: '-0.02em' }}>
            {result.total_found === 0
              ? 'No dark patterns detected'
              : `${result.total_found} dark pattern${result.total_found !== 1 ? 's' : ''} detected`}
          </h1>
        </div>
        <div style={{
          background: risk.bg, border: `1px solid ${risk.border}`,
          color: risk.color, fontSize: 12, fontWeight: 600,
          padding: '6px 14px', borderRadius: 20, whiteSpace: 'nowrap', flexShrink: 0,
        }}>
          {risk.label}
        </div>
      </div>

      {/* Summary stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 10, marginBottom: 28 }}>
        {[
          { value: result.total_found,          label: 'Patterns found',     danger: result.total_found > 0 },
          { value: result.categories_checked,   label: 'Categories checked', danger: false },
          { value: result.findings.filter(f => f.severity === 'high').length, label: 'High severity', danger: true },
          { value: `${Math.round(result.confidence * 100)}%`, label: 'Avg confidence', danger: false },
        ].map((stat, i) => (
          <div key={i} style={{
            background: 'var(--white)', border: '1px solid var(--grey-100)',
            borderRadius: 'var(--radius-md)', padding: '14px 16px', textAlign: 'center',
          }}>
            <div style={{
              fontSize: 22, fontWeight: 600, letterSpacing: '-0.02em',
              color: stat.danger && stat.value > 0 ? 'var(--red-dot)' : 'var(--navy-900)',
              marginBottom: 2,
            }}>
              {stat.value}
            </div>
            <div style={{ fontSize: 11, color: 'var(--grey-400)', lineHeight: 1.3 }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Findings */}
      {result.findings.length > 0 ? (
        <div>
          <h2 style={{
            fontSize: 13, fontWeight: 600, color: 'var(--grey-400)',
            letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 14,
          }}>
            Findings — click to expand
          </h2>
          {result.findings.map(f => <FindingCard key={f.id} finding={f} />)}
        </div>
      ) : (
        <div style={{
          textAlign: 'center', padding: '48px 32px',
          background: 'var(--white)', border: '1px solid var(--grey-100)',
          borderRadius: 'var(--radius-lg)',
        }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>✅</div>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--navy-900)', marginBottom: 6 }}>
            No dark patterns found
          </h2>
          <p style={{ fontSize: 13, color: 'var(--grey-600)' }}>
            This page appears clean across all 6 categories.
          </p>
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 10, marginTop: 24 }}>
        <button onClick={exportJson} style={{
          display: 'flex', alignItems: 'center', gap: 6,
          fontSize: 13, padding: '9px 16px', borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--grey-200)', background: 'var(--white)',
          color: 'var(--grey-600)', cursor: 'pointer',
        }}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 10V12H12V10M7 2V9M7 9L4.5 6.5M7 9L9.5 6.5"
              stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Export JSON
        </button>
        <button onClick={onReset} style={{
          display: 'flex', alignItems: 'center', gap: 6,
          fontSize: 13, padding: '9px 16px', borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--accent-border)', background: 'var(--accent-light)',
          color: 'var(--accent)', cursor: 'pointer',
        }}>
          Analyse another URL
        </button>
      </div>

      <p style={{ marginTop: 24, fontSize: 11, color: 'var(--grey-400)', lineHeight: 1.6 }}>
        <strong>Research prototype.</strong> Results are generated by rule-based heuristics and
        a trained ML classifier. Treat findings as a starting point for manual review.
      </p>
    </main>
  );
}
