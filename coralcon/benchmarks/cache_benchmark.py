"""Observed repeated-query benchmark."""

import os
import time

from coralcon.queries import skill_gaps


def run_cache_benchmark(sample: bool = True) -> dict:
    previous_coral = os.getenv("CORAL_AVAILABLE")
    previous_cache = os.getenv("CORALCON_QUERY_CACHE")
    if sample:
        os.environ["CORAL_AVAILABLE"] = "false"
    os.environ["CORALCON_QUERY_CACHE"] = "true"

    start = time.perf_counter()
    rows_1 = skill_gaps.fetch()
    run_1 = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    rows_2 = skill_gaps.fetch()
    run_2 = (time.perf_counter() - start) * 1000

    _restore("CORAL_AVAILABLE", previous_coral)
    _restore("CORALCON_QUERY_CACHE", previous_cache)

    return {
        "query": "skill_gap_detection_cross_source",
        "run_1_ms": round(run_1, 2),
        "run_2_ms": round(run_2, 2),
        "speedup": round(run_1 / run_2, 2) if run_2 else 0,
        "rows_returned": len(rows_2 or rows_1),
        "metadata_note": "Cache metadata unavailable. Reporting observed repeated-query speedup.",
    }


def _restore(key: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = value
