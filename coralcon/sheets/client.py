"""
Google Sheets client for the CoralCon application tracker.

Responsibilities (the things Coral can't do):
  - read the tracker sheet into clean dict rows (mapping the header row onto
    Sheets' positional value arrays),
  - write/append application rows back to the sheet,
  - sync the sheet down to data/applications.csv, which the Coral `sheets`
    file source then queries as `sheets.applications`.

All Google API access is lazy and optional, so sample mode never imports it.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

from coralcon.google.auth import get_credentials

# Canonical column order. Must match coral/sources/sheets/source.yaml and the
# header row written to the sheet + CSV.
COLUMNS = [
    "id",
    "company",
    "role_title",
    "status",
    "applied_date",
    "responded_date",
    "required_skills",
    "salary_range",
    "source",
    "notes",
]

DEFAULT_TAB = "Applications"


def _csv_path() -> Path:
    raw = os.getenv("SHEETS_CSV_PATH")
    if raw:
        base = Path(raw).expanduser()
    elif os.getenv("VERCEL"):
        # Read-only project filesystem on serverless; /tmp is the only writable dir.
        base = Path("/tmp")
    else:
        base = Path(__file__).parent.parent.parent / "data"
    return base / "applications.csv"


def _spreadsheet_id(explicit: str | None = None) -> str:
    sid = explicit or os.getenv("SHEETS_SPREADSHEET_ID")
    if not sid:
        raise RuntimeError(
            "Missing spreadsheet id. Set SHEETS_SPREADSHEET_ID to the id in your "
            "Google Sheet URL: docs.google.com/spreadsheets/d/<THIS_PART>/edit"
        )
    return sid


def _service():
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "google-api-python-client is required. Install with:\n"
            "    pip install google-api-python-client"
        ) from exc
    return build("sheets", "v4", credentials=get_credentials(), cache_discovery=False)


def _tab() -> str:
    return os.getenv("SHEETS_TAB", DEFAULT_TAB)


_TAB_CACHE: dict[str, str] = {}


def _resolved_tab(spreadsheet_id: str) -> str:
    """The real first-sheet title for this spreadsheet (or the SHEETS_TAB override).

    Importing a CSV names the *spreadsheet* after the file but leaves the tab as
    whatever Google chose, so a hardcoded tab name breaks. When SHEETS_TAB isn't
    set we ask the API for the actual first sheet's title and use that, which
    works regardless of what the tab is called.
    """
    explicit = os.getenv("SHEETS_TAB")
    if explicit:
        return explicit
    if spreadsheet_id in _TAB_CACHE:
        return _TAB_CACHE[spreadsheet_id]
    meta = (
        _service()
        .spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title")
        .execute()
    )
    sheets = meta.get("sheets", [])
    title = sheets[0]["properties"]["title"] if sheets else DEFAULT_TAB
    _TAB_CACHE[spreadsheet_id] = title
    return title


def _rng(spreadsheet_id: str, a1: str) -> str:
    """Build an A1 range against the resolved tab, quoted to survive spaces/symbols."""
    title = _resolved_tab(spreadsheet_id).replace("'", "''")
    return f"'{title}'!{a1}"


# ---------------------------------------------------------------------------
# Normalization helpers (shared shape with coral_client app dicts)
# ---------------------------------------------------------------------------

def _skills_to_str(value) -> str:
    if isinstance(value, list):
        return ";".join(str(s).strip() for s in value if str(s).strip())
    return str(value or "")


def _row_to_cells(row: dict) -> list[str]:
    cells = []
    for col in COLUMNS:
        val = row.get(col, "")
        if col == "required_skills":
            val = _skills_to_str(val)
        cells.append("" if val is None else str(val))
    return cells


def _cells_to_row(header: list[str], cells: list[str]) -> dict:
    row = {}
    for i, key in enumerate(header):
        row[key] = cells[i] if i < len(cells) else ""
    # Normalize skills back to a list for downstream consumers.
    skills = row.get("required_skills", "")
    row["required_skills"] = [
        s.strip() for s in skills.replace(";", ",").split(",") if s.strip()
    ]
    return row


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def read_applications(spreadsheet_id: str | None = None) -> list[dict]:
    """Read the tracker sheet into dict rows, mapping the header row to columns."""
    sid = _spreadsheet_id(spreadsheet_id)
    rng = _rng(sid, "A1:Z10000")
    resp = (
        _service()
        .spreadsheets()
        .values()
        .get(spreadsheetId=sid, range=rng)
        .execute()
    )
    values = resp.get("values", [])
    if not values:
        return []
    header = [h.strip() for h in values[0]]
    rows = []
    for cells in values[1:]:
        if not any(str(c).strip() for c in cells):
            continue
        rows.append(_cells_to_row(header, cells))
    return rows


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def write_applications(rows: list[dict], spreadsheet_id: str | None = None) -> int:
    """Overwrite the tracker tab with header + rows. Returns rows written."""
    sid = _spreadsheet_id(spreadsheet_id)
    svc = _service().spreadsheets().values()
    body_rows = [COLUMNS] + [_row_to_cells(r) for r in rows]

    svc.clear(spreadsheetId=sid, range=_rng(sid, "A1:Z10000")).execute()
    svc.update(
        spreadsheetId=sid,
        range=_rng(sid, "A1"),
        valueInputOption="RAW",
        body={"values": body_rows},
    ).execute()
    return len(rows)


def append_applications(rows: list[dict], spreadsheet_id: str | None = None) -> int:
    """Append rows to the tracker, merging with what's already there by id.

    New ids are added; existing ids are left untouched so manual edits in the
    sheet win. Returns the count of newly appended rows.
    """
    sid = _spreadsheet_id(spreadsheet_id)
    existing = read_applications(sid)
    existing_ids = {r.get("id") for r in existing if r.get("id")}

    new_rows = [r for r in rows if r.get("id") not in existing_ids]
    if not new_rows:
        return 0

    _ensure_header(sid)
    _service().spreadsheets().values().append(
        spreadsheetId=sid,
        range=_rng(sid, "A1"),
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [_row_to_cells(r) for r in new_rows]},
    ).execute()
    return len(new_rows)


def _ensure_header(spreadsheet_id: str) -> None:
    svc = _service().spreadsheets().values()
    resp = svc.get(spreadsheetId=spreadsheet_id, range=_rng(spreadsheet_id, "A1:Z1")).execute()
    if not resp.get("values"):
        svc.update(
            spreadsheetId=spreadsheet_id,
            range=_rng(spreadsheet_id, "A1"),
            valueInputOption="RAW",
            body={"values": [COLUMNS]},
        ).execute()


# ---------------------------------------------------------------------------
# Sync sheet -> local CSV (the bridge Coral reads)
# ---------------------------------------------------------------------------

def sync_to_csv(spreadsheet_id: str | None = None, csv_path: Path | None = None) -> int:
    """Pull the sheet and write data/applications.csv for the Coral file source."""
    rows = read_applications(spreadsheet_id)
    path = csv_path or _csv_path()
    write_csv(rows, path)
    return len(rows)


def write_csv(rows: list[dict], csv_path: Path | None = None) -> Path:
    """Write app rows to the canonical CSV consumed by the Coral `sheets` source."""
    path = csv_path or _csv_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        for row in rows:
            writer.writerow(_row_to_cells(row))
    return path


def read_csv(csv_path: Path | None = None) -> list[dict]:
    """Read the canonical applications CSV (the file the Coral `sheets` source reads)."""
    path = csv_path or _csv_path()
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return []
    header = rows[0]
    return [_cells_to_row(header, cells) for cells in rows[1:] if any(cells)]


def append_to_csv(rows: list[dict], csv_path: Path | None = None) -> int:
    """Append rows directly to the local CSV, merging by id (no Google Sheet needed).

    This is the Sheet-free path: Gmail extraction -> applications.csv -> Coral
    `sheets.applications`. Existing ids are preserved so manual edits win.
    Returns the count of newly added rows.
    """
    path = csv_path or _csv_path()
    existing = read_csv(path)
    existing_ids = {r.get("id") for r in existing if r.get("id")}
    new_rows = [r for r in rows if r.get("id") not in existing_ids]
    if not new_rows:
        return 0
    write_csv(existing + new_rows, path)
    return len(new_rows)
