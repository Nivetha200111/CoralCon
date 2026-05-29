# CoralCon

**Other agents tell you what to do. CoralCon proves why you're failing, with evidence from the data you already have.**

CoralCon is a local-first career intelligence agent that turns rejection history into an evidence-backed improvement plan by joining GitHub proof-of-work, Notion application outcomes, and LinkedIn profile signals through Coral SQL.

## Why Coral Is at the Core

Coral SQL is the central data layer of CoralCon. Every piece of career intelligence flows through it.

Without Coral, CoralCon would need three separate API integrations (GitHub REST API, Notion API, LinkedIn GDPR CSV parsing), each with its own authentication, pagination, rate limiting, schema mapping, and error handling. Correlating data across sources would require custom join logic, date alignment, and manual data normalization.

With Coral, the agent asks **one SQL question across all three sources**:

```sql
SELECT
  n.role_title, n.status,
  g.commits_count, g.languages,
  l.skills, l.headline
FROM notion.applications n
JOIN github.activity g
  ON g.week = date_trunc('week', n.applied_date)
JOIN linkedin.skills l
WHERE n.applied_date > DATE_SUB(NOW(), INTERVAL 6 MONTH)
```

This cross-source JOIN is what makes CoralCon possible. It connects:

- **Notion** (application outcomes: company, role, status, required skills)
- **GitHub** (proof-of-work: commit cadence, repo languages, activity timeline)
- **LinkedIn** (profile signals: headline, skills, endorsements, positions)

CoralCon logs every Coral query as judge-verifiable proof. Run `python -m coralcon.cli proof` to see the full audit trail.

## What CoralCon Proves

| Claim | Evidence Source | Cross-Source JOIN |
|-------|---------------|-------------------|
| React roles have 94% rejection rate | `notion.applications` | No |
| Ghost rate is 70 pts higher in inactive GitHub weeks | `notion.applications` + `github.activity` | Yes |
| Top skill gap (React) appears in 38 rejected apps but 0 repos | `notion.applications` + `github.profile` + `linkedin.skills` | Yes |
| LinkedIn headline mismatches applied role categories | `linkedin.profile` + `notion.applications` | Yes |
| Applications sent 7+ days late have 72% ghost rate | `notion.applications` | No |

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
  GitHub    Notion    LinkedIn
  (repos,   (apps,    (GDPR export:
   events,   status,   skills,
   profile)  skills)   positions)
```

**Recon Agent** — queries all three sources through Coral SQL, collects raw data.
**Analyst Agent** — generates deterministic evidence-backed insights with rule-based analysis. Optionally enriches with Claude API narrative.
**Dashboard Agent** — writes structured results to Notion dashboard (when configured).
**Action Agent** — creates prioritized Notion tasks from insights.

All data retrieval goes through Coral SQL. The agent pipeline never calls GitHub, Notion, or LinkedIn APIs directly.

## Real Coral Mode

Connect your actual data sources for live analysis:

```bash
# Install Coral
brew install withcoral/tap/coral   # macOS
# Linux: see https://withcoral.com/docs

# Connect sources
coral source add --interactive github
coral source add --interactive notion
coral source add --file ./coral/sources/linkedin/source.yaml
coral source list

# Verify
coral sql --format json "SELECT * FROM github.repos LIMIT 5"
```

Set environment variables in `.env`:

```env
CORAL_AVAILABLE=true
ANTHROPIC_API_KEY=...     # Optional: enables Claude narrative insights
GITHUB_TOKEN=...          # Used by Coral GitHub source
NOTION_API_KEY=...        # Used by Coral Notion source
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

## All CLI Commands

```bash
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
| **Data source** | Seeded JSON in `data/sample/` | Coral SQL queries to GitHub, Notion, LinkedIn |
| **API keys needed** | None | `CORAL_AVAILABLE=true` + source credentials |
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
