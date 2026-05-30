"""FastAPI web dashboard for CoralCon."""

import os
from fastapi import FastAPI, File, Request, UploadFile
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
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
from coralcon.agents import recommender, router
from coralcon.cohort.analyzer import analyze_cohort
from coralcon.portfolio import inspect_portfolio
from coralcon.proof.report import proof_summary
from coralcon.resume import parse_resume_upload, public_resume_profile
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


@app.get("/ask", response_class=HTMLResponse)
async def ask_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"request": request}
    )


@app.get("/sources", response_class=HTMLResponse)
async def sources_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"request": request}
    )


# ---------------------------------------------------------------------------
# Google / Gmail import — "everything on the site"
#
# The dashboard lets the user connect Google and import rejections from Gmail
# without touching a terminal. OAuth uses the redirect (Authorization Code)
# flow so it works on a deployed host with no local browser. Imported rows are
# ingested into SQLite so the dashboard updates immediately, even where the
# Coral CLI isn't installed (e.g. the free-tier deployment).
# ---------------------------------------------------------------------------


@app.get("/api/google/status")
async def api_google_status():
    from coralcon.google import web_auth

    return await run_in_threadpool(web_auth.status)


@app.get("/api/google/connect")
async def api_google_connect(request: Request):
    from coralcon.google import web_auth

    try:
        auth_url, _state = await run_in_threadpool(
            web_auth.authorization_url, str(request.base_url)
        )
    except RuntimeError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    return RedirectResponse(auth_url)


@app.get("/oauth2callback")
async def oauth2_callback(request: Request):
    from coralcon.google import web_auth

    params = request.query_params
    if params.get("error"):
        return RedirectResponse(f"/sources?google=error&reason={params.get('error')}")
    code = params.get("code")
    if not code:
        return RedirectResponse("/sources?google=error&reason=missing_code")
    try:
        await run_in_threadpool(
            web_auth.exchange_code,
            code,
            str(request.base_url),
            str(request.url),
        )
    except Exception as exc:  # noqa: BLE001 - surface any OAuth error to the user
        return RedirectResponse(f"/sources?google=error&reason={type(exc).__name__}")
    return RedirectResponse("/sources?google=connected")


class GmailImportRequest(BaseModel):
    query: str | None = None
    max_results: int = 50
    use_ai: bool = True
    write_sheet: bool = True


@app.post("/api/gmail/import")
async def api_gmail_import(payload: GmailImportRequest):
    return await run_in_threadpool(_run_gmail_import, payload)


@app.post("/api/resume/upload")
async def api_resume_upload(file: UploadFile = File(...)):
    try:
        content = await file.read()
        profile = await run_in_threadpool(parse_resume_upload, file.filename or "resume", content)
    except ValueError as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": f"Resume upload failed: {exc}"}, status_code=500)
    return {"ok": True, "resume": public_resume_profile(profile)}


@app.get("/api/resume")
async def api_resume():
    return {"resume": public_resume_profile()}


def _run_gmail_import(payload: GmailImportRequest) -> dict:
    from coralcon.google import auth as google_auth
    from coralcon.gmail import extractor
    from coralcon import ingest

    if not google_auth.has_credentials():
        return {"ok": False, "error": "Google account not connected. Click Connect Google first."}

    try:
        rows = extractor.extract_rejections(
            query=payload.query or None,
            max_results=max(1, min(payload.max_results, 200)),
            use_ai=payload.use_ai and bool(os.getenv("ANTHROPIC_API_KEY")),
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"Gmail extraction failed: {exc}"}

    sheet_written = False
    sheet_error = None
    spreadsheet_id = os.getenv("SHEETS_SPREADSHEET_ID")
    if payload.write_sheet and spreadsheet_id and rows:
        try:
            from coralcon.sheets import client as sheets_client

            added_to_sheet = sheets_client.append_applications(rows)
            sheets_client.sync_to_csv(spreadsheet_id, sheets_client._csv_path())
            sheet_written = added_to_sheet >= 0
        except Exception as exc:  # noqa: BLE001
            sheet_error = str(exc)

    # Always reflect the import in the dashboard, Coral or not.
    summary = ingest.ingest_applications(rows)

    return {
        "ok": True,
        "extracted": len(rows),
        "added": summary.get("added", 0),
        "totalApplications": summary.get("total_applications", 0),
        "sheetWritten": sheet_written,
        "sheetError": sheet_error,
        "rowsPreview": rows[:8],
        "query": payload.query or None,
        "usedAi": payload.use_ai and bool(os.getenv("ANTHROPIC_API_KEY")),
        "usingSampleData": os.getenv("CORAL_AVAILABLE", "false").lower() != "true",
    }


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
    ps = proof_summary()
    if not ps["queries"]:
        from coralcon.orchestrator import CoralConOrchestrator
        await run_in_threadpool(
            lambda: CoralConOrchestrator().run_full_analysis(use_ai=False, dry_run=True)
        )
        ps = proof_summary()
    return ps


@app.get("/api/cohort")
async def api_cohort():
    return analyze_cohort()


@app.get("/api/status")
async def api_status():
    return await run_in_threadpool(check_coral_connection)


class AskRequest(BaseModel):
    question: str
    use_ai: bool = True


@app.post("/api/ask")
async def api_ask(payload: AskRequest):
    question = (payload.question or "").strip()
    if not question:
        return {"error": "Ask a question about your job search."}

    use_ai = payload.use_ai and bool(os.getenv("ANTHROPIC_API_KEY"))
    result = await run_in_threadpool(router.answer, question, use_ai)

    raw_proof = result.get("proof") or {}
    sources = raw_proof.get("sources_used", [])
    proof = {
        "query_id": raw_proof.get("query_id"),
        "sources": sources,
        "is_cross_source": raw_proof.get("is_cross_source", len(sources) > 1),
        "rows": raw_proof.get("rows_returned"),
    } if raw_proof else None

    # The proof table only needs a small, bounded preview of rows.
    rows = result.get("rows") or []
    return {
        "question": result.get("question"),
        "intentId": result.get("intent_id"),
        "queryName": result.get("query_name"),
        "summary": result.get("summary"),
        "classifiedBy": result.get("classified_by"),
        "headline": result.get("headline"),
        "narrative": result.get("narrative"),
        "narrativeSource": result.get("narrative_source"),
        "rowCount": result.get("row_count"),
        "rowsPreview": rows[:8],
        "proof": proof,
        "usingSampleData": os.getenv("CORAL_AVAILABLE", "false").lower() != "true",
    }


def _build_dashboard_payload() -> dict:
    connection = check_coral_connection()
    patterns = rejection_patterns.fetch()
    github_rows = github_correlation.fetch()
    gaps = skill_gaps.fetch()
    timing = timing_analysis.fetch()
    followups = followup_tracker.fetch()
    portfolio = inspect_portfolio()
    resume = public_resume_profile()

    detected = {str(skill).casefold() for skill in portfolio.get("detected_skills", [])}
    resume_skills = {str(skill).casefold() for skill in (resume or {}).get("skills", [])}
    for gap in gaps:
        skill = str(gap.get("skill", "")).casefold()
        gap["in_portfolio"] = skill in detected
        gap["in_resume"] = skill in resume_skills

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
        "resume": resume,
        "usingSampleData": not (
            connection.get("coral_installed")
            and connection.get("sheets_connected")
            and connection.get("github_connected")
            and connection.get("linkedin_connected")
        ),
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
                + (20 if gap.get("in_portfolio") else 0)
                + (10 if gap.get("in_resume") else 0),
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
        role = worst.get("role_title", "Role")
        rate = worst.get("rejection_rate", 0)
        total = worst.get("total", 0)
        insights.append(
            {
                "id": "rejection-pattern",
                "title": f"Stop applying to {role} roles" if rate >= 70 else f"{role} roles are a weak spot",
                "severity": "critical" if rate >= 80 else "high",
                "claim": f"{role} roles have a {rate:.0f}% rejection rate across {total} applications. That's your worst category.",
                "rootCause": f"Your public profile doesn't match what {role} roles are looking for. Recruiters see the mismatch immediately.",
                "action": actions[0] if actions else "Fix your profile for this role type or stop applying until you do.",
                "impact": f"Either fix the gap or redirect those {total} applications to roles where your profile is stronger.",
                "evidence": {"queryId": "rejection_patterns", "rows": total, "sources": ["sheets.applications"]},
                "confidence": 0.82,
            }
        )

    if gaps:
        top_gap = max(gaps, key=lambda row: row.get("times_required", 0))
        skill = top_gap.get("skill", "Skill")
        count = top_gap.get("times_required", 0)
        missing_sources = [
            label
            for label, present in (
                ("GitHub", top_gap.get("in_github")),
                ("LinkedIn", top_gap.get("in_linkedin")),
                ("portfolio", top_gap.get("in_portfolio")),
                ("resume", top_gap.get("in_resume")),
            )
            if not present
        ]
        insights.append(
            {
                "id": "skill-gap",
                "title": f"Jobs want {skill}, your profile doesn't show it",
                "severity": "high" if top_gap.get("priority") in {"critical", "high"} else "medium",
                "claim": f"{skill} appears in {count} target roles but is missing from {', '.join(missing_sources) or 'your profile'}.",
                "rootCause": f"Recruiters look for {skill} on your GitHub and LinkedIn. When they don't find it, your application gets filtered out.",
                "action": next((item for item in actions if skill in item), actions[0] if actions else f"Build a project using {skill} and add it to your profile."),
                "impact": f"Fixing this one gap affects {count} roles you're targeting.",
                "evidence": {"queryId": "skill_gap_detection", "rows": count, "sources": ["sheets.applications", "github.activity", "linkedin.skills"]},
                "confidence": 0.86,
            }
        )

    ghost_gap = github_signal.get("ghost_rate_inactive_weeks", 0) - github_signal.get("ghost_rate_active_weeks", 0)
    if ghost_gap > 0:
        insights.append(
            {
                "id": "github-activity",
                "title": "Your GitHub goes quiet when you job search",
                "severity": "high" if ghost_gap >= 30 else "medium",
                "claim": f"Ghost rate is {ghost_gap:.0f} points higher during weeks you don't commit.",
                "rootCause": "Recruiters check your GitHub. When the contribution graph is empty, it signals disengagement.",
                "action": next((item for item in actions if "GitHub" in item), "Commit something every day during your search, even small things."),
                "impact": "Active GitHub weeks show significantly higher response rates.",
                "evidence": {"queryId": "github_activity_correlation", "rows": 1, "sources": ["github.activity", "sheets.applications"]},
                "confidence": 0.78,
            }
        )

    if portfolio.get("configured"):
        reachable = portfolio.get("reachable")
        skills_found = len(portfolio.get("detected_skills", []))
        insights.append(
            {
                "id": "portfolio-scan",
                "title": "Portfolio is reachable" if reachable else "Your portfolio isn't loading",
                "severity": "medium" if reachable else "critical",
                "claim": f"Portfolio {'shows ' + str(skills_found) + ' skills to recruiters' if reachable else 'is not reachable. Recruiters cannot see your work'}.",
                "rootCause": "Your portfolio is the first thing many recruiters check. It needs to load and show proof immediately.",
                "action": next((item for item in actions if "portfolio" in item.lower()), "Make your top skills and project links visible above the fold."),
                "impact": "A working portfolio with clear proof is the fastest way to stand out.",
                "evidence": {"queryId": "portfolio_scan", "rows": 1, "sources": [portfolio.get("url") or "portfolio"]},
                "confidence": 0.72,
            }
        )

    resume = public_resume_profile()
    if resume:
        skills = resume.get("skills", [])
        missing_sections = [
            label
            for key, label in (
                ("projects", "projects"),
                ("experience", "experience"),
                ("links", "proof links"),
            )
            if not resume.get("sections", {}).get(key)
        ]
        insights.append(
            {
                "id": "resume-scan",
                "title": "Resume profile imported",
                "severity": "medium" if missing_sections else "low",
                "claim": f"Your resume shows {len(skills)} recruiter-visible skills.",
                "rootCause": (
                    f"Missing resume sections: {', '.join(missing_sections)}."
                    if missing_sections
                    else "Resume has the core sections CoralCon expects."
                ),
                "action": (
                    f"Add {missing_sections[0]} to the resume and include measurable project evidence."
                    if missing_sections
                    else "Keep the imported resume in sync as you update your profile."
                ),
                "impact": "Resume skills now count toward profile-fit checks on the dashboard.",
                "evidence": {"queryId": "resume_upload", "rows": 1, "sources": [resume.get("filename") or "resume"]},
                "confidence": 0.7,
            }
        )

    return insights[:6]
