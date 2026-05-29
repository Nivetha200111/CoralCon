// CoralCon App — Main shell: sidebar, navigation, theme toggle, tweaks integration

const { useState: useAppState, useEffect: useAppEffect, useCallback: useAppCb } = React;

const TABS = [
  { id: 'dashboard', label: 'My Report', icon: 'layoutDashboard' },
  { id: 'ask', label: 'Ask', icon: 'search' },
  { id: 'proof', label: 'How It Works', icon: 'database' },
  { id: 'cohort', label: 'Teams', icon: 'users' },
  { id: 'privacy', label: 'Privacy', icon: 'shield' },
];

const TAB_PATHS = {
  dashboard: '/dashboard',
  ask: '/ask',
  proof: '/proof',
  cohort: '/cohort',
  privacy: '/privacy',
};

function getInitialTab() {
  const path = window.location.pathname.replace(/\/+$/, '') || '/';
  const match = Object.entries(TAB_PATHS).find(([, tabPath]) => tabPath === path);
  return match ? match[0] : 'dashboard';
}

/* ====== COMPASS LOGO SVG ====== */
function CoralConLogo({ size = 36 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      <circle cx="24" cy="24" r="22" stroke="currentColor" strokeWidth="1.5" opacity="0.3" />
      <circle cx="24" cy="24" r="16" stroke="currentColor" strokeWidth="1" opacity="0.2" />
      {/* Compass rose */}
      <path d="M24 4 L26.5 20 L24 22 L21.5 20 Z" fill="currentColor" opacity="0.9" />
      <path d="M24 44 L26.5 28 L24 26 L21.5 28 Z" fill="currentColor" opacity="0.4" />
      <path d="M4 24 L20 21.5 L22 24 L20 26.5 Z" fill="currentColor" opacity="0.4" />
      <path d="M44 24 L28 21.5 L26 24 L28 26.5 Z" fill="currentColor" opacity="0.9" />
      <circle cx="24" cy="24" r="3" fill="currentColor" />
    </svg>
  );
}

/* ====== LIVE / SAMPLE STATUS PILL ====== */
function LiveStatusPill() {
  const [status, setStatus] = useAppState(null);

  useAppEffect(() => {
    let cancelled = false;
    fetch('/api/status')
      .then(r => r.ok ? r.json() : null)
      .then(s => { if (!cancelled) setStatus(s); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  if (!status) return null;

  const live = !status.using_sample_data && status.coral_installed;
  const connected = ['github', 'notion', 'linkedin']
    .filter(src => status[`${src}_connected`])
    .map(src => src.charAt(0).toUpperCase() + src.slice(1));

  return (
    <div
      className="cc-source-pill"
      style={{
        display: 'flex', alignItems: 'center', gap: 6,
        margin: '0 var(--cc-sp-3) var(--cc-sp-2)',
        borderColor: live ? '#20c9a0' : 'var(--cc-border)',
      }}
      title={live
        ? `Coral connected: ${connected.join(', ') || 'sources'}`
        : 'Running on bundled demo data'}
    >
      <span style={{
        width: 8, height: 8, borderRadius: '50%',
        background: live ? '#20c9a0' : '#f0a500',
        boxShadow: live ? '0 0 8px #20c9a0' : 'none',
      }} />
      {live
        ? <>Live via Coral{connected.length ? ` · ${connected.join(' · ')}` : ''}</>
        : <>Demo data</>}
    </div>
  );
}

/* ====== MAIN APP ====== */
function CoralConApp() {
  const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{"pirateIntensity":"subtle","accentColor":"#f0a500","chartStyle":"outlined","theme":"dark"}/*EDITMODE-END*/;

  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [activeTab, setActiveTab] = useAppState(getInitialTab);
  const [tabKey, setTabKey] = useAppState(0);

  // Apply theme to HTML
  useAppEffect(() => {
    document.documentElement.setAttribute('data-theme', tweaks.theme);
  }, [tweaks.theme]);

  const switchTab = useAppCb((id) => {
    setActiveTab(id);
    setTabKey(k => k + 1);
    const nextPath = TAB_PATHS[id] || '/dashboard';
    if (window.location.pathname !== nextPath) {
      window.history.pushState({ tab: id }, '', nextPath);
    }
  }, []);

  useAppEffect(() => {
    const onPopState = () => {
      setActiveTab(getInitialTab());
      setTabKey(k => k + 1);
    };
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  const toggleTheme = useAppCb(() => {
    setTweak('theme', tweaks.theme === 'dark' ? 'light' : 'dark');
  }, [tweaks.theme, setTweak]);

  const renderTab = () => {
    switch (activeTab) {
      case 'dashboard': return <DashboardTab tweaks={tweaks} />;
      case 'ask': return <AskTab tweaks={tweaks} />;
      case 'proof': return <ProofTab tweaks={tweaks} />;
      case 'cohort': return <CohortTab tweaks={tweaks} />;
      case 'privacy': return <PrivacyTab tweaks={tweaks} />;
      default: return <DashboardTab tweaks={tweaks} />;
    }
  };

  const accentStyle = {
    '--cc-gold': tweaks.accentColor,
    '--cc-gold-dim': tweaks.accentColor + '1a',
    '--cc-glow-gold': `0 0 24px ${tweaks.accentColor}33`,
    display: 'flex',
    height: '100vh',
    overflow: 'hidden',
    width: '100%',
  };

  return (
    <div style={accentStyle}>
      {/* Sidebar */}
      <aside className="cc-sidebar">
        <div className="cc-logo">
          <div className="cc-logo-icon">
            <CoralConLogo size={36} />
          </div>
          <div>
            <div className="cc-logo-text">CoralCon</div>
            <div className="cc-logo-sub">Local-First Career Intelligence</div>
          </div>
        </div>

        <nav className="cc-nav">
          {TABS.map(tab => (
            <div
              key={tab.id}
              className={`cc-nav-item ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => switchTab(tab.id)}
            >
              <CCIcon name={tab.icon} size={18} />
              {tab.label}
              {tab.badge && <span className="cc-badge">{tab.badge}</span>}
            </div>
          ))}
        </nav>

        <div className="cc-sidebar-footer">
          <LiveStatusPill />
          <button className="cc-theme-toggle" onClick={toggleTheme}>
            <CCIcon name={tweaks.theme === 'dark' ? 'sun' : 'moon'} size={16} />
            {tweaks.theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
          </button>
          <div style={{ fontSize: 11, color: 'var(--cc-text-muted)', padding: '0 var(--cc-sp-3)' }}>
            Pirates of the Coral-bean
          </div>
        </div>
      </aside>

      <nav className="cc-mobile-nav" aria-label="Primary">
        {TABS.map(tab => (
          <button
            key={tab.id}
            type="button"
            className={`cc-mobile-nav-item ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => switchTab(tab.id)}
            aria-label={tab.label}
          >
            <CCIcon name={tab.icon} size={18} />
            <span>{tab.label}</span>
          </button>
        ))}
      </nav>

      {/* Main Content */}
      <main className="cc-main" key={`tab-${activeTab}-${tabKey}`}>
        {renderTab()}
      </main>

      {/* Tweaks Panel */}
      <TweaksPanel title="CoralCon Tweaks">
        <TweakSection label="Theme">
          <TweakRadio
            label="Appearance"
            value={tweaks.theme}
            options={['dark', 'light']}
            onChange={v => setTweak('theme', v)}
          />
        </TweakSection>

        <TweakSection label="Pirate Intensity">
          <TweakSelect
            label="Copy & Style"
            value={tweaks.pirateIntensity}
            options={['minimal', 'subtle', 'moderate', 'full']}
            onChange={v => setTweak('pirateIntensity', v)}
          />
        </TweakSection>

        <TweakSection label="Accent Color">
          <TweakColor
            label="Primary Accent"
            value={tweaks.accentColor}
            options={['#f0a500', '#20c9a0', '#4e8cff', '#a78bfa', '#ff6b6b']}
            onChange={v => setTweak('accentColor', v)}
          />
        </TweakSection>

        <TweakSection label="Charts">
          <TweakRadio
            label="Chart Style"
            value={tweaks.chartStyle}
            options={['filled', 'outlined']}
            onChange={v => setTweak('chartStyle', v)}
          />
        </TweakSection>
      </TweaksPanel>
    </div>
  );
}

/* ====== MOUNT ====== */
const ccRoot = ReactDOM.createRoot(document.getElementById('root'));
ccRoot.render(<CoralConApp />);
