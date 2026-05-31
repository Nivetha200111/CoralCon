
  CORAL PROOF REPORT
  ==================

  Total Coral Queries:    9
  Cross-Source JOINs:     2
  Total Rows Returned:    98
  Total Execution Time:   19.7ms
  Cached Queries:         0
  Cache Hit Rate:         0.0%
  Mode:                   sample

  Sources Used:
    - github.activity
    - github.user_repos
    - linkedin.profile
    - linkedin.skills
    - sheets.applications

  Best Coral Query:
    Query ID:    q_007
    Name:        skill_gap_detection
    Sources:     github.user_repos, linkedin.skills, sheets.applications
    Rows:        12
    Execution:   4.93ms
    Cached:      no
    SQL:         WITH demand AS ( SELECT TRIM(skill) AS skill, COUNT(*) AS times_required FROM ( SELECT UNNEST(string_to_array(n.required_skills, ';')) AS skill FROM sheets.applications n WHERE n.status = 'rejected' AND n.required_skills <> '' ) GROUP BY TRIM(skill) ), li AS (SELECT DISTINCT LOWER(name) AS name FROM linkedin.skills), gh AS (SELECT DISTINCT LOWER(language) AS lang FROM github.user_repos WHERE language IS NOT NULL) SELECT d.skill, d.times_required, MAX(CASE WHEN li.name LIKE '%' || LOWER(d.skill) || '%' THEN 1 ELSE 0 END) AS in_linkedin, MAX(CASE WHEN gh.lang = LOWER(d.skill) THEN 1 ELSE 0 END) AS in_github FROM demand d LEFT JOIN li ON li.name LIKE '%' || LOWER(d.skill) || '%' LEFT JOIN gh ON gh.lang = LOWER(d.skill) GROUP BY d.skill, d.times_required ORDER BY d.times_required DESC, in_linkedin ASC, in_github ASC LIMIT 15

  All Queries:
    q_001  applications                       8 rows       1.8ms
    q_002  github_activity                   20 rows       1.0ms
    q_003  linkedin_profile                   1 rows       0.9ms
    q_004  linkedin_skills                    8 rows       1.1ms
    q_005  rejection_patterns                 6 rows       1.5ms
    q_006  github_activity_correlation       26 rows       3.8ms [CROSS-SOURCE]
    q_007  skill_gap_detection               12 rows       4.9ms [CROSS-SOURCE]
    q_008  timing_analysis                    5 rows       3.8ms
    q_009  followup_tracker                  12 rows       0.9ms
