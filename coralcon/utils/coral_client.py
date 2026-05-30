"""
Coral SQL client wrapper.

When CORAL_AVAILABLE=true, executes real Coral queries via subprocess.
Otherwise falls back to sample data for development/demo.
"""

import os
import json
import subprocess
import time
from pathlib import Path
from datetime import date

from coralcon.database import run_database_query
from coralcon.proof.query_logger import log_query

SAMPLE_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "sample"
_QUERY_CACHE: dict[str, list[dict]] = {}


def _coral_available() -> bool:
    return os.getenv("CORAL_AVAILABLE", "false").lower() == "true"


def _data_backend() -> str:
    # On serverless hosts (Vercel) the bundled SQLite file is a thin demo, so
    # default to the rich JSON sample that tells the full story.
    default = "json" if os.getenv("VERCEL") else "sqlite"
    return os.getenv("CORALCON_DATA_BACKEND", default).strip().lower()


def run_query(sql: str) -> list[dict]:
    """Execute a Coral SQL query. Falls back to sample data if Coral is not available."""
    use_cache = os.getenv("CORALCON_QUERY_CACHE", "false").lower() == "true"
    start = time.perf_counter()

    if use_cache and sql in _QUERY_CACHE:
        rows = _QUERY_CACHE[sql]
        log_query(sql, len(rows), (time.perf_counter() - start) * 1000, used_cache=True)
        return rows

    if _coral_available():
        try:
            rows = _run_real_query(sql)
        except RuntimeError:
            rows = _run_sample_query(sql) if _data_backend() == "json" else run_database_query(sql)
    elif _data_backend() == "json":
        rows = _run_sample_query(sql)
    else:
        rows = run_database_query(sql)

    if use_cache:
        _QUERY_CACHE[sql] = rows

    log_query(sql, len(rows), (time.perf_counter() - start) * 1000, used_cache=False)
    return rows


def _run_real_query(sql: str) -> list[dict]:
    """Execute real-mode queries, adapting the application tracker when needed."""
    sql_lower = sql.lower()
    if "sheets.applications" in sql_lower:
        return _run_applications_query(sql)
    if "from github.activity" in sql_lower and (
        "commits_count" in sql_lower or "active_repos" in sql_lower or "week" in sql_lower
    ):
        return _fetch_github_activity_summary()
    return _run_coral_query(sql)


def _run_coral_query(sql: str) -> list[dict]:
    """Execute a real Coral SQL query via CLI."""
    try:
        result = _run_coral_sql_command(sql)
    except FileNotFoundError:
        raise RuntimeError(
            "Coral CLI not found. Install with: brew install withcoral/tap/coral"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Coral query timed out after 30s")

    # Coral 0.4.1 can panic on teardown ("Cannot start a runtime from within a
    # runtime") AFTER it has already written valid JSON to stdout, leaving a
    # non-zero exit code. The query result is still correct, so prefer parsing
    # stdout; only treat it as an error when stdout has no usable JSON.
    stdout = (result.stdout or "").strip()
    if stdout:
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            pass
    raise RuntimeError(f"Coral error: {result.stderr or 'no output from coral'}")


def _run_applications_query(sql: str) -> list[dict]:
    """Read application rows from the Google Sheets file source and aggregate."""
    apps = _fetch_applications_table()
    sql_lower = sql.lower()

    if "github.activity" in sql_lower:
        github_rows = _fetch_github_activity_summary()
        return _github_correlation_from_apps(apps, github_rows)

    if "required_skills" in sql_lower and "linkedin" in sql_lower:
        linkedin_rows = _run_coral_query(
            "SELECT name, endorsements FROM linkedin.skills ORDER BY endorsements DESC"
        )
        github_rows = _fetch_github_activity_summary()
        return _skill_gaps_from_apps(apps, linkedin_rows, github_rows)

    if "days_waiting" in sql_lower or "follow-up" in sql_lower or "followup" in sql_lower:
        return _followups_from_apps(apps)

    if "timing_bucket" in sql_lower or "days_to_apply" in sql_lower:
        return _timing_from_apps(apps)

    if "group by" in sql_lower and "role_title" in sql_lower:
        return _rejection_patterns_from_apps(apps)

    return apps


def _run_coral_sql_command(sql: str) -> subprocess.CompletedProcess[str]:
    """Run Coral SQL using the current CLI, with legacy command fallback."""
    try:
        result = subprocess.run(
            ["coral", "sql", "--format", "json", sql],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        raise

    # returncode 0, or a teardown panic that still produced JSON on stdout.
    if result.returncode == 0 or (result.stdout or "").lstrip().startswith(("[", "{")):
        return result

    legacy = subprocess.run(
        ["coral", "query", "--format", "json", sql],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return legacy if legacy.returncode == 0 else result


def _fetch_applications_table() -> list[dict]:
    """Fetch application rows for real mode.

    Primary source is the Google Sheets-backed Coral file source
    (`sheets.applications`), synced from the Sheet by `coralcon sheets-sync`.
    """
    rows = _run_coral_query(
        "SELECT id, company, role_title, status, applied_date, "
        "responded_date, required_skills, salary_range, source "
        "FROM sheets.applications LIMIT 1000"
    )
    return [_normalize_sheets_row(row, index) for index, row in enumerate(rows, 1)]


def _normalize_sheets_row(row: dict, index: int) -> dict:
    """Coerce a raw sheets.applications row into CoralCon's application shape."""
    raw_skills = row.get("required_skills", "") or ""
    if isinstance(raw_skills, list):
        skills = [str(s).strip() for s in raw_skills if str(s).strip()]
    else:
        skills = [s.strip() for s in str(raw_skills).replace(";", ",").split(",") if s.strip()]
    return {
        "id": row.get("id") or f"sheet_row_{index:03d}",
        "company": row.get("company", ""),
        "role_title": row.get("role_title", ""),
        "applied_date": row.get("applied_date", ""),
        "responded_date": row.get("responded_date", ""),
        "status": _normalize_status(row.get("status", "")),
        "required_skills": skills,
        "salary_range": row.get("salary_range", ""),
        "source": row.get("source", "Sheets"),
    }


def _normalize_header(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _normalize_status(value: str) -> str:
    status = value.strip().lower().replace(" ", "_")
    aliases = {
        "wishlist": "applied",
        "wish_list": "applied",
        "to_apply": "applied",
        "not_applied": "applied",
        "interview": "interviewing",
        "interviewed": "interviewing",
        "accepted": "offer",
        "offered": "offer",
    }
    return aliases.get(status, status or "applied")


def _rejection_patterns_from_apps(apps: list[dict]) -> list[dict]:
    by_role: dict[str, dict] = {}
    for app in apps:
        role = app.get("role_title") or "Unknown"
        row = by_role.setdefault(
            role,
            {
                "role_title": role,
                "total": 0,
                "rejected": 0,
                "ghosted": 0,
                "interviewed": 0,
                "offers": 0,
            },
        )
        row["total"] += 1
        status = app.get("status")
        if status == "rejected":
            row["rejected"] += 1
        elif status == "ghosted":
            row["ghosted"] += 1
        elif status == "interviewing":
            row["interviewed"] += 1
        elif status == "offer":
            row["offers"] += 1

    rows = []
    for row in by_role.values():
        total = row["total"] or 1
        row["rejection_rate"] = round(row["rejected"] * 100.0 / total, 1)
        row["ghost_rate"] = round(row["ghosted"] * 100.0 / total, 1)
        row["response_rate"] = round((row["interviewed"] + row["offers"]) * 100.0 / total, 1)
        rows.append(row)
    return sorted(rows, key=lambda r: r["rejection_rate"], reverse=True)


def _skill_gaps_from_apps(apps: list[dict], linkedin_rows: list[dict], github_rows: list[dict]) -> list[dict]:
    counts: dict[str, int] = {}
    for app in apps:
        if app.get("status") not in {"rejected", "ghosted", "applied"}:
            continue
        for skill in app.get("required_skills", []):
            counts[skill] = counts.get(skill, 0) + 1

    linkedin_skills = {str(row.get("name", "")).lower() for row in linkedin_rows}
    github_languages = set()
    for row in github_rows:
        languages = row.get("languages", [])
        if isinstance(languages, str):
            try:
                languages = json.loads(languages)
            except json.JSONDecodeError:
                languages = [languages]
        github_languages.update(str(lang).lower() for lang in languages)

    rows = []
    for skill, count in sorted(counts.items(), key=lambda item: item[1], reverse=True):
        in_github = skill.lower() in github_languages
        in_linkedin = skill.lower() in linkedin_skills
        if count >= 3 and not (in_github or in_linkedin):
            priority = "critical"
        elif count >= 2:
            priority = "high"
        else:
            priority = "medium"
        rows.append(
            {
                "skill": skill,
                "times_required": count,
                "in_github": in_github,
                "in_linkedin": in_linkedin,
                "priority": priority,
            }
        )
    return rows[:15]


def _github_correlation_from_apps(apps: list[dict], github_rows: list[dict]) -> list[dict]:
    fallback = github_rows[0] if github_rows else {}
    rows = []
    for app in apps:
        rows.append(
            {
                "company": app.get("company", ""),
                "applied_date": app.get("applied_date", ""),
                "status": app.get("status", ""),
                "role_title": app.get("role_title", ""),
                "commits_count": fallback.get("commits_count", 0),
                "active_repos": fallback.get("active_repos", 0),
                "languages": fallback.get("languages", []),
            }
        )
    return rows


def _fetch_github_activity_summary() -> list[dict]:
    """Aggregate GitHub public events into CoralCon's weekly activity shape."""
    username = os.getenv("GITHUB_USERNAME") or _fetch_github_username()
    if not username:
        return []

    events = _run_coral_query(
        "SELECT created_at, type, repo__name "
        "FROM github.user_event_public "
        f"WHERE username = '{username}' LIMIT 100"
    )
    by_week: dict[str, dict] = {}
    for event in events:
        created = str(event.get("created_at") or "")[:10]
        try:
            event_date = date.fromisoformat(created)
        except ValueError:
            continue
        week_start = event_date.fromordinal(event_date.toordinal() - event_date.weekday()).isoformat()
        row = by_week.setdefault(
            week_start,
            {
                "week": week_start,
                "commits_count": 0,
                "active_repos": 0,
                "languages": [],
                "stars_earned": 0,
                "_repos": set(),
            },
        )
        row["commits_count"] += 1 if event.get("type") == "PushEvent" else 0
        if event.get("repo__name"):
            row["_repos"].add(event["repo__name"])

    rows = []
    for row in by_week.values():
        row["active_repos"] = len(row.pop("_repos"))
        rows.append(row)
    return sorted(rows, key=lambda row: row["week"], reverse=True)


def _fetch_github_username() -> str | None:
    rows = _run_coral_query("SELECT login FROM github.user LIMIT 1")
    if not rows:
        return None
    return rows[0].get("login")


def _timing_from_apps(apps: list[dict]) -> list[dict]:
    total = len(apps)
    if not total:
        return []
    responses = sum(1 for app in apps if app.get("status") in {"interviewing", "offer"})
    ghosted = sum(1 for app in apps if app.get("status") == "ghosted")
    return [
        {
            "timing_bucket": "unknown",
            "total": total,
            "response_rate": round(responses * 100.0 / total, 1),
            "ghost_rate": round(ghosted * 100.0 / total, 1),
        }
    ]


def _followups_from_apps(apps: list[dict]) -> list[dict]:
    today = date.today()
    rows = []
    for app in apps:
        if app.get("status") != "applied" or not app.get("applied_date"):
            continue
        try:
            applied = date.fromisoformat(app["applied_date"])
        except ValueError:
            continue
        days = (today - applied).days
        if days < 7:
            continue
        priority = "hot" if days <= 14 else "warm" if days <= 21 else "cold"
        rows.append(
            {
                "company": app.get("company", ""),
                "role_title": app.get("role_title", ""),
                "applied_date": app.get("applied_date", ""),
                "days_waiting": days,
                "priority": priority,
                "recommended_action": "Send follow-up email now"
                if priority == "hot"
                else "Last chance follow-up"
                if priority == "warm"
                else "Move on - mark as ghosted",
            }
        )
    return sorted(rows, key=lambda row: row["days_waiting"])


def _run_sample_query(sql: str) -> list[dict]:
    """
    Route to the appropriate sample dataset based on the SQL query.
    Parses the FROM clause to determine which table to read.
    """
    sql_lower = sql.lower()

    if "sheets.applications" in sql_lower and "github.activity" in sql_lower:
        return _load_sample("github_correlation.json")
    elif "followup" in sql_lower or "days_waiting" in sql_lower or "datediff" in sql_lower:
        return _load_sample("followup.json")
    elif "skill_gap" in sql_lower or (
        "required_skills" in sql_lower and "linkedin" in sql_lower
    ):
        return _load_sample("skill_gaps.json")
    elif "sheets.applications" in sql_lower and "group by" in sql_lower:
        return _load_sample("rejection_patterns.json")
    elif "timing" in sql_lower or "days_to_apply" in sql_lower or "timing_bucket" in sql_lower:
        return _load_sample("timing_analysis.json")
    elif "sheets.applications" in sql_lower:
        return _load_sample("applications.json")
    elif "github" in sql_lower:
        return _load_sample("github_activity.json")
    elif "linkedin" in sql_lower:
        return _load_sample("linkedin_skills.json")
    else:
        return []


def _load_sample(filename: str) -> list[dict]:
    """Load a sample data file."""
    path = SAMPLE_DATA_DIR / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("rows", [])


def check_coral_connection() -> dict:
    """Check if Coral is installed and sources are connected."""
    status = {
        "coral_installed": False,
        "github_connected": False,
        "sheets_connected": False,
        "gmail_connected": False,
        "linkedin_connected": False,
        "using_sample_data": not _coral_available(),
    }

    if not _coral_available():
        return status

    sources = _installed_coral_sources()
    if sources is None:
        return status

    status["coral_installed"] = True
    status["github_connected"] = "github" in sources
    status["sheets_connected"] = "sheets" in sources
    status["gmail_connected"] = "gmail" in sources
    status["linkedin_connected"] = "linkedin" in sources

    return status


def _installed_coral_sources() -> set[str] | None:
    """Return installed Coral source names, or None when Coral is unavailable."""
    try:
        result = subprocess.run(
            ["coral", "source", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if result.returncode == 0:
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, list):
                return {
                    str(item.get("name", item)).strip()
                    for item in parsed
                    if str(item.get("name", item)).strip()
                }
            if isinstance(parsed, dict):
                rows = parsed.get("sources", [])
                return {
                    str(item.get("name", item)).strip()
                    for item in rows
                    if str(item.get("name", item)).strip()
                }
        except json.JSONDecodeError:
            pass

    result = subprocess.run(
        ["coral", "source", "list"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return None

    known_sources = {"github", "sheets", "gmail", "linkedin"}
    found = set()
    for line in result.stdout.splitlines():
        for source in known_sources:
            if source in line.lower().split():
                found.add(source)
    return found
