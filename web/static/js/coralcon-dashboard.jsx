// CoralCon Dashboard Tab — Hero, Health Score, Stats, Insights

const { useState: useDashState, useEffect: useDashEffect, useRef: useDashRef } = React;

/* ====== SCROLL REVEAL HOOK ====== */
function useReveal(threshold = 0.15) {
  const ref = useDashRef(null);
  const [visible, setVisible] = useDashState(false);
  useDashEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { setVisible(true); obs.unobserve(el); }
    }, { threshold });
    obs.observe(el);
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
          setVisible(true);
        }
      });
    });
    // Safety net: never leave content permanently hidden if the observer
    // doesn't fire (e.g. headless render, no scroll, exotic browsers).
    const failsafe = setTimeout(() => setVisible(true), 1400);
    return () => { obs.disconnect(); clearTimeout(failsafe); };
  }, [threshold]);
  return [ref, visible];
}

function Reveal({ children, className = '', delay = 0 }) {
  const [ref, visible] = useReveal();
  return (
    <div
      ref={ref}
      className={`cc-reveal ${visible ? 'is-visible' : ''} ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}

/* ====== ANIMATED COUNTER ====== */
function AnimCounter({ target, duration = 1500, suffix = '', decimals = 0 }) {
  const [val, setVal] = useDashState(0);

  useDashEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setVal(eased * target);
      if (progress >= 1) clearInterval(interval);
    }, 16);
    return () => clearInterval(interval);
  }, [target, duration]);

  return <>{decimals > 0 ? val.toFixed(decimals) : Math.round(val)}{suffix}</>;
}

/* ====== SHARE REPORT CARD ====== */
function ShareReportButton({ data }) {
  const [copied, setCopied] = useDashState(false);

  const buildCard = () => {
    const s = data.stats || {};
    const worst = (data.rejectionByRole || []).reduce(
      (a, b) => (b.rate > (a?.rate ?? -1) ? b : a), null);
    const topInsight = (data.insights || [])[0];
    const lines = [
      '🧭 My CoralCon Career Report',
      `${s.totalApplications} applications → ${s.responseRate}% response rate`,
      worst ? `Worst category: ${worst.role} (${worst.rate}% rejection)` : null,
      topInsight ? `Biggest fix: ${topInsight.title}` : null,
      `Search health: ${s.healthScore}/100`,
      `Decoded with one Coral SQL query across GitHub + Sheets + LinkedIn.`,
    ].filter(Boolean);
    return lines.join('\n');
  };

  const onShare = async () => {
    const text = buildCard();
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement('textarea');
        ta.value = text; document.body.appendChild(ta); ta.select();
        document.execCommand('copy'); document.body.removeChild(ta);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2200);
    } catch (e) {
      setCopied(false);
    }
  };

  return (
    <button type="button" className="cc-share-btn" onClick={onShare}>
      <CCIcon name={copied ? 'check' : 'share'} size={15} />
      {copied ? 'Copied to clipboard' : 'Share my report card'}
    </button>
  );
}

/* ====== HEALTH GAUGE ====== */
function HealthGauge({ score, accent }) {
  const [offset, setOffset] = useDashState(440);
  const radius = 70;
  const circumference = 2 * Math.PI * radius;

  useDashEffect(() => {
    const t = setTimeout(() => {
      setOffset(circumference - (score / 100) * circumference);
    }, 400);
    return () => clearTimeout(t);
  }, [score, circumference]);

  const strokeColor = score < 30 ? 'var(--cc-red)' : score < 60 ? accent : 'var(--cc-teal)';

  return (
    <div className="cc-health-gauge">
      <svg viewBox="0 0 160 160">
        <circle className="track" cx="80" cy="80" r={radius} />
        <circle
          className="fill"
          cx="80" cy="80" r={radius}
          stroke={strokeColor}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="cc-health-score">
        <div className="cc-health-number" style={{ color: strokeColor }}>
          <AnimCounter target={score} duration={2000} />
        </div>
        <div className="cc-health-label">/ 100</div>
      </div>
    </div>
  );
}

/* ====== STAT CARD ====== */
function StatCard({ label, value, suffix, sublabel, color, decimals = 0, delay = 0 }) {
  return (
    <Reveal delay={delay}>
      <div className="cc-stat-card">
        <div className="cc-stat-label">{label}</div>
        <div className="cc-stat-value" style={{ color: color || 'var(--cc-gold)' }}>
          <AnimCounter target={value} suffix={suffix} decimals={decimals} duration={1800} />
        </div>
        {sublabel && (
          <div style={{ fontSize: 12, color: 'var(--cc-text-muted)' }}>
            {sublabel}
          </div>
        )}
      </div>
    </Reveal>
  );
}

/* ====== INSIGHT CARD ====== */
function InsightCard({ insight, startOpen = false, delay = 0 }) {
  const [expanded, setExpanded] = useDashState(startOpen);
  return (
    <Reveal delay={delay}>
      <div className={`cc-insight-card ${expanded ? 'expanded' : ''}`} onClick={() => setExpanded(!expanded)}>
        <div className="cc-insight-header">
          <span className={`cc-insight-severity ${insight.severity}`}>{insight.severity}</span>
          <span className="cc-insight-title">{insight.title}</span>
          <CCIcon name="chevronRight" size={16} className="cc-insight-chevron" />
        </div>
        <p style={{ fontSize: 14, color: 'var(--cc-text-secondary)', marginTop: 8 }}>{insight.claim}</p>
        {expanded && (
          <div className="cc-insight-body" onClick={e => e.stopPropagation()}>
            <div className="cc-insight-row">
              <span className="cc-insight-label">Why</span>
              <span className="cc-insight-value">{insight.rootCause}</span>
            </div>
            <div className="cc-insight-row">
              <span className="cc-insight-label">Fix</span>
              <span className="cc-insight-value" style={{ color: 'var(--cc-teal)', fontWeight: 600 }}>{insight.action}</span>
            </div>
            <div className="cc-insight-row">
              <span className="cc-insight-label">Impact</span>
              <span className="cc-insight-value">{insight.impact}</span>
            </div>
            <div className="cc-insight-row">
              <span className="cc-insight-label">Data Source</span>
              <span className="cc-insight-value">
                {insight.evidence.sources.join(' + ')} ({insight.evidence.rows} rows analyzed)
                {insight.confidence && <span style={{ color: 'var(--cc-text-muted)' }}> &middot; {Math.round(insight.confidence * 100)}% confidence</span>}
              </span>
            </div>
          </div>
        )}
      </div>
    </Reveal>
  );
}

function buildPortfolioProductData(result) {
  const skills = result?.detected_skills || [];
  const projectCount = (result?.project_links || []).length;
  const githubCount = (result?.github_links || []).length;
  const score = Math.min(100, Math.round(
    (result?.reachable ? 28 : 0)
    + Math.min(skills.length * 4, 36)
    + Math.min(projectCount * 8, 20)
    + Math.min(githubCount * 8, 16)
  ));
  const topSkills = skills.slice(0, 8);

  return {
    portfolioMode: true,
    stats: {
      totalApplications: skills.length,
      responseRate: projectCount,
      interviewRate: githubCount,
      offerRate: score,
      healthScore: score,
    },
    rejectionByRole: [
      { role: 'Skills', applied: Math.max(skills.length, 1), rejected: 0, rate: Math.min(100, skills.length * 8) },
      { role: 'Projects', applied: Math.max(projectCount, 1), rejected: 0, rate: Math.min(100, projectCount * 25) },
      { role: 'GitHub Proof', applied: Math.max(githubCount, 1), rejected: 0, rate: Math.min(100, githubCount * 25) },
    ],
    skillGap: {
      labels: topSkills.length ? topSkills : ['Skills', 'Projects', 'GitHub', 'Case Studies'],
      demanded: topSkills.length ? topSkills.map(() => 100) : [100, 100, 100, 100],
      present: topSkills.length ? topSkills.map(() => 85) : [
        skills.length ? 80 : 15,
        projectCount ? 80 : 15,
        githubCount ? 80 : 15,
        projectCount >= 2 ? 80 : 20,
      ],
    },
    insights: [
      {
        id: 'portfolio-readiness',
        title: result.reachable ? 'Portfolio is reachable' : 'Portfolio access issue',
        severity: result.reachable ? 'medium' : 'critical',
        claim: result.reachable
          ? `${result.title || result.url} exposes ${skills.length} skills, ${projectCount} project links, and ${githubCount} GitHub links.`
          : `Could not reach ${result.url}. Recruiters won't be able to see your work.`,
        rootCause: result.reachable
          ? 'Page loads fine, but recruiter-facing proof depends on clear skills, projects, and source links being visible above the fold.'
          : 'The URL is not returning inspectable HTML from the public internet.',
        action: skills.length
          ? 'Move your strongest skills and project links into the first viewport. Keep GitHub links visible.'
          : 'Add an explicit skills section listing the exact technologies you want recruiters to find.',
        impact: 'Turns the portfolio into a proof surface instead of a passive page.',
        evidence: { queryId: 'portfolio_scan', rows: 1, sources: [result.url] },
        confidence: 0.78,
      },
      {
        id: 'project-proof',
        title: projectCount ? 'Project links found' : 'No project links detected',
        severity: projectCount ? 'medium' : 'high',
        claim: projectCount
          ? `${projectCount} project-style links were detected on the page.`
          : 'No project links were found. Recruiters need to see shipped work.',
        rootCause: 'Recruiters need direct paths from claims to shipped work.',
        action: 'Add direct live demo and repository links for your top 3 projects.',
        impact: 'Reduces friction between reading the portfolio and verifying proof.',
        evidence: { queryId: 'portfolio_links', rows: projectCount, sources: [result.url] },
        confidence: 0.74,
      },
    ],
  };
}

function PortfolioInspector({ accent, onScan }) {
  const [url, setUrl] = useDashState('');
  const [result, setResult] = useDashState(null);
  const [loading, setLoading] = useDashState(false);
  const [error, setError] = useDashState('');

  const scanPortfolio = async () => {
    const trimmed = url.trim();
    if (!trimmed) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`/api/portfolio?url=${encodeURIComponent(trimmed)}`);
      const payload = await res.json();
      setResult(payload);
      onScan?.(payload);
      if (payload.error && !payload.reachable) setError(payload.error);
    } catch (err) {
      setError(err.message || 'Unable to inspect portfolio.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const skills = result?.detected_skills || [];

  return (
    <div className="cc-portfolio-panel">
      <div className="cc-portfolio-copy">
        <div className="cc-card-title">Check Your Portfolio</div>
        <p>Paste your portfolio URL to see what recruiters actually find when they visit.</p>
      </div>
      <div className="cc-portfolio-controls">
        <input
          className="cc-portfolio-input"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          onKeyDown={(event) => { if (event.key === 'Enter') scanPortfolio(); }}
          placeholder="https://your-portfolio.com"
          type="url"
        />
        <button className="cc-portfolio-button" onClick={scanPortfolio} disabled={loading || !url.trim()}>
          <CCIcon name="search" size={16} />
          {loading ? 'Scanning...' : 'Scan'}
        </button>
      </div>
      {result && (
        <div className="cc-portfolio-result">
          <span className={`cc-portfolio-status ${result.reachable ? 'ok' : 'bad'}`}>
            {result.reachable ? 'Reachable' : 'Not Reachable'}
          </span>
          <span>{skills.length} skills found</span>
          <span>{(result.project_links || []).length} project links</span>
          <span>{(result.github_links || []).length} GitHub links</span>
          {skills.slice(0, 8).map(skill => (
            <span className="cc-skill-chip" key={skill} style={{ borderColor: accent }}>{skill}</span>
          ))}
        </div>
      )}
      {error && <div className="cc-portfolio-error">{error}</div>}
    </div>
  );
}

/* ====== HOW IT WORKS BANNER ====== */
function HowItWorksBanner({ accent }) {
  const [dismissed, setDismissed] = useDashState(false);
  if (dismissed) return null;

  const steps = [
    { icon: 'database', title: 'Pull your data', desc: 'GitHub repos, Google Sheets applications, LinkedIn profile' },
    { icon: 'code', title: 'Find patterns', desc: 'SQL queries join all 3 sources to find what\'s failing' },
    { icon: 'target', title: 'Get fixes', desc: 'Each recommendation is backed by data, not guesswork' },
  ];

  return (
    <div className="cc-how-banner">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--cc-sp-4)' }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: accent, textTransform: 'uppercase', letterSpacing: '0.06em' }}>How CoralCon works</div>
        <button
          onClick={(e) => { e.stopPropagation(); setDismissed(true); }}
          style={{ background: 'none', border: 'none', color: 'var(--cc-text-muted)', cursor: 'pointer', fontSize: 18, padding: 4 }}
        >&times;</button>
      </div>
      <div className="cc-how-steps">
        {steps.map((step, i) => (
          <div key={i} className="cc-how-step">
            <div className="cc-how-step-num" style={{ background: accent, color: 'var(--cc-text-on-accent)' }}>{i + 1}</div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2 }}>{step.title}</div>
              <div style={{ fontSize: 13, color: 'var(--cc-text-secondary)' }}>{step.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ====== DASHBOARD TAB ====== */
/* ====== MORNING STANDUP — Track 2 daily first-mate briefing ====== */
function MorningBriefing() {
  const [m, setM] = useDashState(null);
  const [err, setErr] = useDashState('');

  useDashEffect(() => {
    let cancelled = false;
    fetch('/api/morning')
      .then(r => (r.ok ? r.json() : Promise.reject(new Error('morning ' + r.status))))
      .then(d => { if (!cancelled) setM(d); })
      .catch(e => { if (!cancelled) setErr(e.message || 'load failed'); });
    return () => { cancelled = true; };
  }, []);

  if (err || !m) return null;

  const rate = m.response_rate ?? 0;
  const rateColor = rate >= 15 ? 'var(--cc-teal)' : (rate >= 5 ? 'var(--cc-gold)' : '#c0392b');

  return (
    <div className="cc-card" style={{ padding: 'var(--cc-sp-4)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <div style={{ fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--cc-text-muted)' }}>
            Morning standup · your first mate
          </div>
          <div style={{ fontFamily: 'Fraunces, serif', fontSize: 22, fontWeight: 600 }}>What to do today</div>
        </div>
        <div style={{ fontSize: 13, color: 'var(--cc-text-muted)' }}>{m.date_label}</div>
      </div>

      <div style={{ margin: '12px 0 16px', fontSize: 14 }}>
        <span style={{ color: 'var(--cc-text-muted)' }}>Where you stand: </span>
        <strong>{m.total_applications}</strong> applications
        <span style={{ color: 'var(--cc-text-muted)' }}> · </span>
        <strong style={{ color: rateColor }}>{rate}% response rate</strong>
      </div>

      <ol style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: 12 }}>
        {(m.priorities || []).map((p, i) => (
          <li key={i} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
            <span style={{
              flex: '0 0 auto', width: 24, height: 24, borderRadius: '50%',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 12, fontWeight: 700, border: '1px solid var(--cc-border)',
              background: p.severity === 'high' ? 'var(--cc-gold-dim)' : 'transparent',
              color: p.severity === 'high' ? 'var(--cc-gold)' : 'var(--cc-text-muted)',
            }}>{i + 1}</span>
            <div>
              <div style={{ fontWeight: 600 }}>{p.title}</div>
              <div style={{ fontSize: 13, color: 'var(--cc-text-muted)' }}>{p.detail}</div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

function DashboardTab({ tweaks }) {
  const [data, setData] = useDashState(CORALCON_DATA);
  const [loading, setLoading] = useDashState(true);
  const [loadError, setLoadError] = useDashState('');
  const accent = tweaks.accentColor || '#f0a500';
  const theme = tweaks.theme || 'dark';
  const portfolioMode = data.portfolioMode;

  useDashEffect(() => {
    let cancelled = false;
    async function loadDashboard() {
      try {
        const res = await fetch('/api/dashboard');
        if (!res.ok) throw new Error(`Dashboard API returned ${res.status}`);
        const payload = await res.json();
        if (!cancelled) {
          setData({ ...CORALCON_DATA, ...payload, stats: { ...CORALCON_DATA.stats, ...(payload.stats || {}) } });
          setLoadError('');
        }
      } catch (err) {
        if (!cancelled) setLoadError(err.message || 'Unable to load live data.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadDashboard();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className={portfolioMode ? 'cc-dashboard portfolio-mode' : 'cc-dashboard'}>
      {/* Hero */}
      <Reveal>
        <div className="cc-hero">
          <div>
            {!portfolioMode && (
              <div className="cc-hero-kicker">
                I turned my rejection history into a queryable evidence system.
              </div>
            )}
            <div className="cc-hero-tagline">
              {portfolioMode ? (
                <>Portfolio Report</>
              ) : (
                <>Why you're getting rejected<em> — and what to fix</em></>
              )}
            </div>
            <p className="cc-hero-sub">
              {portfolioMode
                ? 'Your portfolio scanned for recruiter-visible skills, projects, and proof.'
                : 'CoralCon joins your applications, GitHub activity, and LinkedIn profile with one Coral SQL query — every finding below is backed by data, not guesswork.'
              }
            </p>
            <div className="cc-live-status">
              <span className={data.usingSampleData ? 'sample' : 'live'}>
                {data.usingSampleData ? 'Local import mode' : 'Live Coral SQL'}
              </span>
              {loading && <span>Loading...</span>}
              {loadError && <span className="error">{loadError}</span>}
            </div>
            {!portfolioMode && <ShareReportButton data={data} />}
          </div>
          {!portfolioMode && (
            <div className="cc-hero-stat">
              <div className="cc-hero-stat-num">{data.stats.totalApplications}</div>
              <div className="cc-hero-stat-label">applications<br/>decoded</div>
              <div className="cc-hero-sources" style={{ marginTop: 'var(--cc-sp-3)' }}>
                {['gitBranch:GitHub', 'database:Sheets', 'link:LinkedIn'].map((s) => {
                  const [icon, label] = s.split(':');
                  return (
                    <span key={label} className="cc-source-pill">
                      <CCIcon name={icon} size={14} /> {label}
                    </span>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </Reveal>

      {/* Morning standup — daily first-mate briefing (Track 2) */}
      {!portfolioMode && (
        <Reveal delay={60}>
          <MorningBriefing />
        </Reveal>
      )}

      {/* How It Works */}
      {!portfolioMode && (
        <Reveal>
          <HowItWorksBanner accent={accent} />
        </Reveal>
      )}

      {/* Health Score + Stats */}
      <Reveal delay={100}>
        <div className="cc-health-section">
          <HealthGauge score={data.stats.healthScore} accent={accent} />
          <div className="cc-health-info">
            <h2>{portfolioMode ? 'Portfolio Readiness' : 'Your Search Health'}</h2>
            <p>
              {portfolioMode
                ? 'How recruiter-ready your portfolio looks based on visible skills, projects, and GitHub links.'
                : data.stats.healthScore < 40
                  ? 'Your score is low. The biggest issues are below — start with the top one.'
                  : data.stats.healthScore < 70
                    ? 'Getting there. Fix the top issues below and this score will climb fast.'
                    : 'Looking strong. Fine-tune the remaining issues to maximize your response rate.'
              }
            </p>
          </div>
        </div>
      </Reveal>

      {/* Stat Cards */}
      <div className="cc-stats-grid">
        <StatCard
          label={portfolioMode ? 'Skills Found' : 'Applications'}
          value={data.stats.totalApplications}
          color={accent}
          sublabel={portfolioMode ? 'on your portfolio' : 'tracked in Sheets'}
          delay={0}
        />
        <StatCard
          label={portfolioMode ? 'Project Links' : 'Response Rate'}
          value={data.stats.responseRate}
          suffix={portfolioMode ? '' : '%'}
          color={data.stats.responseRate < 25 ? 'var(--cc-red)' : 'var(--cc-teal)'}
          sublabel={portfolioMode ? 'visible to recruiters' : data.stats.responseRate < 25 ? 'below average' : 'on track'}
          delay={70}
        />
        <StatCard
          label={portfolioMode ? 'GitHub Links' : 'Interview Rate'}
          value={data.stats.interviewRate}
          suffix={portfolioMode ? '' : '%'}
          color="var(--cc-orange)"
          sublabel={portfolioMode ? 'proof of work' : data.stats.interviewRate < 10 ? 'needs improvement' : 'decent'}
          delay={140}
        />
        <StatCard
          label={portfolioMode ? 'Readiness' : 'Offer Rate'}
          value={data.stats.offerRate}
          suffix="%"
          decimals={portfolioMode ? 0 : 1}
          color={data.stats.offerRate < 3 ? 'var(--cc-red)' : 'var(--cc-teal)'}
          sublabel={portfolioMode ? 'portfolio score' : data.stats.offerRate < 3 ? 'way too low' : 'keep it up'}
          delay={210}
        />
      </div>

      {/* Top Findings — first insight expanded */}
      <Reveal>
        <div className="cc-section-title">What's Hurting You Most</div>
      </Reveal>
      <div className="cc-insights" style={{ marginBottom: 'var(--cc-sp-6)' }}>
        {data.insights.length === 0 && (
          <div className="cc-card">
            <div className="cc-card-title">Import your data to generate insights</div>
            <p style={{ color: 'var(--cc-text-secondary)', lineHeight: 1.6, marginTop: 'var(--cc-sp-2)' }}>
              Connect Google and import Gmail application outcomes from the Import tab.
              CoralCon will replace this with evidence-backed findings.
            </p>
          </div>
        )}
        {data.insights.slice(0, 3).map((ins, i) => (
          <InsightCard key={ins.id} insight={ins} startOpen={i === 0} delay={i * 60} />
        ))}
      </div>

      {/* Portfolio Inspector */}
      <Reveal delay={120}>
        <PortfolioInspector
          accent={accent}
          onScan={(result) => setData(current => ({ ...current, ...buildPortfolioProductData(result), portfolio: result }))}
        />
      </Reveal>

      {/* Charts */}
      <Reveal delay={50}>
        <div className="cc-section-title">The Evidence</div>
      </Reveal>
      <div className="cc-charts-grid" style={{ marginBottom: 'var(--cc-sp-6)' }}>
        <Reveal delay={0}>
          <div className="cc-chart-card">
            <div className="cc-card-title">{portfolioMode ? 'Portfolio Coverage' : 'Rejection Rate by Role'}</div>
            <p style={{ fontSize: 13, color: 'var(--cc-text-muted)', marginBottom: 12 }}>
              {portfolioMode ? 'How well your portfolio covers each proof category.' : 'Which types of roles reject you most. High bars = bad fit.'}
            </p>
            <RejectionBars data={data.rejectionByRole} animate={true} />
          </div>
        </Reveal>
        <Reveal delay={100}>
          <div className="cc-chart-card">
            <div className="cc-card-title">{portfolioMode ? 'Activity Timeline' : 'Your GitHub Activity'}</div>
            <p style={{ fontSize: 13, color: 'var(--cc-text-muted)', marginBottom: 12 }}>
              Weeks with no commits have an 85% ghost rate. Active weeks drop to 34%.
            </p>
            <GithubHeatmap data={data.githubHeatmap} theme={theme} accent={accent} />
          </div>
        </Reveal>
        <Reveal delay={50}>
          <div className="cc-chart-card">
            <div className="cc-card-title">Skills: Demanded vs Your Profile</div>
            <p style={{ fontSize: 13, color: 'var(--cc-text-muted)', marginBottom: 12 }}>
              Red = what jobs want. Green = what's on your GitHub/LinkedIn. Gaps = why you're rejected.
            </p>
            <SkillRadar data={data.skillGap} theme={theme} accent={accent} chartStyle={tweaks.chartStyle} />
          </div>
        </Reveal>
        <Reveal delay={150}>
          <div className="cc-chart-card">
            <div className="cc-card-title">Does Applying Early Matter?</div>
            <p style={{ fontSize: 13, color: 'var(--cc-text-muted)', marginBottom: 12 }}>
              Ghost rate by how many days after posting you applied. Earlier = better.
            </p>
            <TimingChart data={data.timing} theme={theme} accent={accent} chartStyle={tweaks.chartStyle} />
          </div>
        </Reveal>
      </div>

      {/* Remaining Insights */}
      {data.insights.length > 3 && (
        <>
          <Reveal>
            <div className="cc-section-title">More Findings</div>
          </Reveal>
          <div className="cc-insights">
            {data.insights.slice(3).map((ins, i) => (
              <InsightCard key={ins.id} insight={ins} delay={i * 60} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

Object.assign(window, { DashboardTab, AnimCounter, HealthGauge, PortfolioInspector, Reveal, useReveal });
