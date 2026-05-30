"""Daily job-search standup — the Track 2 "first mate" briefing.

Joins the same three Coral sources the rest of CoralCon uses (sheets.applications,
github.user_repos, linkedin.skills) into a single morning view: where you stand
and the highest-leverage moves for today. Shared by the `coralcon morning` CLI
command and the `/api/morning` dashboard endpoint so both stay in sync.
"""

from __future__ import annotations

import os
from datetime import date

from coralcon.agents import recommender
from coralcon.queries import (
    followup_tracker,
    github_correlation,
    rejection_patterns,
    skill_gaps,
)


def build_standup() -> dict:
    """Return structured daily-briefing data computed from real Coral queries."""
    patterns = rejection_patterns.fetch()
    gaps = skill_gaps.fetch()
    followups = followup_tracker.fetch()
    github_data = github_correlation.fetch()
    signal = recommender.compute_github_signal(github_data, github_data)

    total = sum(int(p.get("total", 0)) for p in patterns)
    responses = sum(int(p.get("interviewed", 0)) + int(p.get("offers", 0)) for p in patterns)
    response_rate = round(responses * 100.0 / total, 1) if total else 0.0

    # The headline skill move: the most-demanded skill missing from BOTH your
    # GitHub and LinkedIn (fall back to the single biggest gap).
    missing = [g for g in gaps if not g.get("in_github") and not g.get("in_linkedin")]
    top_gap = missing[0] if missing else (gaps[0] if gaps else None)

    hot_followups = [f for f in followups if f.get("priority") == "hot"]
    ghost_diff = round(
        signal.get("ghost_rate_inactive_weeks", 0) - signal.get("ghost_rate_active_weeks", 0), 1
    )

    priorities: list[dict] = []

    if top_gap:
        where = []
        if not top_gap.get("in_github"):
            where.append("not in your GitHub")
        if not top_gap.get("in_linkedin"):
            where.append("not on your LinkedIn")
        priorities.append(
            {
                "severity": "high",
                "title": f"Build proof in {top_gap.get('skill', '')}",
                "detail": (
                    f"Demanded by {top_gap.get('times_required', 0)} roles that rejected you, "
                    f"{' and '.join(where) or 'underrepresented in your profile'}."
                ),
            }
        )

    if hot_followups:
        names = ", ".join(f.get("company", "?") for f in hot_followups[:3])
        priorities.append(
            {
                "severity": "high",
                "title": f"Send {len(hot_followups)} follow-up(s) today",
                "detail": f"In the optimal 7–14 day window: {names}.",
            }
        )
    else:
        priorities.append(
            {
                "severity": "info",
                "title": "No follow-ups in the 7–14 day window",
                "detail": "Add applied_date to pending rows to track this.",
            }
        )

    if ghost_diff > 10:
        priorities.append(
            {
                "severity": "high",
                "title": "Push code today",
                "detail": f"Your ghost rate is {ghost_diff:.0f}% higher in weeks you don't commit.",
            }
        )
    else:
        priorities.append(
            {
                "severity": "info",
                "title": "GitHub cadence looks fine",
                "detail": "Keep shipping.",
            }
        )

    return {
        "date": date.today().isoformat(),
        "date_label": date.today().strftime("%A, %B %d, %Y"),
        "total_applications": total,
        "response_rate": response_rate,
        "top_gap": top_gap,
        "hot_followups": hot_followups,
        "github_ghost_diff": ghost_diff,
        "priorities": priorities,
        "using_sample_data": os.getenv("CORAL_AVAILABLE", "false").lower() != "true",
    }
