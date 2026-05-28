# CoralCon — 3-Minute Demo Script

## 0:00-0:20 — Hook

"I got rejected again and again, but I had no feedback. So I built CoralCon
to turn rejection history into data."

Show the problem: hundreds of applications, no signal about what's failing.

## 0:20-0:50 — Show Coral

"Coral lets me query GitHub, Notion, and LinkedIn as SQL sources."

Run `python -m coralcon.cli status` to show connected sources.
Run `python -m coralcon.cli proof` to show the query audit trail.

Point out: all data retrieval goes through Coral SQL. No direct API calls.

## 0:50-1:30 — Show Cross-Source Query

"This is the key query — application outcomes from Notion joined with GitHub
activity and LinkedIn skills."

Show the cross-source JOIN in the proof report or web dashboard Coral Proof tab.

```sql
SELECT n.role_title, n.status, g.commits_count, l.skills
FROM notion.applications n
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
