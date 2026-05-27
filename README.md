# CoralCon

CoralCon is a local-first career intelligence agent that turns rejection history into an evidence-backed improvement plan by joining GitHub proof-of-work, Notion application outcomes, and LinkedIn profile signals through Coral SQL.

> Without Coral, CoralCon would need separate GitHub, Notion, and LinkedIn integrations plus custom pagination, auth, schema mapping, and correlation logic. With Coral, the agent asks one SQL question across all sources.

## Demo

GIF placeholder: `submission/screenshots/demo.gif`

```bash
coralcon judge-demo --sample
coralcon proof
coralcon serve
```

## Why This Matters

Job seekers apply to hundreds of roles without knowing why they are rejected. CoralCon turns the search into an evidence loop: application outcomes, public portfolio activity, and LinkedIn signals become one queryable system.

## Architecture

```text
CLI/Web
  -> Recon Agent
  -> Coral SQL
  -> GitHub + Notion + LinkedIn GDPR export
  -> Analyst Agent
  -> Dashboard Agent + Action Agent
```

## Features

- Four-agent pipeline: Recon, Analyst, Dashboard, Action.
- Deterministic sample mode for demos without API keys.
- Coral proof logging for every SQL query.
- Evidence-backed insights saved to `runs/latest`.
- Optional Notion dashboard and action task writes.
- Cache benchmark and privacy report.
- Submission pack generator for hackathon materials.
- Cohort mode for placement teams, bootcamps, and colleges.

## Coral SQL Examples

```sql
SELECT n.company, n.status, g.commits_count, g.languages
FROM notion.applications n
JOIN github.activity g
  ON g.week = date_trunc('week', n.applied_date)
```

```sql
SELECT n.required_skills, g.languages, l.skills
FROM notion.applications n
JOIN github.profile g
JOIN linkedin.skills l
WHERE n.status = 'rejected'
```

## Commands

```bash
coralcon analyze --no-ai --dry-run
coralcon recon
coralcon insights --no-ai
coralcon dashboard --sample
coralcon actions --no-ai --dry-run
coralcon judge-demo --sample
coralcon proof
coralcon benchmark-cache --sample
coralcon privacy-report
coralcon submit-pack
coralcon cohort analyze
coralcon serve
```

## Local Setup

```bash
python -m pip install -r requirements.txt
python -m coralcon.cli judge-demo --sample
```

On this Windows workspace, the Codex bundled Python path is:

```powershell
& 'C:\Users\NivethaSivakumar\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m coralcon.cli judge-demo --sample
```

## Sample Mode

Sample mode uses seeded local JSON data under `data/sample`. It requires no Coral, Notion, LinkedIn, or LLM credentials.

## Real Mode

Set these values in `.env`:

```env
CORAL_AVAILABLE=true
ANTHROPIC_API_KEY=...
NOTION_TOKEN=...
NOTION_DASHBOARD_PAGE_ID=...
NOTION_ACTIONS_DATABASE_ID=...
```

Reads should go through Coral SQL. Notion is used only for optional dashboard/task writes.

## Custom LinkedIn Source

LinkedIn API access is restricted, so CoralCon uses a user-provided LinkedIn GDPR export or compatible CSV/JSON sample as a local Coral source. The source spec lives in `coral/sources/linkedin`.

## Privacy Note

CoralCon is designed to keep raw source data local. If LLM analysis is enabled, summarized query results may be sent to the configured LLM provider.

## Submission Checklist

- Run `coralcon judge-demo --sample`.
- Run `coralcon submit-pack`.
- Capture dashboard screenshots from `coralcon serve`.
- Submit generated files from `submission/`.
