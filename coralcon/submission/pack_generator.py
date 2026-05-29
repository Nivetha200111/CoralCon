"""Generate hackathon submission markdown files."""

import json
from pathlib import Path

from coralcon.privacy.report import build_privacy_report
from coralcon.proof.report import build_proof_report, proof_summary


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
    ps = proof_summary()
    return f"""# CoralCon — Pirates of the Coral-bean Submission

> Other agents tell you what to do. CoralCon proves why you're failing,
> with evidence from the data you already have.

## What It Is

CoralCon is a local-first career intelligence agent that turns rejection history
into an evidence-backed improvement plan by joining GitHub proof-of-work, a Google
Sheets tracker (auto-filled from Gmail rejections), and LinkedIn profile signals
through Coral SQL.

## Why Coral Is Essential

Coral SQL is the central data layer. Every piece of career intelligence flows through it.

Without Coral, CoralCon would need three separate API integrations (GitHub, Google
Sheets, LinkedIn GDPR), each with custom auth, pagination, schema mapping, and
correlation logic. With Coral, the agent asks one SQL question across all sources.

Cross-source JOINs are what make the insights possible. Joining `sheets.applications`
with `github.activity` proves whether commit cadence correlates with response rate.
Joining with `linkedin.skills` proves whether profile signals match role requirements.

## Coral Proof

- Total queries: {ps['total_queries']}
- Cross-source JOINs: {ps['cross_source_queries']}
- Sources: {', '.join(ps['sources'])}
- Mode: {ps['mode']}

## Demo Commands

```bash
pip install -r requirements.txt
python -m coralcon.cli judge-demo --sample   # Full pipeline with sample data
python -m coralcon.cli proof                  # Coral query audit trail
python -m coralcon.cli serve                  # Web dashboard at :8000
python -m coralcon.cli submit-pack            # Generate these files
```

## Architecture

CLI/Web -> Orchestrator -> Recon Agent -> Coral SQL -> GitHub + Sheets + LinkedIn
                       -> Analyst Agent (evidence-backed insights)
                       -> Dashboard Agent (Notion writes)
                       -> Action Agent (prioritized tasks)

## Privacy

Local-first. Raw data stays on your machine. Coral queries execute locally.
LLM analysis (optional) sends only summarized results.
"""


def _demo_script() -> str:
    return """# CoralCon — 3-Minute Demo Script

## 0:00-0:20 — Hook

"I got rejected again and again, but I had no feedback. So I built CoralCon
to turn rejection history into data."

Show the problem: hundreds of applications, no signal about what's failing.

## 0:20-0:50 — Show Coral

"Coral lets me query GitHub, my Google Sheets tracker, and LinkedIn as SQL sources."

Run `python -m coralcon.cli status` to show connected sources.
Run `python -m coralcon.cli proof` to show the query audit trail.

Point out: all data retrieval goes through Coral SQL. No direct API calls.

## 0:50-1:30 — Show Cross-Source Query

"This is the key query — application outcomes from my Google Sheet joined with GitHub
activity and LinkedIn skills."

Show the cross-source JOIN in the proof report or web dashboard Coral Proof tab.

```sql
SELECT n.role_title, n.status, g.commits_count, l.skills
FROM sheets.applications n
JOIN github.activity g ON g.week = date_trunc('week', n.applied_date)
JOIN linkedin.skills l
```

Point out: this JOIN is why Coral matters. Three sources, one query.

## 1:30-2:10 — Show Evidence-Backed Insights

"The app does not just say 'improve your profile.' It shows exactly what
evidence caused the recommendation."

Run `python -m coralcon.cli judge-demo --sample` and show:
- Each insight has a query ID, source tables, row count
- Supporting numbers come from actual query results
- Confidence scores based on evidence strength
- No hallucinated data

Show the web dashboard insights panel (expand one card to show evidence).

## 2:10-2:40 — Show Action Plan

"Every recommendation is backed by evidence and prioritized by impact."

Show the action items from the demo output.
Show the portfolio inspector on the dashboard.
Mention cohort mode for placement teams.

## 2:40-3:00 — Close

"Other agents tell you what to do. CoralCon proves why you're failing,
with evidence from the data you already have."

Show the evidence pack: `submission/coralcon_evidence_pack.md`
"""


def _architecture() -> str:
    return """# CoralCon Architecture

## Pipeline

```
User -> CLI / Web Dashboard
     -> CoralCon Orchestrator
        -> Recon Agent
           -> Coral SQL Layer
              -> GitHub (repos, events, profile)
              -> Google Sheets (applications, status, skills) [from Gmail]
              -> LinkedIn (GDPR export: skills, positions, headline)
        -> Analyst Agent
           -> Deterministic rule-based insights
           -> Optional Claude API narrative analysis
        -> Dashboard Agent
           -> Notion dashboard writes (optional)
        -> Action Agent
           -> Prioritized Notion tasks (optional)
```

## Data Flow

1. **Recon Agent** executes Coral SQL queries to collect raw data from all sources.
   Every query is logged with source tables, row count, execution time, and cache status.

2. **Analyst Agent** processes the raw data through deterministic rules to generate
   evidence-backed insights. Each insight includes the query ID, supporting numbers,
   and confidence score. Optionally, Claude API adds narrative analysis.

3. **Dashboard Agent** writes structured results to a Notion page (when configured).

4. **Action Agent** creates prioritized tasks in a Notion database (when configured).

## Key Design Decisions

- **Coral SQL is the only analysis path.** The agent never queries sources for
  analysis directly — every JOIN and aggregation is a logged, auditable Coral query.
  The only direct API calls are Gmail extraction and the Sheets write (Coral is
  read-only); those land rows in the sheet that Coral then reads.

- **Deterministic first, LLM second.** All core insights use rule-based analysis.
  Claude API narrative is optional and never generates numbers — those come from queries.

- **Evidence-backed insights.** Every claim includes the query ID, source tables,
  row count, and supporting numbers. No insight without evidence.

- **Sample fallback.** Deterministic sample mode uses seeded JSON data for reproducible
  judging. Same pipeline, same output format, no credentials needed.

- **Local-first privacy.** Raw data stays on the machine. LLM analysis sends only
  summarized results.
"""


def _sample_output() -> str:
    insights_path = Path("runs") / "latest" / "insights.json"
    if not insights_path.exists():
        return "# Sample Output\n\nRun `python -m coralcon.cli judge-demo --sample` to generate sample output."
    data = json.loads(insights_path.read_text(encoding="utf-8"))

    lines = [
        "# CoralCon Sample Output",
        "",
        f"- Applications analyzed: {data.get('total_applications', 0)}",
        f"- Response rate: {data.get('response_rate', 0)}%",
        f"- Health score: {data.get('overall_health_score', 0)}/100",
        f"- Offer rate: {data.get('offer_rate', 0)}%",
        "",
        "## Evidence-Backed Insights",
        "",
    ]
    for insight in data.get("evidence_insights", []):
        evidence = insight.get("evidence", {})
        lines.extend([
            f"### {insight['title']}",
            f"- **Claim:** {insight['claim']}",
            f"- **Severity:** {insight['severity']}",
            f"- **Confidence:** {insight.get('confidence', 0):.0%}",
            f"- **Query:** {evidence.get('query_id', 'unknown')}",
            f"- **Sources:** {', '.join(evidence.get('sources', []))}",
            f"- **Action:** {insight['recommended_action']}",
            "",
        ])
    return "\n".join(lines)
