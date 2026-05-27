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
