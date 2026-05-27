import os

from coralcon.agents.analyst import AnalystAgent
from coralcon.agents.recon import ReconAgent
from coralcon.demo.judge_demo import run_judge_demo
from coralcon.proof.query_logger import get_query_log, reset_query_log
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
