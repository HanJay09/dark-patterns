// src/App.js
import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import HomePage from './pages/HomePage';
import LoadingPage from './pages/LoadingPage';
import ReportPage from './pages/ReportPage';
import HistoryPage, { saveToHistory } from './pages/HistoryPage';
import { analyseUrl, mockAnalyse } from './utils/api';

const USE_MOCK = false; // ← flip to true to use mock data without backend

export default function App() {
  const [view, setView]     = useState('home');   // 'home' | 'loading' | 'report' | 'history'
  const [url, setUrl]       = useState('');
  const [result, setResult] = useState(null);
  const [error, setError]   = useState('');
  const [page, setPage]     = useState('home');   // sidebar nav state

  async function handleSubmit(submittedUrl) {
    setUrl(submittedUrl);
    setError('');
    setView('loading');

    try {
      const fn   = USE_MOCK ? mockAnalyse : analyseUrl;
      const data = await fn(submittedUrl);
      setResult(data);
      saveToHistory(data);   // persist to localStorage
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

  function handleNavPage(p) {
    setPage(p);
    if (p === 'history') setView('history');
    if (p === 'home')    setView(result ? 'report' : 'home');
  }

  function handleReanalyse(reUrl) {
    setPage('home');
    handleSubmit(reUrl);
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar page={page} setPage={handleNavPage} result={result} />

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {/* Error banner */}
        {error && (
          <div style={{
            background: 'var(--red-bg)', border: '1px solid var(--red-border)',
            color: 'var(--red-text)', padding: '12px 24px', fontSize: 13,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span>⚠ {error}</span>
            <button onClick={() => setError('')} style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--red-text)', fontSize: 16,
            }}>×</button>
          </div>
        )}

        {view === 'home'    && <HomePage onSubmit={handleSubmit} loading={false} />}
        {view === 'loading' && <LoadingPage url={url} />}
        {view === 'report'  && <ReportPage result={result} onReset={handleReset} />}
        {view === 'history' && <HistoryPage onReanalyse={handleReanalyse} />}
      </div>
    </div>
  );
}
