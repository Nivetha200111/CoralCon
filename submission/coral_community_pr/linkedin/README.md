# LinkedIn (data export)

Exposes a LinkedIn data export (the GDPR archive LinkedIn lets any member download)
as queryable SQL tables. No API key, no scraping — it reads the CSV files LinkedIn
gives you directly.

## Setup

### 1. Export your LinkedIn data
1. Go to **LinkedIn → Settings → Data Privacy → Get a copy of your data**.
2. Select at least: **Connections, Skills, Profile, Positions**.
3. Request the archive (LinkedIn emails it within ~24 hours).
4. Extract the ZIP into a directory, e.g. `./linkedin_export/`.

### 2. Register the source
```bash
coral source add --file ./linkedin/manifest.yaml
```

Point the source at your export directory with the `LINKEDIN_EXPORT_PATH` input
(defaults to `./linkedin_export`).

### 3. Verify
```bash
coral sql "SELECT * FROM linkedin.skills LIMIT 5"
coral sql "SELECT * FROM linkedin.positions ORDER BY started_on DESC LIMIT 3"
```

## Tables

| Table | File | Description |
|---|---|---|
| `linkedin.profile` | `Profile.csv` | First/last name, headline, summary, location, industry |
| `linkedin.skills` | `Skills.csv` | Skill name and endorsement count |
| `linkedin.positions` | `Positions.csv` | Work history: company, title, description, dates |
| `linkedin.connections` | `Connections.csv` | Network: name, email, company, position, connected date |

## Example queries

```sql
-- Most endorsed skills
SELECT name, endorsements
FROM linkedin.skills
ORDER BY endorsements DESC
LIMIT 10;
```

```sql
-- Cross-source: skills required by rejected job applications
-- that are absent from your LinkedIn profile (the missing row is the signal)
SELECT required.skill, COUNT(*) AS times_required
FROM (
  SELECT UNNEST(required_skills) AS skill
  FROM sheets.applications
  WHERE status = 'rejected'
) required
LEFT JOIN linkedin.skills l ON l.name = required.skill
WHERE l.name IS NULL
GROUP BY required.skill
ORDER BY times_required DESC;
```

## Notes
- Uses the official LinkedIn data export — legitimate, member-initiated data access.
- LinkedIn permits one export roughly every 24 hours; re-download to refresh.
- Column names follow the headers in a standard English-locale LinkedIn export.
  Older or localized exports may differ slightly; adjust `columns` to match your CSV headers.
