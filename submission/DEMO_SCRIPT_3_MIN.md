# CoralCon — 3-Minute Demo Script (winning cut)

> **Goal:** prove this runs on *real Coral*, not a mock — and that the agent is
> safe and verifiable. Each beat is tagged with the judging criterion it scores.
>
> **Before you record:** run in **real mode** so the live badge is green.
> ```bash
> CORAL_AVAILABLE=true python -m coralcon.cli serve
> ```
> Pre-warm the page so there's no cold start on camera.

---

## 0:00–0:20 — Hook  ·  *Potential Impact*

> "I applied to hundreds of jobs and got rejected with zero feedback. The data
> that explains *why* was sitting in three tools that don't talk to each other —
> my Notion tracker, my GitHub, my LinkedIn. So I made them talk. In one SQL query."

Show the dashboard hero. **Point at the green `Live via Coral · GitHub · Notion · LinkedIn` pill in the sidebar.** Say: "That's real — connected through Coral right now, not seeded data."

## 0:20–0:55 — The Ask (your differentiator)  ·  *Creativity · Aesthetics · Best Use of Coral*

Open the **Ask** tab. Type: **"which roles reject me the most?"**

> "I ask in plain English. But here's the part that matters: the language model
> never writes SQL. A deterministic router picks one of a fixed set of safe Coral
> queries, runs it unchanged, and the model only narrates the real rows."

Point at the answer card: the **headline number**, then the proof line — **the exact Coral query name, the source pills, the row count.** Say: "Every answer ships with proof. No hallucinated stats."

## 0:55–1:35 — The cross-source JOIN  ·  *Best Use of Coral · Technical Implementation*

Open the **How It Works** tab (or run `coral sql` in a terminal split).

> "This is the query that makes CoralCon possible — Notion application outcomes,
> JOINed with GitHub commit activity, JOINed with LinkedIn skills."

```sql
SELECT n.role_title, n.status, g.commits_count, l.skills
FROM notion.applications n
JOIN github.activity g ON g.week = date_trunc('week', n.applied_date)
JOIN linkedin.skills l;
```

> "Three sources, one query, zero glue code. Coral handles auth, pagination, and
> rate limits below deck. And I had to *build* the LinkedIn source myself — it
> didn't exist, so I wrote the source spec and submitted it back to Coral."

Flash the PR: **withcoral/coral#994**.

## 1:35–2:20 — The verdict  ·  *Potential Impact · Technical Implementation*

Back to **My Report**. Expand the top insight.

> "It doesn't say 'improve your profile.' It says: *React roles reject you 94% of
> the time, and your GitHub has zero React repos.* The absence is the signal — a
> LEFT JOIN finds the skills jobs demand that I can't prove I have."

Point at: query ID, source tables, row count, confidence. "All evidence-backed."

## 2:20–2:45 — Local-first  ·  *Best Use of Coral · Learning & Growth*

Open the **Privacy** tab.

> "Everything runs locally. My applications, my GitHub, my LinkedIn export never
> leave my machine. When the LLM is involved, it only ever sees summarized,
> PII-stripped rows — never company names or personal data."

## 2:45–3:00 — Close

> "Other agents tell you what to do. CoralCon *proves* why you're failing — with
> the data you already have, joined in one query, by Coral."

Show repo + live URL on screen.

---

## Shot checklist (so nothing is missed)
- [ ] Green **Live via Coral** pill visible (record in `CORAL_AVAILABLE=true`)
- [ ] Ask tab answering a question + visible proof line
- [ ] The 3-source JOIN on screen (How It Works tab or terminal)
- [ ] PR #994 flashed
- [ ] One expanded insight showing query ID / sources / row count
- [ ] Privacy tab
- [ ] Repo URL + live demo URL in the final frame
- [ ] Under 3:00 total

## Honesty note (keeps the score)
If any segment uses seeded data, say "this mirrors my real pattern" once — judges
respect disclosure and punish discovering it themselves. The live pill + a single
real JOIN on camera is enough to remove all doubt.
