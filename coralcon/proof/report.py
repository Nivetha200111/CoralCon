"""Generate human-readable Coral proof reports."""

from coralcon.proof.query_logger import get_query_log


def build_proof_report() -> str:
    entries = get_query_log()
    sources = sorted({source for entry in entries for source in entry.get("sources_used", [])})
    cross_source = [entry for entry in entries if entry.get("is_cross_source")]
    best = _best_query(entries)

    lines = [
        "CORAL PROOF REPORT",
        "=" * 19,
        f"Total Coral Queries: {len(entries)}",
        f"Cross-source JOINs: {len(cross_source)}",
        "",
        "Sources Used:",
    ]
    lines.extend(f"- {source}" for source in sources)
    lines.extend(["", "Best Coral Query:"])
    if best:
        lines.extend(
            [
                f"Query ID: {best['query_id']}",
                f"Name: {best['query_name']}",
                f"Rows: {best['rows_returned']}",
                f"Execution: {best['execution_ms']}ms",
                best["sql"],
            ]
        )
    else:
        lines.append("No queries logged yet. Run `coralcon analyze --no-ai` first.")

    return "\n".join(lines)


def proof_summary() -> dict:
    entries = get_query_log()
    return {
        "total_queries": len(entries),
        "cross_source_queries": sum(1 for entry in entries if entry.get("is_cross_source")),
        "sources": sorted({source for entry in entries for source in entry.get("sources_used", [])}),
        "queries": entries,
    }


def _best_query(entries: list[dict]) -> dict | None:
    cross_source = [entry for entry in entries if entry.get("is_cross_source")]
    pool = cross_source or entries
    if not pool:
        return None
    return max(pool, key=lambda entry: (len(entry.get("sources_used", [])), entry.get("rows_returned", 0)))
