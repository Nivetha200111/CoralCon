// CoralCon Charts — Chart.js wrappers + custom visualizations

const { useRef, useEffect, useState, useCallback } = React;

/* ====== CHART.JS THEME HELPER ====== */
function getChartColors(theme, accent) {
  const isDark = theme === 'dark';
  // Editorial palette: rust primary, deep forest secondary, warm inks.
  return {
    grid: isDark ? 'rgba(236,229,216,0.08)' : 'rgba(27,26,23,0.08)',
    text: isDark ? '#b3a994' : '#5c574d',
    gold: accent || (isDark ? '#d96a4f' : '#b4452f'),
    teal: isDark ? '#6fae9a' : '#3f6b5e',
    red: isDark ? '#df6b54' : '#b4452f',
    blue: isDark ? '#8aa6c2' : '#3a5a78',
    purple: isDark ? '#b59bc9' : '#6b4e8a',
    orange: isDark ? '#d68a4a' : '#c2722c',
    bgCard: isDark ? '#221f18' : '#fffdf8',
  };
}

/* ====== REJECTION BAR CHART (custom CSS) ====== */
function RejectionBars({ data, animate }) {
  const [show, setShow] = useState(false);
  useEffect(() => { if (animate) { const t = setTimeout(() => setShow(true), 200); return () => clearTimeout(t); } }, [animate]);

  const getSeverity = (rate) => {
    if (rate >= 80) return 'critical';
    if (rate >= 60) return 'high';
    if (rate >= 40) return 'medium';
    return 'low';
  };

  return (
    <div className="cc-bars">
      {data.map((d, i) => (
        <div className="cc-bar-row" key={d.role} style={{ animationDelay: `${i * 60}ms` }}>
          <span className="cc-bar-label" title={d.role}>{d.role}</span>
          <div className="cc-bar-track">
            <div
              className={`cc-bar-fill ${getSeverity(d.rate)}`}
              style={{ width: show ? `${d.rate}%` : '0%' }}
            >
              {d.rate}%
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ====== GITHUB HEATMAP (custom CSS grid) ====== */
function GithubHeatmap({ data, theme, accent }) {
  const colors = getChartColors(theme, accent);
  const isDark = theme === 'dark';

  const cellColor = (val) => {
    if (val === 0) return isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.04)';
    const levels = isDark
      ? ['rgba(32,201,160,0.15)', 'rgba(32,201,160,0.35)', 'rgba(32,201,160,0.6)', 'rgba(32,201,160,0.9)']
      : ['rgba(14,168,126,0.15)', 'rgba(14,168,126,0.3)', 'rgba(14,168,126,0.5)', 'rgba(14,168,126,0.8)'];
    return levels[Math.min(val - 1, 3)];
  };

  const dayLabels = ['Mon', '', 'Wed', '', 'Fri', '', ''];
  const flat = [];
  if (data && data.length > 0) {
    for (let w = 0; w < data[0].length; w++) {
      for (let d = 0; d < data.length; d++) {
        flat.push({ val: data[d][w], week: w, day: d });
      }
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', gap: 4, alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 3, paddingTop: 0, marginRight: 4 }}>
          {dayLabels.map((l, i) => (
            <span key={i} style={{ fontSize: 10, color: 'var(--cc-text-muted)', height: 14, lineHeight: '14px', width: 24 }}>{l}</span>
          ))}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: `repeat(26, 1fr)`, gridTemplateRows: `repeat(7, 1fr)`, gap: 3, flex: 1 }}>
          {flat.map((c, i) => (
            <div
              key={i}
              className="cc-heatmap-cell"
              style={{ background: cellColor(c.val), aspectRatio: '1' }}
              title={`Week ${c.week + 1}, ${['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][c.day]}: ${c.val} commits`}
            />
          ))}
        </div>
      </div>
      <div className="cc-heatmap-labels" style={{ marginLeft: 32 }}>
        <span>26 weeks ago</span>
        <span>Now</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 8, marginLeft: 32, fontSize: 11, color: 'var(--cc-text-muted)' }}>
        <span>Less</span>
        {[0, 1, 2, 3, 4].map(v => (
          <div key={v} style={{ width: 12, height: 12, borderRadius: 2, background: cellColor(v) }} />
        ))}
        <span>More</span>
      </div>
    </div>
  );
}

/* ====== RADAR CHART (Chart.js) ====== */
function SkillRadar({ data, theme, accent, chartStyle }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || !data) return;
    const c = getChartColors(theme, accent);
    const filled = chartStyle !== 'outlined';

    if (chartRef.current) chartRef.current.destroy();

    chartRef.current = new Chart(canvasRef.current, {
      type: 'radar',
      data: {
        labels: data.labels,
        datasets: [
          {
            label: 'Demanded in Rejected Apps (%)',
            data: data.demanded,
            borderColor: c.red,
            backgroundColor: filled ? (theme === 'dark' ? 'rgba(255,107,107,0.12)' : 'rgba(220,38,38,0.08)') : 'transparent',
            borderWidth: 2, pointRadius: 3, pointBackgroundColor: c.red,
          },
          {
            label: 'Present in Your Profile (%)',
            data: data.present,
            borderColor: c.teal,
            backgroundColor: filled ? (theme === 'dark' ? 'rgba(32,201,160,0.12)' : 'rgba(14,168,126,0.08)') : 'transparent',
            borderWidth: 2, pointRadius: 3, pointBackgroundColor: c.teal,
          },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        scales: {
          r: {
            beginAtZero: true, max: 100,
            grid: { color: c.grid },
            angleLines: { color: c.grid },
            pointLabels: { color: c.text, font: { family: "'DM Sans'", size: 11, weight: '500' } },
            ticks: { display: false },
          },
        },
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: c.text, font: { family: "'DM Sans'", size: 11 }, boxWidth: 12, padding: 16 },
          },
        },
        animation: { duration: 1200, easing: 'easeOutQuart' },
      },
    });

    return () => { if (chartRef.current) chartRef.current.destroy(); };
  }, [data, theme, accent, chartStyle]);

  return <canvas ref={canvasRef} />;
}

/* ====== TIMING LINE CHART (Chart.js) ====== */
function TimingChart({ data, theme, accent, chartStyle }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || !data) return;
    const c = getChartColors(theme, accent);
    const filled = chartStyle !== 'outlined';

    if (chartRef.current) chartRef.current.destroy();

    chartRef.current = new Chart(canvasRef.current, {
      type: 'line',
      data: {
        labels: data.map(d => d.label),
        datasets: [
          {
            label: 'Ghost Rate (%)',
            data: data.map(d => d.ghostRate),
            borderColor: c.red,
            backgroundColor: filled ? (theme === 'dark' ? 'rgba(255,107,107,0.08)' : 'rgba(220,38,38,0.05)') : 'transparent',
            fill: filled, tension: 0.4, borderWidth: 2,
            pointRadius: 4, pointBackgroundColor: c.bgCard, pointBorderColor: c.red, pointBorderWidth: 2,
          },
          {
            label: 'Response Rate (%)',
            data: data.map(d => d.responseRate),
            borderColor: c.teal,
            backgroundColor: filled ? (theme === 'dark' ? 'rgba(32,201,160,0.08)' : 'rgba(14,168,126,0.05)') : 'transparent',
            fill: filled, tension: 0.4, borderWidth: 2,
            pointRadius: 4, pointBackgroundColor: c.bgCard, pointBorderColor: c.teal, pointBorderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        scales: {
          x: {
            grid: { color: c.grid },
            ticks: { color: c.text, font: { family: "'DM Sans'", size: 11 } },
            title: { display: true, text: 'Days After Job Posted', color: c.text, font: { family: "'DM Sans'", size: 12 } },
          },
          y: {
            grid: { color: c.grid },
            ticks: { color: c.text, font: { family: "'DM Sans'", size: 11 }, callback: v => v + '%' },
            min: 0, max: 100,
          },
        },
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: c.text, font: { family: "'DM Sans'", size: 11 }, boxWidth: 12, padding: 16 },
          },
          tooltip: {
            callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y}%` },
          },
        },
        animation: { duration: 1200, easing: 'easeOutQuart' },
      },
    });

    return () => { if (chartRef.current) chartRef.current.destroy(); };
  }, [data, theme, accent, chartStyle]);

  return <canvas ref={canvasRef} />;
}

/* ====== CACHE BENCHMARK BARS ====== */
function CacheBars({ run1, run2 }) {
  const [show, setShow] = useState(false);
  useEffect(() => { const t = setTimeout(() => setShow(true), 300); return () => clearTimeout(t); }, []);
  const max = Math.max(run1, run2);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ width: 60, fontSize: 13, color: 'var(--cc-text-muted)' }}>Run 1</span>
        <div className="cc-bar-track" style={{ flex: 1 }}>
          <div className="cc-bar-fill medium" style={{ width: show ? `${(run1 / max) * 100}%` : '0%' }}>{run1}ms</div>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ width: 60, fontSize: 13, color: 'var(--cc-text-muted)' }}>Run 2</span>
        <div className="cc-bar-track" style={{ flex: 1 }}>
          <div className="cc-bar-fill low" style={{ width: show ? `${(run2 / max) * 100}%` : '0%' }}>{run2}ms</div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { RejectionBars, GithubHeatmap, SkillRadar, TimingChart, CacheBars, getChartColors });
