"""Generate human-readable Coral proof reports."""

import os

from coralcon.proof.query_logger import get_query_log


def build_proof_report() -> str:
    entries = get_query_log()
    sources = sorted({source for entry in entries for source in entry.get("sources_used", [])})
    cross_source = [entry for entry in entries if entry.get("is_cross_source")]
    best = _best_query(entries)
    total_rows = sum(entry.get("rows_returned", 0) for entry in entries)
    total_time = sum(entry.get("execution_ms", 0) for entry in entries)
    cached_count = sum(1 for entry in entries if entry.get("used_cache"))
    mode = "real" if os.getenv("CORAL_AVAILABLE", "false").lower() == "true" else "sample"

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
    mode = "real" if os.getenv("CORAL_AVAILABLE", "false").lower() == "true" else "sample"

    return {
        "total_queries": len(entries),
        "cross_source_queries": cross_source_count,
        "sources": sources,
        "total_rows": total_rows,
        "total_execution_ms": round(total_time, 2),
        "cached_queries": cached_count,
        "mode": mode,
        "best_query": best,
        "queries": entries,
    }


def _best_query(entries: list[dict]) -> dict | None:
    cross_source = [entry for entry in entries if entry.get("is_cross_source")]
    pool = cross_source or entries
    if not pool:
        return None
    return max(pool, key=lambda entry: (len(entry.get("sources_used", [])), entry.get("rows_returned", 0)))
