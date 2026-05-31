# CoralCon — 3-Minute Demo Script

**Hard cap: 3:00.** Aim for 2:45 so you have breathing room.
Record terminal + browser. Keep the cursor calm. Read the **SAY** lines; do the **DO** lines.

Live URL: https://coral-con.vercel.app
Repo: this folder. Real-Coral proof: `bash scripts/real_coral_proof.sh`

---

## 0:00 — 0:20 · The hook (talking head or voiceover over logo)

**SAY:**
> "Every career tool tells you what to do. None of them tell you *why* you're getting rejected.
> CoralCon does — it joins your GitHub, your application tracker, and your LinkedIn through
> Coral SQL, and proves the pattern with your own data."

**DO:** Have the terminal open, clean, font bumped up. Repo root.

---

## 0:20 — 0:50 · One question, three sources (the core idea)

**SAY:**
> "Watch. I ask one plain-English question. CoralCon routes it to a Coral SQL query that
> spans three different data sources."

**DO — type:**
```bash
python -m coralcon.cli ask "why am I getting rejected for react roles"
```

**SAY (while it prints):**
> "There's the headline answer — and notice the *Coral proof* line at the bottom: the query
> ID, the row count, and the sources it touched. This isn't a guess. It's a SQL join."

---

## 0:50 — 1:30 · Cross-source JOIN = the moment Coral earns its keep

**SAY:**
> "Here's why Coral matters. Skill gaps aren't in any single source. The job wants React,
> my LinkedIn lists skills, my GitHub shows what I actually ship. One Coral query joins all
> three and shows me the gap."

**DO — type:**
```bash
python -m coralcon.cli gaps
```

**SAY:**
> "Top of the list — the skills roles keep asking for, with whether they show up on my
> LinkedIn or in my GitHub repos. Where both columns are empty, that's a rejection waiting
> to happen. No CoralCon, and this is three API integrations and a correlation script.
> With Coral, it's one SELECT."

---

## 1:30 — 2:05 · Proof report (judges love receipts)

**SAY:**
> "Everything CoralCon claims is backed by a logged Coral query — and this is running on my
> real data, live. Here's the audit trail."

**DO — type:**
```bash
python -m coralcon.cli proof
```

**SAY (point at the screen):**
> "Mode: real. Two genuine cross-source JOINs, every source listed. The best query joins
> Sheets, LinkedIn, and GitHub in one statement — and there's the full SQL. That's the
> requirement, proven on real data."

*(Local runs are real mode — the `.env` sets `CORAL_AVAILABLE=true`, so `proof` shows
"Mode: real" with 2 cross-source JOINs, not the 9-query sample story. Say what's on screen.)*

---

## 2:05 — 2:35 · It's REAL data, live (not seeded)

**SAY:**
> "And this runs on real data, live through the Coral CLI — not a fixture."

**DO — type:**
```bash
bash scripts/real_coral_proof.sh
```

**SAY (over the output):**
> "Three sources listed by Coral. One query spanning all three. A real cross-source JOIN of
> my actual applications against my LinkedIn profile. And my real rejection pattern by
> company — pulled straight from Gmail into the tracker Coral reads. Every row is live SQL."

> *(If short on time, cut this and let the deployed dashboard carry the "it's real" weight.)*

---

## 2:35 — 3:00 · The product + close

**DO:** Switch to browser → **https://coral-con.vercel.app**. Scroll the dashboard once.

**SAY:**
> "Same engine, deployed. Charts for rejection patterns, the GitHub-activity correlation,
> and the skill-gap heatmap — all Coral-powered.
> CoralCon: other agents tell you what to do. CoralCon proves *why* you're failing,
> with the data you already have. Built on Coral."

**DO:** End on the dashboard or the logo. Stop.

---

## Pre-flight checklist (run 10 min before recording)

```bash
# 1. Deps + DB ready
pip install -r requirements.txt
python -m coralcon.cli db init

# 2. Smoke-test every on-camera command once (so nothing surprises you live)
python -m coralcon.cli ask "why am I getting rejected for react roles"
python -m coralcon.cli gaps
python -m coralcon.cli proof
bash scripts/real_coral_proof.sh

# 3. Confirm the deployed site loads
#    open https://coral-con.vercel.app
```

**Gotchas:**
- The real-Coral script sends stderr to `/dev/null` on purpose — Coral 0.4.1 prints a
  harmless tokio panic *after* returning correct rows. Don't let it spook you.
- Deployed site is intentionally **sample mode** (the polished 147-app story). Real-data
  proof lives in the terminal segment. Don't try to show real data in the browser.
- Clear scrollback before each command so the screen is clean.
- 3:00 is a hard cap. If you're running long, drop the `real_coral_proof.sh` segment
  (2:05–2:35) — `proof` already demonstrates the cross-source requirement.
```
