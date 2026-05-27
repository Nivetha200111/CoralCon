"""FastAPI web dashboard for CoralCon."""

import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from dotenv import load_dotenv

from coralcon.queries import (
    rejection_patterns,
    github_correlation,
    skill_gaps,
    timing_analysis,
    followup_tracker,
)
from coralcon.agents import recommender
from coralcon.cohort.analyzer import analyze_cohort
from coralcon.privacy.report import build_privacy_report
from coralcon.proof.report import proof_summary

load_dotenv()

app = FastAPI(title="CoralCon Dashboard", docs_url=None, redoc_url=None)

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_alias(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/proof", response_class=HTMLResponse)
async def proof_page(request: Request):
    return templates.TemplateResponse(request=request, name="proof.html", context={"proof": proof_summary()})


@app.get("/cohort", response_class=HTMLResponse)
async def cohort_page(request: Request):
    return templates.TemplateResponse(request=request, name="cohort.html", context={"cohort": analyze_cohort()})


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    return templates.TemplateResponse(request=request, name="privacy.html", context={"report": build_privacy_report()})


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
    return skill_gaps.fetch()


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
        patterns, gaps, signal, timing, len(followups)
    )
    return {"actions": actions}


@app.get("/api/proof")
async def api_proof():
    return proof_summary()


@app.get("/api/cohort")
async def api_cohort():
    return analyze_cohort()
