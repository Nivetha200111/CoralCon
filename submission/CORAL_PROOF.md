
  CORAL PROOF REPORT
  ==================

  Total Coral Queries:    9
  Cross-Source JOINs:     2
  Total Rows Returned:    106
  Total Execution Time:   0.7ms
  Cached Queries:         0
  Mode:                   sample

  Sources Used:
    - github.activity
    - github.profile
    - linkedin.profile
    - linkedin.skills
    - notion.applications

  Best Coral Query:
    Query ID:    q_007
    Name:        skill_gap_detection
    Sources:     github.profile, linkedin.skills, notion.applications
    Rows:        12
    Execution:   0.06ms
    Cached:      no
    SQL:         SELECT skill, COUNT(*) as times_required, MAX(CASE WHEN in_github = true THEN 1 ELSE 0 END) as in_github, MAX(CASE WHEN in_linkedin = true THEN 1 ELSE 0 END) as in_linkedin FROM ( SELECT skill_name as skill, (g.languages LIKE '%' || skill_name || '%') as in_github, (l.name LIKE '%' || skill_name || '%') as in_linkedin FROM ( SELECT UNNEST(n.required_skills) as skill_name FROM notion.applications n WHERE n.status = 'rejected' ) skills JOIN github.profile g JOIN linkedin.skills l ) sub GROUP BY skill ORDER BY times_required DESC LIMIT 15

  All Queries:
    q_001  applications                       8 rows       0.1ms
    q_002  github_activity                   20 rows       0.1ms
    q_003  linkedin_profile                   8 rows       0.1ms
    q_004  linkedin_skills                    8 rows       0.1ms
    q_005  rejection_patterns                 6 rows       0.1ms
    q_006  github_activity_correlation       26 rows       0.1ms [CROSS-SOURCE]
    q_007  skill_gap_detection               12 rows       0.1ms [CROSS-SOURCE]
    q_008  timing_analysis                    6 rows       0.1ms
    q_009  followup_tracker                  12 rows       0.1ms
