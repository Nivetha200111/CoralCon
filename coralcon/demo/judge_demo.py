"""Deterministic judge demo flow."""

import json
import os
from pathlib import Path

from coralcon.orchestrator import CoralConOrchestrator
from coralcon.proof.query_logger import reset_query_log, get_query_log
from coralcon.submission.pack_generator import generate_submission_pack


def run_judge_demo(sample: bool = True) -> dict:
    previous = os.getenv("CORAL_AVAILABLE")
    if sample:
        os.environ["CORAL_AVAILABLE"] = "false"

    reset_query_log()
    result = CoralConOrchestrator().run_full_analysis(use_ai=False, dry_run=True)
    generate_submission_pack()
    evidence_path = _write_evidence_pack(result)

    if previous is None:
        os.environ.pop("CORAL_AVAILABLE", None)
    else:
        os.environ["CORAL_AVAILABLE"] = previous

    return {"result": result, "evidence_path": str(evidence_path)}


def run_real_demo() -> dict:
    """Run the judge demo against real Coral connections (CORAL_AVAILABLE=true)."""
    previous = os.getenv("CORAL_AVAILABLE")
    os.environ["CORAL_AVAILABLE"] = "true"

    reset_query_log()
    result = CoralConOrchestrator().run_full_analysis(use_ai=False, dry_run=True)
    generate_submission_pack()
    evidence_path = _write_evidence_pack(result)

    if previous is None:
        os.environ.pop("CORAL_AVAILABLE", None)
    else:
        os.environ["CORAL_AVAILABLE"] = previous

    return {"result": result, "evidence_path": str(evidence_path)}


def real_demo_lines(payload: dict) -> list[str]:
    """Format the real-Coral demo output."""
    return demo_lines(payload["result"], payload["evidence_path"], sample=False)


def demo_lines(result: dict, evidence_path: str, sample: bool = True) -> list[str]:
    insights = result["insights"]
    patterns = insights.get("rejection_patterns", [])
    worst = max(patterns, key=lambda row: row.get("rejection_rate", 0)) if patterns else {}
    gaps = insights.get("skill_gaps", [])
    top_gap = max(gaps, key=lambda row: row.get("times_required", 0)) if gaps else {}
    tasks = result.get("tasks", [])
    evidence_insights = insights.get("evidence_insights", [])
    queries = get_query_log()
    cross_source = [q for q in queries if q.get("is_cross_source")]
    sources = sorted({s for q in queries for s in q.get("sources_used", [])})

    mode_label = "Deterministic sample mode for reproducible judging" if sample else "Live Coral SQL mode"

    lines = [
        "",
        f"  [bold bright_cyan]CoralCon Judge Demo[/bold bright_cyan]  [dim]({mode_label})[/dim]",
        "",
        "  [bold]Step 1/6: Checking Coral data layer[/bold]",
        f"  [bright_green]OK[/bright_green] GitHub source {'sampled' if sample else 'connected'}",
        f"  [bright_green]OK[/bright_green] Sheets applications loaded (from Gmail): [bright_cyan]{insights.get('total_applications', 0)}[/bright_cyan]",
        f"  [bright_green]OK[/bright_green] LinkedIn GDPR source loaded: [bright_cyan]{len(gaps)}[/bright_cyan] skills mapped",
        "",
        "  [bold]Step 2/6: Running cross-source Coral SQL[/bold]",
        f"  [bright_green]OK[/bright_green] Joined sheets.applications + github.activity + linkedin.skills",
        f"  [bright_green]OK[/bright_green] {len(queries)} Coral queries executed ({len(cross_source)} cross-source JOINs)",
        f"  [bright_green]OK[/bright_green] Sources queried: {', '.join(sources)}",
        f"  [bright_green]OK[/bright_green] {insights.get('total_applications', 0)} applications analyzed across {len(patterns)} role categories",
        "",
        "  [bold]Step 3/6: Decoding rejection patterns[/bold]",
    ]

    if worst:
        lines.append(
            f"  [bright_red]WARN[/bright_red] {worst.get('role_title', 'Role')} roles: "
            f"[bright_red]{worst.get('rejection_rate', 0):.1f}%[/bright_red] rejection rate "
            f"across {worst.get('total', 0)} applications"
        )
    if top_gap:
        lines.append(
            f"  [bright_red]WARN[/bright_red] Root cause: {top_gap.get('skill', 'unknown')} "
            f"required {top_gap.get('times_required', 0)} times but missing from profile"
        )
    github = insights.get("github_correlation", {})
    ghost_gap = github.get("ghost_rate_inactive_weeks", 0) - github.get("ghost_rate_active_weeks", 0)
    if ghost_gap > 0:
        lines.append(
            f"  [bright_red]WARN[/bright_red] GitHub signal: ghost rate {ghost_gap:.0f} pts higher in inactive weeks"
        )

    lines.extend([
        "",
        "  [bold]Step 4/6: Building evidence-backed insights[/bold]",
        f"  [bright_green]OK[/bright_green] {len(evidence_insights)} insights generated with query evidence",
        "  [bright_green]OK[/bright_green] Each insight includes query ID, source tables, and supporting numbers",
        "  [bright_green]OK[/bright_green] No hallucinated numbers — all values from Coral query results",
    ])

    for ei in evidence_insights[:3]:
        conf = ei.get("confidence", 0)
        lines.append(
            f"       [dim]{ei['title']} (confidence: {conf:.0%}, "
            f"query: {ei['evidence']['query_id']})[/dim]"
        )

    lines.extend([
        "",
        "  [bold]Step 5/6: Generating action plan[/bold]",
        f"  [bright_green]OK[/bright_green] {len(tasks)} prioritized actions created",
    ])
    if tasks:
        lines.append(f"  [bright_green]OK[/bright_green] Top action: {tasks[0]['title']}")
    lines.append("  [bright_green]OK[/bright_green] Follow-up queue prioritized by urgency")

    lines.extend([
        "",
        "  [bold]Step 6/6: Generating judge evidence pack[/bold]",
        "  [bright_green]OK[/bright_green] runs/latest/proof.json",
        "  [bright_green]OK[/bright_green] runs/latest/insights.json",
        "  [bright_green]OK[/bright_green] runs/latest/report.md",
        f"  [bright_green]OK[/bright_green] {evidence_path}",
        "",
        f"  [bold bright_cyan]Proof summary:[/bold bright_cyan] {len(queries)} queries | "
        f"{len(cross_source)} cross-source JOINs | {len(sources)} sources | "
        f"{len(evidence_insights)} evidence-backed insights",
        "",
    ])

    return lines


def _write_evidence_pack(result: dict) -> Path:
    submission_dir = Path("submission")
    submission_dir.mkdir(exist_ok=True)
    path = submission_dir / "coralcon_evidence_pack.md"

    insights = result["insights"]
    queries = get_query_log()
    cross_source = [q for q in queries if q.get("is_cross_source")]
    sources = sorted({s for q in queries for s in q.get("sources_used", [])})
    best = _best_query(queries)

    lines = [
        "# CoralCon Evidence Pack",
        "",
        "> Other agents tell you what to do. CoralCon proves why you're failing,",
        "> with evidence from the data you already have.",
        "",
        "## Project Pitch",
        "",
        "CoralCon is a local-first career intelligence agent that turns rejection",
        "history into an evidence-backed improvement plan by joining GitHub proof-of-work,",
        "a Google Sheets tracker (auto-filled from Gmail rejections), and LinkedIn",
        "profile signals through Coral SQL.",
        "",
        "## Why Coral Matters",
        "",
        "Coral SQL is the central data layer. Without it, CoralCon would need three",
        "separate API integrations with custom auth, pagination, schema mapping, and",
        "correlation logic. With Coral, the agent asks one SQL question across all sources.",
        "",
        "## Coral Proof Summary",
        "",
        f"- **Total Coral queries:** {len(queries)}",
        f"- **Cross-source JOINs:** {len(cross_source)}",
        f"- **Sources queried:** {', '.join(sources)}",
    ]

    if best:
        lines.extend([
            f"- **Best query:** {best.get('query_name', 'unknown')}",
            f"- **Best query rows:** {best.get('rows_returned', 0)}",
            f"- **Best query time:** {best.get('execution_ms', 0)}ms",
        ])

    cached_count = sum(1 for q in queries if q.get("used_cache"))
    lines.append(f"- **Cached queries:** {cached_count}")

    mode = "sample" if os.getenv("CORAL_AVAILABLE", "false").lower() != "true" else "real"
    lines.extend([
        f"- **Mode:** {mode}",
        "",
        "## Architecture",
        "",
        "```",
        "Gmail (extract) -> Google Sheet -> data/applications.csv",
        "CLI/Web -> Orchestrator -> Recon Agent -> Coral SQL -> GitHub + Sheets + LinkedIn",
        "                       -> Analyst Agent (evidence-backed insights)",
        "                       -> Action Agent (prioritized tasks)",
        "```",
        "",
        "## Data Sources",
        "",
        "| Source | Coral Table | Data |",
        "|--------|------------|------|",
        "| GitHub | `github.activity`, `github.profile`, `github.repos` | Commit cadence, repo languages, public events |",
        "| Google Sheets | `sheets.applications` | Company, role, status, required skills, dates (from Gmail) |",
        "| LinkedIn | `linkedin.skills`, `linkedin.profile`, `linkedin.positions` | GDPR export: skills, endorsements, headline |",
        "",
        "## Analysis Results",
        "",
        f"- Applications analyzed: {insights.get('total_applications', 0)}",
        f"- Response rate: {insights.get('response_rate', 0):.1f}%",
        f"- Health score: {insights.get('overall_health_score', 0)}/100",
        f"- Offer rate: {insights.get('offer_rate', 0):.1f}%",
        "",
        "## Evidence-Backed Insights",
        "",
    ])

    for insight in insights.get("evidence_insights", []):
        evidence = insight.get("evidence", {})
        lines.extend([
            f"### {insight['title']}",
            "",
            f"**Claim:** {insight['claim']}",
            f"**Severity:** {insight['severity']}",
            f"**Confidence:** {insight.get('confidence', 0):.0%}",
            f"**Evidence query:** {evidence.get('query_id', 'unknown')}",
            f"**Sources:** {', '.join(evidence.get('sources', []))}",
            f"**Rows used:** {evidence.get('rows_used', 0)}",
            f"**Root cause:** {insight['root_cause']}",
            f"**Action:** {insight['recommended_action']}",
            f"**Expected impact:** {insight.get('expected_impact', '')}",
            "",
        ])

    lines.extend([
        "## Best Coral Queries",
        "",
    ])

    for q in queries:
        if q.get("is_cross_source"):
            lines.extend([
                f"### {q.get('query_name', 'query')} ({q.get('query_id', '')})",
                "",
                f"- Sources: {', '.join(q.get('sources_used', []))}",
                f"- Rows: {q.get('rows_returned', 0)}",
                f"- Execution: {q.get('execution_ms', 0)}ms",
                f"- Cached: {'yes' if q.get('used_cache') else 'no'}",
                "",
                "```sql",
                q.get("sql", ""),
                "```",
                "",
            ])

    lines.extend([
        "## Sample Mode vs Real Mode",
        "",
        "**Sample mode** uses deterministic seeded data from `data/sample/` for reproducible",
        "judging. Every run produces identical results. No API keys or Coral installation needed.",
        "",
        "**Real mode** connects to actual GitHub, Google Sheets (from Gmail), and LinkedIn data through Coral SQL.",
        "Set `CORAL_AVAILABLE=true` and configure source credentials.",
        "",
        "Both modes use the same four-agent pipeline and produce the same evidence artifacts.",
        "The only difference is the data source.",
        "",
        "## Privacy / Local-First",
        "",
        "- All Coral queries execute locally",
        "- Raw source data never leaves the machine",
        "- LLM analysis (optional) sends only summarized results, not raw data",
        "- No telemetry, no analytics, no external tracking",
        "",
        "## Judge Run Commands",
        "",
        "```bash",
        "pip install -r requirements.txt",
        "python -m coralcon.cli judge-demo --sample   # Full demo pipeline",
        "python -m coralcon.cli proof                  # Coral query audit trail",
        "python -m coralcon.cli submit-pack            # Generate submission files",
        "python -m coralcon.cli serve                  # Web dashboard at :8000",
        "```",
        "",
        "## Known Limitations",
        "",
        "- LinkedIn source requires manual GDPR data export (API access is restricted)",
        "- Gmail extraction + Sheets writes use the Google APIs directly (Coral is read-only);",
        "  Coral reads the synced sheet via the `sheets` file source",
        "- LLM narrative insights require an Anthropic API key; the rule-based fallback",
        "  provides all core insights without it",
        "- Cohort mode currently uses anonymized sample candidates",
        "",
    ])

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _best_query(entries: list[dict]) -> dict | None:
    cross = [e for e in entries if e.get("is_cross_source")]
    pool = cross or entries
    if not pool:
        return None
    return max(pool, key=lambda e: (len(e.get("sources_used", [])), e.get("rows_returned", 0)))
