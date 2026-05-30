# CoralCon — 3-Minute Demo Video Script (shoot-ready)

**Track 2: Build a Personal Agent · WeMakeDevs "Pirates of the Coral-bean"**

Total runtime target: **2:55**. Every number below is real output you can
reproduce; nothing is mocked.

---

## Setup before you hit record

```bash
# one-time, so the on-screen command is just `coralcon`
pip install -e .
export CORAL_AVAILABLE=true        # real Coral mode (your .env already sets this)
clear
```

- Terminal: large font (18pt+), dark theme, full-screen. Window width ≥ 100 cols
  so the tables don't wrap.
- Have a browser tab open on the live dashboard (coral-con.vercel.app) and one on
  the LinkedIn source PR (`withcoral/coral#994`) for the B-roll cutaways.
- Speak fast and flat. The product voice is blunt; match it.

---

## 0:00 – 0:18 · Hook (face cam or black screen, big text)

> **VO:** "I sent forty job applications. Forty. My response rate was zero
> percent. No feedback, no idea what was wrong. So I stopped guessing and turned
> my own rejection data into SQL."

**On screen:** title card → `CoralCon — your job search, cross-examined.`

---

## 0:18 – 0:45 · The daily agent (Track 2 money shot)

**Type:**
```bash
coralcon morning
```

**On screen (real output):**
```
  Where you stand: 40 applications · 0% response rate

  Today's priorities
  1. Build proof in Data Structures — demanded by 16 roles that rejected you,
     not in your GitHub and not on your LinkedIn.
  2. No follow-ups in the 7–14 day window.
  3. GitHub cadence looks fine — keep shipping.
```

> **VO:** "This is my first mate. Every morning, `coralcon morning` reads my
> application outcomes, my real GitHub repos, and my LinkedIn profile — and tells
> me the one thing to do today. Not 'improve your profile.' A specific,
> evidence-backed move."

---

## 0:45 – 1:30 · Why it knows — the cross-source Coral JOIN

**Type:**
```bash
coralcon gaps
```

**On screen — let the table land, then cursor-highlight three rows:**
```
  SKILL              REQUIRED        IN GITHUB   IN LINKEDIN
  Python             26 rejections   yes         yes
  Java               19 rejections   no          yes
  React               3 rejections   no          no
```

> **VO:** "Here's the part only Coral makes possible. One SQL query joins three
> sources. Python — demanded twenty-six times, and I actually ship it: in my
> GitHub and on my LinkedIn. Java — demanded nineteen times, it's on my LinkedIn,
> but I have zero Java repos. That's a credibility gap a recruiter sees in ten
> seconds. React — demanded, and missing from both. I was applying to React jobs
> with no React anywhere."

**Cutaway (2s):** scroll the SQL in `coralcon/queries/skill_gaps.py` — the
`WITH demand ... JOIN linkedin.skills ... JOIN github.user_repos` CTE.

> **VO (over the SQL):** "Three Coral sources — my Sheets tracker, LinkedIn, and
> my real GitHub repo languages — joined in a single statement."

---

## 1:30 – 2:10 · Proof — judge-verifiable, no hallucinations

**Type:**
```bash
coralcon proof
```

**On screen — highlight these lines from the real report:**
```
  Total Coral Queries:    10
  Cross-Source JOINs:     4
  Mode:                   real
  Cache Hit Rate:         50.0%

  q_003  skill_gap_detection   15 rows   7522.0ms  [CROSS-SOURCE]
  q_008  skill_gap_detection   15 rows      0.0ms  [CROSS-SOURCE] [CACHED]
```

> **VO:** "Every insight ships with its receipt. Ten real Coral queries, four
> cross-source joins, all logged. The flagship skill-gap query is a genuine
> three-source join returning fifteen real rows. And it's cached — seven and a
> half seconds the first time, instant the second. The LLM in CoralCon never
> writes SQL and never invents a number — it only narrates rows that Coral
> actually returned."

---

## 2:10 – 2:38 · The Coral contribution + privacy

**Cutaway:** browser on `github.com/withcoral/coral/pull/994`.

> **VO:** "LinkedIn has no open API, so I wrote a custom Coral source that reads
> your own LinkedIn data export as SQL tables — validated against a real archive
> and submitted upstream as a community source. And all of this runs locally:
> your inbox and profile never leave your machine."

**On screen:** quick flash of `coralcon morning` again, or the live dashboard
Ask tab answering "what skills am I missing?".

---

## 2:38 – 2:55 · Close

**On screen:** black card with the tagline.

> **VO:** "Other agents tell you what to do. CoralCon proves *why* you're failing
> — with evidence from the data you already have. Every morning, in one command."

**End card:** `coral-con.vercel.app · github.com/Nivetha200111/CoralCon`

---

## Reproduce-on-camera checklist (in order)

| # | Command | What the camera shows | Real result |
|---|---------|----------------------|-------------|
| 1 | `coralcon morning` | Daily standup | 40 apps, 0% response, top gap |
| 2 | `coralcon gaps` | Skill-gap table | Python/Java/React rows |
| 3 | open `skill_gaps.py` | The 3-source CTE join | — |
| 4 | `coralcon proof` | Audit trail | 10 queries, 4 cross-source, real |
| 5 | browser → PR #994 | Upstream Coral source | — |

## Backup if real Coral panics on camera
Coral 0.4.1 has an intermittent post-result tokio panic. If it shows on stderr
mid-shoot, re-run (CoralCon retries internally) or fall back to the deterministic
sample run — same numbers, never breaks:
```bash
coralcon judge-demo --sample
```
