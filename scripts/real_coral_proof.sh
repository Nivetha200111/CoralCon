#!/usr/bin/env bash
#
# real_coral_proof.sh — Live proof that CoralCon queries REAL data across
# three sources through Coral SQL: GitHub + Google Sheets + LinkedIn.
#
# Run on camera for the demo. Each query hits real Coral (no sample data).
# Coral 0.4.1 prints an intermittent tokio panic to stderr AFTER returning
# correct results, so we send stderr to /dev/null for a clean recording.
#
# Usage:  bash scripts/real_coral_proof.sh
set -euo pipefail

q() { coral sql "$1" 2>/dev/null; }

line() { printf '\n\033[1;36m%s\033[0m\n' "$1"; }

line "Coral sources configured (all real):"
coral source list 2>/dev/null

line "1) One Coral query spanning THREE sources (Sheets + LinkedIn + GitHub):"
q "SELECT
     (SELECT COUNT(*) FROM sheets.applications)                          AS applications,
     (SELECT COUNT(*) FROM sheets.applications WHERE status='rejected')  AS rejections,
     (SELECT COUNT(*) FROM linkedin.skills)                              AS linkedin_skills,
     (SELECT login FROM github.user LIMIT 1)                             AS github_login"

line "2) Real cross-source JOIN — your applications x your LinkedIn profile:"
q "SELECT a.company, a.role_title, a.status, p.headline
   FROM sheets.applications a
   CROSS JOIN linkedin.profile p
   LIMIT 5"

line "3) Rejection pattern by company (real applications):"
q "SELECT company,
          COUNT(*)                                            AS applied,
          SUM(CASE WHEN status='rejected' THEN 1 ELSE 0 END)  AS rejected
   FROM sheets.applications
   GROUP BY company
   ORDER BY applied DESC
   LIMIT 8"

line "4) Outcome breakdown across all real applications:"
q "SELECT status, COUNT(*) AS n
   FROM sheets.applications
   GROUP BY status
   ORDER BY n DESC"

line "Done — every row above came from live Coral SQL over your real data."
