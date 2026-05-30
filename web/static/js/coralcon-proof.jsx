// CoralCon Coral Proof Tab — SQL queries, sources, execution metrics

/* ====== SQL SYNTAX HIGHLIGHTER ====== */
function HighlightedSQL({ sql }) {
  const keywords = /\b(SELECT|FROM|JOIN|WHERE|ON|GROUP BY|ORDER BY|HAVING|AND|OR|NOT|AS|IN|CASE|WHEN|THEN|ELSE|END|DESC|ASC|LIMIT|COUNT|SUM|ROUND|AVG|MAX|MIN|DISTINCT|INTERVAL|DATEDIFF|DATE_SUB|NOW)\b/gi;
  const strings = /'[^']*'/g;
  const tables = /\b(sheets\.\w+|github\.\w+|linkedin\.\w+)\b/g;
  const functions = /\b(date_trunc|ROUND|COUNT|SUM|AVG|DATEDIFF|DATE_SUB|NOW)\b/gi;

  let html = sql
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(strings, m => `<span class="str">${m}</span>`)
    .replace(tables, m => `<span class="tbl">${m}</span>`)
    .replace(functions, m => `<span class="fn">${m}</span>`)
    .replace(keywords, m => `<span class="kw">${m.toUpperCase()}</span>`);

  return <div className="cc-sql-block" dangerouslySetInnerHTML={{ __html: html }} />;
}

/* ====== QUERY CARD ====== */
function QueryCard({ query, accent }) {
  const [expanded, setExpanded] = React.useState(true);

  return (
    <div className="cc-query-card" style={{ marginBottom: 'var(--cc-sp-4)' }}>
      <div className="cc-query-header" style={{ cursor: 'pointer' }} onClick={() => setExpanded(!expanded)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cc-sp-3)' }}>
          <CCIcon name="code" size={16} style={{ color: accent }} />
          <span className="cc-query-name">{query.name}</span>
        </div>
        <div className="cc-query-badges">
          {query.crossSource && <span className="cc-badge-cross">Cross-Source</span>}
          {query.cached && <span className="cc-badge-cross cc-badge-cached">Cached</span>}
        </div>
      </div>
      {expanded && (
        <>
          <HighlightedSQL sql={query.sql} />
          <div className="cc-query-meta">
            <div className="cc-query-meta-item">
              <CCIcon name="layers" size={14} />
              <span>Sources: <strong>{query.sources.join(', ')}</strong></span>
            </div>
            <div className="cc-query-meta-item">
              <CCIcon name="clock" size={14} />
              <span>Execution: <strong>{query.executionMs}ms</strong></span>
            </div>
            <div className="cc-query-meta-item">
              <CCIcon name="database" size={14} />
              <span>Rows: <strong>{query.rows}</strong></span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/* ====== PROOF TAB ====== */
function ProofTab({ tweaks }) {
  const [liveProof, setLiveProof] = React.useState(null);
  const accent = tweaks.accentColor || '#f0a500';

  React.useEffect(() => {
    fetch('/api/proof').then(r => r.json()).then(ps => {
      if (ps.queries && ps.queries.length > 0) {
        setLiveProof(ps);
      }
    }).catch(() => {});
  }, []);

  const queries = liveProof ? liveProof.queries.map(q => ({
    id: q.query_id,
    name: q.query_name,
    sql: q.sql,
    sources: q.sources_used || [],
    crossSource: q.is_cross_source,
    rows: q.rows_returned,
    executionMs: q.execution_ms,
    cached: q.used_cache,
  })) : [];
  const crossSourceCount = queries.filter(q => q.crossSource).length;
  const totalRows = queries.reduce((s, q) => s + q.rows, 0);
  const allSources = [...new Set(queries.flatMap(q => q.sources))];
  const avgExec = queries.length ? Math.round(queries.reduce((s, q) => s + q.executionMs, 0) / queries.length) : 0;
  const cachedCount = queries.filter(q => q.cached).length;
  const hitRate = liveProof && liveProof.cache_hit_rate != null
    ? liveProof.cache_hit_rate
    : (queries.length ? Math.round(cachedCount * 100 / queries.length) : 0);
  const mode = liveProof ? liveProof.mode : 'sample';
  const bestCross = queries.filter(q => q.crossSource).sort((a, b) => b.sources.length - a.sources.length || b.rows - a.rows)[0];

  return (
    <div>
      <div className="cc-page-header">
        <h1 className="cc-page-title">How It Works</h1>
        <span className="cc-page-subtitle">Every data query CoralCon ran, with sources and results</span>
        <span className={`cc-mode-badge ${mode === 'real' ? 'real' : 'sample'}`}>
          {mode === 'real' ? 'LIVE CORAL' : 'SAMPLE MODE'}
        </span>
      </div>
      <div className="cc-card" style={{ marginBottom: 'var(--cc-sp-6)', padding: 'var(--cc-sp-5)' }}>
        <p style={{ fontSize: 14, color: 'var(--cc-text-secondary)', lineHeight: 1.7 }}>
          CoralCon uses <strong style={{ color: 'var(--cc-text-primary)' }}>Coral SQL</strong> to query your GitHub, Google Sheets, and LinkedIn data as if they were database tables.
          Instead of writing three separate API integrations, Coral lets us write one SQL query that joins data across all sources.
          Every query below is real — you can see exactly what data was pulled and how conclusions were reached.
        </p>
      </div>

      {/* Summary Stats */}
      <Reveal>
      <div className="cc-proof-stats">
        <div className="cc-stat-card">
          <div className="cc-stat-label">Total Coral Queries</div>
          <div className="cc-stat-value" style={{ color: accent }}><AnimCounter target={queries.length} /></div>
          <div style={{ fontSize: 12, color: 'var(--cc-text-muted)' }}>{crossSourceCount} cross-source JOINs</div>
        </div>
        <div className="cc-stat-card">
          <div className="cc-stat-label">Data Sources</div>
          <div className="cc-stat-value" style={{ color: 'var(--cc-teal)' }}><AnimCounter target={allSources.length} /></div>
          <div style={{ fontSize: 12, color: 'var(--cc-text-muted)' }}>GitHub + Sheets + LinkedIn</div>
        </div>
        <div className="cc-stat-card">
          <div className="cc-stat-label">Rows Returned</div>
          <div className="cc-stat-value" style={{ color: 'var(--cc-blue)' }}><AnimCounter target={totalRows} /></div>
          <div style={{ fontSize: 12, color: 'var(--cc-text-muted)' }}>avg {avgExec}ms / query</div>
        </div>
        <div className="cc-stat-card">
          <div className="cc-stat-label">Cache Hit Rate</div>
          <div className="cc-stat-value" style={{ color: 'var(--cc-orange)' }}><AnimCounter target={hitRate} suffix="%" /></div>
          <div style={{ fontSize: 12, color: 'var(--cc-text-muted)' }}>
            {cachedCount} of {queries.length} queries cached
          </div>
        </div>
      </div>
      </Reveal>

      {/* Best Cross-Source Query — the headline proof */}
      {bestCross && (
        <Reveal delay={40}>
        <div className="cc-section-title">Best Cross-Source Query</div>
        <div className="cc-query-card cc-best-query" style={{ marginBottom: 'var(--cc-sp-6)', borderColor: accent }}>
          <div className="cc-query-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--cc-sp-3)' }}>
              <CCIcon name="zap" size={16} style={{ color: accent }} />
              <span className="cc-query-name">{bestCross.name}</span>
            </div>
            <div className="cc-query-badges">
              <span className="cc-badge-cross">{bestCross.sources.length} sources joined</span>
              {bestCross.cached && <span className="cc-badge-cross cc-badge-cached">Cached</span>}
            </div>
          </div>
          <HighlightedSQL sql={bestCross.sql} />
          <div className="cc-query-meta">
            <div className="cc-query-meta-item">
              <CCIcon name="layers" size={14} />
              <span>Sources: <strong>{bestCross.sources.join(', ')}</strong></span>
            </div>
            <div className="cc-query-meta-item">
              <CCIcon name="clock" size={14} />
              <span>Execution: <strong>{bestCross.executionMs}ms</strong></span>
            </div>
            <div className="cc-query-meta-item">
              <CCIcon name="database" size={14} />
              <span>Rows: <strong>{bestCross.rows}</strong></span>
            </div>
          </div>
          <p style={{ fontSize: 13, color: 'var(--cc-text-muted)', marginTop: 'var(--cc-sp-3)' }}>
            One SQL statement joins {bestCross.sources.length} sources. Without Coral this would need
            {' '}{bestCross.sources.length} separate API integrations and custom correlation logic.
          </p>
        </div>
        </Reveal>
      )}

      {/* Sources Used */}
      <Reveal delay={80}>
      <div className="cc-section-title">Sources Queried</div>
      <div style={{ display: 'flex', gap: 'var(--cc-sp-3)', flexWrap: 'wrap', marginBottom: 'var(--cc-sp-6)' }}>
        {allSources.map(src => {
          const platform = src.split('.')[0];
          const icon = platform === 'github' ? 'gitBranch' : platform === 'sheets' ? 'database' : 'link';
          return (
            <span key={src} className="cc-source-pill" style={{ fontSize: 13 }}>
              <CCIcon name={icon} size={14} /> {src}
            </span>
          );
        })}
      </div>
      </Reveal>

      {/* Cache Benchmark */}
      <Reveal delay={60}>
      <div className="cc-section-title">Cache Benchmark</div>
      <div className="cc-card" style={{ marginBottom: 'var(--cc-sp-6)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--cc-sp-4)' }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>Repeated Query Speedup</div>
            <div style={{ fontSize: 13, color: 'var(--cc-text-muted)' }}>
              Query: <span style={{ fontFamily: 'var(--cc-font-mono)', color: 'var(--cc-text-secondary)' }}>skill_gap_detection_cross_source</span>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontFamily: 'var(--cc-font-display)', fontSize: 32, fontWeight: 700, color: 'var(--cc-teal)' }}>
              {liveProof && liveProof.cache_hit_rate ? `${liveProof.cache_hit_rate}%` : '0%'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--cc-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Speedup</div>
          </div>
        </div>
        <CacheBars run1={0} run2={0} />
        <p style={{ fontSize: 12, color: 'var(--cc-text-muted)', marginTop: 12, fontStyle: 'italic' }}>
          Coral avoids repeated expensive API/file retrieval during agent analysis.
        </p>
      </div>
      </Reveal>

      {/* All Queries */}
      <Reveal>
        <div className="cc-section-title">All Coral Queries ({queries.length})</div>
      </Reveal>
      {queries.length === 0 && (
        <div className="cc-card" style={{ color: 'var(--cc-text-muted)' }}>
          No proof queries have been logged yet. Import data or run an analysis to populate this view.
        </div>
      )}
      {queries.map((q, i) => (
        <Reveal key={q.id} delay={i * 50}>
          <QueryCard query={q} accent={accent} />
        </Reveal>
      ))}

      {/* Why Coral */}
      <Reveal delay={100}>
      <div className="cc-card" style={{ marginTop: 'var(--cc-sp-6)', borderColor: accent, background: 'var(--cc-gold-dim)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--cc-sp-4)' }}>
          <CCIcon name="zap" size={24} style={{ color: accent, flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 6 }}>Why Coral Is at the Core</div>
            <p style={{ fontSize: 14, color: 'var(--cc-text-secondary)', lineHeight: 1.7, marginBottom: 8 }}>
              Coral SQL is the central data layer. Without it, CoralCon would need three separate
              API integrations with custom auth, pagination, schema mapping, and correlation logic.
              With Coral, the agent asks one SQL question across all sources.
            </p>
            <p style={{ fontSize: 14, color: 'var(--cc-text-secondary)', lineHeight: 1.7 }}>
              The {crossSourceCount} cross-source JOINs above are what make evidence-backed insights
              possible. Joining <code>sheets.applications</code> with <code>github.activity</code> and{' '}
              <code>linkedin.skills</code> proves whether your profile signals match role requirements.
            </p>
          </div>
        </div>
      </div>
      </Reveal>
    </div>
  );
}

Object.assign(window, { ProofTab, HighlightedSQL });
