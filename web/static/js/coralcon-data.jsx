// CoralCon Sample Data — Dramatic numbers for demo impact

const CORALCON_DATA = {
  stats: {
    totalApplications: 650,
    responseRate: 18,
    interviewRate: 6,
    offerRate: 1.5,
    healthScore: 31,
    reposScanned: 52,
    skillsMapped: 31,
    queriesRun: 9,
    crossSourceJoins: 6,
  },

  rejectionByRole: [
    { role: 'React Frontend', applied: 89, rejected: 84, rate: 94 },
    { role: 'Full Stack', applied: 127, rejected: 94, rate: 74 },
    { role: 'Vue / Angular', applied: 56, rejected: 39, rate: 70 },
    { role: 'AI / ML Engineer', applied: 78, rejected: 43, rate: 55 },
    { role: 'Python Backend', applied: 145, rejected: 51, rate: 35 },
    { role: 'DevOps / SRE', applied: 68, rejected: 17, rate: 25 },
    { role: 'Data Engineer', applied: 87, rejected: 19, rate: 22 },
  ],

  // 7 rows (days) x 26 cols (weeks) — values 0-4 for heatmap intensity
  githubHeatmap: (() => {
    const weeks = 26, days = 7;
    const data = [];
    for (let d = 0; d < days; d++) {
      const row = [];
      for (let w = 0; w < weeks; w++) {
        let base = w < 9 ? 0.3 : w < 17 ? 1.2 : 2.5;
        if (d >= 5) base *= 0.3;
        const val = Math.min(4, Math.max(0, Math.round(base + (Math.sin(w * 0.7 + d) * 1.2))));
        row.push(val);
      }
      data.push(row);
    }
    return data;
  })(),

  skillGap: {
    labels: ['TypeScript', 'Docker', 'React', 'Kubernetes', 'System Design', 'CI/CD', 'GraphQL', 'AWS'],
    demanded: [92, 78, 88, 65, 71, 82, 48, 74],
    present: [30, 15, 5, 10, 25, 20, 35, 18],
  },

  timing: [
    { day: 0, label: 'Same day', ghostRate: 18, responseRate: 42 },
    { day: 1, label: '1 day', ghostRate: 24, responseRate: 36 },
    { day: 2, label: '2 days', ghostRate: 32, responseRate: 28 },
    { day: 3, label: '3 days', ghostRate: 41, responseRate: 22 },
    { day: 5, label: '5 days', ghostRate: 56, responseRate: 14 },
    { day: 7, label: '1 week', ghostRate: 72, responseRate: 9 },
    { day: 10, label: '10 days', ghostRate: 81, responseRate: 5 },
    { day: 14, label: '2 weeks', ghostRate: 88, responseRate: 3 },
    { day: 21, label: '3 weeks', ghostRate: 94, responseRate: 1 },
  ],

  insights: [
    {
      id: 'insight_001',
      title: 'React Role Rejection Pattern',
      severity: 'critical',
      claim: 'React frontend roles have a 94% rejection rate — highest across all categories by 20 points.',
      rootCause: 'GitHub profile contains 0 React repositories. 52 repos scanned, all Python/ML focused. Recruiters see a Python engineer applying to React jobs.',
      action: 'Build and pin one production-quality React project within 7 days. Target: todo app with TypeScript, tests, and deployed demo.',
      impact: 'Projected improvement: React role response rate from 6% to ~35%.',
      evidence: { queryId: 'q_003', rows: 89, sources: ['notion.applications', 'github.repos'] },
      confidence: 0.91,
    },
    {
      id: 'insight_002',
      title: 'Application Timing Dead Zone',
      severity: 'critical',
      claim: 'Applications submitted 7+ days after posting have a 72% ghost rate. 67% of your applications fall in this window.',
      rootCause: 'Batch-applying weekly instead of monitoring new listings daily. By day 7, roles have 200+ applicants and recruiters stop reviewing.',
      action: 'Set up daily job alerts. Apply within 48 hours of posting. Prioritize speed over perfection in cover letters.',
      impact: 'Expected ghost rate reduction from 72% to ~30% for timely applications.',
      evidence: { queryId: 'q_005', rows: 435, sources: ['notion.applications'] },
      confidence: 0.87,
    },
    {
      id: 'insight_003',
      title: 'GitHub Activity Correlation',
      severity: 'high',
      claim: 'During weeks with 0 GitHub commits, ghosting rate was 85%. During active weeks (5+ commits), it dropped to 34%.',
      rootCause: 'Recruiters check GitHub profiles. Inactive contribution graphs signal disengagement or lack of passion for coding.',
      action: 'Maintain daily commits during active job search. Even small contributions (docs, tests) keep the graph green.',
      impact: 'Active GitHub weeks correlate with 2.5x higher response rate.',
      evidence: { queryId: 'q_002', rows: 156, sources: ['notion.applications', 'github.activity'] },
      confidence: 0.82,
    },
    {
      id: 'insight_004',
      title: 'TypeScript Skill Gap',
      severity: 'high',
      claim: 'TypeScript was required in 92% of rejected frontend applications. Your GitHub shows 0 TypeScript repos. LinkedIn lists JavaScript but not TypeScript.',
      rootCause: 'Market has shifted to TypeScript-first. JavaScript-only profiles are filtered out by automated screening.',
      action: 'Convert one existing project to TypeScript. Add TypeScript to LinkedIn skills. Target: 2 TS repos within 10 days.',
      impact: 'Closes the #1 skill gap across all rejected applications.',
      evidence: { queryId: 'q_003', rows: 247, sources: ['notion.applications', 'github.repos', 'linkedin.skills'] },
      confidence: 0.89,
    },
    {
      id: 'insight_005',
      title: 'Profile-Role Headline Mismatch',
      severity: 'medium',
      claim: 'LinkedIn headline says "Python Developer" but 45% of applications target "Frontend Engineer" or "Full Stack" roles. Automatic mismatch flag.',
      rootCause: 'Recruiters cross-reference LinkedIn with application. Headline mismatch triggers instant disqualification in ATS systems.',
      action: 'Update LinkedIn headline to "Software Engineer | Python & React" or role-neutral positioning.',
      impact: 'Removes ATS mismatch flag from ~290 future applications.',
      evidence: { queryId: 'q_006', rows: 293, sources: ['linkedin.profile', 'notion.applications'] },
      confidence: 0.78,
    },
    {
      id: 'insight_006',
      title: 'Follow-up Window Missed',
      severity: 'medium',
      claim: '23 applications have had no response for 14+ days. Follow-ups sent at day 10 historically had 22% response rate vs 3% at day 21.',
      rootCause: 'No systematic follow-up process. Applications are submitted and forgotten.',
      action: 'Send follow-up emails to 23 stale applications today. Set calendar reminders for day-10 follow-ups on all future applications.',
      impact: 'Expected to recover 4-5 responses from the 23 stale applications.',
      evidence: { queryId: 'q_007', rows: 23, sources: ['notion.applications'] },
      confidence: 0.74,
    },
  ],

  coralQueries: [
    {
      id: 'q_001', name: 'Rejection Pattern Analysis',
      sql: `SELECT\n  n.role_title,\n  COUNT(*) as total,\n  SUM(CASE WHEN n.status = 'rejected'\n    THEN 1 ELSE 0 END) as rejected,\n  ROUND(rejected * 100.0 / total, 1)\n    as rejection_rate\nFROM notion.applications n\nGROUP BY n.role_title\nORDER BY rejection_rate DESC`,
      sources: ['notion.applications'],
      crossSource: false, rows: 7, executionMs: 342, cached: false,
    },
    {
      id: 'q_002', name: 'GitHub Activity vs Response Rate',
      sql: `SELECT\n  n.company,\n  n.applied_date,\n  n.status,\n  g.commits_count,\n  g.active_repos\nFROM notion.applications n\nJOIN github.activity g\n  ON g.week = date_trunc(\n    'week', n.applied_date)\nWHERE n.status IN (\n  'rejected','ghosted',\n  'interviewing','offer')\nORDER BY n.applied_date DESC`,
      sources: ['notion.applications', 'github.activity'],
      crossSource: true, rows: 156, executionMs: 1240, cached: false,
    },
    {
      id: 'q_003', name: 'Skill Gap Detection',
      sql: `SELECT\n  n.required_skills,\n  g.languages,\n  l.skills as linkedin_skills\nFROM notion.applications n\nJOIN github.profile g\nJOIN linkedin.skills l\nWHERE n.status = 'rejected'`,
      sources: ['notion.applications', 'github.profile', 'linkedin.skills'],
      crossSource: true, rows: 247, executionMs: 1870, cached: false,
    },
    {
      id: 'q_004', name: 'Application Timing Patterns',
      sql: `SELECT\n  DATEDIFF(n.applied_date,\n    n.posted_date) as days_after,\n  COUNT(*) as total,\n  SUM(CASE WHEN n.status = 'ghosted'\n    THEN 1 ELSE 0 END) as ghosted,\n  ROUND(ghosted * 100.0 / total, 1)\n    as ghost_rate\nFROM notion.applications n\nGROUP BY days_after\nORDER BY days_after`,
      sources: ['notion.applications'],
      crossSource: false, rows: 22, executionMs: 287, cached: true,
    },
    {
      id: 'q_005', name: 'Cross-Source Career Profile',
      sql: `SELECT\n  g.username,\n  g.total_repos,\n  g.top_languages,\n  l.headline,\n  l.skills,\n  l.endorsements,\n  COUNT(n.id) as total_apps\nFROM github.profile g\nJOIN linkedin.profile l\nJOIN notion.applications n\nGROUP BY g.username`,
      sources: ['github.profile', 'linkedin.profile', 'notion.applications'],
      crossSource: true, rows: 1, executionMs: 2100, cached: false,
    },
    {
      id: 'q_006', name: 'LinkedIn Headline vs Applied Roles',
      sql: `SELECT\n  l.headline,\n  n.role_title,\n  COUNT(*) as times_applied,\n  SUM(CASE WHEN n.status = 'rejected'\n    THEN 1 ELSE 0 END) as rejections\nFROM linkedin.profile l\nJOIN notion.applications n\nGROUP BY l.headline, n.role_title\nHAVING rejections > 5`,
      sources: ['linkedin.profile', 'notion.applications'],
      crossSource: true, rows: 8, executionMs: 890, cached: false,
    },
    {
      id: 'q_007', name: 'Stale Application Tracker',
      sql: `SELECT\n  n.company,\n  n.role_title,\n  n.applied_date,\n  DATEDIFF(NOW(), n.applied_date)\n    as days_waiting\nFROM notion.applications n\nWHERE n.status = 'applied'\n  AND DATEDIFF(NOW(),\n    n.applied_date) > 14\nORDER BY days_waiting DESC`,
      sources: ['notion.applications'],
      crossSource: false, rows: 23, executionMs: 198, cached: true,
    },
    {
      id: 'q_008', name: 'GitHub Repo Language Distribution',
      sql: `SELECT\n  g.primary_language,\n  COUNT(*) as repo_count,\n  SUM(g.stars) as total_stars\nFROM github.repos g\nGROUP BY g.primary_language\nORDER BY repo_count DESC`,
      sources: ['github.repos'],
      crossSource: false, rows: 12, executionMs: 156, cached: true,
    },
    {
      id: 'q_009', name: 'Full Career Intelligence Join',
      sql: `SELECT\n  n.role_title,\n  n.status,\n  g.commits_count,\n  g.languages,\n  l.skills,\n  l.headline,\n  DATEDIFF(n.applied_date,\n    n.posted_date) as timing\nFROM notion.applications n\nJOIN github.activity g\n  ON g.week = date_trunc(\n    'week', n.applied_date)\nJOIN linkedin.skills l\nWHERE n.applied_date >\n  DATE_SUB(NOW(), INTERVAL 6 MONTH)`,
      sources: ['notion.applications', 'github.activity', 'linkedin.skills'],
      crossSource: true, rows: 312, executionMs: 3200, cached: false,
    },
  ],

  cohort: {
    candidates: [
      { name: 'Candidate A', score: 72, topIssue: 'Docker skill gap', trend: 'up' },
      { name: 'Candidate B', score: 58, topIssue: 'Inactive GitHub (3 weeks)', trend: 'down' },
      { name: 'Candidate C', score: 51, topIssue: 'LinkedIn headline mismatch', trend: 'up' },
      { name: 'Candidate D', score: 44, topIssue: 'Late applications (avg 9 days)', trend: 'flat' },
      { name: 'Candidate E', score: 39, topIssue: 'No TypeScript repos', trend: 'down' },
      { name: 'Candidate F', score: 35, topIssue: 'React skill gap + timing', trend: 'down' },
      { name: 'Candidate G', score: 31, topIssue: 'Multi-factor: 4 gaps detected', trend: 'down' },
      { name: 'Candidate H', score: 27, topIssue: 'Zero follow-ups sent', trend: 'flat' },
    ],
    commonGaps: [
      { skill: 'TypeScript', count: 41, pct: 85 },
      { skill: 'Docker', count: 29, pct: 60 },
      { skill: 'System Design', count: 22, pct: 46 },
      { skill: 'CI/CD', count: 19, pct: 40 },
      { skill: 'Kubernetes', count: 16, pct: 33 },
      { skill: 'AWS', count: 14, pct: 29 },
    ],
    actions: [
      'Run a 7-day TypeScript portfolio sprint for 10 candidates',
      'Fix LinkedIn headline mismatch for 8 candidates',
      'Prioritize Python backend roles for 5 candidates with strong Python profiles',
      'Set up daily job-alert automation for all 12 candidates',
    ],
  },

  cacheBenchmark: {
    query: 'skill_gap_detection_cross_source',
    run1Ms: 1870,
    run2Ms: 312,
    speedup: '6.0x',
  },
};

Object.assign(window, { CORALCON_DATA });
