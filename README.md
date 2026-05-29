# CoralCon

**Other agents tell you what to do. CoralCon proves why you're failing, with evidence from the data you already have.**

CoralCon is a local-first career intelligence agent that turns rejection history into an evidence-backed improvement plan by joining GitHub proof-of-work, your Google Sheets application tracker (auto-populated from Gmail rejections), and LinkedIn profile signals through Coral SQL.

## From Gmail to a Coral-Queryable Tracker

You don't keep a tidy spreadsheet of every rejection — your inbox does. CoralCon
reads rejection emails straight from Gmail, classifies them into structured rows
(company, role, status, date), and writes them to a Google Sheet you can edit by
hand. Coral then queries that sheet as `sheets.applications` and JOINs it against
GitHub and LinkedIn.

```
Gmail API ──► classify rejections ──► Google Sheet (you manage here)
                                            │
                  python -m coralcon.cli sheets-sync (Sheets API)
                                            ▼
                                  data/applications.csv
                                            │
                                   Coral `sheets` file source
                                            ▼
                              SELECT ... FROM sheets.applications
                                  JOIN github.* JOIN linkedin.*
```

Gmail extraction and Sheet writes use the Google APIs directly (Coral is a
read-only query layer and can't write). Everything *analytical* — the queries,
the cross-source JOINs, the proof log — runs through Coral.

## Why Coral Is at the Core

Coral SQL is the central data layer of CoralCon. Every piece of career intelligence flows through it.

Without Coral, CoralCon would need three separate API integrations (GitHub REST API, Google Sheets API, LinkedIn GDPR CSV parsing), each with its own authentication, pagination, rate limiting, schema mapping, and error handling. Correlating data across sources would require custom join logic, date alignment, and manual data normalization.

With Coral, the agent asks **one SQL question across all three sources**:

```sql
SELECT
  n.role_title, n.status,
  g.commits_count, g.languages,
  l.skills, l.headline
FROM sheets.applications n
JOIN github.activity g
  ON g.week = date_trunc('week', n.applied_date)
JOIN linkedin.skills l
WHERE n.applied_date > DATE_SUB(NOW(), INTERVAL 6 MONTH)
```

This cross-source JOIN is what makes CoralCon possible. It connects:

- **Google Sheets** (application outcomes: company, role, status, required skills — populated from Gmail)
- **GitHub** (proof-of-work: commit cadence, repo languages, activity timeline)
- **LinkedIn** (profile signals: headline, skills, endorsements, positions)

CoralCon logs every Coral query as judge-verifiable proof. Run `python -m coralcon.cli proof` to see the full audit trail.

## Ask in Plain English (the LLM never writes SQL)

Ask CoralCon a question in natural language, from the CLI or the web dashboard:

```bash
python -m coralcon.cli ask "which roles reject me the most?"
python -m coralcon.cli ask "when should I apply to get a response?"
```

Most "text-to-SQL" agents let the model generate SQL — which means hallucinated
columns, unbounded queries, and made-up numbers. CoralCon does the opposite:

1. A deterministic **router** classifies the question to one of a fixed set of
   schema-safe Coral queries. The LLM is used *only* as an intent classifier
   (and falls back to keyword matching with no API key at all).
2. The chosen Coral query runs unchanged — bounded, safe, and identical every time.
3. The LLM then *narrates the real rows*. It never invents a number, and every
   answer ships with proof: the exact query that ran, the source tables joined,
   and the row count.

This keeps the agent fast, safe, and verifiable — the LLM is an interface layer,
never the source of truth. The same `ask` endpoint backs the **Ask** tab in the
web dashboard, so it works from any browser, not just the terminal.

## What CoralCon Proves

| Claim | Evidence Source | Cross-Source JOIN |
|-------|---------------|-------------------|
| React roles have 94% rejection rate | `sheets.applications` | No |
| Ghost rate is 70 pts higher in inactive GitHub weeks | `sheets.applications` + `github.activity` | Yes |
| Top skill gap (React) appears in 38 rejected apps but 0 repos | `sheets.applications` + `github.profile` + `linkedin.skills` | Yes |
| LinkedIn headline mismatches applied role categories | `linkedin.profile` + `sheets.applications` | Yes |
| Applications sent 7+ days late have 72% ghost rate | `sheets.applications` | No |

Every insight includes the query ID, source tables, row count, and supporting numbers. No hallucinated data.

## Quick Start: Judge Demo (Sample Mode)

Deterministic sample mode for reproducible judging. No API keys, no Coral installation, no network access required.

```bash
pip install -r requirements.txt
python -m coralcon.cli judge-demo --sample
```

This runs the full four-agent pipeline against seeded sample data and produces:

- `runs/latest/proof.json` — every Coral query logged with sources, rows, and timing
- `runs/latest/insights.json` — evidence-backed insights with supporting numbers
- `runs/latest/report.md` — human-readable analysis report
- `submission/coralcon_evidence_pack.md` — complete judge evidence pack

### View the Proof Report

```bash
python -m coralcon.cli proof
```

### View the Web Dashboard

```bash
python -m coralcon.cli serve
```

Open `http://127.0.0.1:8000`. The dashboard includes a dedicated **Coral Proof** tab showing every query, every source, every JOIN, with execution times and row counts.

### Local SQLite Database

CoralCon now uses a real local SQLite database in sample/local mode. The default
path is `data/coralcon.sqlite`, and it is seeded from the bundled sample data the
first time a query runs.

```bash
python -m coralcon.cli db init --reset
python -m coralcon.cli db status
python -m coralcon.cli db query "SELECT company, role_title, status FROM applications LIMIT 5"
```

Set `CORALCON_DATA_BACKEND=json` only if you want to bypass SQLite and read the
raw JSON fixtures directly.

### Generate the Submission Pack

```bash
python -m coralcon.cli submit-pack
```

## Architecture

```text
               CLI / Web Dashboard
                      |
              CoralCon Orchestrator
                      |
        +-------------+-------------+
        |             |             |
   Recon Agent   Analyst Agent  Action Agent
        |             |             |
        +------+------+      Dashboard Agent
               |
         Coral SQL Layer
               |
     +---------+---------+
     |         |         |
  GitHub    Sheets    LinkedIn
  (repos,   (apps,    (GDPR export:
   events,   status,   skills,
   profile)  dates)    positions)
               ^
               |  Gmail API extract + Sheets API write (outside Coral)
            Gmail rejections
```

**Recon Agent** — queries all three sources through Coral SQL, collects raw data.
**Analyst Agent** — generates deterministic evidence-backed insights with rule-based analysis. Optionally enriches with Claude API narrative.
**Dashboard Agent** — writes structured results to Notion dashboard (when configured).
**Action Agent** — creates prioritized Notion tasks from insights.

All *analysis* goes through Coral SQL — the agent pipeline never queries sources
directly. The only direct API calls are the Gmail extractor (reading rejection
emails) and the Sheets writer (saving them to your tracker), because Coral is a
read-only query layer. Once rows land in the Sheet, Coral takes over.

## Real Coral Mode

Connect your actual data sources for live analysis:

```bash
# Install Coral
brew install withcoral/tap/coral   # macOS
# Linux: see https://withcoral.com/docs

# Connect sources
coral source add --interactive github
coral source add --interactive --file ./coral/sources/sheets/source.yaml
coral source add --file ./coral/sources/linkedin/source.yaml
coral source list

# Verify
coral sql --format json "SELECT * FROM github.repos LIMIT 5"
coral sql --format json "SELECT role_title, status FROM sheets.applications LIMIT 5"
```

### Populate your tracker from Gmail

```bash
# One-time: create a Desktop OAuth client in Google Cloud Console with the
# Gmail API + Google Sheets API enabled, then point CoralCon at it:
#   GOOGLE_CLIENT_SECRETS=/path/to/client_secret.json
#   SHEETS_SPREADSHEET_ID=<id from your Google Sheet URL>

python -m coralcon.cli gmail-extract            # Gmail -> classify -> write to Sheet + CSV
python -m coralcon.cli gmail-extract --dry-run  # preview without writing
python -m coralcon.cli sheets-sync              # pull Sheet -> data/applications.csv for Coral
```

### …or do it entirely from the dashboard (no terminal)

The web app has an **Import** tab that runs the same Gmail extraction in the
browser — connect Google with one click, then pull rejections into your tracker.
Imported rows update your report immediately, even where the Coral CLI isn't
installed (e.g. a free-tier deploy).

For the web flow, create a **Web application** OAuth client (not Desktop) in
Google Cloud Console with the Gmail + Sheets APIs enabled, and add your site's
callback as an **Authorized redirect URI**:

```
http://localhost:8000/oauth2callback          # local
https://<your-app>.onrender.com/oauth2callback # deployed
```

While the OAuth app is in "testing", add your Google account as a test user.
Then point CoralCon at the same client (`GOOGLE_CLIENT_SECRETS` or
`GOOGLE_OAUTH_CLIENT_ID` + `GOOGLE_OAUTH_CLIENT_SECRET`). If the callback host
can't be auto-derived, set it explicitly:

```env
OAUTH_REDIRECT_URI=https://<your-app>.onrender.com/oauth2callback
```

Set environment variables in `.env`:

```env
CORAL_AVAILABLE=true
ANTHROPIC_API_KEY=...               # Optional: classifies emails + narrates insights
GITHUB_TOKEN=...                    # Used by Coral GitHub source
GOOGLE_CLIENT_SECRETS=...           # Path to your Google OAuth client_secret.json
SHEETS_SPREADSHEET_ID=...           # Your Google Sheet id
SHEETS_CSV_PATH=/abs/path/to/data   # Dir holding applications.csv (the Coral file source)
```

Run with real sources:

```bash
CORAL_AVAILABLE=true python -m coralcon.cli recon
CORAL_AVAILABLE=true python -m coralcon.cli judge-demo --real
CORAL_AVAILABLE=true python -m coralcon.cli proof
```

## Custom LinkedIn Source Spec

LinkedIn API access is restricted. CoralCon uses a Coral file source spec that reads LinkedIn GDPR data exports (CSV) as SQL tables:

- `linkedin.profile` — name, headline, summary, location
- `linkedin.skills` — skill name, endorsement count
- `linkedin.positions` — company, title, start/end dates
- `linkedin.connections` — name, company, position, connected date

The source spec lives in `coral/sources/linkedin/source.yaml`. To get your data: LinkedIn Settings > Data Privacy > Get a copy of your data.

**Contributed upstream:** the LinkedIn source spec has been submitted as a pull
request to the official Coral source library so any Coral user can query their
LinkedIn export as SQL — [withcoral/coral#994](https://github.com/withcoral/coral/pull/994).

## All CLI Commands

```bash
# Ask in plain English (routes to a safe Coral query, narrates real rows)
python -m coralcon.cli ask "which roles reject me the most?"
python -m coralcon.cli ask "what skills am I missing?" --no-ai

# Gmail -> Google Sheets tracker (populates sheets.applications for Coral)
python -m coralcon.cli gmail-extract                 # extract rejections, write to Sheet
python -m coralcon.cli gmail-extract --dry-run       # preview classification only
python -m coralcon.cli sheets-sync                   # sync Sheet -> applications.csv

# Core analysis
python -m coralcon.cli db init --reset               # Create local SQLite DB
python -m coralcon.cli db status                     # Show DB table counts
python -m coralcon.cli analyze --no-ai --dry-run    # Full pipeline
python -m coralcon.cli recon                         # Data collection only
python -m coralcon.cli insights --no-ai              # Analysis without Notion writes
python -m coralcon.cli rejections                    # Rejection patterns
python -m coralcon.cli gaps                          # Skill gap analysis
python -m coralcon.cli timing                        # Application timing patterns
python -m coralcon.cli followup                      # Follow-up priority queue
python -m coralcon.cli github-check                  # GitHub activity signal

# Judge demo and proof
python -m coralcon.cli judge-demo --sample           # Deterministic demo run
python -m coralcon.cli proof                         # Coral query audit trail
python -m coralcon.cli submit-pack                   # Generate submission files

# Web dashboard
python -m coralcon.cli serve                         # Launch FastAPI dashboard

# Portfolio inspection
python -m coralcon.cli portfolio-check https://your-site.com

# Cohort mode
python -m coralcon.cli cohort analyze                # Multi-candidate analysis

# Utilities
python -m coralcon.cli benchmark-cache --sample      # Cache speedup measurement
python -m coralcon.cli privacy-report                # Data handling report
python -m coralcon.cli status                        # Source connection check
```

## Cohort Mode / Placement Team Use Case

The same CoralCon pipeline that analyzes one job seeker can analyze an entire cohort. This makes CoralCon useful for:

- **Colleges** running placement drives across 50-200 students
- **Bootcamps** tracking graduate job search outcomes
- **Career coaches** managing multiple clients
- **Placement teams** identifying systematic skill gaps across candidates

Cohort mode aggregates individual CoralCon analyses to surface:
- Common skill gaps across the group (e.g., 85% missing TypeScript)
- Candidates with the weakest proof-of-work signals
- Group-level GitHub activity trends
- Prioritized intervention recommendations

```bash
python -m coralcon.cli cohort analyze
```

## Sample Mode vs Real Mode

| | Sample Mode | Real Mode |
|---|---|---|
| **Purpose** | Deterministic sample mode for reproducible judging | Live analysis with real data |
| **Data source** | Seeded JSON in `data/sample/` | Coral SQL over GitHub, Google Sheets (from Gmail), LinkedIn |
| **API keys needed** | None | `CORAL_AVAILABLE=true` + Google OAuth + source credentials |
| **Coral required** | No | Yes |
| **Output** | Identical on every run | Reflects current data |

## Privacy

CoralCon is local-first by design. Raw source data stays on your machine. Coral queries execute locally. If LLM analysis is enabled (`ANTHROPIC_API_KEY`), only summarized query results are sent to the Claude API — never raw application data, company names, or personal details.

## Deploy

```bash
# Docker
docker build -t coralcon .
docker run --env-file .env -p 8000:8000 coralcon

# Render (render.yaml included)
git push origin main
```

## License

Built for the [Pirates of the Coral-bean](https://wemakedevs.org) hackathon by WeMakeDevs.
