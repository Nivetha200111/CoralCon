"""
Ingest imported application rows into the local SQLite store and recompute the
aggregate tables the dashboard reads.

Why this exists
---------------
In real mode, `coral sql` queries `sheets.applications` (the Coral file source
synced from the Google Sheet) and CoralCon aggregates the rows on the fly. But
the deployed dashboard runs on a host without the Coral CLI, so it reads the
pre-aggregated SQLite tables instead (rejection_patterns, skill_gaps, ...).

When the user imports rejections from Gmail *on the site*, we want the dashboard
to reflect the new data immediately — even though Coral isn't on that host. So we:

  1. Merge the imported rows into the SQLite `applications` (+ `application_skills`).
  2. Recompute every aggregate table from the full application set, reusing the
     same pure helpers the Coral path uses (`coralcon.utils.coral_client._*_from_apps`).

This keeps one source of truth for the aggregation logic and makes the deployed,
Coral-less dashboard update right after an import.
"""

from __future__ import annotations

import json

from coralcon import database
from coralcon.utils import coral_client


_VALID_STATUSES = {"applied", "interviewing", "rejected", "ghosted", "offer"}


def _normalize_app(app: dict) -> dict:
    """Coerce a row into the shape the aggregate helpers + schema expect."""
    raw_skills = app.get("required_skills", []) or []
    if isinstance(raw_skills, str):
        skills = [s.strip() for s in raw_skills.replace(";", ",").split(",") if s.strip()]
    else:
        skills = [str(s).strip() for s in raw_skills if str(s).strip()]

    status = coral_client._normalize_status(app.get("status", ""))
    if status not in _VALID_STATUSES:
        status = "rejected"  # Gmail extractions are rejections by default

    return {
        "id": app.get("id") or "",
        "company": app.get("company", "") or "Unknown",
        "role_title": app.get("role_title", "") or "Unknown role",
        "applied_date": app.get("applied_date", "") or "",
        "responded_date": app.get("responded_date", "") or "",
        "status": status,
        "required_skills": skills,
        "salary_range": app.get("salary_range", "") or "",
        "source": app.get("source", "Gmail") or "Gmail",
    }


def _existing_applications(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT id, company, role_title, applied_date, status, salary_range, source "
        "FROM applications"
    ).fetchall()
    skills = database._application_skills(conn)
    return [
        {**dict(row), "required_skills": skills.get(row["id"], [])}
        for row in rows
    ]


def _write_applications(conn, apps: list[dict]) -> None:
    conn.execute("DELETE FROM application_skills")
    conn.execute("DELETE FROM applications")
    for app in apps:
        conn.execute(
            """
            INSERT INTO applications (
              id, company, role_title, applied_date, status, salary_range, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                app["id"],
                app["company"],
                app["role_title"],
                # Schema requires a non-null applied_date; fall back to responded.
                app["applied_date"] or app.get("responded_date", "") or "",
                app["status"],
                app["salary_range"],
                app["source"],
            ),
        )
        for skill in app.get("required_skills", []):
            conn.execute(
                "INSERT OR IGNORE INTO application_skills (application_id, skill) "
                "VALUES (?, ?)",
                (app["id"], skill),
            )


def _recompute_aggregates(conn, apps: list[dict]) -> None:
    """Rebuild every aggregate table from the full application set."""
    # Reference data already seeded in SQLite (used by the gap/correlation logic).
    linkedin_rows = database._select_all("linkedin_skills", order_by="endorsements DESC")
    github_rows = database._select_all("github_activity", order_by="week DESC")

    patterns = coral_client._rejection_patterns_from_apps(apps)
    gaps = coral_client._skill_gaps_from_apps(apps, linkedin_rows, github_rows)
    timing = coral_client._timing_from_apps(apps)
    followups = coral_client._followups_from_apps(apps)
    correlation = coral_client._github_correlation_from_apps(apps, github_rows)

    conn.execute("DELETE FROM rejection_patterns")
    for row in patterns:
        conn.execute(
            """
            INSERT INTO rejection_patterns (
              role_title, total, rejected, ghosted, interviewed, offers,
              rejection_rate, ghost_rate, response_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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

    conn.execute("DELETE FROM skill_gaps")
    for row in gaps:
        conn.execute(
            """
            INSERT OR REPLACE INTO skill_gaps (
              skill, times_required, in_github, in_linkedin, priority
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                row.get("skill"),
                row.get("times_required", 0),
                int(bool(row.get("in_github"))),
                int(bool(row.get("in_linkedin"))),
                row.get("priority", "medium"),
            ),
        )

    conn.execute("DELETE FROM timing_analysis")
    for row in timing:
        conn.execute(
            """
            INSERT OR REPLACE INTO timing_analysis (
              timing_bucket, total, response_rate, ghost_rate
            ) VALUES (?, ?, ?, ?)
            """,
            (
                row.get("timing_bucket"),
                row.get("total", 0),
                row.get("response_rate", 0),
                row.get("ghost_rate", 0),
            ),
        )

    conn.execute("DELETE FROM followup_queue")
    for row in followups:
        conn.execute(
            """
            INSERT OR REPLACE INTO followup_queue (
              company, role_title, applied_date, days_waiting, priority, recommended_action
            ) VALUES (?, ?, ?, ?, ?, ?)
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

    conn.execute("DELETE FROM github_correlation")
    seen = set()
    for row in correlation:
        key = (row.get("company"), row.get("role_title"), row.get("applied_date"))
        if key in seen:
            continue
        seen.add(key)
        conn.execute(
            """
            INSERT OR REPLACE INTO github_correlation (
              company, applied_date, status, role_title,
              commits_count, active_repos, languages
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
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


def ingest_applications(new_rows: list[dict], *, replace: bool = False) -> dict:
    """Merge imported application rows into SQLite and recompute aggregates.

    Args:
        new_rows: applications (e.g. from Gmail extraction).
        replace: if True, drop existing applications first; otherwise merge by id
                 (existing rows win, so manual edits in the Sheet aren't clobbered).

    Returns a small summary dict for the web response.
    """
    database.ensure_database()
    normalized_new = [_normalize_app(r) for r in new_rows if r]

    with database.connect() as conn:
        existing = [] if replace else _existing_applications(conn)
        merged: dict[str, dict] = {}
        for app in existing:
            merged[app["id"]] = app
        added = 0
        for app in normalized_new:
            if not app["id"]:
                continue
            if app["id"] not in merged:
                added += 1
            merged.setdefault(app["id"], app)  # existing rows win on conflict

        all_apps = list(merged.values())
        _write_applications(conn, all_apps)
        _recompute_aggregates(conn, all_apps)
        conn.commit()

    return {
        "imported": len(normalized_new),
        "added": added,
        "total_applications": len(all_apps),
    }
