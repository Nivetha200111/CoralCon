
  CORAL PROOF REPORT
  ==================

  Total Coral Queries:    9
  Cross-Source JOINs:     2
  Total Rows Returned:    98
  Total Execution Time:   13.6ms
  Cached Queries:         0
  Mode:                   sample

  Sources Used:
    - github.activity
    - github.profile
    - linkedin.profile
    - linkedin.skills
    - sheets.applications

  Best Coral Query:
    Query ID:    q_007
    Name:        skill_gap_detection
    Sources:     github.profile, linkedin.skills, sheets.applications
    Rows:        12
    Execution:   1.46ms
    Cached:      no
    SQL:         SELECT skill, COUNT(*) as times_required, MAX(CASE WHEN in_github = true THEN 1 ELSE 0 END) as in_github, MAX(CASE WHEN in_linkedin = true THEN 1 ELSE 0 END) as in_linkedin FROM ( SELECT skill_name as skill, (g.languages LIKE '%' || skill_name || '%') as in_github, (l.name LIKE '%' || skill_name || '%') as in_linkedin FROM ( SELECT UNNEST(n.required_skills) as skill_name FROM sheets.applications n WHERE n.status = 'rejected' ) skills JOIN github.profile g JOIN linkedin.skills l ) sub GROUP BY skill ORDER BY times_required DESC LIMIT 15

  All Queries:
    q_001  applications                       8 rows       1.3ms
    q_002  github_activity                   20 rows       2.1ms
    q_003  linkedin_profile                   1 rows       1.9ms
    q_004  linkedin_skills                    8 rows       1.0ms
    q_005  rejection_patterns                 6 rows       1.1ms
    q_006  github_activity_correlation       26 rows       1.2ms [CROSS-SOURCE]
    q_007  skill_gap_detection               12 rows       1.5ms [CROSS-SOURCE]
    q_008  timing_analysis                    5 rows       1.0ms
    q_009  followup_tracker                  12 rows       2.6ms
