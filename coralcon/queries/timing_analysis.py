from coralcon.utils.coral_client import run_query

SQL = """
SELECT
  CASE
    WHEN days_to_apply <= 1 THEN 'same_day'
    WHEN days_to_apply <= 2 THEN '1-2_days'
    WHEN days_to_apply <= 7 THEN '3-7_days'
    WHEN days_to_apply <= 14 THEN '1-2_weeks'
    ELSE '2_weeks_plus'
  END as timing_bucket,
  COUNT(*) as total,
  ROUND(
    SUM(CASE WHEN status IN ('interviewing', 'offer') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1
  ) as response_rate,
  ROUND(
    SUM(CASE WHEN status = 'ghosted' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1
  ) as ghost_rate
FROM notion.applications
GROUP BY timing_bucket
ORDER BY
  CASE timing_bucket
    WHEN 'same_day' THEN 1
    WHEN '1-2_days' THEN 2
    WHEN '3-7_days' THEN 3
    WHEN '1-2_weeks' THEN 4
    ELSE 5
  END
"""


def fetch() -> list[dict]:
    return run_query(SQL)
