// CoralCon Ask — natural-language question box backed by the deterministic router.
// The LLM only classifies intent + narrates; every answer runs a fixed Coral query.

const { useState: useAskState } = React;

const ASK_SUGGESTIONS = [
  'Which roles reject me the most?',
  'What skills am I missing?',
  'Does my GitHub activity affect responses?',
  'When should I apply to get a response?',
  'Who should I follow up with?',
];

function AskTab({ tweaks }) {
  const accent = tweaks.accentColor || '#f0a500';
  const [question, setQuestion] = useAskState('');
  const [loading, setLoading] = useAskState(false);
  const [error, setError] = useAskState('');
  const [answer, setAnswer] = useAskState(null);

  async function runAsk(q) {
    const text = (q ?? question).trim();
    if (!text || loading) return;
    setQuestion(text);
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text }),
      });
      if (!res.ok) throw new Error(`Ask API returned ${res.status}`);
      const payload = await res.json();
      if (payload.error) throw new Error(payload.error);
      setAnswer(payload);
    } catch (err) {
      setError(err.message || 'Unable to answer that right now.');
      setAnswer(null);
    } finally {
      setLoading(false);
    }
  }

  const proof = answer && answer.proof ? answer.proof : null;
  const sources = proof && proof.sources ? proof.sources : [];
  const isCross = proof && (proof.is_cross_source || sources.length > 1);

  return (
    <div className="cc-ask">
      <div className="cc-page-header">
        <div className="cc-page-title">Ask CoralCon</div>
        <div className="cc-page-subtitle">
          Ask in plain English. CoralCon picks the right Coral query, runs it on your
          data, and answers with real numbers — the AI never invents facts.
        </div>
      </div>

      <div className="cc-card" style={{ marginBottom: 'var(--cc-sp-4)' }}>
        <form
          onSubmit={(e) => { e.preventDefault(); runAsk(); }}
          style={{ display: 'flex', gap: 'var(--cc-sp-2)', flexWrap: 'wrap' }}
        >
          <input
            className="cc-portfolio-input"
            style={{ flex: '1 1 320px' }}
            type="text"
            value={question}
            placeholder="e.g. Which roles reject me the most?"
            onChange={(e) => setQuestion(e.target.value)}
            aria-label="Ask a question about your job search"
          />
          <button
            className="cc-portfolio-button"
            type="submit"
            disabled={loading || !question.trim()}
          >
            {loading ? 'Asking…' : 'Ask'}
          </button>
        </form>

        <div style={{ display: 'flex', gap: 'var(--cc-sp-2)', flexWrap: 'wrap', marginTop: 'var(--cc-sp-3)' }}>
          {ASK_SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              className="cc-skill-chip"
              style={{ cursor: 'pointer', border: 'none' }}
              onClick={() => runAsk(s)}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="cc-card cc-portfolio-error" style={{ marginBottom: 'var(--cc-sp-4)' }}>
          {error}
        </div>
      )}

      {answer && !error && (
        <div className="cc-card cc-tab-enter">
          <div className="cc-card-title" style={{ color: accent }}>
            {answer.headline}
          </div>

          {answer.narrative && answer.narrative !== answer.headline && (
            <p style={{ marginTop: 'var(--cc-sp-2)', lineHeight: 1.6 }}>
              {answer.narrative}
            </p>
          )}

          <div className="cc-query-meta" style={{ marginTop: 'var(--cc-sp-4)' }}>
            <span className="cc-query-meta-item">
              Coral query: <strong>{answer.queryName}</strong>
            </span>
            <span className="cc-query-meta-item">
              Routed by: <strong>{answer.classifiedBy === 'llm' ? 'AI intent match' : 'keyword match'}</strong>
            </span>
            <span className="cc-query-meta-item">
              Narrative: <strong>{answer.narrativeSource === 'llm' ? 'AI from rows' : 'deterministic'}</strong>
            </span>
            <span className="cc-query-meta-item">
              Rows: <strong>{answer.rowCount}</strong>
            </span>
            {isCross && <span className="cc-badge-cross">cross-source JOIN</span>}
          </div>

          {sources.length > 0 && (
            <div style={{ display: 'flex', gap: 'var(--cc-sp-2)', flexWrap: 'wrap', marginTop: 'var(--cc-sp-3)' }}>
              {sources.map((src) => (
                <span key={src} className="cc-source-pill">{src}</span>
              ))}
            </div>
          )}

          <div style={{ marginTop: 'var(--cc-sp-3)', fontSize: 12, color: 'var(--cc-text-muted)' }}>
            {answer.usingSampleData
              ? 'Answered from demo data. Connect Coral to query your real sources.'
              : 'Answered from your live Coral sources.'}
          </div>
        </div>
      )}
    </div>
  );
}

Object.assign(window, { AskTab });
