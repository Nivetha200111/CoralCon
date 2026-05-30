// CoralCon Cohort Tab — Multi-candidate analysis for enterprise/bootcamp framing

function CohortTab({ tweaks }) {
  const [data, setData] = React.useState(CORALCON_DATA.cohort);
  const accent = tweaks.accentColor || '#f0a500';
  const candidates = data.candidates || [];
  const gaps = data.commonGaps || data.common_gaps || [];
  const actions = data.actions || [];

  React.useEffect(() => {
    fetch('/api/cohort')
      .then(r => r.ok ? r.json() : null)
      .then(payload => {
        if (payload) {
          setData({
            candidates: (payload.candidates || payload.leaderboard || []).map(item => ({
              name: item.name || item.candidate || 'Candidate',
              score: item.score || item.health_score || 0,
              topIssue: item.topIssue || item.best_fit || payload.most_common_rejection_cause || 'Needs review',
            })),
            commonGaps: (payload.common_gaps || payload.commonGaps || payload.top_missing_skills || []).map(item => ({
              skill: item.skill || 'Skill',
              count: item.count || item.times_required || 0,
              pct: item.pct || Math.min(100, (item.times_required || item.count || 0) * 10),
            })),
            actions: payload.actions || payload.placement_actions || [],
          });
        }
      })
      .catch(() => {});
  }, []);

  const scoreColor = (score) => {
    if (score >= 60) return 'var(--cc-teal)';
    if (score >= 40) return accent;
    return 'var(--cc-red)';
  };

  const barColor = (score) => {
    if (score >= 60) return 'var(--cc-teal)';
    if (score >= 40) return accent;
    return 'var(--cc-red)';
  };

  return (
    <div>
      <div className="cc-page-header">
        <h1 className="cc-page-title">Team Analysis</h1>
        <span className="cc-page-subtitle">For bootcamps, colleges, and career coaches managing multiple candidates</span>
      </div>

      {/* Cohort Summary */}
      <Reveal>
      <div className="cc-proof-stats" style={{ marginBottom: 'var(--cc-sp-6)' }}>
        <div className="cc-stat-card">
          <div className="cc-stat-label">Candidates</div>
          <div className="cc-stat-value" style={{ color: accent }}><AnimCounter target={candidates.length} /></div>
          <div style={{ fontSize: 12, color: 'var(--cc-text-muted)' }}>analyzed this cohort</div>
        </div>
        <div className="cc-stat-card">
          <div className="cc-stat-label">Avg Health Score</div>
          <div className="cc-stat-value" style={{ color: 'var(--cc-red)' }}>
            <AnimCounter target={candidates.length ? Math.round(candidates.reduce((s, c) => s + c.score, 0) / candidates.length) : 0} />
          </div>
          <div style={{ fontSize: 12, color: 'var(--cc-text-muted)' }}>below 50 threshold</div>
        </div>
        <div className="cc-stat-card">
          <div className="cc-stat-label">Skill Gaps Found</div>
          <div className="cc-stat-value" style={{ color: 'var(--cc-orange)' }}><AnimCounter target={gaps.length} /></div>
          <div style={{ fontSize: 12, color: 'var(--cc-text-muted)' }}>common across cohort</div>
        </div>
      </div>
      </Reveal>

      {/* Leaderboard */}
      <div className="cc-section-title">Candidate Health Scores</div>
      <div className="cc-leaderboard" style={{ marginBottom: 'var(--cc-sp-6)' }}>
        {candidates.length === 0 && (
          <div className="cc-card" style={{ color: 'var(--cc-text-muted)' }}>
            No cohort data is loaded yet.
          </div>
        )}
        {candidates.map((c, i) => (
          <Reveal key={i} delay={i * 50}>
          <div className="cc-leaderboard-row">
            <div className="cc-rank">{i + 1}</div>
            <div>
              <div className="cc-candidate-name">{c.name}</div>
              <div className="cc-candidate-issue">
                <CCIcon name="alertTriangle" size={11} style={{ display: 'inline', verticalAlign: '-1px', marginRight: 4, color: 'var(--cc-orange)' }} />
                {c.topIssue}
              </div>
            </div>
            <div className="cc-mini-bar">
              <div className="cc-mini-bar-fill" style={{ width: `${c.score}%`, background: barColor(c.score) }} />
            </div>
            <div className="cc-score-val" style={{ color: scoreColor(c.score) }}>{c.score}/100</div>
          </div>
          </Reveal>
        ))}
      </div>

      {/* Common Skill Gaps */}
      <Reveal>
      <div className="cc-section-title">Most Common Skill Gaps</div>
      </Reveal>
      <Reveal delay={60}>
      <div className="cc-card" style={{ marginBottom: 'var(--cc-sp-6)' }}>
        <div className="cc-bars">
          {gaps.map((g, i) => (
            <div className="cc-bar-row" key={g.skill}>
              <span className="cc-bar-label" style={{ width: 120 }}>
                {g.skill}
                <span style={{ fontSize: 11, color: 'var(--cc-text-muted)', marginLeft: 6 }}>({g.count})</span>
              </span>
              <div className="cc-bar-track">
                <div className="cc-bar-fill medium" style={{ width: `${g.pct}%`, background: accent }}>{g.pct}%</div>
              </div>
            </div>
          ))}
        </div>
        <p style={{ fontSize: 12, color: 'var(--cc-text-muted)', marginTop: 16 }}>
          Percentage of candidates missing each skill in their GitHub/LinkedIn profiles.
        </p>
      </div>
      </Reveal>

      {/* Placement Team Actions */}
      <div className="cc-section-title">Placement Team Recommendations</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--cc-sp-3)' }}>
        {actions.map((action, i) => (
          <Reveal key={i} delay={i * 70}>
          <div className="cc-check-item">
            <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'var(--cc-gold-dim)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: accent, fontWeight: 700, fontSize: 13 }}>
              {i + 1}
            </div>
            <div className="cc-check-text">
              <span style={{ fontSize: 14, color: 'var(--cc-text-primary)' }}>{action}</span>
            </div>
          </div>
          </Reveal>
        ))}
      </div>

      {/* Enterprise Framing */}
      <Reveal delay={100}>
      <div className="cc-card" style={{ marginTop: 'var(--cc-sp-7)', borderColor: 'var(--cc-blue)', background: 'var(--cc-blue-dim)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--cc-sp-4)' }}>
          <CCIcon name="users" size={24} style={{ color: 'var(--cc-blue)', flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 6 }}>Enterprise Cohort Mode</div>
            <p style={{ fontSize: 14, color: 'var(--cc-text-secondary)', lineHeight: 1.7 }}>
              Placement teams, bootcamps, and colleges can use CoralCon to diagnose why candidates
              are failing across applications, portfolios, and profile positioning — all through
              Coral SQL queries over their aggregated data.
            </p>
          </div>
        </div>
      </div>
      </Reveal>
    </div>
  );
}

Object.assign(window, { CohortTab });
