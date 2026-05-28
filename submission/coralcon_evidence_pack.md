# CoralCon Evidence Pack

> Other agents tell you what to do. CoralCon proves why you're failing,
> with evidence from the data you already have.

## Project Pitch

CoralCon is a local-first career intelligence agent that turns rejection
history into an evidence-backed improvement plan by joining GitHub proof-of-work,
Notion application outcomes, and LinkedIn profile signals through Coral SQL.

## Why Coral Matters

Coral SQL is the central data layer. Without it, CoralCon would need three
separate API integrations with custom auth, pagination, schema mapping, and
correlation logic. With Coral, the agent asks one SQL question across all sources.

## Coral Proof Summary

- **Total Coral queries:** 9
- **Cross-source JOINs:** 2
- **Sources queried:** github.activity, github.profile, linkedin.profile, linkedin.skills, notion.applications
- **Best query:** skill_gap_detection
- **Best query rows:** 12
- **Best query time:** 0.06ms
- **Cached queries:** 0
- **Mode:** sample

## Architecture

```
CLI/Web -> Orchestrator -> Recon Agent -> Coral SQL -> GitHub + Notion + LinkedIn
                       -> Analyst Agent (evidence-backed insights)
                       -> Dashboard Agent (Notion writes)
                       -> Action Agent (prioritized tasks)
```

## Data Sources

| Source | Coral Table | Data |
|--------|------------|------|
| GitHub | `github.activity`, `github.profile`, `github.repos` | Commit cadence, repo languages, public events |
| Notion | `notion.applications` | Company, role, status, required skills, dates |
| LinkedIn | `linkedin.skills`, `linkedin.profile`, `linkedin.positions` | GDPR export: skills, endorsements, headline |

## Analysis Results

- Applications analyzed: 147
- Response rate: 16.3%
- Health score: 25/100
- Offer rate: 2.7%

## Evidence-Backed Insights

### React Frontend Engineer rejection pattern

**Claim:** React Frontend Engineer roles have a 81.6% rejection rate.
**Severity:** high
**Confidence:** 84%
**Evidence query:** q_005
**Sources:** notion.applications
**Rows used:** 38
**Root cause:** The role category is currently outperforming the visible proof-of-work on the profile.
**Action:** Pause cold applications to React Frontend Engineer roles and ship one targeted proof-of-work project.
**Expected impact:** Improve profile-fit before adding more applications to this bucket.

### React proof gap

**Claim:** React appears in 38 rejected applications but is missing from key profile signals.
**Severity:** high
**Confidence:** 88%
**Evidence query:** q_007
**Sources:** github.profile, linkedin.skills, notion.applications
**Rows used:** 38
**Root cause:** The job descriptions ask for the skill, but the public evidence is weak or absent.
**Action:** Build and pin one React project within 7 days.
**Expected impact:** Raise recruiter confidence for roles requiring this skill.

### GitHub activity signal

**Claim:** Ghost rate is 70.0 points higher in inactive GitHub weeks.
**Severity:** high
**Confidence:** 80%
**Evidence query:** q_006
**Sources:** github.activity, notion.applications
**Rows used:** 26
**Root cause:** Recruiter-visible activity drops during parts of the application cycle.
**Action:** Keep a steady commit cadence while applying, even if it is one focused commit per day.
**Expected impact:** Reduce ghosting risk tied to stale proof-of-work signals.

### Follow-up window

**Claim:** 10 applications are in the 7-14 day follow-up window.
**Severity:** medium
**Confidence:** 78%
**Evidence query:** q_009
**Sources:** notion.applications
**Rows used:** 10
**Root cause:** Pending applications are aging without a second touch.
**Action:** Send follow-up emails to the hot queue today.
**Expected impact:** Capture the strongest follow-up timing window before applications go cold.

## Best Coral Queries

### github_activity_correlation (q_006)

- Sources: github.activity, notion.applications
- Rows: 26
- Execution: 0.09ms
- Cached: no

```sql
SELECT n.company, n.applied_date, n.status, n.role_title, g.commits_count, g.active_repos, g.languages FROM notion.applications n JOIN github.activity g ON g.week = date_trunc('week', n.applied_date) WHERE n.status IN ('rejected', 'ghosted', 'interviewing', 'offer') ORDER BY n.applied_date DESC
```

### skill_gap_detection (q_007)

- Sources: github.profile, linkedin.skills, notion.applications
- Rows: 12
- Execution: 0.06ms
- Cached: no

```sql
SELECT skill, COUNT(*) as times_required, MAX(CASE WHEN in_github = true THEN 1 ELSE 0 END) as in_github, MAX(CASE WHEN in_linkedin = true THEN 1 ELSE 0 END) as in_linkedin FROM ( SELECT skill_name as skill, (g.languages LIKE '%' || skill_name || '%') as in_github, (l.name LIKE '%' || skill_name || '%') as in_linkedin FROM ( SELECT UNNEST(n.required_skills) as skill_name FROM notion.applications n WHERE n.status = 'rejected' ) skills JOIN github.profile g JOIN linkedin.skills l ) sub GROUP BY skill ORDER BY times_required DESC LIMIT 15
```

## Sample Mode vs Real Mode

**Sample mode** uses deterministic seeded data from `data/sample/` for reproducible
judging. Every run produces identical results. No API keys or Coral installation needed.

**Real mode** connects to actual GitHub, Notion, and LinkedIn data through Coral SQL.
Set `CORAL_AVAILABLE=true` and configure source credentials.

Both modes use the same four-agent pipeline and produce the same evidence artifacts.
The only difference is the data source.

## Privacy / Local-First

- All Coral queries execute locally
- Raw source data never leaves the machine
- LLM analysis (optional) sends only summarized results, not raw data
- No telemetry, no analytics, no external tracking

## Judge Run Commands

```bash
pip install -r requirements.txt
python -m coralcon.cli judge-demo --sample   # Full demo pipeline
python -m coralcon.cli proof                  # Coral query audit trail
python -m coralcon.cli submit-pack            # Generate submission files
python -m coralcon.cli serve                  # Web dashboard at :8000
```

## Known Limitations

- LinkedIn source requires manual GDPR data export (API access is restricted)
- Real-mode Notion integration reads simple table blocks, not database views
- LLM narrative insights require an Anthropic API key; the rule-based fallback
  provides all core insights without it
- Cohort mode currently uses anonymized sample candidates
