# PHASE 3: Winning Project Upgrade — CoralCon Judge-Ready Layer

## Codex Prompt

You are Codex working inside the existing CoralCon repo.

Context:

Phase 1 created the CoralCon scaffold with Coral SQL queries, CLI, sample data, and basic analysis.

Phase 2 upgraded CoralCon into a 4-agent system:

1. Recon Agent — reads GitHub + Notion + LinkedIn through Coral SQL
2. Analyst Agent — generates structured career insights
3. Dashboard Agent — writes a Notion dashboard
4. Action Agent — creates Notion action tasks

Phase 3 must make this project competitive enough to win the WeMakeDevs Coral hackathon.

The project must visibly demonstrate:

- Coral SQL as the central data layer
- Cross-source JOINs across GitHub, Notion, and LinkedIn
- A custom LinkedIn source spec
- Local-first architecture
- Caching / repeated-query performance proof
- Judge-friendly UX
- A strong 3-minute demo flow
- Real action loop, not just a dashboard

Do not replace the Phase 1/2 architecture. Extend it cleanly.

---

## Product Reframe

Upgrade CoralCon from:

> AI job search dashboard

to:

> CoralCon is a local-first career intelligence agent that turns rejection history into an evidence-backed improvement plan by joining GitHub proof-of-work, Notion application outcomes, and LinkedIn profile signals through Coral SQL.

Also support an optional enterprise/cohort framing:

> Placement teams, bootcamps, and colleges can use CoralCon to diagnose why candidates are failing across applications, portfolios, and profile positioning.

This gives the project both Track 2 personal-agent strength and Track 1 enterprise-agent flavor.

---

## Phase 3 Goals

Build the following winning-layer features:

1. Judge Demo Mode
2. Coral Proof Panel
3. Evidence-Backed Insight Engine
4. Cohort Mode
5. Cache Benchmark Mode
6. Local-First Privacy Report
7. Submission Pack Generator
8. Polished Web Dashboard
9. Deterministic Fallback Mode
10. README and Demo Script Upgrade

---

## 1. Judge Demo Mode

Add a command:

```bash
coralcon judge-demo
```

This command should run a complete deterministic demo pipeline using seeded sample data.

It should print a dramatic, clean, pirate-themed but professional flow:

```txt
🏴‍☠️ CoralCon Judge Demo

Step 1/6: Proving Coral sources
✓ GitHub source detected
✓ Notion applications loaded
✓ LinkedIn GDPR source loaded

Step 2/6: Running cross-source Coral SQL
✓ Query joined notion.applications + github.activity + linkedin.skills
✓ 147 applications analyzed
✓ 47 GitHub repos scanned
✓ 23 LinkedIn skills mapped

Step 3/6: Decoding rejection patterns
⚠ React roles: 92% rejection
Root cause: 0 React repos found on GitHub

Step 4/6: Building action plan
✓ 7 Notion tasks generated
✓ Top task: Build one React proof-of-work project

Step 5/6: Generating dashboard
✓ Dashboard available at /dashboard

Step 6/6: Producing judge evidence pack
✓ ./submission/coralcon_evidence_pack.md created
```

Requirements:

- Must work even without real API keys by using sample data.
- Must clearly show that Coral SQL is the center of the app.
- Must not hallucinate numbers. Use seeded sample values or real query outputs only.
- Add `--real` flag to use real Coral connections.
- Add `--sample` flag to force sample mode.

Files:

- `coralcon/demo/judge_demo.py`
- Update `coralcon/cli.py`

---

## 2. Coral Proof Panel

Create a proof system that records every Coral query executed.

Add:

```python
coralcon/proof/query_logger.py
```

Every Recon Agent query should be logged with:

```json
{
  "query_id": "q_001",
  "query_name": "skill_gap_detection",
  "sql": "SELECT ...",
  "sources_used": ["notion.applications", "github.profile", "linkedin.skills"],
  "is_cross_source": true,
  "rows_returned": 42,
  "execution_ms": 813,
  "used_cache": false,
  "timestamp": "2026-05-27T..."
}
```

Create a CLI command:

```bash
coralcon proof
```

Output:

```txt
CORAL PROOF REPORT
━━━━━━━━━━━━━━━━━━
Total Coral Queries: 6
Cross-source JOINs: 4
Sources Used:
- notion.applications
- github.repos
- github.activity
- linkedin.profile
- linkedin.skills

Best Coral Query:
SELECT ...
FROM notion.applications n
JOIN github.profile g
JOIN linkedin.skills l
...
```

Also expose proof data in the web dashboard as a **Coral Proof** tab.

This is critical for judges. They should not have to guess whether Coral was deeply used.

Files:

- `coralcon/proof/__init__.py`
- `coralcon/proof/query_logger.py`
- `coralcon/proof/report.py`
- Update `ReconAgent` to log every Coral SQL call
- Update web dashboard

---

## 3. Evidence-Backed Insight Engine

Refactor Analyst Agent so every insight contains evidence.

Current insights are good but must become judge-grade.

Required insight schema:

```json
{
  "id": "insight_001",
  "title": "React role rejection pattern",
  "severity": "high",
  "claim": "React roles have a 92% rejection rate.",
  "evidence": {
    "query_id": "q_003",
    "rows_used": 37,
    "sources": ["notion.applications", "github.repos", "linkedin.skills"],
    "supporting_numbers": {
      "react_applications": 25,
      "react_rejections": 23,
      "react_repos": 0
    }
  },
  "root_cause": "GitHub profile does not show React proof-of-work.",
  "recommended_action": "Build and pin one React project within 7 days.",
  "expected_impact": "Improve React role profile-fit score from 22 to 61.",
  "confidence": 0.86
}
```

Rules:

- No insight can be created without evidence.
- Every number must come from raw data or deterministic sample data.
- If LLM is unavailable, use deterministic rules.
- If LLM output is invalid JSON, repair or fallback.
- Save insights to:
  - `./runs/latest/insights.json`
  - `./runs/latest/proof.json`
  - `./runs/latest/report.md`

Files:

- `coralcon/models/insight_schema.py`
- `coralcon/agents/analyst.py`
- `coralcon/agents/rule_based_analyst.py`
- `coralcon/utils/json_guard.py`

---

## 4. Cohort Mode

Add optional cohort mode to make the project feel bigger and more enterprise-worthy.

Command:

```bash
coralcon cohort analyze
```

Purpose:

Analyze multiple candidates/job seekers at once using sample anonymized data.

Data:

Create sample candidate folders:

```txt
data/sample/cohort/
  candidate_001/
    applications.csv
    github_activity.csv
    linkedin_skills.csv
  candidate_002/
    applications.csv
    github_activity.csv
    linkedin_skills.csv
  candidate_003/
    applications.csv
    github_activity.csv
    linkedin_skills.csv
```

Cohort report should show:

```txt
COHORT CAREER INTELLIGENCE REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Candidates analyzed: 12
Most common rejection cause: Missing proof-of-work for claimed skills
Top missing skills:
1. TypeScript — demanded in 41 rejected applications
2. Docker — demanded in 29 rejected applications
3. System Design — demanded in 22 rejected applications

Placement Team Actions:
1. Run a 7-day TypeScript portfolio sprint
2. Fix LinkedIn headline mismatch for 8 candidates
3. Prioritize Python backend roles for 5 candidates
```

Dashboard:

Add a Cohort tab with:

- candidate health score leaderboard
- common skill gaps
- role-fit heatmap
- recommended training sprint
- before/after intervention plan

Files:

- `coralcon/cohort/analyzer.py`
- `coralcon/cohort/sample_loader.py`
- `coralcon/cohort/report.py`
- `data/sample/cohort/...`

Keep this buildable. It can use sample files if Coral file-source setup is difficult, but the report must still include Coral-style SQL proof if possible.

---

## 5. Cache Benchmark Mode

Coral judging rewards best use of Coral including caching.

Add command:

```bash
coralcon benchmark-cache
```

It should run the same heavy cross-source query twice and show timing:

```txt
CACHE BENCHMARK
━━━━━━━━━━━━━━━
Query: skill_gap_detection_cross_source

Run 1: 1240ms
Run 2: 312ms
Speedup: 3.97x

Why this matters:
Coral avoids repeated expensive API/file retrieval during agent analysis.
```

If real Coral cache metadata is not exposed, measure wall-clock execution time and label it honestly:

```txt
Cache metadata unavailable. Reporting observed repeated-query speedup.
```

Files:

- `coralcon/benchmarks/cache_benchmark.py`
- Update CLI

---

## 6. Local-First Privacy Report

Add command:

```bash
coralcon privacy-report
```

Generate a local-first report:

```txt
LOCAL-FIRST PRIVACY REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Coral runs locally
✓ Raw GitHub/Notion/LinkedIn data is queried locally through SQL
✓ LLM receives only summarized query results
✓ No LinkedIn scraping required
✓ LinkedIn data comes from user-provided GDPR export
✓ Credentials are read from environment variables
✓ Reports are stored locally in ./runs
```

Also generate:

```txt
./submission/privacy_report.md
```

Important:

Do not claim absolute security. Be precise.

Say:

> CoralCon is designed to keep raw source data local. If LLM analysis is enabled, summarized query results may be sent to the configured LLM provider.

Files:

- `coralcon/privacy/report.py`

---

## 7. Submission Pack Generator

Add command:

```bash
coralcon submit-pack
```

It should generate a `/submission` folder:

```txt
submission/
  README_SUBMISSION.md
  DEMO_SCRIPT_3_MIN.md
  ARCHITECTURE.md
  CORAL_PROOF.md
  PRIVACY_REPORT.md
  SAMPLE_OUTPUT.md
  screenshots/
```

Generate markdown files automatically from current run artifacts.

`README_SUBMISSION.md` must include:

- Project name
- One-line pitch
- Problem
- Solution
- Why Coral is essential
- Architecture
- Sources used
- Cross-source SQL examples
- Demo commands
- What makes it original
- Track fit: Personal Agent + optional Enterprise/Cohort angle

`DEMO_SCRIPT_3_MIN.md` must include:

- 0:00-0:30 hook
- 0:30-1:00 Coral setup/source proof
- 1:00-1:30 cross-source SQL demo
- 1:30-2:00 insight/action generation
- 2:00-2:30 dashboard/cohort mode
- 2:30-3:00 closing line

Files:

- `coralcon/submission/pack_generator.py`
- `templates/submission/*.md.j2` or simple Python string templates

---

## 8. Polished Web Dashboard

Upgrade the existing FastAPI dashboard.

Routes:

```txt
/
 /dashboard
 /proof
 /cohort
 /privacy
```

Dashboard sections:

1. Hero section
   - CoralCon
   - “The job market conned you. Query it back.”
   - Health score card

2. Insight cards
   - Severity
   - Claim
   - Root cause
   - Recommended action
   - Evidence query id

3. Charts
   - Rejection rate by role
   - GitHub activity vs response rate
   - Skill gap frequency
   - Application timing vs ghost rate

4. Coral Proof tab
   - SQL queries shown in readable code blocks
   - sources used
   - cross-source badge
   - execution time
   - rows returned

5. Cohort tab
   - leaderboard
   - common skill gaps
   - placement team recommendations

6. Privacy tab
   - local-first architecture explanation

Frontend style:

- Sleek dark mode
- Pirate accent but not childish
- Minimal, premium, demo-friendly
- Use CSS only or simple Chart.js
- No heavy frontend framework unless already present

Files:

- `web/app.py`
- `web/templates/dashboard.html`
- `web/templates/proof.html`
- `web/templates/cohort.html`
- `web/templates/privacy.html`
- `web/static/styles.css`
- `web/static/dashboard.js`

---

## 9. Deterministic Fallback Mode

The demo must not fail if:

- Anthropic/OpenAI key is missing
- Coral is not configured
- Notion API write fails
- LinkedIn export is missing

Add robust fallbacks:

```txt
Real mode:
Coral + real sources + optional LLM + optional Notion writes

Sample mode:
Seeded data + deterministic rules + local dashboard only
```

Rules:

- `coralcon judge-demo` should always work.
- If a real integration fails, print a clear warning and continue in sample mode.
- Do not crash during demo.
- Never expose secrets.
- Use `.env.example`.

Files:

- `coralcon/config.py`
- `coralcon/utils/fallbacks.py`
- `.env.example`

---

## 10. README Upgrade

Rewrite `README.md` to be judge-ready.

Required sections:

- CoralCon logo/title
- One-line pitch
- 30-second demo GIF placeholder
- Why this matters
- Why Coral is essential
- Architecture diagram
- Features
- Coral SQL examples
- Commands
- Local setup
- Sample mode
- Real mode
- Custom LinkedIn source spec
- Privacy/local-first note
- Demo script
- Submission checklist

Add this exact positioning:

> Without Coral, CoralCon would need separate GitHub, Notion, and LinkedIn integrations plus custom pagination, auth, schema mapping, and correlation logic. With Coral, the agent asks one SQL question across all sources.

---

## Implementation Priority

Do in this order:

1. Deterministic sample mode
2. Query logger / Coral Proof Report
3. Judge Demo command
4. Evidence-backed insight schema
5. Submission pack generator
6. Web dashboard polish
7. Cache benchmark
8. Privacy report
9. Cohort mode
10. README polish

If time is limited, prioritize:

- judge-demo
- proof report
- evidence-backed insights
- submit-pack
- README

These are the winning pieces.

---

## Acceptance Tests

After implementation, these commands must work:

```bash
coralcon judge-demo --sample
coralcon proof
coralcon privacy-report
coralcon benchmark-cache --sample
coralcon submit-pack
coralcon dashboard --sample
```

Expected files:

```txt
runs/latest/insights.json
runs/latest/proof.json
runs/latest/report.md
submission/README_SUBMISSION.md
submission/DEMO_SCRIPT_3_MIN.md
submission/CORAL_PROOF.md
submission/PRIVACY_REPORT.md
```

Run tests:

```bash
pytest
```

Add tests for:

- query logger
- insight schema validation
- fallback mode
- submit-pack generation
- sample judge-demo run

---

## Non-Negotiables

- Do not remove existing Phase 1/2 code.
- Do not hardcode secrets.
- Do not hallucinate metrics.
- Do not make LLM mandatory.
- Do not make Notion mandatory for demo.
- Do not directly call GitHub/Notion/LinkedIn for read operations in real mode. Reads must go through Coral SQL.
- Notion writes are allowed only for dashboard/action output.
- Keep the project local-first.
- Make the demo impossible to break.
- Every insight must have evidence.
- Every judge should understand Coral usage within 20 seconds.

---

## Final Output Wanted From Codex

Implement Phase 3 fully.

At the end, print:

1. Files created/modified
2. Commands to run
3. What works in sample mode
4. What requires real API keys
5. Any honest limitations
