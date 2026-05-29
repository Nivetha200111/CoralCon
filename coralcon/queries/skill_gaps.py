from coralcon.utils.coral_client import run_query

SQL = """
SELECT
  skill,
  COUNT(*) as times_required,
  MAX(CASE WHEN in_github = true THEN 1 ELSE 0 END) as in_github,
  MAX(CASE WHEN in_linkedin = true THEN 1 ELSE 0 END) as in_linkedin
FROM (
  SELECT
    skill_name as skill,
    (g.languages LIKE '%' || skill_name || '%') as in_github,
    (l.name LIKE '%' || skill_name || '%') as in_linkedin
  FROM (
    SELECT UNNEST(n.required_skills) as skill_name
    FROM sheets.applications n
    WHERE n.status = 'rejected'
  ) skills
  JOIN github.profile g
  JOIN linkedin.skills l
) sub
GROUP BY skill
ORDER BY times_required DESC
LIMIT 15
"""


def fetch() -> list[dict]:
    return run_query(SQL)
