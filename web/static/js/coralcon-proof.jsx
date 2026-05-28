// CoralCon Coral Proof Tab — SQL queries, sources, execution metrics

/* ====== SQL SYNTAX HIGHLIGHTER ====== */
function HighlightedSQL({ sql }) {
  const keywords = /\b(SELECT|FROM|JOIN|WHERE|ON|GROUP BY|ORDER BY|HAVING|AND|OR|NOT|AS|IN|CASE|WHEN|THEN|ELSE|END|DESC|ASC|LIMIT|COUNT|SUM|ROUND|AVG|MAX|MIN|DISTINCT|INTERVAL|DATEDIFF|DATE_SUB|NOW)\b/gi;
  const strings = /'[^']*'/g;
  const tables = /\b(notion\.\w+|github\.\w+|linkedin\.\w+)\b/g;
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
  const data = CORALCON_DATA;
  const accent = tweaks.accentColor || '#f0a500';
  const queries = data.coralQueries;
  const crossSourceCount = queries.filter(q => q.crossSource).length;
  const totalRows = queries.reduce((s, q) => s + q.rows, 0);
  const allSources = [...new Set(queries.flatMap(q => q.sources))];
  const avgExec = Math.round(queries.reduce((s, q) => s + q.executionMs, 0) / queries.length);
  const cachedCount = queries.filter(q => q.cached).length;

  return (
    <div>
      <div className="cc-page-header">
        <h1 className="cc-page-title">Coral Proof</h1>
        <span className="cc-page-subtitle">Every query. Every source. Every JOIN. Verified.</span>
      </div>

      {/* Summary Stats */}
      <Reveal>
      <div className="cc-proof-stats">
        <div className="cc-stat-card">
          <div className="cc-stat-label">Total Queries</div>
          <div className="cc-stat-value" style={{ color: accent }}><AnimCounter target={queries.length} /></div>
          <div style={{ fontSize: 12, color: 'var(--cc-text-muted)' }}>{crossSourceCount} cross-source JOINs</div>
        </div>
        <div className="cc-stat-card">
          <div className="cc-stat-label">Data Sources</div>
          <div className="cc-stat-value" style={{ color: 'var(--cc-teal)' }}><AnimCounter target={allSources.length} /></div>
          <div style={{ fontSize: 12, color: 'var(--cc-text-muted)' }}>across 3 platforms</div>
        </div>
        <div className="cc-stat-card">
          <div className="cc-stat-label">Total Rows Processed</div>
          <div className="cc-stat-value" style={{ color: 'var(--cc-blue)' }}><AnimCounter target={totalRows} /></div>
          <div style={{ fontSize: 12, color: 'var(--cc-text-muted)' }}>avg {avgExec}ms / query</div>
        </div>
      </div>
      </Reveal>

      {/* Sources Used */}
      <Reveal delay={80}>
      <div className="cc-section-title">Sources Queried</div>
      <div style={{ display: 'flex', gap: 'var(--cc-sp-3)', flexWrap: 'wrap', marginBottom: 'var(--cc-sp-6)' }}>
        {allSources.map(src => {
          const platform = src.split('.')[0];
          const icon = platform === 'github' ? 'gitBranch' : platform === 'notion' ? 'fileText' : 'link';
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
              Query: <span style={{ fontFamily: 'var(--cc-font-mono)', color: 'var(--cc-text-secondary)' }}>{data.cacheBenchmark.query}</span>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontFamily: 'var(--cc-font-display)', fontSize: 32, fontWeight: 700, color: 'var(--cc-teal)' }}>
              {data.cacheBenchmark.speedup}
            </div>
            <div style={{ fontSize: 11, color: 'var(--cc-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Speedup</div>
          </div>
        </div>
        <CacheBars run1={data.cacheBenchmark.run1Ms} run2={data.cacheBenchmark.run2Ms} />
        <p style={{ fontSize: 12, color: 'var(--cc-text-muted)', marginTop: 12, fontStyle: 'italic' }}>
          Coral avoids repeated expensive API/file retrieval during agent analysis.
        </p>
      </div>
      </Reveal>

      {/* All Queries */}
      <Reveal>
        <div className="cc-section-title">All Coral Queries ({queries.length})</div>
      </Reveal>
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
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 6 }}>Why Coral Is Essential</div>
            <p style={{ fontSize: 14, color: 'var(--cc-text-secondary)', lineHeight: 1.7 }}>
              Without Coral, CoralCon would need separate GitHub, Notion, and LinkedIn integrations
              plus custom pagination, auth, schema mapping, and correlation logic. With Coral,
              the agent asks one SQL question across all sources.
            </p>
          </div>
        </div>
      </div>
      </Reveal>
    </div>
  );
}

Object.assign(window, { ProofTab, HighlightedSQL });
