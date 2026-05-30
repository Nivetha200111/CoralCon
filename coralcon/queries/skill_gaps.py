from coralcon.utils.coral_client import run_query

# Flagship cross-source query: which skills do the roles that rejected you demand,
# and are those skills actually visible on your LinkedIn profile and in your real
# GitHub repos? Joins three Coral sources in one statement:
#   sheets.applications  - required skills per rejected role (inferred from title)
#   linkedin.skills      - skills you list on LinkedIn
#   github.user_repos    - languages you actually ship code in
# A skill with times_required high but in_linkedin = 0 and in_github = 0 is a real,
# evidence-backed gap. Counts are taken in the `demand` CTE before the existence
# joins so LEFT JOIN fan-out can't inflate them.
SQL = """
WITH demand AS (
  SELECT TRIM(skill) AS skill, COUNT(*) AS times_required
  FROM (
    SELECT UNNEST(string_to_array(n.required_skills, ';')) AS skill
    FROM sheets.applications n
    WHERE n.status = 'rejected' AND n.required_skills <> ''
  )
  GROUP BY TRIM(skill)
),
li AS (SELECT DISTINCT LOWER(name) AS name FROM linkedin.skills),
gh AS (SELECT DISTINCT LOWER(language) AS lang FROM github.user_repos WHERE language IS NOT NULL)
SELECT
  d.skill,
  d.times_required,
  MAX(CASE WHEN li.name LIKE '%' || LOWER(d.skill) || '%' THEN 1 ELSE 0 END) AS in_linkedin,
  MAX(CASE WHEN gh.lang = LOWER(d.skill) THEN 1 ELSE 0 END) AS in_github
FROM demand d
LEFT JOIN li ON li.name LIKE '%' || LOWER(d.skill) || '%'
LEFT JOIN gh ON gh.lang = LOWER(d.skill)
GROUP BY d.skill, d.times_required
ORDER BY d.times_required DESC, in_linkedin ASC, in_github ASC
LIMIT 15
"""


def fetch() -> list[dict]:
    return run_query(SQL)
