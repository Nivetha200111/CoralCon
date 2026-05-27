"""Deterministic evidence-backed insight generation."""

from coralcon.models.insight_schema import EvidenceBackedInsight, InsightEvidence
from coralcon.proof.query_logger import find_query


def build_evidence_insights(analysis: dict) -> list[dict]:
    insights: list[EvidenceBackedInsight] = []

    patterns = analysis.get("rejection_patterns", [])
    if patterns:
        worst = max(patterns, key=lambda row: row.get("rejection_rate", 0))
        query = find_query(name="rejection_patterns") or {}
        insights.append(
            EvidenceBackedInsight(
                id="insight_001",
                title=f"{worst.get('role_title')} rejection pattern",
                severity="high" if worst.get("rejection_rate", 0) >= 70 else "medium",
                claim=f"{worst.get('role_title')} roles have a {worst.get('rejection_rate', 0):.1f}% rejection rate.",
                evidence=_evidence(
                    query,
                    worst.get("total", 0),
                    {
                        "applications": worst.get("total", 0),
                        "rejections": worst.get("rejected", 0),
                        "ghosted": worst.get("ghosted", 0),
                        "rejection_rate": worst.get("rejection_rate", 0),
                    },
                ),
                root_cause="The role category is currently outperforming the visible proof-of-work on the profile.",
                recommended_action=f"Pause cold applications to {worst.get('role_title')} roles and ship one targeted proof-of-work project.",
                expected_impact="Improve profile-fit before adding more applications to this bucket.",
                confidence=0.84,
            )
        )

    gaps = analysis.get("skill_gaps", [])
    critical = [gap for gap in gaps if gap.get("priority") == "critical"]
    if critical:
        top_gap = max(critical, key=lambda row: row.get("times_required", 0))
        query = find_query(name="skill_gap_detection") or {}
        insights.append(
            EvidenceBackedInsight(
                id="insight_002",
                title=f"{top_gap.get('skill')} proof gap",
                severity="high",
                claim=f"{top_gap.get('skill')} appears in {top_gap.get('times_required', 0)} rejected applications but is missing from key profile signals.",
                evidence=_evidence(
                    query,
                    top_gap.get("times_required", 0),
                    {
                        "times_required": top_gap.get("times_required", 0),
                        "in_github": top_gap.get("in_github", False),
                        "in_linkedin": top_gap.get("in_linkedin", False),
                    },
                ),
                root_cause="The job descriptions ask for the skill, but the public evidence is weak or absent.",
                recommended_action=f"Build and pin one {top_gap.get('skill')} project within 7 days.",
                expected_impact="Raise recruiter confidence for roles requiring this skill.",
                confidence=0.88,
            )
        )

    github = analysis.get("github_correlation", {})
    ghost_gap = github.get("ghost_rate_inactive_weeks", 0) - github.get("ghost_rate_active_weeks", 0)
    if ghost_gap > 0:
        query = find_query(name="github_activity_correlation") or {}
        insights.append(
            EvidenceBackedInsight(
                id="insight_003",
                title="GitHub activity signal",
                severity="high" if ghost_gap >= 30 else "medium",
                claim=f"Ghost rate is {ghost_gap:.1f} points higher in inactive GitHub weeks.",
                evidence=_evidence(
                    query,
                    query.get("rows_returned", 0),
                    {
                        "active_week_ghost_rate": github.get("ghost_rate_active_weeks", 0),
                        "inactive_week_ghost_rate": github.get("ghost_rate_inactive_weeks", 0),
                        "ghost_rate_gap": ghost_gap,
                    },
                ),
                root_cause="Recruiter-visible activity drops during parts of the application cycle.",
                recommended_action="Keep a steady commit cadence while applying, even if it is one focused commit per day.",
                expected_impact="Reduce ghosting risk tied to stale proof-of-work signals.",
                confidence=0.8,
            )
        )

    followups = analysis.get("followup_priorities", [])
    hot = [item for item in followups if item.get("priority") == "hot"]
    if hot:
        query = find_query(name="followup_tracker") or {}
        insights.append(
            EvidenceBackedInsight(
                id="insight_004",
                title="Follow-up window",
                severity="medium",
                claim=f"{len(hot)} applications are in the 7-14 day follow-up window.",
                evidence=_evidence(
                    query,
                    len(hot),
                    {"hot_followups": len(hot), "total_followups": len(followups)},
                ),
                root_cause="Pending applications are aging without a second touch.",
                recommended_action="Send follow-up emails to the hot queue today.",
                expected_impact="Capture the strongest follow-up timing window before applications go cold.",
                confidence=0.78,
            )
        )

    return [insight.model_dump() for insight in insights]


def _evidence(query: dict, rows_used: int, supporting_numbers: dict) -> InsightEvidence:
    return InsightEvidence(
        query_id=query.get("query_id", "q_unknown"),
        rows_used=rows_used,
        sources=query.get("sources_used", []),
        supporting_numbers=supporting_numbers,
    )
