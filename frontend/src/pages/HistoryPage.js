// src/pages/HistoryPage.js
import React, { useState, useEffect } from 'react';

const STORAGE_KEY = 'darkdetect_history';
const MAX_HISTORY = 50;

export function saveToHistory(result) {
  try {
    const existing = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    const deduped  = existing.filter(r =>
      !(r.url === result.url && Math.abs(new Date(r.analysed_at) - new Date(result.analysed_at)) < 60000)
    );
    localStorage.setItem(STORAGE_KEY, JSON.stringify([result, ...deduped].slice(0, MAX_HISTORY)));
  } catch (e) { console.warn('Failed to save history:', e); }
}

export function clearHistory() { localStorage.removeItem(STORAGE_KEY); }

const RISK = {
  high:   { color: '#991B1B', bg: '#FEF2F2', border: '#FECACA' },
  medium: { color: '#92400E', bg: '#FFFBEB', border: '#FDE68A' },
  low:    { color: '#14532D', bg: '#F0FDF4', border: '#86EFAC' },
  none:   { color: '#374151', bg: '#F9FAFB', border: '#E5E7EB' },
};

function HistoryEntry({ result, onReanalyse }) {
  const [expanded, setExpanded] = useState(false);
  const risk       = RISK[result.overall_risk] || RISK.none;
  const date       = new Date(result.analysed_at);
  const displayUrl = result.url.replace(/^https?:\/\//, '');

  return (
    <div style={{ background: 'var(--white)', border: '1px solid var(--grey-100)', borderRadius: 'var(--radius-md)', marginBottom: 10, overflow: 'hidden' }}>

      {/* Summary row */}
      <div style={{ padding: '14px 16px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--navy-900)', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: 4 }}>
              {displayUrl}
            </div>
            <div style={{ fontSize: 11, color: 'var(--grey-400)' }}>
              {date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
              {' · '}{date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
              {' · '}{result.total_found} pattern{result.total_found !== 1 ? 's' : ''} found
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            <span style={{ fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 20, background: risk.bg, border: `1px solid ${risk.border}`, color: risk.color, textTransform: 'capitalize' }}>
              {result.overall_risk === 'none' ? 'Clean' : result.overall_risk}
            </span>
            <button onClick={() => onReanalyse(result.url)} style={{ fontSize: 11, padding: '4px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--accent-border)', background: 'var(--accent-light)', color: 'var(--accent)', cursor: 'pointer' }}>
              Re-analyse
            </button>
            <button onClick={() => setExpanded(e => !e)} style={{ fontSize: 11, padding: '4px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--grey-200)', background: 'var(--white)', color: 'var(--grey-600)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}>
              {expanded ? 'Hide' : 'Details'}
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" style={{ transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform .15s' }}>
                <path d="M2 4L5 7L8 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        </div>

        {/* Category chips */}
        {result.findings && result.findings.length > 0 && (
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 10 }}>
            {result.findings.map(f => (
              <span key={f.id} style={{ fontSize: 10, fontWeight: 500, padding: '2px 8px', borderRadius: 20, background: 'var(--grey-100)', color: 'var(--grey-800)', fontFamily: 'var(--font-mono)' }}>
                {f.id} {f.category}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Expanded detail panel */}
      {expanded && (
        <div style={{ borderTop: '1px solid var(--grey-100)', padding: '14px 16px', background: 'var(--grey-50)' }}>
          {(!result.findings || result.findings.length === 0) ? (
            <p style={{ fontSize: 13, color: 'var(--grey-400)' }}>No dark patterns detected on this page.</p>
          ) : result.findings.map(f => {
            const sevBg  = f.severity === 'high' ? '#FEF2F2' : f.severity === 'medium' ? '#FFFBEB' : '#F0FDF4';
            const sevClr = f.severity === 'high' ? '#991B1B' : f.severity === 'medium' ? '#92400E' : '#14532D';
            const sevBdr = f.severity === 'high' ? '#FECACA' : f.severity === 'medium' ? '#FDE68A' : '#86EFAC';
            return (
              <div key={f.id} style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 20, background: sevBg, color: sevClr, border: `1px solid ${sevBdr}`, fontFamily: 'var(--font-mono)' }}>
                    {f.id}
                  </span>
                  <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--navy-900)' }}>{f.category}</span>
                  <span style={{ fontSize: 11, color: 'var(--grey-400)' }}>· {f.count} instance{f.count !== 1 ? 's' : ''}</span>
                </div>
                {f.instances && f.instances.slice(0, 2).map((inst, ii) => (
                  <div key={ii} style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--grey-700)', background: 'var(--white)', border: '1px solid var(--grey-100)', borderRadius: 'var(--radius-sm)', padding: '6px 10px', marginBottom: 4, wordBreak: 'break-word' }}>
                    {inst.evidence}
                    {inst.location && <span style={{ color: 'var(--grey-400)', marginLeft: 8, fontSize: 10 }}>— {inst.location}</span>}
                  </div>
                ))}
                {f.explanation && (
                  <p style={{ fontSize: 12, color: 'var(--grey-600)', lineHeight: 1.6, marginTop: 6 }}>{f.explanation}</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function HistoryPage({ onReanalyse }) {
  const [history, setHistory] = useState([]);
  const [filter,  setFilter]  = useState('all');

  useEffect(() => {
    try { setHistory(JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')); }
    catch { setHistory([]); }
  }, []);

  function handleClear() {
    if (window.confirm('Clear all history? This cannot be undone.')) {
      clearHistory(); setHistory([]);
    }
  }

  const filtered = filter === 'all' ? history : history.filter(r => r.overall_risk === filter);

  return (
    <main style={{ maxWidth: 680, margin: '0 auto', padding: '32px 32px 64px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 600, color: 'var(--navy-900)', letterSpacing: '-0.02em', marginBottom: 4 }}>Analysis History</h1>
          <p style={{ fontSize: 13, color: 'var(--grey-400)' }}>{history.length} {history.length === 1 ? 'analysis' : 'analyses'} stored locally</p>
        </div>
        {history.length > 0 && (
          <button onClick={handleClear} style={{ fontSize: 12, padding: '6px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--grey-200)', background: 'var(--white)', color: 'var(--grey-600)', cursor: 'pointer' }}>
            Clear all
          </button>
        )}
      </div>

      {history.length > 0 && (
        <div style={{ display: 'flex', gap: 6, marginBottom: 20 }}>
          {['all','high','medium','low','none'].map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{ fontSize: 12, padding: '5px 12px', borderRadius: 20, border: '1px solid', cursor: 'pointer', borderColor: filter === f ? 'var(--accent)' : 'var(--grey-200)', background: filter === f ? 'var(--accent-light)' : 'var(--white)', color: filter === f ? 'var(--accent)' : 'var(--grey-600)', textTransform: 'capitalize' }}>
              {f === 'all' ? `All (${history.length})` : f}
            </button>
          ))}
        </div>
      )}

      {history.length === 0 && (
        <div style={{ textAlign: 'center', padding: '64px 32px', background: 'var(--white)', border: '1px solid var(--grey-100)', borderRadius: 'var(--radius-lg)' }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>🕓</div>
          <h2 style={{ fontSize: 16, fontWeight: 500, color: 'var(--navy-900)', marginBottom: 6 }}>No history yet</h2>
          <p style={{ fontSize: 13, color: 'var(--grey-400)' }}>Analyses you run will appear here automatically.</p>
        </div>
      )}

      {filtered.map((result, i) => (
        <HistoryEntry key={i} result={result} onReanalyse={onReanalyse} />
      ))}

      {filtered.length === 0 && history.length > 0 && (
        <div style={{ textAlign: 'center', padding: 32, color: 'var(--grey-400)', fontSize: 13 }}>No analyses matching this filter.</div>
      )}

      <p style={{ marginTop: 24, fontSize: 11, color: 'var(--grey-400)', lineHeight: 1.6 }}>
        History is stored in your browser only and is not sent to any server. It will be cleared if you clear your browser data.
      </p>
    </main>
  );
}
