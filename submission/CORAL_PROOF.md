CORAL PROOF REPORT
===================
Total Coral Queries: 9
Cross-source JOINs: 2

Sources Used:
- github.activity
- github.profile
- linkedin.profile
- linkedin.skills
- notion.applications

Best Coral Query:
Query ID: q_007
Name: skill_gap_detection
Rows: 12
Execution: 0.79ms
SELECT skill, COUNT(*) as times_required, MAX(CASE WHEN in_github = true THEN 1 ELSE 0 END) as in_github, MAX(CASE WHEN in_linkedin = true THEN 1 ELSE 0 END) as in_linkedin FROM ( SELECT skill_name as skill, (g.languages LIKE '%' || skill_name || '%') as in_github, (l.skills LIKE '%' || skill_name || '%') as in_linkedin FROM ( SELECT UNNEST(n.required_skills) as skill_name FROM notion.applications n WHERE n.status = 'rejected' ) skills JOIN github.profile g JOIN linkedin.skills l ) sub GROUP BY skill ORDER BY times_required DESC LIMIT 15