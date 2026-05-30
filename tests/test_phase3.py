import os

from coralcon.agents.analyst import AnalystAgent
from coralcon.agents.recon import ReconAgent
from coralcon.database import database_status, initialize_database
from coralcon.demo.judge_demo import run_judge_demo
from coralcon.portfolio.inspector import _detect_skills
from coralcon.proof.query_logger import get_query_log, reset_query_log
from coralcon.queries import rejection_patterns
from coralcon.resume import parse_resume_upload, public_resume_profile
from coralcon.submission.pack_generator import generate_submission_pack


def test_query_logger_records_recon_queries():
    os.environ["CORAL_AVAILABLE"] = "false"
    reset_query_log()
    ReconAgent().fetch_all()
    entries = get_query_log()
    assert entries
    assert any(entry["is_cross_source"] for entry in entries)


def test_analyst_generates_evidence_insights():
    os.environ["CORAL_AVAILABLE"] = "false"
    reset_query_log()
    raw = ReconAgent().fetch_all()
    insights = AnalystAgent().analyze(raw, use_ai=False)
    assert insights["evidence_insights"]
    assert insights["evidence_insights"][0]["evidence"]["query_id"].startswith("q_")


def test_judge_demo_sample_generates_artifacts():
    result = run_judge_demo(sample=True)
    assert result["result"]["insights"]["total_applications"] == 147
    assert result["evidence_path"].endswith("coralcon_evidence_pack.md")


def test_submit_pack_generation():
    paths = generate_submission_pack()
    names = {path.name for path in paths}
    assert "README_SUBMISSION.md" in names
    assert "CORAL_PROOF.md" in names


def test_portfolio_skill_detection_is_deterministic():
    text = "Production React and TypeScript portfolio using FastAPI, PostgreSQL, Docker, and AWS."
    assert _detect_skills(text.lower()) == [
        "aws",
        "docker",
        "fastapi",
        "postgresql",
        "react",
        "typescript",
    ]


def test_sqlite_database_seeds_and_serves_queries(tmp_path, monkeypatch):
    monkeypatch.setenv("CORAL_AVAILABLE", "false")
    monkeypatch.setenv("CORALCON_DATA_BACKEND", "sqlite")
    monkeypatch.setenv("CORALCON_DB_PATH", str(tmp_path / "coralcon.sqlite"))

    db_path = initialize_database(reset=True)
    status = database_status(db_path)

    assert status["exists"]
    assert status["tables"]["applications"] == 8
    assert status["tables"]["rejection_patterns"] == 6
    assert sum(row["total"] for row in rejection_patterns.fetch()) == 147


def test_resume_upload_parser_extracts_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("CORALCON_RUNS_DIR", str(tmp_path))
    content = b"""
Nivetha Example
nivetha@example.com
https://github.com/nivetha

Skills
Python, React, TypeScript, FastAPI, Docker, AWS

Projects
Built a production FastAPI and React dashboard.
"""
    profile = parse_resume_upload("resume.txt", content)
    public = public_resume_profile(profile)

    assert profile["email"] == "nivetha@example.com"
    assert "python" in profile["skills"]
    assert "react" in profile["skills"]
    assert public["filename"] == "resume.txt"
    assert public["sections"]["projects"]
    assert "text" not in public
