# PHASE 2: Multi-Agent Architecture Upgrade

## Context
Phase 1 scaffolded the basic CoralCon project with Coral SQL queries and CLI. 
Phase 2 upgrades it from a single-query tool to a multi-agent system.

## What Changed
CoralCon is now a 4-agent system, not a single script. Each agent has a specific role and passes output to the next.

## Agent Architecture

### Agent 1: Recon Agent (`coralcon/agents/recon.py`)
- Executes all Coral SQL queries across GitHub + Notion + LinkedIn
- Returns structured raw data as JSON
- No LLM calls — pure data retrieval
- Methods:
  - `fetch_applications()` → all Notion application records
  - `fetch_github_activity()` → repos, commits, languages, contribution frequency
  - `fetch_linkedin_profile()` → skills, headline, positions
  - `fetch_all()` → combined dataset from all sources

### Agent 2: Analyst Agent (`coralcon/agents/analyst.py`)
- Takes raw data from Recon Agent
- Calls Claude API to analyze patterns
- Generates structured insights as JSON:
```json
{
  "rejection_patterns": [
    {"role_type": "React", "rejection_rate": 92, "reason": "0 React repos on GitHub"}
  ],
  "timing_insights": [
    {"pattern": "Applications after 7 days", "ghost_rate": 78}
  ],
  "skill_gaps": [
    {"skill": "TypeScript", "demanded_count": 34, "present_on_github": false, "present_on_linkedin": false}
  ],
  "github_correlation": {
    "active_weeks_response_rate": 60,
    "inactive_weeks_response_rate": 15
  },
  "followup_priorities": [
    {"company": "Acme Corp", "days_since_applied": 16, "priority": "high"}
  ],
  "overall_health_score": 35
}
```
- System prompt for Claude API:
```
You are a brutally honest career data analyst. You receive job search data from multiple sources (GitHub, Notion, LinkedIn). 
Analyze patterns and return structured JSON with specific, data-backed insights.
Never be vague. Use exact numbers. Be blunt.
Example: "92% rejection rate on React roles because you have 0 React repos" not "consider building React projects"
```

### Agent 3: Dashboard Agent (`coralcon/agents/dashboard.py`)
- Takes structured insights from Analyst Agent
- Writes/updates a Notion page as a visual dashboard
- Uses Notion API (NOT through Coral — Coral is read-only, dashboard needs write access)
- Creates/updates these Notion blocks:
  - **Header**: "CoralCon Career Dashboard — Last updated: {timestamp}"
  - **Health Score**: Overall score out of 100 with color indicator
  - **Rejection Patterns Table**: role_type | total_applied | rejected | rejection_rate | root_cause
  - **Skill Gap Table**: skill | times_demanded | on_github | on_linkedin | action
  - **GitHub Activity Heatmap**: week | commits | applications_sent | response_rate (as Notion table)
  - **Follow-up Priority List**: company | role | days_waiting | priority | suggested_action
  - **Timing Analysis**: time_to_apply | ghost_rate | recommendation
  - **Weekly Action Items**: auto-generated from insights

### Agent 4: Action Agent (`coralcon/agents/action.py`)
- Takes recommendations from Analyst Agent
- Creates actual Notion tasks/to-do items in a separate "CoralCon Actions" database
- Each task has:
  - Title: specific action ("Build a React todo app and push to GitHub")
  - Priority: High/Medium/Low
  - Deadline: auto-calculated (e.g., "within 7 days")
  - Category: skill_gap / follow_up / profile_fix / application_strategy
  - Impact: estimated improvement ("Expected +30% response rate for React roles")
  - Status: Not Started

## Orchestrator (`coralcon/orchestrator.py`)
Coordinates all 4 agents in sequence:

```python
class CoralConOrchestrator:
    def __init__(self):
        self.recon = ReconAgent()
        self.analyst = AnalystAgent()
        self.dashboard = DashboardAgent()
        self.action = ActionAgent()
    
    def run_full_analysis(self):
        # Step 1: Recon
        print("🏴‍☠️ Agent 1: Recon — Scanning the seas...")
        raw_data = self.recon.fetch_all()
        
        # Step 2: Analyze
        print("🔍 Agent 2: Analyst — Decoding patterns...")
        insights = self.analyst.analyze(raw_data)
        
        # Step 3: Dashboard
        print("📊 Agent 3: Dashboard — Building your war room...")
        dashboard_url = self.dashboard.update(insights)
        
        # Step 4: Actions
        print("⚔️ Agent 4: Action — Assigning missions...")
        tasks = self.action.create_tasks(insights)
        
        return {
            "insights": insights,
            "dashboard_url": dashboard_url,
            "tasks_created": len(tasks)
        }
```

## Updated CLI Commands
```bash
# Full pipeline — all 4 agents
coralcon analyze

# Individual agents
coralcon recon          # Just fetch data
coralcon insights       # Recon + Analyst only
coralcon dashboard      # Recon + Analyst + Dashboard update
coralcon actions        # Recon + Analyst + Action items only

# Utilities
coralcon status         # Show last analysis summary
coralcon setup          # Configure Notion pages and databases
```

## New Files to Create
```
coralcon/
├── orchestrator.py              # NEW — coordinates all agents
├── agents/
│   ├── recon.py                 # NEW — Coral SQL data fetcher
│   ├── analyst.py               # REFACTOR from existing analyzer.py
│   ├── dashboard.py             # NEW — Notion dashboard writer
│   └── action.py                # NEW — Notion task creator
├── notion/
│   ├── __init__.py              # NEW
│   ├── client.py                # NEW — Notion API write client
│   ├── dashboard_template.py    # NEW — dashboard page structure
│   └── task_template.py         # NEW — task database schema
```

## Notion Setup Required
CoralCon needs TWO Notion databases:
1. **Applications Database** (already exists — user's job tracker) — READ via Coral
2. **CoralCon Dashboard** page — WRITE via Notion API (Agent 3 creates this)
3. **CoralCon Actions** database — WRITE via Notion API (Agent 4 creates this)

Add a `coralcon setup` command that:
- Creates the Dashboard page in the user's Notion workspace
- Creates the Actions database
- Stores page/database IDs in local config (`~/.coralcon/config.json`)

## Notion API Integration
```python
# Use notion-client package
# pip install notion-client

from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])

# Create dashboard page
notion.pages.create(
    parent={"database_id": config["workspace_id"]},
    properties={...},
    children=[...blocks...]
)

# Create task in actions database
notion.pages.create(
    parent={"database_id": config["actions_db_id"]},
    properties={
        "Title": {"title": [{"text": {"content": task.title}}]},
        "Priority": {"select": {"name": task.priority}},
        "Deadline": {"date": {"start": task.deadline}},
        "Category": {"select": {"name": task.category}},
        "Impact": {"rich_text": [{"text": {"content": task.impact}}]},
        "Status": {"select": {"name": "Not Started"}}
    }
)
```

## Dependencies to Add
```
notion-client>=2.0.0
```

## Important Notes
- Coral = READ from all sources (SQL queries)
- Notion API = WRITE dashboard and tasks (direct API, not through Coral)
- This separation is intentional — Coral is read-only by design
- Keep Coral queries in recon.py, keep Notion writes in notion/client.py
- Don't mix them

## Demo Flow After Phase 2
```
$ coralcon analyze

🏴‍☠️ CoralCon — The job market conned you. Now you con the data back.

🏴‍☠️ Agent 1: Recon — Scanning the seas...
   ✓ GitHub: 47 repos, 1,243 commits scanned
   ✓ Notion: 147 applications loaded
   ✓ LinkedIn: 23 skills, 4 positions mapped

🔍 Agent 2: Analyst — Decoding patterns...
   ✓ 5 rejection patterns identified
   ✓ 8 skill gaps detected
   ✓ 23 follow-ups overdue

📊 Agent 3: Dashboard — Building your war room...
   ✓ Dashboard updated: https://notion.so/coralcon-dashboard-xxx

⚔️ Agent 4: Action — Assigning missions...
   ✓ 7 tasks created in Notion
   ✓ Top priority: "Build React project" (deadline: June 3)

Career Health Score: 35/100 🔴
"You're applying to React jobs with a Python portfolio. That's like bringing a sword to a cannon fight."
```
