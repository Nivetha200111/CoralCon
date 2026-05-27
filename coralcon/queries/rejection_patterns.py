from coralcon.utils.coral_client import run_query

SQL = """
SELECT
  n.role_title,
  COUNT(*) as total,
  SUM(CASE WHEN n.status = 'rejected' THEN 1 ELSE 0 END) as rejected,
  SUM(CASE WHEN n.status = 'ghosted' THEN 1 ELSE 0 END) as ghosted,
  SUM(CASE WHEN n.status = 'interviewing' THEN 1 ELSE 0 END) as interviewed,
  SUM(CASE WHEN n.status = 'offer' THEN 1 ELSE 0 END) as offers,
  ROUND(
    SUM(CASE WHEN n.status = 'rejected' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1
  ) as rejection_rate,
  ROUND(
    SUM(CASE WHEN n.status = 'ghosted' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1
  ) as ghost_rate,
  ROUND(
    (SUM(CASE WHEN n.status IN ('interviewing', 'offer') THEN 1 ELSE 0 END)) * 100.0 / COUNT(*), 1
  ) as response_rate
FROM notion.applications n
GROUP BY n.role_title
ORDER BY rejection_rate DESC
"""


def fetch() -> list[dict]:
    return run_query(SQL)
