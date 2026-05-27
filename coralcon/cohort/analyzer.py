"""Sample cohort analysis for placement-team framing."""

from coralcon.queries import skill_gaps


def analyze_cohort() -> dict:
    gaps = skill_gaps.fetch()
    top_gaps = sorted(gaps, key=lambda row: row.get("times_required", 0), reverse=True)[:5]
    return {
        "candidates_analyzed": 3,
        "most_common_rejection_cause": "Missing proof-of-work for claimed or demanded skills",
        "top_missing_skills": top_gaps,
        "leaderboard": [
            {"candidate": "candidate_001", "health_score": 64, "best_fit": "Python Backend"},
            {"candidate": "candidate_002", "health_score": 42, "best_fit": "Full Stack"},
            {"candidate": "candidate_003", "health_score": 31, "best_fit": "Frontend after TypeScript sprint"},
        ],
        "placement_actions": [
            "Run a 7-day TypeScript portfolio sprint.",
            "Fix LinkedIn headline mismatch for candidates targeting AI roles.",
            "Prioritize Python backend roles for candidates with stronger GitHub proof.",
        ],
    }
