"""
Rule-based action item generator.
Converts structured data into prioritized, concrete action items.
No LLM needed — pure logic.
"""

from coralcon.models.schemas import RejectionPattern, SkillGap


def generate_action_items(
    patterns: list[dict],
    skill_gaps: list[dict],
    github_signal: dict,
    timing: list[dict],
    follow_up_count: int = 0,
) -> list[str]:
    """Generate prioritized action items from analysis data."""
    actions = []

    # 1. Rejection pattern actions
    critical_roles = [
        p for p in patterns if p.get("rejection_rate", 0) >= 80
    ]
    if critical_roles:
        role = critical_roles[0]["role_title"]
        rate = critical_roles[0]["rejection_rate"]
        actions.append(
            f"Stop applying to {role} roles until you fix your profile. "
            f"{rate:.0f}% rejection rate."
        )

    # 2. Skill gap actions
    critical_gaps = [g for g in skill_gaps if g.get("priority") == "critical"]
    if critical_gaps:
        top_skill = critical_gaps[0]["skill"]
        count = critical_gaps[0]["times_required"]
        actions.append(
            f"Build 1 project using {top_skill} this week. "
            f"Missing from {count} rejected applications."
        )

    # 3. GitHub signal
    active_ghost = github_signal.get("ghost_rate_active_weeks", 100)
    inactive_ghost = github_signal.get("ghost_rate_inactive_weeks", 100)
    if inactive_ghost - active_ghost > 20:
        diff = inactive_ghost - active_ghost
        actions.append(
            f"Commit to GitHub daily during job search. "
            f"Your ghost rate drops {diff:.0f}% in active commit weeks."
        )

    # 4. Timing actions
    same_day_rate = next(
        (t.get("response_rate", 0) for t in timing if t.get("timing_bucket") == "same_day"),
        None,
    )
    late_rate = next(
        (t.get("response_rate", 0) for t in timing if t.get("timing_bucket") == "2_weeks_plus"),
        None,
    )
    if same_day_rate and late_rate and same_day_rate > late_rate * 2:
        actions.append(
            f"Apply within 24 hours of job posting. "
            f"Same-day applications have {same_day_rate:.0f}% response rate vs {late_rate:.0f}% late."
        )

    # 5. Follow-up
    if follow_up_count >= 10:
        actions.append(
            f"Send follow-up emails to your {follow_up_count} pending applications. "
            f"Day 10 follow-ups have 22% response rate."
        )

    # Fallback if no data-driven actions
    if not actions:
        actions = [
            "Connect Notion, GitHub, and LinkedIn to get personalized recommendations.",
            "Log at least 20 applications to get statistically meaningful patterns.",
        ]

    return actions[:6]


def prioritize_followups(followups: list[dict]) -> list[dict]:
    """Sort and annotate follow-ups by priority."""
    priority_order = {"hot": 0, "warm": 1, "cold": 2}
    return sorted(followups, key=lambda x: priority_order.get(x.get("priority", "cold"), 2))


def compute_github_signal(activity: list[dict], applications: list[dict]) -> dict:
    """
    Correlate GitHub commit weeks with application outcomes.
    Returns ghost rates for active vs inactive weeks.
    """
    if not activity or not applications:
        return {
            "ghost_rate_active_weeks": 0,
            "ghost_rate_inactive_weeks": 0,
            "top_language": "N/A",
            "total_repos": 0,
        }

    active_apps = [a for a in applications if a.get("commits_count", 0) > 0]
    inactive_apps = [a for a in applications if a.get("commits_count", 0) == 0]

    def ghost_rate(apps):
        if not apps:
            return 0
        ghosts = sum(1 for a in apps if a.get("status") == "ghosted")
        return round(ghosts * 100 / len(apps), 1)

    languages = []
    for row in activity:
        langs = row.get("languages", [])
        if isinstance(langs, list):
            languages.extend(langs)
        elif isinstance(langs, str):
            languages.extend(langs.split(","))

    from collections import Counter
    top_lang = Counter(l.strip() for l in languages if l.strip()).most_common(1)

    return {
        "ghost_rate_active_weeks": ghost_rate(active_apps),
        "ghost_rate_inactive_weeks": ghost_rate(inactive_apps),
        "top_language": top_lang[0][0] if top_lang else "N/A",
        "total_repos": max((a.get("active_repos", 0) or 0 for a in activity), default=0),
    }
