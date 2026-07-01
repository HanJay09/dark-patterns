// src/App.js
// Root component — manages the global state machine:
//   home → loading → report (and back to home)
//
// To test the UI without a running backend, set USE_MOCK = true below.
// Switch it to false when the FastAPI backend is ready.

import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import HomePage from './pages/HomePage';
import LoadingPage from './pages/LoadingPage';
import ReportPage from './pages/ReportPage';
import { analyseUrl, mockAnalyse } from './utils/api';

const USE_MOCK = true; // ← flip to false once backend is running

export default function App() {
  const [view, setView]     = useState('home');   // 'home' | 'loading' | 'report'
  const [url, setUrl]       = useState('');
  const [result, setResult] = useState(null);
  const [error, setError]   = useState('');
  const [page, setPage]     = useState('home');   // sidebar nav state

  async function handleSubmit(submittedUrl) {
    setUrl(submittedUrl);
    setError('');
    setView('loading');

    try {
      const fn = USE_MOCK ? mockAnalyse : analyseUrl;
      const data = await fn(submittedUrl);
      setResult(data);
      setView('report');
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.');
      setView('home');
    }
  }

  function handleReset() {
    setView('home');
    setUrl('');
    setResult(null);
    setPage('home');
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar page={page} setPage={setPage} result={result} />

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {/* Error banner */}
        {error && (
          <div style={{
            background: 'var(--red-bg)', border: '1px solid var(--red-border)',
            color: 'var(--red-text)', padding: '12px 24px', fontSize: 13,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span>⚠ {error}</span>
            <button onClick={() => setError('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--red-text)', fontSize: 16 }}>×</button>
          </div>
        )}

        {view === 'home'    && <HomePage  onSubmit={handleSubmit} loading={false} />}
        {view === 'loading' && <LoadingPage url={url} />}
        {view === 'report'  && <ReportPage result={result} onReset={handleReset} />}
      </div>
    </div>
  );
}
