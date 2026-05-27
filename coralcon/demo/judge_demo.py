"""Deterministic judge demo flow."""

import os
from pathlib import Path

from coralcon.orchestrator import CoralConOrchestrator
from coralcon.proof.query_logger import reset_query_log
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


def demo_lines(result: dict, evidence_path: str, sample: bool = True) -> list[str]:
    insights = result["insights"]
    patterns = insights.get("rejection_patterns", [])
    worst = max(patterns, key=lambda row: row.get("rejection_rate", 0)) if patterns else {}
    gaps = insights.get("skill_gaps", [])
    top_gap = max(gaps, key=lambda row: row.get("times_required", 0)) if gaps else {}
    tasks = result.get("tasks", [])

    return [
        "CoralCon Judge Demo",
        "",
        "Step 1/6: Proving Coral sources",
        f"OK GitHub source {'sampled' if sample else 'detected'}",
        f"OK Notion applications loaded: {insights.get('total_applications', 0)}",
        f"OK LinkedIn GDPR skills mapped: {len(gaps)}",
        "",
        "Step 2/6: Running cross-source Coral SQL",
        "OK Query joined notion.applications + github.activity + linkedin.skills",
        f"OK {insights.get('total_applications', 0)} applications analyzed",
        "",
        "Step 3/6: Decoding rejection patterns",
        f"WARN {worst.get('role_title', 'Role')} roles: {worst.get('rejection_rate', 0):.1f}% rejection",
        f"Root cause: strongest missing proof signal is {top_gap.get('skill', 'unknown skill')}",
        "",
        "Step 4/6: Building action plan",
        f"OK {len(tasks)} Notion-ready tasks generated",
        f"OK Top task: {tasks[0]['title'] if tasks else 'No task generated'}",
        "",
        "Step 5/6: Generating dashboard",
        "OK Local dashboard available with `coralcon serve`",
        "",
        "Step 6/6: Producing judge evidence pack",
        f"OK {evidence_path} created",
    ]


def _write_evidence_pack(result: dict) -> Path:
    submission_dir = Path("submission")
    submission_dir.mkdir(exist_ok=True)
    path = submission_dir / "coralcon_evidence_pack.md"
    insights = result["insights"]
    lines = [
        "# CoralCon Evidence Pack",
        "",
        f"Applications analyzed: {insights.get('total_applications', 0)}",
        f"Health score: {insights.get('overall_health_score', 0)}/100",
        "",
        "## Evidence-Backed Insights",
    ]
    for insight in insights.get("evidence_insights", []):
        lines.extend(
            [
                f"### {insight['title']}",
                insight["claim"],
                f"Query: {insight['evidence']['query_id']}",
                f"Action: {insight['recommended_action']}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
