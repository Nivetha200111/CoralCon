"""Cohort report formatting."""

from coralcon.cohort.analyzer import analyze_cohort


def build_cohort_report() -> str:
    data = analyze_cohort()
    lines = [
        "COHORT CAREER INTELLIGENCE REPORT",
        "=" * 39,
        f"Candidates analyzed: {data['candidates_analyzed']}",
        f"Most common rejection cause: {data['most_common_rejection_cause']}",
        "",
        "Top missing skills:",
    ]
    for index, gap in enumerate(data["top_missing_skills"], 1):
        lines.append(f"{index}. {gap.get('skill')} - demanded in {gap.get('times_required')} rejected applications")
    lines.extend(["", "Placement Team Actions:"])
    for index, action in enumerate(data["placement_actions"], 1):
        lines.append(f"{index}. {action}")
    return "\n".join(lines)
