# CoralCon — Pirates of the Coral-bean Submission

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

- Total queries: 9
- Cross-source JOINs: 2
- Sources: github.activity, github.profile, linkedin.profile, linkedin.skills, sheets.applications
- Mode: sample

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
