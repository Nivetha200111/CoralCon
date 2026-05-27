# CLAUDE.md — CoralCon Project Context

## What Is This
CoralCon is an AI-powered career agent that analyzes job search data across GitHub, Notion, and LinkedIn using Coral's SQL interface to decode rejection patterns and give actionable career advice.

## Hackathon Context
- **Event**: Pirates of the Coral-bean (WeMakeDevs)
- **Deadline**: May 31, 2026
- **Prize**: MacBook Neo (Track 1) or iPad (Track 2)
- **Key requirement**: Must use Coral for cross-source SQL queries
- **Must be a NEW project** — no existing codebases

## Tech Stack
- Python 3.11+
- Coral CLI (`brew install withcoral/tap/coral` or Linux equivalent)
- Click or Typer for CLI
- FastAPI for optional web dashboard
- Claude API (anthropic SDK) for LLM insight generation
- Chart.js or Plotly for visualizations
- Coral source specs: GitHub (built-in), Notion (built-in), LinkedIn (custom file source)

## Project Structure
```
coralcon/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── setup.py
├── coral/
│   └── sources/
│       └── linkedin/           # Custom source spec for LinkedIn GDPR data
│           ├── source.yaml
│           └── README.md
├── coralcon/
│   ├── __init__.py
│   ├── cli.py                  # Main CLI entry point (Click/Typer)
│   ├── queries/
│   │   ├── __init__.py
│   │   ├── rejection_patterns.py    # Query 1: rejection rate by role type
│   │   ├── github_correlation.py    # Query 2: GitHub activity vs response rate
│   │   ├── skill_gaps.py           # Query 3: skill gap detection
│   │   ├── timing_analysis.py      # Query 4: application timing patterns
│   │   └── followup_tracker.py     # Query 5: follow-up priority list
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── analyzer.py            # LLM-powered insight generator
│   │   └── recommender.py         # Action item generator
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Data models for applications, insights
│   └── utils/
│       ├── __init__.py
│       ├── coral_client.py        # Coral SQL execution wrapper
│       └── formatters.py          # CLI output formatting (tables, colors)
├── web/                           # Optional web dashboard
│   ├── app.py                     # FastAPI server
│   ├── static/
│   │   └── dashboard.js           # Chart.js visualizations
│   └── templates/
│       └── index.html             # Dashboard template
├── data/
│   └── sample/                    # Sample data for demo
│       ├── applications.json      # Sample Notion application data
│       ├── github_activity.json   # Sample GitHub activity
│       └── linkedin_export/       # Sample LinkedIn GDPR export CSVs
└── tests/
    └── test_queries.py
```

## Coral Setup
```bash
# Install Coral
# macOS: brew install withcoral/tap/coral
# Linux: check https://withcoral.com/docs for Linux install

# Onboard and connect sources
coral onboard

# Add GitHub source
coral source add github

# Add Notion source  
coral source add notion

# Add custom LinkedIn file source (we build this)
coral source add ./coral/sources/linkedin/source.yaml

# Test connection
coral query "SELECT * FROM github.repos LIMIT 5"
coral query "SELECT * FROM notion.applications LIMIT 5"
```

## Core Queries to Implement

### 1. Rejection Pattern Analysis
```sql
SELECT 
  n.role_title,
  COUNT(*) as total,
  SUM(CASE WHEN n.status = 'rejected' THEN 1 ELSE 0 END) as rejected,
  ROUND(SUM(CASE WHEN n.status = 'rejected' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as rejection_rate
FROM notion.applications n
GROUP BY n.role_title
ORDER BY rejection_rate DESC
```

### 2. GitHub Activity vs Response Rate
```sql
SELECT 
  n.company,
  n.applied_date,
  n.status,
  g.commits_count
FROM notion.applications n
JOIN github.activity g 
  ON g.week = date_trunc('week', n.applied_date)
ORDER BY n.applied_date DESC
```

### 3. Skill Gap Detection
```sql
SELECT 
  n.required_skills,
  g.languages,
  l.skills
FROM notion.applications n
JOIN github.profile g
JOIN linkedin.skills l
WHERE n.status = 'rejected'
```

## LinkedIn Source Spec
LinkedIn API is restricted. Use LinkedIn GDPR data export instead:
1. Go to LinkedIn Settings → Data Privacy → Get a copy of your data
2. Download CSV files (Connections, Skills, Profile, Positions)
3. Write a Coral file source spec that reads these CSVs as SQL tables

Source spec should expose:
- `linkedin.profile` — name, headline, summary, location
- `linkedin.skills` — skill name, endorsement count
- `linkedin.positions` — company, title, start_date, end_date
- `linkedin.connections` — name, company, position, connected_date

## LLM Analysis Layer
After Coral returns query results, pass them to Claude API for insight generation:

```python
import anthropic

client = anthropic.Anthropic()

def generate_insights(query_results: dict) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Analyze this job search data and provide actionable insights.
            
            Rejection patterns: {query_results['rejections']}
            GitHub activity correlation: {query_results['github']}
            Skill gaps: {query_results['skills']}
            
            Give 3-5 specific, data-backed recommendations. Be blunt. 
            Format as actionable items with expected impact."""
        }]
    )
    return response.content[0].text
```

## CLI Commands
```bash
# Full analysis
coralcon analyze

# Specific analyses
coralcon rejections      # Rejection pattern breakdown
coralcon gaps            # Skill gap analysis
coralcon timing          # Application timing patterns
coralcon followup        # Follow-up priority list
coralcon github-check    # GitHub profile health check
coralcon dashboard       # Launch web dashboard
```

## Demo Data Strategy
For the hackathon demo, seed realistic data:
- Notion: 150+ applications across different roles (React, Python, AI/ML, DevOps)
- GitHub: Real account data (Nyra's actual GitHub)
- LinkedIn: Either real GDPR export or realistic sample data

Make the data tell a story:
- React roles: high rejection rate, no React repos
- Python roles: lower rejection rate, multiple Python repos
- Weeks with no commits: high ghost rate
- Applications after 7 days: mostly ghosted

## Key Rules
1. ALL data retrieval must go through Coral SQL — no direct API calls
2. New project — no code from existing repos
3. Must demonstrate cross-source JOINs
4. LinkedIn source spec should be submitted as a PR to Coral for $100 bounty
5. Keep it buildable — CLI first, web dashboard only if time permits
6. Demo video max 3 minutes

## Voice & Tone
CLI output should be:
- Direct, no fluff
- Data-backed ("85% ghost rate" not "you might want to consider")
- Actionable ("Build 1 React project this week" not "consider learning React")
- Slightly irreverent ("Stop applying to React jobs. Your GitHub screams Python.")

## Environment
- Development: CachyOS Linux (home laptop)
- Coral runs locally
- Python virtual environment
- Git for version control
- Push to GitHub for submission
