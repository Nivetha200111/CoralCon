# CoralCon `sheets` source

A Coral **file source** that exposes your Google Sheets job tracker as the SQL
table `sheets.applications`.

## Why a file source (and not a direct Sheets HTTP source)

The Google Sheets REST API returns rows as **positional arrays**
(`values: [[...], [...]]`) with no column names. Coral's HTTP backend has no
row strategy that maps an array-of-arrays onto named columns, so a pure HTTP
`sheets` source can't expose `company`, `status`, etc. as real columns.

CoralCon solves this with a thin bridge:

```
Gmail API ──► classify rejections ──► Google Sheet (you manage here)
                                            │
                  python -m coralcon.cli sheets-sync (Sheets API)
                                            ▼
                                  data/applications.csv
                                            │
                                   Coral file source
                                            ▼
                              SELECT ... FROM sheets.applications
                                  JOIN github.* JOIN linkedin.*
```

The Sheet stays the human-friendly surface you edit by hand. Coral remains the
query + cross-source JOIN engine — exactly what it's good at.

## Setup

```bash
# 1. Point the source at your data dir (where applications.csv lives)
#    Edit SHEETS_CSV_PATH default in source.yaml, or pass at add time.

# 2. Register the source
coral source add --interactive --file coral/sources/sheets/source.yaml

# 3. Keep the CSV in sync with your Google Sheet
python -m coralcon.cli sheets-sync

# 4. Query through Coral
coral sql --format json "SELECT role_title, status FROM sheets.applications"
```

## Columns

| column | notes |
|---|---|
| `id` | stable row id (e.g. `app_001`) |
| `company` | hiring company |
| `role_title` | normalized role (React Frontend Engineer, Python Developer, …) |
| `status` | `applied` / `interviewing` / `rejected` / `ghosted` / `offer` |
| `applied_date` | ISO date you applied |
| `responded_date` | ISO date of the rejection/response email (from Gmail), if any |
| `required_skills` | `;`-separated skills |
| `salary_range` | free text |
| `source` | how you found the role |
| `notes` | free text |
