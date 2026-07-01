// src/pages/LoadingPage.js
import React, { useEffect, useState } from 'react';

const STEPS = [
  { label: 'Fetching page',              duration: 600 },
  { label: 'Rendering JavaScript',       duration: 900 },
  { label: 'Extracting DOM & text',      duration: 500 },
  { label: 'Running rule-based checks',  duration: 400 },
  { label: 'Running ML classifier',      duration: 700 },
  { label: 'Building report',            duration: 200 },
];

export default function LoadingPage({ url }) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    let i = 0;
    function advance() {
      if (i < STEPS.length - 1) {
        i++;
        setStep(i);
        setTimeout(advance, STEPS[i].duration);
      }
    }
    const t = setTimeout(advance, STEPS[0].duration);
    return () => clearTimeout(t);
  }, []);

  const displayUrl = url.replace(/^https?:\/\//, '').split('/')[0];

  return (
    <main style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: 32 }}>
      <div style={{ width: '100%', maxWidth: 440, textAlign: 'center' }}>

        {/* Animated scan icon */}
        <div style={{ position: 'relative', width: 72, height: 72, margin: '0 auto 28px' }}>
          <div style={{
            width: 72, height: 72, borderRadius: '50%',
            border: '2px solid var(--accent-border)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <path d="M14 3L25 8V14C25 20 20 25.5 14 27C8 25.5 3 20 3 14V8L14 3Z"
                stroke="var(--accent)" strokeWidth="2" strokeLinejoin="round" />
              <path d="M9 14L12.5 17.5L19 10.5"
                stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          {/* Spinning ring */}
          <div style={{
            position: 'absolute', top: -4, left: -4,
            width: 80, height: 80, borderRadius: '50%',
            border: '2px solid transparent',
            borderTopColor: 'var(--accent)',
            animation: 'spin 1.2s linear infinite',
          }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>

        <h2 style={{ fontSize: 18, fontWeight: 600, color: 'var(--navy-900)', marginBottom: 6 }}>
          Analysing
        </h2>
        <p style={{
          fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--accent)',
          background: 'var(--accent-light)', border: '1px solid var(--accent-border)',
          borderRadius: 20, display: 'inline-block', padding: '4px 14px', marginBottom: 32,
        }}>
          {displayUrl}
        </p>

        {/* Steps */}
        <div style={{ textAlign: 'left', background: 'var(--white)', border: '1px solid var(--grey-100)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
          {STEPS.map((s, i) => {
            const done    = i < step;
            const active  = i === step;
            const pending = i > step;
            return (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '11px 16px',
                borderBottom: i < STEPS.length - 1 ? '1px solid var(--grey-100)' : 'none',
                background: active ? 'var(--accent-light)' : 'transparent',
                transition: 'background .2s',
              }}>
                {/* Status icon */}
                {done ? (
                  <span style={{ width: 18, height: 18, borderRadius: '50%', background: 'var(--green-dot)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 5L4.5 7.5L8 3" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
                  </span>
                ) : active ? (
                  <span style={{ width: 18, height: 18, borderRadius: '50%', border: '2px solid var(--accent)', borderTopColor: 'transparent', animation: 'spin 0.8s linear infinite', flexShrink: 0 }} />
                ) : (
                  <span style={{ width: 18, height: 18, borderRadius: '50%', border: '1.5px solid var(--grey-200)', flexShrink: 0 }} />
                )}
                <span style={{
                  fontSize: 13,
                  color: done ? 'var(--grey-600)' : active ? 'var(--navy-900)' : 'var(--grey-400)',
                  fontWeight: active ? 500 : 400,
                }}>
                  {s.label}
                </span>
              </div>
            );
          })}
        </div>

        <p style={{ marginTop: 16, fontSize: 12, color: 'var(--grey-400)' }}>
          This usually takes 10–30 seconds for a typical page.
        </p>
      </div>
    </main>
  );
}
