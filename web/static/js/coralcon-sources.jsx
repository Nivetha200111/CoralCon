// CoralCon Sources/Import — connect Google and pull rejections from Gmail,
// entirely from the dashboard. No terminal, nothing run locally.

const { useState: useSrcState, useEffect: useSrcEffect } = React;

function SourcesTab({ tweaks }) {
  const accent = tweaks.accentColor || '#b4452f';
  const [google, setGoogle] = useSrcState(null);       // { connected, token_path }
  const [loadingStatus, setLoadingStatus] = useSrcState(true);
  const [importing, setImporting] = useSrcState(false);
  const [result, setResult] = useSrcState(null);
  const [error, setError] = useSrcState('');
  const [maxResults, setMaxResults] = useSrcState(50);
  const [query, setQuery] = useSrcState('');
  const [useAi, setUseAi] = useSrcState(true);
  const [writeSheet, setWriteSheet] = useSrcState(true);
  const [banner, setBanner] = useSrcState('');

  // Surface the ?google=connected / ?google=error redirect from the OAuth callback.
  useSrcEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const g = params.get('google');
    if (g === 'connected') setBanner('Google connected. You can import from Gmail now.');
    else if (g === 'error') setBanner(`Google connection failed${params.get('reason') ? ': ' + params.get('reason') : ''}.`);
    if (g) {
      // Clean the query string so a refresh doesn't re-trigger the banner.
      window.history.replaceState({}, '', '/sources');
    }
  }, []);

  function refreshStatus() {
    setLoadingStatus(true);
    fetch('/api/google/status')
      .then(r => r.ok ? r.json() : null)
      .then(s => setGoogle(s))
      .catch(() => setGoogle(null))
      .finally(() => setLoadingStatus(false));
  }

  useSrcEffect(refreshStatus, []);

  function connectGoogle() {
    window.location.href = '/api/google/connect';
  }

  async function runImport() {
    if (importing) return;
    setImporting(true);
    setError('');
    setResult(null);
    try {
      const res = await fetch('/api/gmail/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query.trim() || null,
          max_results: Number(maxResults) || 50,
          use_ai: useAi,
          write_sheet: writeSheet,
        }),
      });
      const payload = await res.json();
      if (!res.ok || payload.ok === false || payload.error) {
        throw new Error(payload.error || `Import failed (${res.status})`);
      }
      setResult(payload);
    } catch (err) {
      setError(err.message || 'Import failed.');
    } finally {
      setImporting(false);
    }
  }

  const connected = google && google.connected;

  return (
    <div className="cc-ask">
      <div className="cc-page-header">
        <div className="cc-page-title">Import Your Data</div>
        <div className="cc-page-subtitle">
          Connect Google and pull rejection emails into your tracker. CoralCon
          parses the data, updates your report, and keeps the workflow in the
          browser.
        </div>
      </div>

      {banner && (
        <div className="cc-card" style={{ marginBottom: 'var(--cc-sp-4)', borderColor: accent }}>
          {banner}
        </div>
      )}

      {/* Step 1 — Connect Google */}
      <div className="cc-card" style={{ marginBottom: 'var(--cc-sp-4)' }}>
        <div className="cc-card-title" style={{ color: accent }}>1 · Connect Google</div>
        <p style={{ marginTop: 'var(--cc-sp-2)', lineHeight: 1.6 }}>
          Grants read-only Gmail access (to find rejection emails) and Sheets access
          (to keep your tracker in sync). You can revoke it any time in your Google
          account settings.
        </p>
        <div style={{ display: 'flex', gap: 'var(--cc-sp-2)', alignItems: 'center', marginTop: 'var(--cc-sp-3)', flexWrap: 'wrap' }}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            fontSize: 13, color: 'var(--cc-text-muted)',
          }}>
            <span style={{
              width: 8, height: 8, borderRadius: '50%',
              background: connected ? 'var(--cc-teal)' : 'var(--cc-gold)',
            }} />
            {loadingStatus ? 'Checking…' : connected ? 'Connected' : 'Not connected'}
          </span>
          <button className="cc-portfolio-button" type="button" onClick={connectGoogle}>
            {connected ? 'Reconnect Google' : 'Connect Google'}
          </button>
        </div>
      </div>

      {/* Step 2 — Import */}
      <div className="cc-card" style={{ marginBottom: 'var(--cc-sp-4)' }}>
        <div className="cc-card-title" style={{ color: accent }}>2 · Pull rejections</div>
        <p style={{ marginTop: 'var(--cc-sp-2)', lineHeight: 1.6 }}>
          Scans your inbox for rejection emails, extracts the company and role, and
          adds them to your tracker. Existing rows are kept — your manual edits win.
        </p>
        <div style={{ display: 'flex', gap: 'var(--cc-sp-2)', alignItems: 'center', marginTop: 'var(--cc-sp-3)', flexWrap: 'wrap' }}>
          <label style={{ fontSize: 13, color: 'var(--cc-text-muted)', flex: '1 1 260px' }}>
            Gmail search
            <input
              className="cc-portfolio-input"
              style={{ width: '100%', marginTop: 6 }}
              type="text"
              placeholder='Default: rejection and application-decision emails'
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          <label style={{ fontSize: 13, color: 'var(--cc-text-muted)' }}>
            Scan up to&nbsp;
            <input
              className="cc-portfolio-input"
              style={{ width: 80 }}
              type="number"
              min="1"
              max="200"
              value={maxResults}
              onChange={(e) => setMaxResults(e.target.value)}
            />
            &nbsp;emails
          </label>
          <label style={{ fontSize: 13, color: 'var(--cc-text-muted)', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <input type="checkbox" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} />
            AI classify
          </label>
          <label style={{ fontSize: 13, color: 'var(--cc-text-muted)', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <input type="checkbox" checked={writeSheet} onChange={(e) => setWriteSheet(e.target.checked)} />
            Write Sheet
          </label>
          <button
            className="cc-portfolio-button"
            type="button"
            onClick={runImport}
            disabled={!connected || importing}
            title={connected ? '' : 'Connect Google first'}
          >
            {importing ? 'Importing…' : 'Import from Gmail'}
          </button>
        </div>
        {!connected && !loadingStatus && (
          <div style={{ marginTop: 'var(--cc-sp-2)', fontSize: 12, color: 'var(--cc-text-muted)' }}>
            Connect Google above to enable importing.
          </div>
        )}
      </div>

      {error && (
        <div className="cc-card cc-portfolio-error" style={{ marginBottom: 'var(--cc-sp-4)' }}>
          {error}
        </div>
      )}

      {result && !error && (
        <div className="cc-card cc-tab-enter">
          <div className="cc-card-title" style={{ color: accent }}>
            Imported {result.extracted} email{result.extracted === 1 ? '' : 's'}
          </div>
          <div className="cc-query-meta" style={{ marginTop: 'var(--cc-sp-3)' }}>
            <span className="cc-query-meta-item">New rows: <strong>{result.added}</strong></span>
            <span className="cc-query-meta-item">Tracker total: <strong>{result.totalApplications}</strong></span>
            <span className="cc-query-meta-item">
              Google Sheet: <strong>{result.sheetWritten ? 'updated' : 'not configured'}</strong>
            </span>
          </div>
          {result.sheetError && (
            <div style={{ marginTop: 'var(--cc-sp-2)', fontSize: 12, color: 'var(--cc-text-muted)' }}>
              Sheet sync skipped: {result.sheetError}
            </div>
          )}

          {result.rowsPreview && result.rowsPreview.length > 0 && (
            <div style={{ marginTop: 'var(--cc-sp-4)', overflowX: 'auto' }}>
              <table className="cc-table" style={{ width: '100%', fontSize: 13 }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Company</th>
                    <th style={{ textAlign: 'left' }}>Role</th>
                    <th style={{ textAlign: 'left' }}>Status</th>
                    <th style={{ textAlign: 'left' }}>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {result.rowsPreview.map((row, i) => (
                    <tr key={i}>
                      <td>{row.company || '—'}</td>
                      <td>{row.role_title || '—'}</td>
                      <td>{row.status || '—'}</td>
                      <td>{row.responded_date || row.applied_date || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div style={{ marginTop: 'var(--cc-sp-3)', fontSize: 12, color: 'var(--cc-text-muted)' }}>
            Your report has been updated. Open <strong>My Report</strong> to see the new numbers.
          </div>
        </div>
      )}
    </div>
  );
}

Object.assign(window, { SourcesTab });
