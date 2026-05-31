# LinkedIn Coral Source Spec

Adds LinkedIn GDPR export data as queryable SQL tables in Coral.

## Setup

### 1. Export your LinkedIn data
1. Go to **LinkedIn → Settings → Data Privacy → Get a copy of your data**
2. Select: **Connections, Skills, Profile, Positions**
3. Request the archive (takes up to 24 hours)
4. Extract the ZIP to `data/linkedin_export/`

### 2. Register the source
```bash
coral source add ./coral/sources/linkedin/source.yaml
```

### 3. Verify
```bash
coral sql "SELECT * FROM linkedin.skills LIMIT 5"
coral sql "SELECT * FROM linkedin.positions ORDER BY started_on DESC LIMIT 3"
```

## Tables

| Table | File | Description |
|---|---|---|
| `linkedin.profile` | Profile.csv | Name, headline, summary, location |
| `linkedin.skills` | Skills.csv | Skills and endorsement counts |
| `linkedin.positions` | Positions.csv | Work history |
| `linkedin.connections` | Connections.csv | Network connections |

## Example Queries

```sql
-- Skill gap: what you listed vs what rejected roles required
SELECT 
  required.skill,
  COUNT(*) as times_required,
  MAX(CASE WHEN l.name IS NOT NULL THEN 1 ELSE 0 END) as in_linkedin
FROM (
  SELECT UNNEST(required_skills) as skill
  FROM notion.applications
  WHERE status = 'rejected'
) required
LEFT JOIN linkedin.skills l ON l.name = required.skill
GROUP BY required.skill
ORDER BY times_required DESC
```

## Notes
- LinkedIn GDPR export is legitimate data access — no scraping, no API key needed
- Refresh by re-downloading your export (LinkedIn allows one export per 24h)
- Submitted as a PR to Coral for the $100 bounty: [withcoral/coral#994](https://github.com/withcoral/coral/pull/994)
