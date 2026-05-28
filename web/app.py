"""FastAPI web dashboard for CoralCon."""

import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool
from pathlib import Path
from dotenv import load_dotenv

from coralcon.agents.analyst import AnalystAgent
from coralcon.queries import (
    rejection_patterns,
    github_correlation,
    skill_gaps,
    timing_analysis,
    followup_tracker,
)
from coralcon.agents import recommender
from coralcon.cohort.analyzer import analyze_cohort
from coralcon.portfolio import inspect_portfolio
from coralcon.proof.report import proof_summary
from coralcon.utils.coral_client import check_coral_connection

load_dotenv()

app = FastAPI(title="CoralCon Dashboard", docs_url=None, redoc_url=None)

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"request": request}
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_alias(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"request": request}
    )


@app.get("/proof", response_class=HTMLResponse)
async def proof_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"request": request}
    )


@app.get("/cohort", response_class=HTMLResponse)
async def cohort_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"request": request}
    )


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"request": request}
    )


@app.get("/api/summary")
async def api_summary():
    patterns = rejection_patterns.fetch()
    total = sum(p.get("total", 0) for p in patterns)
    responded = sum(p.get("interviewed", 0) + p.get("offers", 0) for p in patterns)
    interviewed = sum(p.get("interviewed", 0) for p in patterns)
    offers = sum(p.get("offers", 0) for p in patterns)

    return {
        "total_applications": total,
        "response_rate": round(responded / total * 100, 1) if total else 0,
        "interview_rate": round(interviewed / total * 100, 1) if total else 0,
        "offer_rate": round(offers / total * 100, 1) if total else 0,
        "using_sample_data": os.getenv("CORAL_AVAILABLE", "false").lower() != "true",
    }


@app.get("/api/dashboard")
async def api_dashboard():
    return await run_in_threadpool(_build_dashboard_payload)


@app.get("/api/rejections")
async def api_rejections():
    return rejection_patterns.fetch()


@app.get("/api/github")
async def api_github():
    data = github_correlation.fetch()
    signal = recommender.compute_github_signal(data, data)
    return {"rows": data, "signal": signal}


@app.get("/api/skills")
async def api_skills():
    gaps = skill_gaps.fetch()
    portfolio = await run_in_threadpool(inspect_portfolio)
    detected = {str(skill).casefold() for skill in portfolio.get("detected_skills", [])}
    for gap in gaps:
        gap["in_portfolio"] = str(gap.get("skill", "")).casefold() in detected
    return gaps


@app.get("/api/portfolio")
async def api_portfolio(url: str | None = None):
    return await run_in_threadpool(inspect_portfolio, url)


@app.get("/api/timing")
async def api_timing():
    return timing_analysis.fetch()


@app.get("/api/followup")
async def api_followup():
    data = followup_tracker.fetch()
    return recommender.prioritize_followups(data)


@app.get("/api/actions")
async def api_actions():
    patterns = rejection_patterns.fetch()
    gaps = skill_gaps.fetch()
    github_data = github_correlation.fetch()
    timing = timing_analysis.fetch()
    followups = followup_tracker.fetch()
    signal = recommender.compute_github_signal(github_data, github_data)
    actions = recommender.generate_action_items(
        patterns, gaps, signal, timing, len(followups), await run_in_threadpool(inspect_portfolio)
    )
    return {"actions": actions}


@app.get("/api/proof")
async def api_proof():
    return proof_summary()


@app.get("/api/cohort")
async def api_cohort():
    return analyze_cohort()


@app.get("/api/status")
async def api_status():
    return await run_in_threadpool(check_coral_connection)


def _build_dashboard_payload() -> dict:
    patterns = rejection_patterns.fetch()
    github_rows = github_correlation.fetch()
    gaps = skill_gaps.fetch()
    timing = timing_analysis.fetch()
    followups = followup_tracker.fetch()
    portfolio = inspect_portfolio()

    detected = {str(skill).casefold() for skill in portfolio.get("detected_skills", [])}
    for gap in gaps:
        gap["in_portfolio"] = str(gap.get("skill", "")).casefold() in detected

    totals = AnalystAgent._totals(patterns)
    github_signal = recommender.compute_github_signal(github_rows, github_rows)
    health_score = AnalystAgent._health_score(totals, gaps, github_signal, followups, portfolio)
    actions = recommender.generate_action_items(patterns, gaps, github_signal, timing, len(followups), portfolio)

    return {
        "stats": {
            "totalApplications": totals["total_applications"],
            "responseRate": totals["response_rate"],
            "interviewRate": totals["interview_rate"],
            "offerRate": totals["offer_rate"],
            "healthScore": health_score,
            "reposScanned": github_signal.get("total_repos", 0),
            "skillsMapped": len(gaps),
            "queriesRun": len(proof_summary().get("queries", [])),
            "crossSourceJoins": sum(1 for item in proof_summary().get("queries", []) if item.get("is_cross_source")),
        },
        "rejectionByRole": _map_rejection_bars(patterns),
        "githubHeatmap": _map_github_heatmap(github_rows),
        "skillGap": _map_skill_radar(gaps),
        "timing": _map_timing(timing),
        "insights": _map_insights(patterns, gaps, github_signal, actions, portfolio),
        "portfolio": portfolio,
        "usingSampleData": os.getenv("CORAL_AVAILABLE", "false").lower() != "true",
    }


def _map_rejection_bars(patterns: list[dict]) -> list[dict]:
    return [
        {
            "role": row.get("role_title", "Unknown role"),
            "applied": row.get("total", 0),
            "rejected": row.get("rejected", 0),
            "rate": round(row.get("rejection_rate", 0)),
        }
        for row in patterns[:8]
    ]


def _map_github_heatmap(rows: list[dict]) -> list[list[int]]:
    weeks = [0] * 26
    recent = rows[-26:] if len(rows) > 26 else rows
    start = 26 - len(recent)
    for index, row in enumerate(recent):
        commits = row.get("commits_count", 0) or 0
        weeks[start + index] = min(4, max(0, round(commits / 3)))

    grid = []
    for day in range(7):
        grid.append([max(0, min(4, value - (1 if day >= 5 and value else 0))) for value in weeks])
    return grid


def _map_skill_radar(gaps: list[dict]) -> dict:
    top = gaps[:8]
    max_required = max((gap.get("times_required", 0) or 0 for gap in top), default=1)
    return {
        "labels": [gap.get("skill", "Unknown") for gap in top],
        "demanded": [
            round(((gap.get("times_required", 0) or 0) / max_required) * 100)
            for gap in top
        ],
        "present": [
            min(
                100,
                (35 if gap.get("in_github") else 0)
                + (35 if gap.get("in_linkedin") else 0)
                + (30 if gap.get("in_portfolio") else 0),
            )
            for gap in top
        ],
    }


def _map_timing(rows: list[dict]) -> list[dict]:
    label_map = {
        "same_day": "Same day",
        "1-2_days": "1-2 days",
        "3-7_days": "3-7 days",
        "1-2_weeks": "1-2 weeks",
        "2_weeks_plus": "2+ weeks",
    }
    return [
        {
            "day": index,
            "label": label_map.get(row.get("timing_bucket"), str(row.get("timing_bucket", "Unknown"))),
            "ghostRate": row.get("ghost_rate", 0),
            "responseRate": row.get("response_rate", 0),
        }
        for index, row in enumerate(rows)
    ]


def _map_insights(
    patterns: list[dict],
    gaps: list[dict],
    github_signal: dict,
    actions: list[str],
    portfolio: dict,
) -> list[dict]:
    insights = []
    if patterns:
        worst = max(patterns, key=lambda row: row.get("rejection_rate", 0))
        insights.append(
            {
                "id": "rejection-pattern",
                "title": f"{worst.get('role_title', 'Role')} rejection pattern",
                "severity": "critical" if worst.get("rejection_rate", 0) >= 80 else "high",
                "claim": f"{worst.get('role_title', 'This role')} has a {worst.get('rejection_rate', 0):.0f}% rejection rate across {worst.get('total', 0)} applications.",
                "rootCause": "Current public evidence is not matching this role category strongly enough.",
                "action": actions[0] if actions else "Tighten role targeting before increasing application volume.",
                "impact": "Improves fit before adding more applications to a weak bucket.",
                "evidence": {"queryId": "rejection_patterns", "rows": worst.get("total", 0), "sources": ["notion.applications"]},
                "confidence": 0.82,
            }
        )

    if gaps:
        top_gap = max(gaps, key=lambda row: row.get("times_required", 0))
        missing_sources = [
            label
            for label, present in (
                ("GitHub", top_gap.get("in_github")),
                ("LinkedIn", top_gap.get("in_linkedin")),
                ("portfolio", top_gap.get("in_portfolio")),
            )
            if not present
        ]
        insights.append(
            {
                "id": "skill-gap",
                "title": f"{top_gap.get('skill', 'Skill')} evidence gap",
                "severity": "high" if top_gap.get("priority") in {"critical", "high"} else "medium",
                "claim": f"{top_gap.get('skill', 'This skill')} appears in {top_gap.get('times_required', 0)} target roles and is missing from {', '.join(missing_sources) or 'no major source'}.",
                "rootCause": "Recruiter-visible proof does not line up with the skill demand in applications.",
                "action": next((item for item in actions if top_gap.get("skill", "") in item), actions[0] if actions else "Add a targeted proof-of-work project."),
                "impact": "Raises confidence for roles that require the same skill.",
                "evidence": {"queryId": "skill_gap_detection", "rows": top_gap.get("times_required", 0), "sources": ["notion.applications", "github.activity", "linkedin.skills", "portfolio"]},
                "confidence": 0.86,
            }
        )

    ghost_gap = github_signal.get("ghost_rate_inactive_weeks", 0) - github_signal.get("ghost_rate_active_weeks", 0)
    if ghost_gap > 0:
        insights.append(
            {
                "id": "github-activity",
                "title": "GitHub activity signal",
                "severity": "high" if ghost_gap >= 30 else "medium",
                "claim": f"Ghost rate is {ghost_gap:.0f} points higher in inactive GitHub weeks.",
                "rootCause": "The public coding signal drops during parts of the application cycle.",
                "action": next((item for item in actions if "GitHub" in item), "Keep a steady commit cadence while applying."),
                "impact": "Keeps proof-of-work fresh while recruiters are checking profiles.",
                "evidence": {"queryId": "github_activity_correlation", "rows": 1, "sources": ["github.activity", "notion.applications"]},
                "confidence": 0.78,
            }
        )

    if portfolio.get("configured"):
        insights.append(
            {
                "id": "portfolio-scan",
                "title": "Portfolio scan",
                "severity": "medium" if portfolio.get("reachable") else "critical",
                "claim": f"Portfolio is {'reachable' if portfolio.get('reachable') else 'not reachable'} with {len(portfolio.get('detected_skills', []))} visible skills detected.",
                "rootCause": "The portfolio is the fastest public proof surface for recruiters.",
                "action": next((item for item in actions if "portfolio" in item.lower()), "Make top role skills and project links visible above the fold."),
                "impact": "Improves the first proof surface recruiters inspect.",
                "evidence": {"queryId": "portfolio_scan", "rows": 1, "sources": [portfolio.get("url") or "portfolio"]},
                "confidence": 0.72,
            }
        )

    return insights[:6]
