"""Record Coral SQL query evidence for judges and reports."""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

from coralcon.paths import PROJECT_ROOT, runs_dir

RUNS_DIR = runs_dir()
PROOF_PATH = RUNS_DIR / "proof.json"
# Read-only copy bundled in the repo; used as a fallback on serverless hosts
# where each fresh invocation starts with an empty in-memory log and no
# writable proof file yet.
_BUNDLED_PROOF_PATH = PROJECT_ROOT / "runs" / "latest" / "proof.json"

_entries: list[dict] = []


def current_mode() -> str:
    """Return the mode each query is executing in: 'real' or 'sample'."""
    return "real" if os.getenv("CORAL_AVAILABLE", "false").lower() == "true" else "sample"


def reset_query_log() -> None:
    _entries.clear()
    if PROOF_PATH.exists():
        PROOF_PATH.unlink()


def log_query(sql: str, rows_returned: int, execution_ms: float, used_cache: bool) -> dict:
    sources = extract_sources(sql)
    execution_ms = round(execution_ms, 2)
    entry = {
        "query_id": f"q_{len(_entries) + 1:03d}",
        "query_name": infer_query_name(sql),
        "sql": _clean_sql(sql),
        "sources_used": sources,
        "is_cross_source": len(sources) > 1,
        "rows_returned": rows_returned,
        "execution_ms": execution_ms,
        # Judge-facing aliases (explicit field names the proof spec calls for).
        "execution_time_ms": execution_ms,
        "used_cache": used_cache,
        "cache_hit": used_cache,
        "mode": current_mode(),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    _entries.append(entry)
    save_query_log()
    return entry


def cache_hit_rate(entries: list[dict] | None = None) -> float:
    """Percentage of logged queries that were served from cache."""
    entries = entries if entries is not None else get_query_log()
    if not entries:
        return 0.0
    hits = sum(1 for entry in entries if entry.get("cache_hit") or entry.get("used_cache"))
    return round(hits * 100.0 / len(entries), 1)


def get_query_log() -> list[dict]:
    if _entries:
        return list(_entries)
    for path in (PROOF_PATH, _BUNDLED_PROOF_PATH):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
    return []


def save_query_log() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(_entries, indent=2)
    for attempt in range(3):
        try:
            PROOF_PATH.write_text(payload, encoding="utf-8")
            return
        except PermissionError:
            if attempt == 2:
                return
            time.sleep(0.05)


def find_query(*, name: str | None = None, sources: list[str] | None = None) -> dict | None:
    entries = get_query_log()
    for entry in reversed(entries):
        if name and entry.get("query_name") == name:
            return entry
        if sources and all(source in entry.get("sources_used", []) for source in sources):
            return entry
    return entries[-1] if entries else None


def extract_sources(sql: str) -> list[str]:
    matches = re.findall(r"\b(?:from|join)\s+([a-zA-Z_]+\.[a-zA-Z_]+)", sql, flags=re.IGNORECASE)
    return sorted(set(match.lower() for match in matches))


def infer_query_name(sql: str) -> str:
    lowered = sql.lower()
    if "required_skills" in lowered and "linkedin.skills" in lowered:
        return "skill_gap_detection"
    if "github.activity" in lowered and "sheets.applications" in lowered:
        return "github_activity_correlation"
    if "datediff" in lowered:
        return "followup_tracker"
    if "days_to_apply" in lowered or "timing_bucket" in lowered:
        return "timing_analysis"
    if "group by n.role_title" in lowered:
        return "rejection_patterns"
    if "linkedin.profile" in lowered:
        return "linkedin_profile"
    if "linkedin.skills" in lowered:
        return "linkedin_skills"
    if "github.activity" in lowered:
        return "github_activity"
    if "sheets.applications" in lowered:
        return "applications"
    return "coral_query"


def _clean_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip())
