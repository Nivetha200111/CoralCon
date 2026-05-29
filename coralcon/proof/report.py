"""Generate human-readable Coral proof reports."""

import os

from coralcon.proof.query_logger import cache_hit_rate, get_query_log


def _resolved_mode(entries: list[dict]) -> str:
    """Mode the logged queries actually ran in (falls back to live env)."""
    modes = [entry.get("mode") for entry in entries if entry.get("mode")]
    if modes:
        return modes[-1]
    return "real" if os.getenv("CORAL_AVAILABLE", "false").lower() == "true" else "sample"


def build_proof_report() -> str:
    entries = get_query_log()
    sources = sorted({source for entry in entries for source in entry.get("sources_used", [])})
    cross_source = [entry for entry in entries if entry.get("is_cross_source")]
    best = _best_query(entries)
    total_rows = sum(entry.get("rows_returned", 0) for entry in entries)
    total_time = sum(entry.get("execution_ms", 0) for entry in entries)
    cached_count = sum(1 for entry in entries if entry.get("used_cache"))
    hit_rate = cache_hit_rate(entries)
    mode = _resolved_mode(entries)

    lines = [
        "",
        "  CORAL PROOF REPORT",
        "  ==================",
        "",
        f"  Total Coral Queries:    {len(entries)}",
        f"  Cross-Source JOINs:     {len(cross_source)}",
        f"  Total Rows Returned:    {total_rows}",
        f"  Total Execution Time:   {total_time:.1f}ms",
        f"  Cached Queries:         {cached_count}",
        f"  Cache Hit Rate:         {hit_rate:.1f}%",
        f"  Mode:                   {mode}",
        "",
        "  Sources Used:",
    ]
    for source in sources:
        lines.append(f"    - {source}")

    lines.extend(["", "  Best Coral Query:"])
    if best:
        lines.extend([
            f"    Query ID:    {best['query_id']}",
            f"    Name:        {best['query_name']}",
            f"    Sources:     {', '.join(best.get('sources_used', []))}",
            f"    Rows:        {best['rows_returned']}",
            f"    Execution:   {best['execution_ms']}ms",
            f"    Cached:      {'yes' if best.get('used_cache') else 'no'}",
            f"    SQL:         {best['sql']}",
        ])
    else:
        lines.append("    No queries logged yet. Run `coralcon judge-demo --sample` first.")

    lines.extend(["", "  All Queries:"])
    for entry in entries:
        cross_label = " [CROSS-SOURCE]" if entry.get("is_cross_source") else ""
        cache_label = " [CACHED]" if entry.get("used_cache") else ""
        lines.append(
            f"    {entry['query_id']}  {entry['query_name']:<30s}  "
            f"{entry['rows_returned']:>4d} rows  {entry['execution_ms']:>8.1f}ms"
            f"{cross_label}{cache_label}"
        )

    lines.append("")
    return "\n".join(lines)


def proof_summary() -> dict:
    entries = get_query_log()
    sources = sorted({source for entry in entries for source in entry.get("sources_used", [])})
    cross_source_count = sum(1 for entry in entries if entry.get("is_cross_source"))
    total_rows = sum(entry.get("rows_returned", 0) for entry in entries)
    total_time = sum(entry.get("execution_ms", 0) for entry in entries)
    cached_count = sum(1 for entry in entries if entry.get("used_cache"))
    best = _best_query(entries)
    mode = _resolved_mode(entries)

    return {
        "total_queries": len(entries),
        "cross_source_queries": cross_source_count,
        "sources": sources,
        "total_rows": total_rows,
        "total_execution_ms": round(total_time, 2),
        "cached_queries": cached_count,
        "cache_hit_rate": cache_hit_rate(entries),
        "mode": mode,
        "best_query": best,
        "queries": entries,
    }


def proof_bundle(mode: str | None = None) -> dict:
    """Rich, judge-facing proof object: top-level summary + per-query records.

    Written to runs/real-demo/proof.json (and any standalone bundle file). The
    flat list at runs/latest/proof.json is kept separately for backward compat.
    """
    entries = get_query_log()
    summary = proof_summary()
    resolved_mode = mode or summary["mode"]
    return {
        "summary": {
            "total_queries": summary["total_queries"],
            "cross_source_joins": summary["cross_source_queries"],
            "cache_hit_rate": summary["cache_hit_rate"],
            "total_rows": summary["total_rows"],
            "total_execution_time_ms": summary["total_execution_ms"],
            "sources_used": summary["sources"],
            "mode": resolved_mode,
        },
        "queries": [{**entry, "mode": resolved_mode} for entry in entries],
    }


def _best_query(entries: list[dict]) -> dict | None:
    cross_source = [entry for entry in entries if entry.get("is_cross_source")]
    pool = cross_source or entries
    if not pool:
        return None
    return max(pool, key=lambda entry: (len(entry.get("sources_used", [])), entry.get("rows_returned", 0)))
