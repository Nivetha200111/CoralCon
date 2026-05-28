"""Recon agent: reads all job-search data through Coral SQL."""

from coralcon.queries import (
    followup_tracker,
    github_correlation,
    rejection_patterns,
    skill_gaps,
    timing_analysis,
)
from coralcon.portfolio import inspect_portfolio
from coralcon.utils.coral_client import run_query


APPLICATIONS_SQL = """
SELECT
  id,
  company,
  role_title,
  applied_date,
  status,
  required_skills,
  salary_range,
  source
FROM notion.applications
ORDER BY applied_date DESC
"""

GITHUB_ACTIVITY_SQL = """
SELECT
  week,
  commits_count,
  active_repos,
  languages,
  stars_earned
FROM github.activity
ORDER BY week DESC
"""

LINKEDIN_PROFILE_SQL = """
SELECT
  headline,
  summary,
  location
FROM linkedin.profile
LIMIT 1
"""

LINKEDIN_SKILLS_SQL = """
SELECT
  name,
  endorsements
FROM linkedin.skills
ORDER BY endorsements DESC
"""


class ReconAgent:
    """Collect raw data and existing analytical query outputs."""

    def fetch_applications(self) -> list[dict]:
        return run_query(APPLICATIONS_SQL)

    def fetch_github_activity(self) -> list[dict]:
        return run_query(GITHUB_ACTIVITY_SQL)

    def fetch_linkedin_profile(self) -> dict:
        profile_rows = run_query(LINKEDIN_PROFILE_SQL)
        profile = profile_rows[0] if profile_rows else {}
        profile["skills"] = run_query(LINKEDIN_SKILLS_SQL)
        return profile

    def fetch_portfolio(self, url: str | None = None) -> dict:
        return inspect_portfolio(url)

    def fetch_all(self) -> dict:
        """Return a complete dataset for downstream agents."""
        return {
            "applications": self.fetch_applications(),
            "github_activity": self.fetch_github_activity(),
            "linkedin_profile": self.fetch_linkedin_profile(),
            "portfolio": self.fetch_portfolio(),
            "rejection_patterns": rejection_patterns.fetch(),
            "github_correlation": github_correlation.fetch(),
            "skill_gaps": skill_gaps.fetch(),
            "timing": timing_analysis.fetch(),
            "followups": followup_tracker.fetch(),
        }
