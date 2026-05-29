"""
Natural-language intent router.

The deterministic core decides WHICH Coral query answers a question and runs it;
the LLM is only an interface layer (intent classification + result narration) and
never writes SQL. This keeps every query bounded, schema-safe, and judge-verifiable.

Pipeline:
  question -> classify (LLM, or keyword fallback) -> run fixed query macro
           -> deterministic headline (always true) -> optional LLM narrative
"""

from __future__ import annotations

from coralcon.agents import analyzer, recommender
from coralcon.proof.query_logger import find_query
from coralcon.queries import (
    followup_tracker,
    github_correlation,
    rejection_patterns,
    skill_gaps,
    timing_analysis,
)


def _github_rows() -> list[dict]:
    return github_correlation.fetch()


INTENTS: list[dict] = [
    {
        "id": "rejections",
        "query_name": "rejection_patterns",
        "summary": "Rejection and ghost rates broken down by role title.",
        "keywords": [
            "reject", "rejection", "ghost", "ghosted", "turned down", "no response",
            "which roles", "which jobs", "role", "failing", "losing",
        ],
        "fetch": rejection_patterns.fetch,
    },
    {
        "id": "gaps",
        "query_name": "skill_gap_detection",
        "summary": "Skills required in rejected applications but missing from GitHub and LinkedIn.",
        "keywords": [
            "skill", "skills", "gap", "missing", "learn", "qualified", "requirement",
            "underqualified", "what should i learn", "weak",
        ],
        "fetch": skill_gaps.fetch,
    },
    {
        "id": "github",
        "query_name": "github_activity_correlation",
        "summary": "Whether GitHub commit activity correlates with getting ghosted.",
        "keywords": [
            "github", "commit", "commits", "activity", "repo", "repos",
            "proof of work", "code", "contribution", "green squares",
        ],
        "fetch": _github_rows,
    },
    {
        "id": "timing",
        "query_name": "timing_analysis",
        "summary": "Response rate by how quickly an application was sent after the posting.",
        "keywords": [
            "timing", "when", "how soon", "early", "fast", "quick", "late",
            "speed", "first", "deadline", "how fast",
        ],
        "fetch": timing_analysis.fetch,
    },
    {
        "id": "followup",
        "query_name": "followup_tracker",
        "summary": "Pending applications that need a follow-up email and when to send it.",
        "keywords": [
            "follow up", "followup", "follow-up", "email", "waiting", "pending",
            "chase", "reach out", "who should i", "remind",
        ],
        "fetch": followup_tracker.fetch,
    },
]

_INTENT_BY_ID = {it["id"]: it for it in INTENTS}
_DEFAULT_INTENT = "rejections"

# Fields stripped before any rows reach the LLM, so narration never sees
# company names or personal identifiers (matches the local-first privacy claim).
_REDACT_FIELDS = {"company", "name", "email", "contact", "applied_date"}


def _redact(rows: list[dict]) -> list[dict]:
    return [{k: v for k, v in row.items() if k.lower() not in _REDACT_FIELDS} for row in rows]


def _keyword_intent(question: str) -> str:
    q = question.casefold()
    best_id, best_score = _DEFAULT_INTENT, 0
    for intent in INTENTS:
        score = sum(1 for kw in intent["keywords"] if kw in q)
        if score > best_score:
            best_id, best_score = intent["id"], score
    return best_id


def classify(question: str, use_ai: bool = True) -> tuple[str, str]:
    """Return (intent_id, method) where method is 'llm' or 'keyword'."""
    if use_ai:
        try:
            return analyzer.classify_intent(question, INTENTS), "llm"
        except Exception:
            pass
    return _keyword_intent(question), "keyword"


def headline(intent_id: str, rows: list[dict]) -> str:
    """A deterministic, always-true one-liner derived straight from the rows."""
    if not rows:
        return "Not enough data logged yet to answer this confidently."

    if intent_id == "rejections":
        top = max(rows, key=lambda r: r.get("rejection_rate", 0))
        return (
            f"{top.get('role_title', 'Unknown')} roles have a "
            f"{top.get('rejection_rate', 0):.0f}% rejection rate "
            f"across {top.get('total', 0)} applications."
        )

    if intent_id == "gaps":
        top = max(rows, key=lambda r: r.get("times_required", 0))
        return (
            f"{top.get('skill', 'A required skill')} appears in "
            f"{top.get('times_required', 0)} rejected applications "
            f"but is missing from your profile."
        )

    if intent_id == "github":
        signal = recommender.compute_github_signal(rows, rows)
        diff = signal["ghost_rate_inactive_weeks"] - signal["ghost_rate_active_weeks"]
        return (
            f"Ghost rate is {diff:.0f} points higher in weeks with no GitHub commits "
            f"({signal['ghost_rate_inactive_weeks']:.0f}% vs "
            f"{signal['ghost_rate_active_weeks']:.0f}%)."
        )

    if intent_id == "timing":
        top = max(rows, key=lambda r: r.get("response_rate", 0))
        return (
            f"'{str(top.get('timing_bucket', '')).replace('_', ' ')}' applications have the "
            f"best response rate at {top.get('response_rate', 0):.0f}%."
        )

    if intent_id == "followup":
        hot = sum(1 for r in rows if r.get("priority") == "hot")
        return f"{len(rows)} applications are pending follow-up; {hot} are in the optimal window."

    return f"{len(rows)} rows returned."


def answer(question: str, use_ai: bool = True) -> dict:
    """Route a question to a Coral query and return a full answer payload."""
    intent_id, method = classify(question, use_ai=use_ai)
    intent = _INTENT_BY_ID.get(intent_id, _INTENT_BY_ID[_DEFAULT_INTENT])

    rows = intent["fetch"]()
    proof = find_query(name=intent["query_name"]) or find_query(sources=None)

    line = headline(intent["id"], rows)

    narrative = line
    narrative_source = "deterministic"
    if use_ai:
        try:
            narrative = analyzer.narrate(question, intent["summary"], _redact(rows))
            narrative_source = "llm"
        except Exception:
            pass

    return {
        "question": question,
        "intent_id": intent["id"],
        "query_name": intent["query_name"],
        "summary": intent["summary"],
        "classified_by": method,
        "headline": line,
        "narrative": narrative,
        "narrative_source": narrative_source,
        "rows": rows,
        "row_count": len(rows),
        "proof": proof,
    }
