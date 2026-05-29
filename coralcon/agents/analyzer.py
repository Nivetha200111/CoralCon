"""
LLM-powered insight generator using Claude API.
Takes structured query results and returns blunt, actionable analysis.
"""

import os
import json

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Add it to your .env file."
            )
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError(
                "anthropic is not installed. Run `pip install -r requirements.txt`."
            ) from exc
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def generate_full_analysis(query_results: dict) -> str:
    """
    Generate a full career analysis from all query results.
    Returns blunt, data-backed recommendations.
    """
    client = _get_client()

    rejections = query_results.get("rejections", [])
    github = query_results.get("github_signal", {})
    skills = query_results.get("skill_gaps", [])
    timing = query_results.get("timing", [])
    total_apps = query_results.get("total_applications", 0)
    response_rate = query_results.get("response_rate", 0)

    prompt = f"""You are a blunt career coach analyzing someone's job search data. Give direct, data-backed advice. No fluff.

JOB SEARCH OVERVIEW:
- Total applications: {total_apps}
- Response rate: {response_rate:.1f}%
- Data from: GitHub, Notion (application tracker), LinkedIn

REJECTION PATTERNS BY ROLE:
{json.dumps(rejections[:10], indent=2)}

GITHUB SIGNAL:
- Ghost rate in active commit weeks: {github.get('ghost_rate_active_weeks', 0):.0f}%
- Ghost rate in inactive (zero commit) weeks: {github.get('ghost_rate_inactive_weeks', 0):.0f}%
- Top language: {github.get('top_language', 'unknown')}
- Total repos: {github.get('total_repos', 0)}

TOP SKILL GAPS (skills required in rejected applications but missing from profile):
{json.dumps(skills[:8], indent=2)}

APPLICATION TIMING:
{json.dumps(timing, indent=2)}

Give exactly 5 numbered insights. Each must:
1. Start with the data point ("Your X rate is Y%...")
2. Explain what it means
3. End with a specific action ("Build a [X] project", "Apply within 48h", etc.)

Be blunt. Use exact numbers. No hedging. Format as plain text, one insight per paragraph."""

    response = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def classify_intent(question: str, intents: list[dict]) -> str:
    """Map a natural-language question to exactly one predefined intent id.

    The LLM only selects from a fixed enum; it never writes SQL. Returns the
    chosen intent id. Raises if the model returns an unknown id so the caller
    can fall back to deterministic keyword routing.
    """
    client = _get_client()

    catalog = "\n".join(f"- {it['id']}: {it['summary']}" for it in intents)
    valid_ids = {it["id"] for it in intents}

    prompt = f"""You route a job-seeker's question to ONE career-analysis query.

Available analyses:
{catalog}

Question: "{question}"

Respond with ONLY the single best id from the list above. No punctuation, no explanation."""

    response = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=16,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip().lower()
    for token in raw.replace("`", " ").replace(".", " ").split():
        if token in valid_ids:
            return token
    if raw in valid_ids:
        return raw
    raise ValueError(f"Unrecognized intent id from model: {raw!r}")


def narrate(question: str, intent_summary: str, rows: list[dict]) -> str:
    """Narrate an answer from query result rows only.

    The model receives the filtered result rows as JSON and nothing else, so it
    cannot invent numbers or be steered by raw source text (prompt-injection safe).
    """
    client = _get_client()

    prompt = f"""You are a blunt career coach. Answer the user's question using ONLY the data rows below.

Question: "{question}"
What this data shows: {intent_summary}

DATA ROWS (the only facts you may use):
{json.dumps(rows[:15], indent=2)}

Rules:
- 2-3 sentences max. No preamble.
- Cite exact numbers from the rows. Never invent a number that is not present.
- End with one specific action.
- If the rows are empty, say there is not enough data yet and what to log."""

    response = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=220,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def generate_rejection_decoder(patterns: list[dict]) -> str:
    """Focused analysis on rejection patterns."""
    client = _get_client()

    prompt = f"""Analyze these rejection patterns from someone's job search data. Be blunt.

{json.dumps(patterns, indent=2)}

Give 3 sentences max. State the pattern, explain why, tell them what to do. Use exact numbers."""

    response = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def generate_skill_gap_summary(gaps: list[dict], github_languages: list[str]) -> str:
    """Focused analysis on skill gaps."""
    client = _get_client()

    prompt = f"""Someone is getting rejected from jobs. Here are the skill gaps — skills required in rejected roles but missing from their GitHub/LinkedIn:

Skill gaps: {json.dumps(gaps[:10], indent=2)}
Their GitHub languages: {github_languages}

Give 3 bullet points:
- Which skills to learn first (highest rejection impact)
- Whether to add them to GitHub (build projects) or LinkedIn (just list them)
- Estimated time to fix each gap

Be specific. No generic advice."""

    response = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
