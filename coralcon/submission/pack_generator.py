"""Generate hackathon submission markdown files."""

import json
from pathlib import Path

from coralcon.privacy.report import build_privacy_report
from coralcon.proof.report import build_proof_report


SUBMISSION_DIR = Path("submission")


def generate_submission_pack() -> list[Path]:
    SUBMISSION_DIR.mkdir(exist_ok=True)
    (SUBMISSION_DIR / "screenshots").mkdir(exist_ok=True)

    files = {
        "README_SUBMISSION.md": _readme_submission(),
        "DEMO_SCRIPT_3_MIN.md": _demo_script(),
        "ARCHITECTURE.md": _architecture(),
        "CORAL_PROOF.md": build_proof_report(),
        "PRIVACY_REPORT.md": build_privacy_report(),
        "SAMPLE_OUTPUT.md": _sample_output(),
    }
    paths = []
    for filename, content in files.items():
        path = SUBMISSION_DIR / filename
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


def _readme_submission() -> str:
    return """# CoralCon

CoralCon is a local-first career intelligence agent that turns rejection history into an evidence-backed improvement plan by joining GitHub proof-of-work, Notion application outcomes, and LinkedIn profile signals through Coral SQL.

## Problem
Job seekers apply to hundreds of roles with almost no feedback loop.

## Solution
CoralCon connects application outcomes, portfolio evidence, and profile signals, then generates grounded insights and action tasks.

## Why Coral Is Essential
Without Coral, CoralCon would need separate GitHub, Notion, and LinkedIn integrations plus custom pagination, auth, schema mapping, and correlation logic. With Coral, the agent asks one SQL question across all sources.

## Demo Commands
- `coralcon judge-demo --sample`
- `coralcon proof`
- `coralcon privacy-report`
- `coralcon benchmark-cache --sample`
- `coralcon submit-pack`
- `coralcon serve`
"""


def _demo_script() -> str:
    return """# 3-Minute Demo Script

## 0:00-0:30 Hook
I applied to hundreds of jobs and got almost no feedback. CoralCon turns rejection history into a dataset.

## 0:30-1:00 Coral Source Proof
Show `coralcon proof` and the logged GitHub, Notion, and LinkedIn SQL sources.

## 1:00-1:30 Cross-Source SQL Demo
Run `coralcon judge-demo --sample` and point out the cross-source join evidence.

## 1:30-2:00 Insight and Action Generation
Show evidence-backed insights and generated Notion-ready action tasks.

## 2:00-2:30 Dashboard
Run `coralcon serve` and show the local dashboard.

## 2:30-3:00 Close
CoralCon turns job rejection into an evidence-backed improvement plan.
"""


def _architecture() -> str:
    return """# Architecture

User -> CoralCon CLI/Web -> Recon Agent -> Coral SQL -> GitHub + Notion + LinkedIn

Recon passes raw query outputs to the Analyst Agent. The Analyst Agent creates evidence-backed insights. Dashboard and Action agents write optional Notion outputs. Sample mode uses seeded local data and deterministic rules.
"""


def _sample_output() -> str:
    insights_path = Path("runs") / "latest" / "insights.json"
    if not insights_path.exists():
        return "# Sample Output\n\nRun `coralcon judge-demo --sample` to generate sample output."
    data = json.loads(insights_path.read_text(encoding="utf-8"))
    lines = [
        "# Sample Output",
        "",
        f"Applications: {data.get('total_applications', 0)}",
        f"Response rate: {data.get('response_rate', 0)}%",
        f"Health score: {data.get('overall_health_score', 0)}/100",
        "",
        "## Insights",
    ]
    for insight in data.get("evidence_insights", []):
        lines.append(f"- {insight['claim']} Action: {insight['recommended_action']}")
    return "\n".join(lines)
