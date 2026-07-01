// src/components/Sidebar.js
import React from 'react';

const CATEGORIES = [
  { id: 'DP-1', label: 'Misdirection' },
  { id: 'DP-2', label: 'Hidden costs' },
  { id: 'DP-3', label: 'Confirmshaming' },
  { id: 'DP-4', label: 'Disguised ads' },
  { id: 'DP-5', label: 'Forced continuity' },
  { id: 'DP-6', label: 'Urgency / scarcity' },
];

const styles = {
  sidebar: {
    width: 'var(--sidebar-w)',
    minHeight: '100vh',
    background: 'var(--navy-900)',
    display: 'flex',
    flexDirection: 'column',
    flexShrink: 0,
    position: 'sticky',
    top: 0,
    height: '100vh',
    overflowY: 'auto',
  },
  logo: {
    padding: '24px 20px 20px',
    borderBottom: '1px solid var(--navy-700)',
  },
  logoMark: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  logoIcon: {
    width: 28,
    height: 28,
    background: 'var(--accent)',
    borderRadius: 6,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    fontSize: 15,
    fontWeight: 600,
    color: 'var(--white)',
    letterSpacing: '-0.02em',
  },
  logoSub: {
    fontSize: 11,
    color: 'var(--navy-200)',
    paddingLeft: 36,
  },
  nav: {
    padding: '20px 12px',
    flex: 1,
  },
  navLabel: {
    fontSize: 10,
    fontWeight: 600,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: 'var(--navy-400)',
    padding: '0 8px',
    marginBottom: 6,
  },
  navItem: (active) => ({
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '7px 8px',
    borderRadius: 'var(--radius-sm)',
    fontSize: 13,
    color: active ? 'var(--white)' : 'var(--navy-200)',
    background: active ? 'var(--navy-700)' : 'transparent',
    cursor: 'pointer',
    border: 'none',
    width: '100%',
    textAlign: 'left',
    transition: 'background .12s, color .12s',
    marginBottom: 2,
  }),
  dot: (color) => ({
    width: 7,
    height: 7,
    borderRadius: '50%',
    background: color,
    flexShrink: 0,
  }),
  catSection: {
    marginTop: 24,
  },
  footer: {
    padding: '16px 20px',
    borderTop: '1px solid var(--navy-800)',
  },
  footerText: {
    fontSize: 11,
    color: 'var(--navy-400)',
    lineHeight: 1.5,
  },
};

export default function Sidebar({ page, setPage, result }) {
  const foundIds = result ? result.findings.map(f => f.id) : [];

  return (
    <aside style={styles.sidebar}>
      {/* Logo */}
      <div style={styles.logo}>
        <div style={styles.logoMark}>
          <div style={styles.logoIcon}>
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 1L13 4V7C13 10.3 10.4 13.4 7 14C3.6 13.4 1 10.3 1 7V4L7 1Z"
                stroke="white" strokeWidth="1.5" strokeLinejoin="round" />
              <path d="M4.5 7L6.5 9L9.5 5.5" stroke="white" strokeWidth="1.5"
                strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <span style={styles.logoText}>DarkDetect</span>
        </div>
        <div style={styles.logoSub}>MSc Project · QMUL 2025–26</div>
      </div>

      {/* Navigation */}
      <nav style={styles.nav}>
        <div style={styles.navLabel}>Tool</div>
        <button style={styles.navItem(page === 'home')} onClick={() => setPage('home')}>
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
            <path d="M7.5 1.5L13.5 6V13H9.5V9.5H5.5V13H1.5V6L7.5 1.5Z"
              stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
          </svg>
          Analyse a URL
        </button>
        <button style={styles.navItem(page === 'history')} onClick={() => setPage('history')}>
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
            <circle cx="7.5" cy="7.5" r="6" stroke="currentColor" strokeWidth="1.3" />
            <path d="M7.5 4.5V7.5L9.5 9.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
          </svg>
          History
        </button>

        {/* Dark pattern categories */}
        <div style={styles.catSection}>
          <div style={styles.navLabel}>Categories</div>
          {CATEGORIES.map(cat => {
            const found = foundIds.includes(cat.id);
            return (
              <div key={cat.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '5px 8px', fontSize: 12, color: 'var(--navy-200)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={styles.dot(found ? 'var(--red-dot)' : 'var(--navy-600)')} />
                  {cat.label}
                </div>
                <span style={{ fontSize: 10, color: 'var(--navy-400)' }}>{cat.id}</span>
              </div>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div style={styles.footer}>
        <div style={styles.footerText}>
          Han Jay Tan<br />
          Supervisor: Jinhua Liang<br />
          <span style={{ color: 'var(--navy-600)' }}>v0.1.0 · prototype</span>
        </div>
      </div>
    </aside>
  );
}
