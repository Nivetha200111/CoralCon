// CoralCon default client state. Real values are loaded from /api/*.

const CORALCON_DATA = {
  stats: {
    totalApplications: 0,
    responseRate: 0,
    interviewRate: 0,
    offerRate: 0,
    healthScore: 0,
    reposScanned: 0,
    skillsMapped: 0,
    queriesRun: 0,
    crossSourceJoins: 0,
  },
  rejectionByRole: [],
  githubHeatmap: [],
  skillGap: { labels: [], demanded: [], present: [] },
  timing: [],
  insights: [],
  coralQueries: [],
  cohort: { candidates: [], commonGaps: [], actions: [] },
  cacheBenchmark: {
    query: 'skill_gap_detection_cross_source',
    run1Ms: 0,
    run2Ms: 0,
    speedup: '0x',
  },
  portfolio: null,
  usingSampleData: false,
};

Object.assign(window, { CORALCON_DATA });
