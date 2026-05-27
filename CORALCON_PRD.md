# CoralCon — Product Requirements Document

## One-Line Pitch
"I got rejected 650 times. So I built an AI agent that decodes why job seekers fail and tells them exactly what to fix — by JOINing their GitHub, Notion, and LinkedIn data through one SQL query."

## Problem
Job seekers apply to hundreds of roles with zero feedback on WHY they're rejected. They repeat the same mistakes — wrong roles, dead GitHub profiles, bad timing, mismatched skills — because no tool connects the dots across their fragmented job search data.

## Solution
CoralCon is an AI career agent powered by Coral that queries across GitHub, Notion, and LinkedIn in a single SQL interface to:
1. Track all applications and their outcomes
2. Analyze rejection patterns across data sources
3. Identify skill gaps between what companies want and what your profile shows
4. Give actionable recommendations to improve success rate

## Target User
Any developer or tech professional actively job hunting.

## Architecture

### Data Sources (via Coral SQL)

**Source 1: Notion (exists)**
- Application tracking board: company, role, date applied, status (applied/interviewing/rejected/ghosted/offer), job description keywords, salary range
- Tables: `notion.applications`

**Source 2: GitHub (exists)**
- Profile activity: repos, languages, commit frequency, contribution graph, stars
- Tables: `github.repos`, `github.commits`, `github.profile`

**Source 3: LinkedIn (NEW source spec — build this)**
- Profile data: headline, skills listed, experience, endorsements
- Tables: `linkedin.profile`, `linkedin.skills`
- Note: LinkedIn API is restricted. Options: scrape public profile, use LinkedIn data export (GDPR download), or mock with CSV/JSON import as proof of concept

### Agent Architecture

```
User Query
    ↓
[CoralCon CLI / Web UI]
    ↓
[Coral SQL Runtime]
    ↓ (one query, multiple sources)
[GitHub API] + [Notion API] + [LinkedIn Data]
    ↓
[Analysis Engine — LLM layer]
    ↓
[Insight Report]
```

### Core Coral Queries

**Query 1: Rejection Pattern Analysis**
```sql
SELECT 
  n.role_title,
  n.status,
  COUNT(*) as total_applied,
  SUM(CASE WHEN n.status = 'rejected' THEN 1 ELSE 0 END) as rejected,
  ROUND(SUM(CASE WHEN n.status = 'rejected' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as rejection_rate
FROM notion.applications n
GROUP BY n.role_title, n.status
ORDER BY rejection_rate DESC
```

**Query 2: GitHub Activity vs Response Rate**
```sql
SELECT 
  n.company,
  n.applied_date,
  n.status,
  g.commits_count,
  g.active_repos
FROM notion.applications n
JOIN github.activity g 
  ON g.week = date_trunc('week', n.applied_date)
WHERE n.status IN ('rejected', 'ghosted', 'interviewing', 'offer')
ORDER BY n.applied_date DESC
```

**Query 3: Skill Gap Detection**
```sql
SELECT 
  n.required_skills,
  g.languages,
  l.skills as linkedin_skills
FROM notion.applications n
JOIN github.profile g
JOIN linkedin.skills l
WHERE n.status = 'rejected'
```

### Agent Insights (LLM-powered analysis on query results)

1. **Rejection Decoder**: "Your rejection rate for React roles is 92% vs 35% for Python roles. Your GitHub has 0 React repos. Stop applying to React jobs or build a React project first."

2. **Timing Analyzer**: "Applications submitted within 48 hours of posting have 3x higher response rate. 67% of your applications were submitted after 7 days."

3. **GitHub Signal Check**: "During weeks with 0 GitHub commits, your ghosting rate was 85%. During active weeks, it dropped to 40%. Recruiters are checking your profile."

4. **Skill Gap Map**: "Top 5 skills requested in roles you were rejected from but missing from your GitHub/LinkedIn: TypeScript, Docker, Kubernetes, CI/CD, System Design."

5. **Follow-up Nudger**: "23 applications have had no response for 14+ days. Based on patterns, follow-up emails sent at day 10 had 22% response rate vs 3% at day 21."

6. **Profile-Role Fit Score**: "Your LinkedIn headline says 'Software Engineer' but you're applying to 'AI Engineer' roles. Mismatch detected in 45 applications."

## Screens / UX

### Option A: CLI (faster to build, judges respect it)
```
$ coralcon analyze

🔍 Scanning your job search across GitHub, Notion, LinkedIn...

📊 REJECTION PATTERN REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Applications: 147
Response Rate: 23%
Interview Rate: 8%
Offer Rate: 2%

⚠️  TOP FINDINGS:
1. React roles: 92% rejection (0 React repos on GitHub)
2. Applications after 7 days: 78% ghosted
3. Weeks with no GitHub activity: 85% ghost rate

🎯 ACTION ITEMS:
1. Build 1 React project this week (estimated +30% response rate)
2. Apply within 48 hours of posting
3. Commit to GitHub daily during active job search

💡 Run `coralcon gaps` for detailed skill gap analysis
💡 Run `coralcon followup` for follow-up priority list
```

### Option B: Web UI (flashier demo video)
- Dashboard with charts: rejection rate by role type, response rate vs GitHub activity heatmap, skill gap radar chart
- Timeline view of applications with color-coded outcomes
- Action items panel with priority scores

### Recommended: Build CLI first, add simple web dashboard for demo video

## Tech Stack
- **Language**: Python
- **Data Layer**: Coral (SQL interface over APIs)
- **LLM**: Claude API or OpenAI for insight generation
- **Source Specs**: GitHub (existing), Notion (existing), LinkedIn (custom — build new)
- **CLI**: Click or Typer
- **Web UI** (optional): FastAPI + simple HTML/JS dashboard
- **Charts** (for demo): matplotlib or plotly for CLI, Chart.js for web

## LinkedIn Source Spec Strategy
LinkedIn's official API is restricted. Options for the hackathon:
1. **Best**: Use LinkedIn GDPR data export (Settings → Get a copy of your data). Parse the CSV files as a Coral source. This is real data, no scraping, no API restrictions.
2. **Backup**: Create a LinkedIn-format JSON/CSV manually and write a Coral file source spec for it.
3. **Stretch**: If LinkedIn API access is available (unlikely), build a proper API source spec.

Option 1 is recommended — it's real data, legitimate, and demonstrates building a file-based Coral source spec.

## Build Plan (May 27-31)

### Day 1 — May 27 (Tonight on CachyOS)
- Install Coral on CachyOS
- Run `coral onboard`, connect GitHub source
- Connect Notion source
- Write first cross-source query
- Verify data flows

### Day 2 — May 28
- Build LinkedIn file source spec (from GDPR export or manual CSV)
- Build core Python CLI with Click/Typer
- Implement Query 1 (rejection patterns) and Query 2 (GitHub activity correlation)
- Test with real data from your Notion job tracking board

### Day 3 — May 29
- Implement Query 3 (skill gap detection)
- Add LLM analysis layer (Claude/OpenAI to generate insights from query results)
- Build all 6 insight generators
- Polish CLI output formatting

### Day 4 — May 30
- Build simple web dashboard for demo video (FastAPI + HTML)
- Charts: rejection rate by role, GitHub activity heatmap, skill gap radar
- Record 3-minute demo video
- Write one-pager / README

### Day 5 — May 31 (Submit)
- Bug fixes only
- Submit to hackathon
- Post on Discord #show-and-tell
- Post on LinkedIn tagging Coral
- Submit LinkedIn source spec PR for $100 bounty

## Submission Checklist
- [ ] GitHub repo with clean README
- [ ] YouTube demo video (max 3 minutes)
- [ ] Discord showcase post with screenshots
- [ ] LinkedIn/X post tagging Coral
- [ ] LinkedIn source spec PR (bonus $100)
- [ ] Blog post "How I built CoralCon" (bonus — Keychron keyboard)

## Demo Script (3-minute video)
1. (0:00-0:30) "I applied to 650 jobs and got rejected from all of them. I had no idea why. So I built CoralCon."
2. (0:30-1:00) Show Coral setup — connecting GitHub, Notion, LinkedIn data in one SQL interface
3. (1:00-1:30) Run `coralcon analyze` — show the rejection pattern report
4. (1:30-2:00) Show skill gap analysis — "I was applying to React roles with zero React repos"
5. (2:00-2:30) Show web dashboard — charts, heatmaps, action items
6. (2:30-3:00) "CoralCon turned my 650 rejections into a dataset. Now I know exactly what to fix. Built with Coral — one SQL query across GitHub, Notion, and LinkedIn."

## Success Metrics
- Win Track 1 (MacBook Neo) or Track 2 (iPad)
- Get LinkedIn source spec accepted ($100 bounty)
- Get featured on Kunal's YouTube (870K subscribers)
- Add to O-1 visa evidence file
- Publish as portfolio piece on GitHub/LinkedIn
