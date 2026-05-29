"""Local SQLite database for CoralCon sample/local mode."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA_DIR = PROJECT_ROOT / "data" / "sample"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "coralcon.sqlite"
SCHEMA_VERSION = 1


def database_path() -> Path:
    configured = os.getenv("CORALCON_DB_PATH")
    if not configured:
        return DEFAULT_DB_PATH
    path = Path(configured).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def connect(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_database(path: Path | None = None) -> Path:
    db_path = path or database_path()
    if not db_path.exists():
        initialize_database(db_path, seed=True)
    return db_path


def initialize_database(
    path: Path | None = None,
    *,
    seed: bool = True,
    reset: bool = False,
) -> Path:
    db_path = path or database_path()
    if reset and db_path.exists():
        db_path.unlink()

    with connect(db_path) as conn:
        _create_schema(conn)
        if seed:
            seed_from_sample_data(conn)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    return db_path


def run_database_query(sql: str) -> list[dict]:
    """Run a CoralCon query against local SQLite-backed tables."""
    ensure_database()
    # sheets.applications is the primary tracker; alias to the shared routing.
    sql_lower = sql.lower().replace("sheets.applications", "notion.applications")

    if "notion.applications" in sql_lower and "github.activity" in sql_lower:
        return _select_all("github_correlation", order_by="applied_date DESC")
    if "followup" in sql_lower or "days_waiting" in sql_lower or "datediff" in sql_lower:
        return _select_all("followup_queue", order_by="days_waiting ASC")
    if "skill_gap" in sql_lower or ("required_skills" in sql_lower and "linkedin" in sql_lower):
        return _select_all("skill_gaps", order_by="times_required DESC")
    if "notion.applications" in sql_lower and "group by" in sql_lower and "role_title" in sql_lower:
        return _select_all("rejection_patterns", order_by="rejection_rate DESC")
    if "timing" in sql_lower or "days_to_apply" in sql_lower or "timing_bucket" in sql_lower:
        return _select_all(
            "timing_analysis",
            order_by=(
                "CASE timing_bucket "
                "WHEN 'same_day' THEN 1 "
                "WHEN '1-2_days' THEN 2 "
                "WHEN '3-7_days' THEN 3 "
                "WHEN '1-2_weeks' THEN 4 "
                "ELSE 5 END"
            ),
        )
    if "notion.applications" in sql_lower:
        return fetch_applications()
    if "linkedin.profile" in sql_lower:
        return _select_all("linkedin_profile", limit=1)
    if "linkedin.skills" in sql_lower or "linkedin" in sql_lower:
        return _select_all("linkedin_skills", order_by="endorsements DESC")
    if "github.activity" in sql_lower or "github" in sql_lower:
        return _select_all("github_activity", order_by="week DESC")
    return []


def fetch_applications() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, company, role_title, applied_date, status, salary_range, source
            FROM applications
            ORDER BY applied_date DESC
            """
        ).fetchall()
        skills = _application_skills(conn)
    return [
        {
            **dict(row),
            "required_skills": skills.get(row["id"], []),
        }
        for row in rows
    ]


def database_status(path: Path | None = None) -> dict[str, Any]:
    db_path = path or database_path()
    exists = db_path.exists()
    if not exists:
        return {"path": str(db_path), "exists": False, "tables": {}, "schema_version": 0}

    with connect(db_path) as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        tables = {}
        for table in (
            "applications",
            "application_skills",
            "github_activity",
            "linkedin_profile",
            "linkedin_skills",
            "rejection_patterns",
            "skill_gaps",
            "timing_analysis",
            "followup_queue",
            "github_correlation",
        ):
            tables[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return {
        "path": str(db_path),
        "exists": True,
        "schema_version": version,
        "tables": tables,
    }


def execute_sql(sql: str, params: tuple[Any, ...] = ()) -> list[dict]:
    ensure_database()
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_decode_row(row) for row in rows]


def seed_from_sample_data(conn: sqlite3.Connection) -> None:
    _clear_tables(conn)
    for app in _load_sample("applications.json"):
        conn.execute(
            """
            INSERT INTO applications (
              id, company, role_title, applied_date, status, salary_range, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                app.get("id"),
                app.get("company"),
                app.get("role_title"),
                app.get("applied_date"),
                app.get("status"),
                app.get("salary_range"),
                app.get("source"),
            ),
        )
        for skill in app.get("required_skills", []):
            conn.execute(
                "INSERT INTO application_skills (application_id, skill) VALUES (?, ?)",
                (app.get("id"), skill),
            )

    for row in _load_sample("github_activity.json"):
        conn.execute(
            """
            INSERT INTO github_activity (
              week, commits_count, active_repos, languages, stars_earned
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                row.get("week"),
                row.get("commits_count", 0),
                row.get("active_repos", 0),
                json.dumps(row.get("languages", [])),
                row.get("stars_earned", 0),
            ),
        )

    conn.execute(
        """
        INSERT INTO linkedin_profile (id, headline, summary, location)
        VALUES (1, ?, ?, ?)
        """,
        (
            "Full-stack engineer building evidence-backed career tools",
            "CoralCon local profile seeded for dashboard development.",
            "Remote",
        ),
    )
    for row in _load_sample("linkedin_skills.json"):
        conn.execute(
            "INSERT INTO linkedin_skills (name, endorsements) VALUES (?, ?)",
            (row.get("name"), row.get("endorsements", 0)),
        )

    _seed_rejection_patterns(conn)
    _seed_skill_gaps(conn)
    _seed_timing_analysis(conn)
    _seed_followups(conn)
    _seed_github_correlation(conn)


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS applications (
          id TEXT PRIMARY KEY,
          company TEXT NOT NULL,
          role_title TEXT NOT NULL,
          applied_date TEXT NOT NULL,
          status TEXT NOT NULL CHECK (
            status IN ('applied', 'interviewing', 'rejected', 'ghosted', 'offer')
          ),
          salary_range TEXT,
          source TEXT DEFAULT 'local'
        );

        CREATE TABLE IF NOT EXISTS application_skills (
          application_id TEXT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
          skill TEXT NOT NULL,
          PRIMARY KEY (application_id, skill)
        );

        CREATE TABLE IF NOT EXISTS github_activity (
          week TEXT PRIMARY KEY,
          commits_count INTEGER NOT NULL DEFAULT 0,
          active_repos INTEGER NOT NULL DEFAULT 0,
          languages TEXT NOT NULL DEFAULT '[]',
          stars_earned INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS linkedin_profile (
          id INTEGER PRIMARY KEY CHECK (id = 1),
          headline TEXT NOT NULL DEFAULT '',
          summary TEXT NOT NULL DEFAULT '',
          location TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS linkedin_skills (
          name TEXT PRIMARY KEY,
          endorsements INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS rejection_patterns (
          role_title TEXT PRIMARY KEY,
          total INTEGER NOT NULL,
          rejected INTEGER NOT NULL,
          ghosted INTEGER NOT NULL,
          interviewed INTEGER NOT NULL,
          offers INTEGER NOT NULL,
          rejection_rate REAL NOT NULL,
          ghost_rate REAL NOT NULL,
          response_rate REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS skill_gaps (
          skill TEXT PRIMARY KEY,
          times_required INTEGER NOT NULL,
          in_github INTEGER NOT NULL DEFAULT 0,
          in_linkedin INTEGER NOT NULL DEFAULT 0,
          priority TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS timing_analysis (
          timing_bucket TEXT PRIMARY KEY,
          total INTEGER NOT NULL,
          response_rate REAL NOT NULL,
          ghost_rate REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS followup_queue (
          company TEXT NOT NULL,
          role_title TEXT NOT NULL,
          applied_date TEXT NOT NULL,
          days_waiting INTEGER NOT NULL,
          priority TEXT NOT NULL,
          recommended_action TEXT NOT NULL,
          PRIMARY KEY (company, role_title, applied_date)
        );

        CREATE TABLE IF NOT EXISTS github_correlation (
          company TEXT NOT NULL,
          applied_date TEXT NOT NULL,
          status TEXT NOT NULL,
          role_title TEXT NOT NULL,
          commits_count INTEGER NOT NULL DEFAULT 0,
          active_repos INTEGER NOT NULL DEFAULT 0,
          languages TEXT NOT NULL DEFAULT '[]',
          PRIMARY KEY (company, role_title, applied_date)
        );

        CREATE INDEX IF NOT EXISTS idx_applications_applied_date
          ON applications(applied_date);
        CREATE INDEX IF NOT EXISTS idx_applications_status
          ON applications(status);
        CREATE INDEX IF NOT EXISTS idx_application_skills_skill
          ON application_skills(skill);
        """
    )


def _clear_tables(conn: sqlite3.Connection) -> None:
    for table in (
        "github_correlation",
        "followup_queue",
        "timing_analysis",
        "skill_gaps",
        "rejection_patterns",
        "linkedin_skills",
        "linkedin_profile",
        "github_activity",
        "application_skills",
        "applications",
    ):
        conn.execute(f"DELETE FROM {table}")


def _seed_rejection_patterns(conn: sqlite3.Connection) -> None:
    for row in _load_sample("rejection_patterns.json"):
        conn.execute(
            """
            INSERT INTO rejection_patterns (
              role_title, total, rejected, ghosted, interviewed, offers,
              rejection_rate, ghost_rate, response_rate
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("role_title"),
                row.get("total", 0),
                row.get("rejected", 0),
                row.get("ghosted", 0),
                row.get("interviewed", 0),
                row.get("offers", 0),
                row.get("rejection_rate", 0),
                row.get("ghost_rate", 0),
                row.get("response_rate", 0),
            ),
        )


def _seed_skill_gaps(conn: sqlite3.Connection) -> None:
    for row in _load_sample("skill_gaps.json"):
        conn.execute(
            """
            INSERT INTO skill_gaps (
              skill, times_required, in_github, in_linkedin, priority
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                row.get("skill"),
                row.get("times_required", 0),
                int(bool(row.get("in_github"))),
                int(bool(row.get("in_linkedin"))),
                row.get("priority", "medium"),
            ),
        )


def _seed_timing_analysis(conn: sqlite3.Connection) -> None:
    for row in _load_sample("timing_analysis.json"):
        conn.execute(
            """
            INSERT INTO timing_analysis (
              timing_bucket, total, response_rate, ghost_rate
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                row.get("timing_bucket"),
                row.get("total", 0),
                row.get("response_rate", 0),
                row.get("ghost_rate", 0),
            ),
        )


def _seed_followups(conn: sqlite3.Connection) -> None:
    for row in _load_sample("followup.json"):
        conn.execute(
            """
            INSERT INTO followup_queue (
              company, role_title, applied_date, days_waiting, priority, recommended_action
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("company"),
                row.get("role_title"),
                row.get("applied_date"),
                row.get("days_waiting", 0),
                row.get("priority"),
                row.get("recommended_action"),
            ),
        )


def _seed_github_correlation(conn: sqlite3.Connection) -> None:
    for row in _load_sample("github_correlation.json"):
        conn.execute(
            """
            INSERT INTO github_correlation (
              company, applied_date, status, role_title,
              commits_count, active_repos, languages
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("company"),
                row.get("applied_date"),
                row.get("status"),
                row.get("role_title"),
                row.get("commits_count", 0),
                row.get("active_repos", 0),
                json.dumps(row.get("languages", [])),
            ),
        )


def _select_all(
    table: str,
    *,
    order_by: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    query = f"SELECT * FROM {table}"
    if order_by:
        query += f" ORDER BY {order_by}"
    if limit is not None:
        query += f" LIMIT {int(limit)}"
    return execute_sql(query)


def _application_skills(conn: sqlite3.Connection) -> dict[str, list[str]]:
    rows = conn.execute(
        """
        SELECT application_id, skill
        FROM application_skills
        ORDER BY application_id, skill
        """
    ).fetchall()
    skills: dict[str, list[str]] = {}
    for row in rows:
        skills.setdefault(row["application_id"], []).append(row["skill"])
    return skills


def _decode_row(row: sqlite3.Row) -> dict:
    decoded = dict(row)
    for key in ("languages",):
        if key in decoded and isinstance(decoded[key], str):
            try:
                decoded[key] = json.loads(decoded[key])
            except json.JSONDecodeError:
                decoded[key] = []
    for key in ("in_github", "in_linkedin"):
        if key in decoded:
            decoded[key] = bool(decoded[key])
    return decoded


def _load_sample(filename: str) -> list[dict]:
    path = SAMPLE_DATA_DIR / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("rows", [])
