// CoralCon Privacy Tab — Local-first architecture, data flow, privacy report

function PrivacyTab({ tweaks }) {
  const accent = tweaks.accentColor || '#f0a500';

  const checks = [
    { title: 'Coral Runs Locally', desc: 'All Coral SQL queries execute on your machine. No data leaves your environment for query processing.', icon: 'server' },
    { title: 'Local Data Retrieval', desc: 'Raw GitHub, Notion, and LinkedIn data is queried locally through Coral SQL. API calls go directly from your machine to each platform.', icon: 'database' },
    { title: 'LLM Receives Summaries Only', desc: 'When AI analysis is enabled, only summarized query results are sent to the configured LLM provider — never raw application data, credentials, or personal identifiers.', icon: 'eye' },
    { title: 'No LinkedIn Scraping', desc: 'LinkedIn data comes from your own GDPR data export (Settings → Data Privacy → Get a copy of your data). No scraping, no unauthorized access.', icon: 'shield' },
    { title: 'Credential Security', desc: 'API keys and tokens are read from environment variables or .env files. Never hardcoded, never logged, never transmitted.', icon: 'lock' },
    { title: 'Reports Stored Locally', desc: 'All generated reports, insights, and proof logs are stored in your local ./runs directory. Nothing is uploaded unless you explicitly share it.', icon: 'fileText' },
  ];

  return (
    <div>
      <div className="cc-page-header">
        <h1 className="cc-page-title">Privacy</h1>
        <span className="cc-page-subtitle">Your data stays on your machine. Nothing is uploaded.</span>
      </div>

      {/* Privacy Checks */}
      <Reveal>
        <div className="cc-section-title">Privacy Guarantees</div>
      </Reveal>
      <div className="cc-check-list" style={{ marginBottom: 'var(--cc-sp-7)' }}>
        {checks.map((check, i) => (
          <Reveal key={i} delay={i * 70}>
          <div className="cc-check-item">
            <CCIcon name="checkCircle" size={22} className="cc-check-icon" />
            <div className="cc-check-text">
              <strong>{check.title}</strong>
              <span>{check.desc}</span>
            </div>
          </div>
          </Reveal>
        ))}
      </div>

      {/* Architecture Diagram */}
      <Reveal>
        <div className="cc-section-title">Data Flow Architecture</div>
      </Reveal>
      <Reveal delay={80} direction="scale">
      <div className="cc-card" style={{ marginBottom: 'var(--cc-sp-6)' }}>
        <div className="cc-arch-flow">
          <div className="cc-arch-node">
            <CCIcon name="terminal" size={20} style={{ margin: '0 auto 6px', display: 'block' }} />
            User Query
          </div>
          <span className="cc-arch-arrow">&rarr;</span>
          <div className="cc-arch-node" style={{ borderColor: accent, color: accent }}>
            <CCIcon name="anchor" size={20} style={{ margin: '0 auto 6px', display: 'block', color: accent }} />
            CoralCon CLI
          </div>
          <span className="cc-arch-arrow">&rarr;</span>
          <div className="cc-arch-node coral">
            <CCIcon name="database" size={20} style={{ margin: '0 auto 6px', display: 'block' }} />
            Coral SQL Runtime
          </div>
          <span className="cc-arch-arrow">&rarr;</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div className="cc-arch-node" style={{ minWidth: 100 }}>
              <CCIcon name="gitBranch" size={16} style={{ display: 'inline', verticalAlign: '-3px', marginRight: 4 }} />
              GitHub API
            </div>
            <div className="cc-arch-node" style={{ minWidth: 100 }}>
              <CCIcon name="fileText" size={16} style={{ display: 'inline', verticalAlign: '-3px', marginRight: 4 }} />
              Notion API
            </div>
            <div className="cc-arch-node" style={{ minWidth: 100 }}>
              <CCIcon name="link" size={16} style={{ display: 'inline', verticalAlign: '-3px', marginRight: 4 }} />
              LinkedIn GDPR
            </div>
          </div>
        </div>

        <div style={{ textAlign: 'center', margin: '16px 0', color: 'var(--cc-text-muted)', fontSize: 13 }}>
          &darr; Summarized results only &darr;
        </div>

        <div className="cc-arch-flow" style={{ paddingTop: 0 }}>
          <div className="cc-arch-node" style={{ borderColor: 'var(--cc-purple)', color: 'var(--cc-purple)' }}>
            <CCIcon name="zap" size={20} style={{ margin: '0 auto 6px', display: 'block' }} />
            LLM Analysis (Optional)
          </div>
          <span className="cc-arch-arrow">&rarr;</span>
          <div className="cc-arch-node" style={{ borderColor: 'var(--cc-teal)', color: 'var(--cc-teal)' }}>
            <CCIcon name="target" size={20} style={{ margin: '0 auto 6px', display: 'block' }} />
            Insight Report
          </div>
          <span className="cc-arch-arrow">&rarr;</span>
          <div className="cc-arch-node">
            <CCIcon name="fileText" size={20} style={{ margin: '0 auto 6px', display: 'block' }} />
            Local ./runs/
          </div>
        </div>
      </div>
      </Reveal>

      {/* Honesty Notice */}
      <Reveal delay={60}>
      <div className="cc-card" style={{ borderColor: 'var(--cc-teal)', background: 'var(--cc-teal-dim)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--cc-sp-4)' }}>
          <CCIcon name="shield" size={24} style={{ color: 'var(--cc-teal)', flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 6 }}>Honest Disclosure</div>
            <p style={{ fontSize: 14, color: 'var(--cc-text-secondary)', lineHeight: 1.7 }}>
              CoralCon is designed to keep raw source data local. If LLM analysis is enabled,
              summarized query results may be sent to the configured LLM provider (Claude API
              or OpenAI). Disable LLM mode with <code style={{ fontFamily: 'var(--cc-font-mono)', background: 'var(--cc-bg-elevated)', padding: '2px 6px', borderRadius: 4 }}>--no-llm</code> for
              fully offline, deterministic analysis using rule-based insights.
            </p>
          </div>
        </div>
      </div>
      </Reveal>

      {/* Commands */}
      <Reveal delay={80}>
      <div className="cc-section-title" style={{ marginTop: 'var(--cc-sp-7)' }}>Quick Commands</div>
      </Reveal>
      <Reveal delay={120}>
      <div className="cc-card">
        <div style={{ fontFamily: 'var(--cc-font-mono)', fontSize: 13, lineHeight: 2, color: 'var(--cc-text-secondary)' }}>
          <div><span style={{ color: 'var(--cc-teal)' }}>$</span> coralcon privacy-report</div>
          <div><span style={{ color: 'var(--cc-teal)' }}>$</span> coralcon analyze --no-llm <span style={{ color: 'var(--cc-text-muted)' }}># fully local</span></div>
          <div><span style={{ color: 'var(--cc-teal)' }}>$</span> coralcon judge-demo --sample <span style={{ color: 'var(--cc-text-muted)' }}># no API keys needed</span></div>
        </div>
      </div>
      </Reveal>
    </div>
  );
}

Object.assign(window, { PrivacyTab });
