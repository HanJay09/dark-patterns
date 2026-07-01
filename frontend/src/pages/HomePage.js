// src/pages/HomePage.js
import React, { useState } from 'react';

const EXAMPLE_URLS = [
  'https://amazon.co.uk',
  'https://booking.com',
  'https://linkedin.com',
  'https://netflix.com',
];

const CATEGORIES = [
  { id: 'DP-1', icon: '👁', label: 'Misdirection',       desc: 'Visual tricks that steer you the wrong way' },
  { id: 'DP-2', icon: '💸', label: 'Hidden costs',       desc: 'Fees revealed only at the last moment' },
  { id: 'DP-3', icon: '😔', label: 'Confirmshaming',     desc: 'Guilt-trip language on opt-out buttons' },
  { id: 'DP-4', icon: '🎭', label: 'Disguised ads',      desc: 'Ads styled to look like real content' },
  { id: 'DP-5', icon: '🔄', label: 'Forced continuity',  desc: 'Hard-to-cancel subscriptions & auto-renewals' },
  { id: 'DP-6', icon: '⏱',  label: 'Urgency / scarcity', desc: 'Fake countdowns and "only X left" claims' },
];

export default function HomePage({ onSubmit, loading }) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  function validate(val) {
    try { new URL(val); return true; } catch { return false; }
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (!url.trim()) { setError('Please enter a URL.'); return; }
    if (!validate(url.trim())) { setError('That doesn\'t look like a valid URL. Try including https://'); return; }
    setError('');
    onSubmit(url.trim());
  }

  return (
    <main style={{ maxWidth: 680, margin: '0 auto', padding: '48px 32px' }}>
      {/* Hero */}
      <div style={{ marginBottom: 40 }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          background: 'var(--accent-light)', color: 'var(--accent)',
          border: '1px solid var(--accent-border)', borderRadius: 20,
          fontSize: 11, fontWeight: 500, padding: '4px 10px', marginBottom: 16,
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)' }} />
          MSc Research Prototype
        </div>
        <h1 style={{
          fontSize: 32, fontWeight: 600, letterSpacing: '-0.03em',
          color: 'var(--navy-900)', lineHeight: 1.25, marginBottom: 12,
        }}>
          Detect dark patterns<br />
          <span style={{ color: 'var(--accent)' }}>on any website</span>
        </h1>
        <p style={{ fontSize: 15, color: 'var(--grey-600)', lineHeight: 1.7, maxWidth: 480 }}>
          Enter a URL and DarkDetect will crawl the page, run rule-based and ML
          analysis across 6 dark pattern categories, and give you a plain-English report.
        </p>
      </div>

      {/* URL input form */}
      <form onSubmit={handleSubmit} style={{ marginBottom: 40 }}>
        <div style={{
          background: 'var(--white)', border: `1.5px solid ${error ? 'var(--red-dot)' : 'var(--grey-200)'}`,
          borderRadius: 'var(--radius-lg)', padding: '4px 4px 4px 16px',
          display: 'flex', alignItems: 'center', gap: 8,
          boxShadow: 'var(--shadow-md)', transition: 'border-color .15s',
        }}
          onClick={e => e.currentTarget.querySelector('input').focus()}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0, color: 'var(--grey-400)' }}>
            <path d="M8 1.5C4.41 1.5 1.5 4.41 1.5 8S4.41 14.5 8 14.5 14.5 11.59 14.5 8 11.59 1.5 8 1.5Z"
              stroke="currentColor" strokeWidth="1.2" />
            <path d="M5.5 8C5.5 6.07 6.07 4.5 8 4.5C9.93 4.5 10.5 6.07 10.5 8C10.5 9.93 9.93 11.5 8 11.5C6.07 11.5 5.5 9.93 5.5 8Z"
              stroke="currentColor" strokeWidth="1.2" />
            <line x1="1.5" y1="8" x2="14.5" y2="8" stroke="currentColor" strokeWidth="1.2" />
          </svg>
          <input
            type="text"
            value={url}
            onChange={e => { setUrl(e.target.value); setError(''); }}
            placeholder="https://example.com"
            disabled={loading}
            style={{
              flex: 1, border: 'none', outline: 'none', fontSize: 14,
              fontFamily: 'var(--font-mono)', color: 'var(--navy-900)',
              background: 'transparent', padding: '10px 0',
            }}
          />
          <button
            type="submit"
            disabled={loading}
            style={{
              background: loading ? 'var(--grey-200)' : 'var(--accent)',
              color: loading ? 'var(--grey-400)' : 'var(--white)',
              border: 'none', borderRadius: 10, padding: '10px 20px',
              fontSize: 13, fontWeight: 500, transition: 'background .15s',
              whiteSpace: 'nowrap',
            }}
          >
            {loading ? 'Analysing…' : 'Analyse →'}
          </button>
        </div>
        {error && (
          <p style={{ marginTop: 8, fontSize: 12, color: 'var(--red-text)' }}>{error}</p>
        )}

        {/* Example URLs */}
        <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 11, color: 'var(--grey-400)' }}>Try:</span>
          {EXAMPLE_URLS.map(u => (
            <button key={u} type="button"
              onClick={() => { setUrl(u); setError(''); }}
              style={{
                fontSize: 11, padding: '3px 10px', borderRadius: 20,
                border: '1px solid var(--grey-200)', background: 'var(--white)',
                color: 'var(--grey-600)', cursor: 'pointer',
                fontFamily: 'var(--font-mono)',
                transition: 'border-color .12s, color .12s',
              }}
            >
              {u.replace('https://', '')}
            </button>
          ))}
        </div>
      </form>

      {/* Category cards */}
      <div>
        <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--grey-400)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 16 }}>
          What we detect
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10 }}>
          {CATEGORIES.map(cat => (
            <div key={cat.id} style={{
              background: 'var(--white)', border: '1px solid var(--grey-100)',
              borderRadius: 'var(--radius-md)', padding: '14px 16px',
              display: 'flex', gap: 12, alignItems: 'flex-start',
            }}>
              <span style={{ fontSize: 20, lineHeight: 1 }}>{cat.icon}</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--navy-900)', marginBottom: 2 }}>
                  {cat.label}
                  <span style={{ fontSize: 10, color: 'var(--grey-400)', fontFamily: 'var(--font-mono)', marginLeft: 6 }}>{cat.id}</span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--grey-600)', lineHeight: 1.5 }}>{cat.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
