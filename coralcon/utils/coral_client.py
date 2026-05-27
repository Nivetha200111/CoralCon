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

from coralcon.proof.query_logger import log_query

SAMPLE_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "sample"
_QUERY_CACHE: dict[str, list[dict]] = {}


def _coral_available() -> bool:
    return os.getenv("CORAL_AVAILABLE", "false").lower() == "true"


def run_query(sql: str) -> list[dict]:
    """Execute a Coral SQL query. Falls back to sample data if Coral is not available."""
    use_cache = os.getenv("CORALCON_QUERY_CACHE", "false").lower() == "true"
    start = time.perf_counter()

    if use_cache and sql in _QUERY_CACHE:
        rows = _QUERY_CACHE[sql]
        log_query(sql, len(rows), (time.perf_counter() - start) * 1000, used_cache=True)
        return rows

    if _coral_available():
        rows = _run_coral_query(sql)
    else:
        rows = _run_sample_query(sql)

    if use_cache:
        _QUERY_CACHE[sql] = rows

    log_query(sql, len(rows), (time.perf_counter() - start) * 1000, used_cache=False)
    return rows


def _run_coral_query(sql: str) -> list[dict]:
    """Execute a real Coral SQL query via CLI."""
    try:
        result = subprocess.run(
            ["coral", "query", "--format", "json", sql],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Coral error: {result.stderr}")
        return json.loads(result.stdout)
    except FileNotFoundError:
        raise RuntimeError(
            "Coral CLI not found. Install with: brew install withcoral/tap/coral"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Coral query timed out after 30s")


def _run_sample_query(sql: str) -> list[dict]:
    """
    Route to the appropriate sample dataset based on the SQL query.
    Parses the FROM clause to determine which table to read.
    """
    sql_lower = sql.lower()

    if "notion.applications" in sql_lower and "github.activity" in sql_lower:
        return _load_sample("github_correlation.json")
    elif "followup" in sql_lower or "days_waiting" in sql_lower or "datediff" in sql_lower:
        return _load_sample("followup.json")
    elif "skill_gap" in sql_lower or (
        "required_skills" in sql_lower and "linkedin" in sql_lower
    ):
        return _load_sample("skill_gaps.json")
    elif "notion.applications" in sql_lower and "group by" in sql_lower:
        return _load_sample("rejection_patterns.json")
    elif "timing" in sql_lower or "days_to_apply" in sql_lower or "timing_bucket" in sql_lower:
        return _load_sample("timing_analysis.json")
    elif "notion.applications" in sql_lower:
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
        "notion_connected": False,
        "linkedin_connected": False,
        "using_sample_data": not _coral_available(),
    }

    if not _coral_available():
        return status

    try:
        result = subprocess.run(
            ["coral", "status", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            status["coral_installed"] = True
            info = json.loads(result.stdout)
            sources = [s.get("name", "") for s in info.get("sources", [])]
            status["github_connected"] = "github" in sources
            status["notion_connected"] = "notion" in sources
            status["linkedin_connected"] = "linkedin" in sources
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    return status
