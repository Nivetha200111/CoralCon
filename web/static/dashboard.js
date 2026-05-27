/* CoralCon Dashboard — fetches from FastAPI, renders charts + tables */

const CYAN   = '#00d4ff';
const GREEN  = '#00ff88';
const RED    = '#ff3b3b';
const AMBER  = '#ffb800';
const PURPLE = '#9b59ff';
const MUTED  = '#555';
const BORDER = '#1e1e1e';

Chart.defaults.color = '#666';
Chart.defaults.borderColor = '#1e1e1e';
Chart.defaults.font.family = "'JetBrains Mono', monospace";
Chart.defaults.font.size = 11;

// ── SECTION NAV ──────────────────────────────────────────────────────────────
function showSection(name) {
  document.querySelectorAll('section[id^="section-"]').forEach(s => s.style.display = 'none');
  document.getElementById('section-' + name).style.display = '';
  document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
  event.currentTarget.classList.add('active');
}

// ── FETCH HELPERS ─────────────────────────────────────────────────────────────
async function get(url) {
  const res = await fetch(url);
  return res.json();
}

// ── SUMMARY STATS ─────────────────────────────────────────────────────────────
async function loadSummary() {
  const d = await get('/api/summary');
  document.getElementById('stat-total').textContent     = d.total_applications;
  document.getElementById('stat-response').textContent  = d.response_rate + '%';
  document.getElementById('stat-interview').textContent = d.interview_rate + '%';
  document.getElementById('stat-offer').textContent     = d.offer_rate + '%';

  const badge = document.getElementById('data-badge');
  badge.textContent = d.using_sample_data ? 'SAMPLE DATA' : 'LIVE DATA';
  badge.className   = 'badge ' + (d.using_sample_data ? 'badge-sample' : 'badge-live');

  document.getElementById('last-updated').textContent =
    'updated ' + new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
}

// ── REJECTION BARS ────────────────────────────────────────────────────────────
function rateColor(rate) {
  if (rate >= 70) return RED;
  if (rate >= 45) return AMBER;
  return GREEN;
}

function renderRejectionBars(patterns, containerId) {
  const el = document.getElementById(containerId);
  el.innerHTML = '';
  const wrap = document.createElement('div');
  wrap.className = 'rejection-list';

  patterns.forEach(p => {
    const rate  = p.rejection_rate || 0;
    const color = rateColor(rate);
    const row   = document.createElement('div');
    row.className = 'rejection-row';
    row.innerHTML = `
      <div class="rejection-meta">
        <span class="rejection-role">${p.role_title}</span>
        <span class="rejection-rate" style="color:${color}">${rate.toFixed(0)}%</span>
      </div>
      <div class="rejection-bar-track">
        <div class="rejection-bar-fill" style="width:0%;background:${color}" data-target="${rate}"></div>
      </div>
      <div class="rejection-sub">
        <span>${p.total} applied</span>
        <span style="color:${RED}">${p.rejected} rejected</span>
        <span style="color:${MUTED}">${p.ghosted} ghosted</span>
        <span style="color:${GREEN}">${p.offers} offers</span>
      </div>`;
    wrap.appendChild(row);
  });

  el.appendChild(wrap);
  // animate bars after render
  requestAnimationFrame(() => {
    document.querySelectorAll('.rejection-bar-fill').forEach(bar => {
      bar.style.width = bar.dataset.target + '%';
    });
  });
}

async function loadRejections() {
  const patterns = await get('/api/rejections');
  document.getElementById('rej-total-badge').textContent = patterns.length + ' roles';
  document.getElementById('nav-rejection-count').textContent = patterns.length;
  renderRejectionBars(patterns, 'rejection-bars');
  renderRejectionBars(patterns, 'rejection-detail');
}

// ── SKILL GAPS ────────────────────────────────────────────────────────────────
async function loadSkillGaps() {
  const gaps = await get('/api/skills');
  document.getElementById('nav-gap-count').textContent = gaps.length;

  const el = document.getElementById('skill-list');
  el.innerHTML = '';

  const criticalCount = gaps.filter(g => g.priority === 'critical').length;
  gaps.forEach(g => {
    const row = document.createElement('div');
    row.className = 'skill-row';
    const pillClass = `priority-pill p-${g.priority}`;
    row.innerHTML = `
      <span class="skill-name">${g.skill}</span>
      <span class="skill-count">${g.times_required} rejections</span>
      <span class="skill-check">${g.in_github ? '<span class="check-yes">✓</span>' : '<span class="check-no">✗</span>'}</span>
      <span class="skill-check">${g.in_linkedin ? '<span class="check-yes">✓</span>' : '<span class="check-no">✗</span>'}</span>
      <span><span class="${pillClass}">${g.priority.toUpperCase()}</span></span>`;
    el.appendChild(row);
  });
}

// ── GITHUB SIGNAL ─────────────────────────────────────────────────────────────
let githubChartMain = null;
let githubChartDetail = null;

async function loadGithub() {
  const data = await get('/api/github');
  const signal = data.signal || {};
  const rows   = data.rows || [];

  // sidebar stat
  const activeGhost   = signal.ghost_rate_active_weeks   || 0;
  const inactiveGhost = signal.ghost_rate_inactive_weeks || 0;

  const ghActive   = document.getElementById('gh-active');
  const ghInactive = document.getElementById('gh-inactive');
  if (ghActive)   ghActive.textContent   = activeGhost.toFixed(0) + '%';
  if (ghInactive) ghInactive.textContent = inactiveGhost.toFixed(0) + '%';

  // collect weeks
  const weeks   = [...new Set(rows.map(r => r.week || ''))].sort().slice(-16);
  const commits  = weeks.map(w => {
    const r = rows.find(x => x.week === w);
    return r ? (r.commits_count || 0) : 0;
  });
  const ghosted  = weeks.map(w => rows.filter(r => r.week === w && r.status === 'ghosted').length);
  const response = weeks.map(w => rows.filter(r => r.week === w && ['interviewing','offer'].includes(r.status)).length);

  const labels = weeks.map(w => w.slice(5)); // MM-DD

  const cfg = {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Commits',
          data: commits,
          backgroundColor: 'rgba(0,212,255,0.18)',
          borderColor: CYAN,
          borderWidth: 1,
          yAxisID: 'y1',
          type: 'line',
          tension: 0.3,
          fill: true,
          pointRadius: 0,
        },
        {
          label: 'Ghosted',
          data: ghosted,
          backgroundColor: 'rgba(255,59,59,0.5)',
          borderColor: RED,
          borderWidth: 0,
          yAxisID: 'y',
        },
        {
          label: 'Response',
          data: response,
          backgroundColor: 'rgba(0,255,136,0.5)',
          borderColor: GREEN,
          borderWidth: 0,
          yAxisID: 'y',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { position: 'top', labels: { boxWidth: 10, padding: 16, usePointStyle: true } } },
      scales: {
        x: { grid: { color: BORDER }, ticks: { maxRotation: 0 } },
        y: { grid: { color: BORDER }, beginAtZero: true, title: { display: true, text: 'Applications' } },
        y1: { position: 'right', grid: { drawOnChartArea: false }, beginAtZero: true, title: { display: true, text: 'Commits' } },
      },
    },
  };

  if (githubChartMain) githubChartMain.destroy();
  if (githubChartDetail) githubChartDetail.destroy();

  const ctx1 = document.getElementById('github-chart');
  if (ctx1) githubChartMain = new Chart(ctx1, JSON.parse(JSON.stringify(cfg)));

  const ctx2 = document.getElementById('github-chart-detail');
  if (ctx2) githubChartDetail = new Chart(ctx2, cfg);
}

// ── TIMING CHART ──────────────────────────────────────────────────────────────
let timingChartMain   = null;
let timingChartDetail = null;

async function loadTiming() {
  const data = await get('/api/timing');
  const labels    = data.map(d => d.timing_bucket.replace(/_/g, ' '));
  const response  = data.map(d => d.response_rate);
  const ghost     = data.map(d => d.ghost_rate);

  const cfg = {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Response Rate %',
          data: response,
          backgroundColor: 'rgba(0,255,136,0.4)',
          borderColor: GREEN,
          borderWidth: 1,
        },
        {
          label: 'Ghost Rate %',
          data: ghost,
          backgroundColor: 'rgba(255,59,59,0.3)',
          borderColor: RED,
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'top', labels: { boxWidth: 10, padding: 16, usePointStyle: true } } },
      scales: {
        x: { grid: { color: BORDER } },
        y: { grid: { color: BORDER }, beginAtZero: true, max: 100,
          ticks: { callback: v => v + '%' } },
      },
    },
  };

  if (timingChartMain)   timingChartMain.destroy();
  if (timingChartDetail) timingChartDetail.destroy();

  const ctx1 = document.getElementById('timing-chart');
  if (ctx1) timingChartMain = new Chart(ctx1, JSON.parse(JSON.stringify(cfg)));

  const ctx2 = document.getElementById('timing-chart-detail');
  if (ctx2) timingChartDetail = new Chart(ctx2, cfg);
}

// ── FOLLOW-UPS ────────────────────────────────────────────────────────────────
async function loadFollowups() {
  const data = await get('/api/followup');
  document.getElementById('nav-followup-count').textContent = data.length;
  document.getElementById('followup-badge').textContent = data.length + ' pending';

  const el = document.getElementById('followup-list');
  el.innerHTML = '';

  if (!data.length) {
    el.innerHTML = '<div class="loading" style="color:#00ff88">✓ No pending follow-ups</div>';
    return;
  }

  const priorityIcon = { hot: '●', warm: '◐', cold: '○' };
  const priorityClass = { hot: 'hot-dot', warm: 'warm-dot', cold: 'cold-dot' };

  data.forEach(f => {
    const row = document.createElement('div');
    row.className = 'followup-row';
    const pc = priorityClass[f.priority] || 'cold-dot';
    const pi = priorityIcon[f.priority]  || '○';
    row.innerHTML = `
      <span class="followup-company">${f.company}</span>
      <span class="followup-role">${f.role_title}</span>
      <span class="followup-days" style="color:${f.priority==='hot'?RED:f.priority==='warm'?AMBER:MUTED}">${f.days_waiting}d</span>
      <span class="followup-priority"><span class="${pc}">${pi} ${f.priority.toUpperCase()}</span></span>`;
    el.appendChild(row);
  });
}

// ── ACTION ITEMS ──────────────────────────────────────────────────────────────
function renderActions(actions, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = '';
  const list = document.createElement('div');
  list.className = 'action-list';
  actions.forEach((a, i) => {
    const item = document.createElement('div');
    item.className = 'action-item';
    item.innerHTML = `<span class="action-num">${String(i+1).padStart(2,'0')}</span><span class="action-text">${a}</span>`;
    list.appendChild(item);
  });
  el.appendChild(list);
}

async function loadActions() {
  const data = await get('/api/actions');
  renderActions(data.actions || [], 'action-list-overview');
  renderActions(data.actions || [], 'action-list-full');
}

// ── BOOT ──────────────────────────────────────────────────────────────────────
async function init() {
  await Promise.all([
    loadSummary(),
    loadRejections(),
    loadSkillGaps(),
    loadGithub(),
    loadTiming(),
    loadFollowups(),
    loadActions(),
  ]);
}

document.addEventListener('DOMContentLoaded', init);
