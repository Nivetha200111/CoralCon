
  CORAL PROOF REPORT
  ==================

  Total Coral Queries:    10
  Cross-Source JOINs:     4
  Total Rows Returned:    190
  Total Execution Time:   14363.2ms
  Cached Queries:         5
  Cache Hit Rate:         50.0%
  Mode:                   real

  Sources Used:
    - github.activity
    - github.user_repos
    - linkedin.skills
    - sheets.applications

  Best Coral Query:
    Query ID:    q_003
    Name:        skill_gap_detection
    Sources:     github.user_repos, linkedin.skills, sheets.applications
    Rows:        15
    Execution:   7522.04ms
    Cached:      no
    SQL:         WITH demand AS ( SELECT TRIM(skill) AS skill, COUNT(*) AS times_required FROM ( SELECT UNNEST(string_to_array(n.required_skills, ';')) AS skill FROM sheets.applications n WHERE n.status = 'rejected' AND n.required_skills <> '' ) GROUP BY TRIM(skill) ), li AS (SELECT DISTINCT LOWER(name) AS name FROM linkedin.skills), gh AS (SELECT DISTINCT LOWER(language) AS lang FROM github.user_repos WHERE language IS NOT NULL) SELECT d.skill, d.times_required, MAX(CASE WHEN li.name LIKE '%' || LOWER(d.skill) || '%' THEN 1 ELSE 0 END) AS in_linkedin, MAX(CASE WHEN gh.lang = LOWER(d.skill) THEN 1 ELSE 0 END) AS in_github FROM demand d LEFT JOIN li ON li.name LIKE '%' || LOWER(d.skill) || '%' LEFT JOIN gh ON gh.lang = LOWER(d.skill) GROUP BY d.skill, d.times_required ORDER BY d.times_required DESC, in_linkedin ASC, in_github ASC LIMIT 15

  All Queries:
    q_001  rejection_patterns                39 rows    1018.9ms
    q_002  github_activity_correlation       40 rows    4193.9ms [CROSS-SOURCE]
    q_003  skill_gap_detection               15 rows    7522.0ms [CROSS-SOURCE]
    q_004  timing_analysis                    1 rows     791.1ms
    q_005  followup_tracker                   0 rows     837.2ms
    q_006  rejection_patterns                39 rows       0.0ms [CACHED]
    q_007  github_activity_correlation       40 rows       0.0ms [CROSS-SOURCE] [CACHED]
    q_008  skill_gap_detection               15 rows       0.0ms [CROSS-SOURCE] [CACHED]
    q_009  timing_analysis                    1 rows       0.0ms [CACHED]
    q_010  followup_tracker                   0 rows       0.0ms [CACHED]
