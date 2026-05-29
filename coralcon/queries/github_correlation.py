from coralcon.utils.coral_client import run_query

SQL = """
SELECT
  n.company,
  n.applied_date,
  n.status,
  n.role_title,
  g.commits_count,
  g.active_repos,
  g.languages
FROM sheets.applications n
JOIN github.activity g
  ON g.week = date_trunc('week', n.applied_date)
WHERE n.status IN ('rejected', 'ghosted', 'interviewing', 'offer')
ORDER BY n.applied_date DESC
"""

SUMMARY_SQL = """
SELECT
  CASE WHEN g.commits_count > 0 THEN 'active' ELSE 'inactive' END as week_type,
  COUNT(*) as total,
  SUM(CASE WHEN n.status = 'ghosted' THEN 1 ELSE 0 END) as ghosted,
  ROUND(
    SUM(CASE WHEN n.status = 'ghosted' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1
  ) as ghost_rate
FROM sheets.applications n
JOIN github.activity g
  ON g.week = date_trunc('week', n.applied_date)
GROUP BY week_type
"""


def fetch() -> list[dict]:
    return run_query(SQL)


def fetch_summary() -> dict:
    rows = run_query(SUMMARY_SQL)
    result = {"ghost_rate_active_weeks": 0, "ghost_rate_inactive_weeks": 0}
    for row in rows:
        if row.get("week_type") == "active":
            result["ghost_rate_active_weeks"] = row.get("ghost_rate", 0)
        else:
            result["ghost_rate_inactive_weeks"] = row.get("ghost_rate", 0)
    return result
