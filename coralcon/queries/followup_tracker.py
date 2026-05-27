from coralcon.utils.coral_client import run_query

SQL = """
SELECT
  n.company,
  n.role_title,
  n.applied_date,
  DATEDIFF('day', n.applied_date, CURRENT_DATE) as days_waiting,
  CASE
    WHEN DATEDIFF('day', n.applied_date, CURRENT_DATE) BETWEEN 7 AND 14 THEN 'hot'
    WHEN DATEDIFF('day', n.applied_date, CURRENT_DATE) BETWEEN 15 AND 21 THEN 'warm'
    ELSE 'cold'
  END as priority,
  CASE
    WHEN DATEDIFF('day', n.applied_date, CURRENT_DATE) BETWEEN 7 AND 14
      THEN 'Send follow-up email now (22% success rate at day 10)'
    WHEN DATEDIFF('day', n.applied_date, CURRENT_DATE) BETWEEN 15 AND 21
      THEN 'Last chance follow-up (8% success rate)'
    ELSE 'Move on — mark as ghosted'
  END as recommended_action
FROM notion.applications n
WHERE n.status = 'applied'
  AND DATEDIFF('day', n.applied_date, CURRENT_DATE) >= 7
ORDER BY days_waiting ASC
"""


def fetch() -> list[dict]:
    return run_query(SQL)
