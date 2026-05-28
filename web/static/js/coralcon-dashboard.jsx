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
    return () => obs.disconnect();
  }, [threshold]);
  return [ref, visible];
}

function Reveal({ children, className = '' }) {
  return <div className={className}>{children}</div>;
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
function StatCard({ label, value, suffix, trend, trendDir, decimals = 0, accent, delay = 0 }) {
  return (
    <Reveal delay={delay}>
      <div className="cc-stat-card">
        <div className="cc-stat-label">{label}</div>
        <div className="cc-stat-value" style={{ color: accent }}>
          <AnimCounter target={value} suffix={suffix} decimals={decimals} duration={1800} />
        </div>
        {trend && (
          <div className={`cc-stat-trend ${trendDir}`}>
            <CCIcon name={trendDir === 'up' ? 'trendingUp' : 'trendingDown'} size={14} />
            {trend}
          </div>
        )}
      </div>
    </Reveal>
  );
}

/* ====== INSIGHT CARD ====== */
function InsightCard({ insight, delay = 0 }) {
  const [expanded, setExpanded] = useDashState(false);
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
              <span className="cc-insight-label">Root Cause</span>
              <span className="cc-insight-value">{insight.rootCause}</span>
            </div>
            <div className="cc-insight-row">
              <span className="cc-insight-label">Action</span>
              <span className="cc-insight-value" style={{ color: 'var(--cc-teal)', fontWeight: 600 }}>{insight.action}</span>
            </div>
            <div className="cc-insight-row">
              <span className="cc-insight-label">Impact</span>
              <span className="cc-insight-value">{insight.impact}</span>
            </div>
            <div className="cc-insight-row">
              <span className="cc-insight-label">Evidence</span>
              <span className="cc-insight-value">
                Query {insight.evidence.queryId} &rarr; {insight.evidence.rows} rows from {insight.evidence.sources.join(', ')}
                {insight.confidence && ` (${Math.round(insight.confidence * 100)}% confidence)`}
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
          : `CoralCon could not inspect ${result.url}.`,
        rootCause: result.reachable
          ? 'The page can be inspected, but recruiter-facing proof still depends on clear skills, projects, and source links.'
          : 'The URL is not returning inspectable HTML from the public internet.',
        action: skills.length
          ? 'Move the strongest skills and project links into the first viewport and keep GitHub links visible.'
          : 'Add an explicit skills section using the exact technologies you want recruiters to match.',
        impact: 'Turns the portfolio into a clear proof surface instead of a passive personal page.',
        evidence: { queryId: 'portfolio_scan', rows: 1, sources: [result.url] },
        confidence: 0.78,
      },
      {
        id: 'project-proof',
        title: projectCount ? 'Project links found' : 'Project proof missing',
        severity: projectCount ? 'medium' : 'high',
        claim: projectCount
          ? `${projectCount} project-style links were detected.`
          : 'No project links were detected from the page markup.',
        rootCause: 'Recruiters need direct paths from claims to shipped work.',
        action: 'Add direct live demo and repository links for the top 3 projects.',
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
        <div className="cc-card-title">Portfolio Inspection</div>
        <p>Paste a public portfolio link to inspect visible skills, project links, and GitHub proof.</p>
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
          {loading ? 'Scanning' : 'Inspect'}
        </button>
      </div>
      {result && (
        <div className="cc-portfolio-result">
          <span className={`cc-portfolio-status ${result.reachable ? 'ok' : 'bad'}`}>
            {result.reachable ? 'Reachable' : 'Needs Fix'}
          </span>
          <span>{skills.length} skills</span>
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

/* ====== PIRATE COPY VARIANTS ====== */
const PIRATE_COPY = {
  minimal: {
    tagline: ['The job market failed you.', ' Query it back.'],
    subtitle: 'CoralCon joins applications, portfolio proof, GitHub, and profile signals into one career intelligence surface.',
    healthTitle: 'Career Health Score',
    healthDesc: 'A composite score from application outcomes, skill alignment, GitHub activity, portfolio evidence, and timing signals.',
  },
  subtle: {
    tagline: ['The job market conned you.', ' Query it back.'],
    subtitle: 'One SQL layer across GitHub, Notion, LinkedIn, and portfolio proof. Evidence first, recommendations second.',
    healthTitle: 'Seaworthiness Score',
    healthDesc: 'Your career vessel scored across rejection patterns, skill gaps, portfolio proof, public activity, and follow-through.',
  },
  moderate: {
    tagline: ['The seas took your treasure.', " We're charting the way back."],
    subtitle: 'CoralCon maps the currents behind weak responses: role targeting, skill evidence, portfolio proof, and public signals.',
    healthTitle: 'Seaworthiness Report',
    healthDesc: 'A practical survey of the leaks: missing skills, weak project proof, stale activity, and application timing.',
  },
  full: {
    tagline: ['Ahoy, Captain.', " Yer ship's been sinkin'."],
    subtitle: "Stop prayin' to the kraken. Query the wreckage, patch the holes, and sail at roles you can actually win.",
    healthTitle: "Cap'n's Seaworthiness Log",
    healthDesc: "Every rejection, skill gap, and portfolio signal charted from bow to stern.",
  },
};

/* ====== DASHBOARD TAB ====== */
function DashboardTab({ tweaks }) {
  const [data, setData] = useDashState(CORALCON_DATA);
  const [loading, setLoading] = useDashState(true);
  const [loadError, setLoadError] = useDashState('');
  const accent = tweaks.accentColor || '#f0a500';
  const intensity = tweaks.pirateIntensity || 'subtle';
  const copy = PIRATE_COPY[intensity] || PIRATE_COPY.subtle;
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
          setData({ ...CORALCON_DATA, ...payload });
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
            <div className="cc-hero-kicker">Overview</div>
            <div className="cc-hero-tagline">
              {copy.tagline[0]}{copy.tagline[1] && <em>{copy.tagline[1]}</em>}
            </div>
            <p className="cc-hero-sub">{copy.subtitle}</p>
            <div className="cc-live-status">
              <span className={data.usingSampleData ? 'sample' : 'live'}>{data.usingSampleData ? 'Sample fallback' : 'Live sources'}</span>
              {loading && <span>Loading source data...</span>}
              {loadError && <span className="error">{loadError}</span>}
            </div>
          </div>
          <div className="cc-hero-sources">
            {['gitBranch:GitHub', 'fileText:Notion', 'link:LinkedIn', 'code:Portfolio'].map((s) => {
              const [icon, label] = s.split(':');
              return (
                <span key={label} className="cc-source-pill">
                  <CCIcon name={icon} size={14} /> {label}
                </span>
              );
            })}
            <span className="cc-source-pill active">
              <CCIcon name="database" size={14} /> Coral SQL
            </span>
          </div>
        </div>
      </Reveal>

      {/* Health Score + Stats */}
      <Reveal delay={100}>
        <div className="cc-health-section">
          <HealthGauge score={data.stats.healthScore} accent={accent} />
          <div className="cc-health-info">
            <h2>{portfolioMode ? 'Portfolio Readiness Score' : copy.healthTitle}</h2>
            <p>{portfolioMode ? 'A public-readiness score from visible skills, project links, and GitHub proof.' : copy.healthDesc}</p>
          </div>
        </div>
      </Reveal>

      <Reveal delay={120}>
        <PortfolioInspector
          accent={accent}
          onScan={(result) => setData(current => ({ ...current, ...buildPortfolioProductData(result), portfolio: result }))}
        />
      </Reveal>

      {/* Stat Cards */}
      <div className="cc-stats-grid">
        <StatCard label={portfolioMode ? 'Skills Found' : 'Applications'} value={data.stats.totalApplications} accent={accent} trend={portfolioMode ? 'from portfolio' : 'past 6 months'} trendDir="up" delay={0} />
        <StatCard label={portfolioMode ? 'Project Links' : 'Response Rate'} value={data.stats.responseRate} suffix={portfolioMode ? '' : '%'} accent={portfolioMode ? 'var(--cc-teal)' : 'var(--cc-red)'} trend={portfolioMode ? 'public proof' : 'below 30% avg'} trendDir={portfolioMode ? 'up' : 'down'} delay={70} />
        <StatCard label={portfolioMode ? 'GitHub Links' : 'Interview Rate'} value={data.stats.interviewRate} suffix={portfolioMode ? '' : '%'} accent="var(--cc-orange)" trend={portfolioMode ? 'source proof' : 'below 12% avg'} trendDir={portfolioMode ? 'up' : 'down'} delay={140} />
        <StatCard label={portfolioMode ? 'Readiness' : 'Offer Rate'} value={data.stats.offerRate} suffix="%" decimals={portfolioMode ? 0 : 1} accent={portfolioMode ? 'var(--cc-teal)' : 'var(--cc-red)'} trend={portfolioMode ? 'portfolio score' : 'below 4% avg'} trendDir={portfolioMode ? 'up' : 'down'} delay={210} />
      </div>

      {/* Charts */}
      <Reveal delay={50}>
        <div className="cc-section-title">Analysis</div>
      </Reveal>
      <div className="cc-charts-grid" style={{ marginBottom: 'var(--cc-sp-6)' }}>
        <Reveal delay={0}>
          <div className="cc-chart-card">
            <div className="cc-card-title">{portfolioMode ? 'Portfolio Proof Coverage' : 'Rejection Rate by Role'}</div>
            <RejectionBars data={data.rejectionByRole} animate={true} />
          </div>
        </Reveal>
        <Reveal delay={100}>
          <div className="cc-chart-card">
            <div className="cc-card-title">{portfolioMode ? 'Public Proof Timeline' : 'GitHub Contribution Heatmap'}</div>
            <GithubHeatmap data={data.githubHeatmap} theme={theme} accent={accent} />
            <p style={{ fontSize: 12, color: 'var(--cc-text-muted)', marginTop: 12 }}>
              Weeks with 0 commits &rarr; 85% ghost rate. Active weeks &rarr; 34% ghost rate.
            </p>
          </div>
        </Reveal>
        <Reveal delay={50}>
          <div className="cc-chart-card">
            <div className="cc-card-title">Skill Gap Radar</div>
            <SkillRadar data={data.skillGap} theme={theme} accent={accent} chartStyle={tweaks.chartStyle} />
          </div>
        </Reveal>
        <Reveal delay={150}>
          <div className="cc-chart-card">
            <div className="cc-card-title">Application Timing vs Outcome</div>
            <TimingChart data={data.timing} theme={theme} accent={accent} chartStyle={tweaks.chartStyle} />
          </div>
        </Reveal>
      </div>

      {/* Insights */}
      <Reveal>
        <div className="cc-section-title">Recommended Actions</div>
      </Reveal>
      <div className="cc-insights">
        {data.insights.map((ins, i) => (
          <InsightCard key={ins.id} insight={ins} delay={i * 60} />
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { DashboardTab, AnimCounter, HealthGauge, PortfolioInspector, Reveal, useReveal });
