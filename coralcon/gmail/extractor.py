"""
Gmail rejection extractor.

Why this lives outside Coral: the Coral Gmail source is discovery-only — it
returns message ids/snippets but never the From / Subject / Date headers, so it
can't tell you who rejected you. This module talks to the Gmail API directly
(read-only OAuth) to pull those headers, then classifies each email into a
structured application row that gets written to your Google Sheet (which Coral
then queries via the `sheets` file source).

Pipeline:
    Gmail search (q) -> message metadata (From/Subject/Date/snippet)
        -> classify (LLM if ANTHROPIC_API_KEY, else keyword heuristics)
        -> application rows: {company, role_title, status, responded_date, ...}

Nothing here runs in sample mode; the demo data already ships as rows.
"""

from __future__ import annotations

import base64
import json
import os
import re
from datetime import datetime, timezone
from email.utils import parseaddr, parsedate_to_datetime

from coralcon.google.auth import get_credentials

# Gmail search that surfaces likely rejection / decision emails. Tunable via env.
DEFAULT_QUERY = (
    'subject:(application OR position OR role OR candidacy) '
    '("unfortunately" OR "we regret" OR "not moving forward" OR '
    '"other candidates" OR "decided not to" OR "will not be moving" OR '
    '"won\'t be moving forward" OR "no longer being considered" OR '
    '"pursue other applicants")'
)

# Cheap, dependency-free signal used both to pre-filter and as LLM fallback.
_REJECTION_MARKERS = [
    "unfortunately",
    "we regret",
    "regret to inform",
    "not moving forward",
    "won't be moving forward",
    "will not be moving forward",
    "other candidates",
    "other applicants",
    "decided not to",
    "no longer being considered",
    "not be progressing",
    "not selected",
    "position has been filled",
]


def _service():
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "google-api-python-client is required. Install with:\n"
            "    pip install google-api-python-client"
        ) from exc
    return build("gmail", "v1", credentials=get_credentials(), cache_discovery=False)


# ---------------------------------------------------------------------------
# Gmail fetch
# ---------------------------------------------------------------------------

def _list_message_ids(svc, query: str, max_results: int) -> list[str]:
    ids: list[str] = []
    page_token = None
    while len(ids) < max_results:
        resp = (
            svc.users()
            .messages()
            .list(
                userId="me",
                q=query,
                maxResults=min(100, max_results - len(ids)),
                pageToken=page_token,
            )
            .execute()
        )
        ids.extend(m["id"] for m in resp.get("messages", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return ids[:max_results]


def _fetch_message(svc, msg_id: str) -> dict:
    """Fetch a message with headers + snippet (metadata format, no full body)."""
    msg = (
        svc.users()
        .messages()
        .get(
            userId="me",
            id=msg_id,
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        )
        .execute()
    )
    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    return {
        "id": msg_id,
        "from": headers.get("from", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "snippet": msg.get("snippet", ""),
    }


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _company_from_sender(from_header: str) -> str:
    """Best-effort company name from a From header.

    'Stripe Recruiting <jobs@stripe.com>' -> 'Stripe'
    'careers@scale.com'                   -> 'Scale'
    """
    name, addr = parseaddr(from_header)
    if name:
        cleaned = re.sub(
            r"\b(recruiting|recruitment|talent|careers?|team|hiring|noreply|no-reply|jobs|hr)\b",
            "",
            name,
            flags=re.IGNORECASE,
        ).strip(" ,-|")
        if cleaned:
            return cleaned
    domain = addr.split("@")[-1] if "@" in addr else ""
    domain = re.sub(
        r"^(mail|email|jobs|careers|recruiting|talent|notifications?|no-?reply)\.",
        "",
        domain,
    )
    base = domain.split(".")[0] if domain else ""
    # Strip ATS vendors so we don't label everything "Greenhouse".
    if base.lower() in {"greenhouse", "lever", "myworkday", "workday", "ashbyhq", "ashby", "smartrecruiters", "icims"}:
        return name or base.title()
    return base.title()


def _iso_date(date_header: str) -> str:
    try:
        dt = parsedate_to_datetime(date_header)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError):
        return datetime.now(timezone.utc).date().isoformat()


def _looks_like_rejection(text: str) -> bool:
    low = text.lower()
    return any(marker in low for marker in _REJECTION_MARKERS)


def _role_from_subject(subject: str) -> str:
    """Pull a plausible role title out of the subject line, else empty."""
    m = re.search(
        r"(?:for|the|your)\s+(?:the\s+)?([A-Z][A-Za-z/ ]*?(?:Engineer|Developer|Designer|Manager|Analyst|Scientist|Intern|Lead))",
        subject,
    )
    if m:
        return m.group(1).strip()
    m = re.search(r"\b([A-Za-z/ ]*?(?:Engineer|Developer|Designer|Manager|Analyst|Scientist))\b", subject)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def _classify_with_llm(messages: list[dict]) -> list[dict] | None:
    """Use Claude to extract company/role/status. Returns None if unavailable."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    try:
        from coralcon.agents.analyzer import _get_client
    except Exception:
        return None

    try:
        client = _get_client()
    except RuntimeError:
        return None

    compact = [
        {"i": idx, "from": m["from"], "subject": m["subject"], "snippet": m["snippet"][:300]}
        for idx, m in enumerate(messages)
    ]
    prompt = (
        "You extract structured job-application outcomes from recruiting emails.\n"
        "For each email, return the hiring COMPANY (not the ATS vendor like "
        "Greenhouse/Lever/Workday), the ROLE title if present, and a STATUS of "
        "exactly one of: rejected, interviewing, offer, applied.\n"
        "Most of these are rejections. If an email is clearly NOT about a job "
        'application outcome, set status to "skip".\n\n'
        f"EMAILS:\n{json.dumps(compact, indent=2)}\n\n"
        'Respond with ONLY a JSON array, one object per email, like:\n'
        '[{"i":0,"company":"Stripe","role_title":"React Frontend Engineer","status":"rejected"}]'
    )
    try:
        resp = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        parsed = json.loads(text)
    except Exception:
        return None

    by_index = {item.get("i"): item for item in parsed if isinstance(item, dict)}
    rows = []
    for idx, msg in enumerate(messages):
        info = by_index.get(idx, {})
        status = str(info.get("status", "")).lower().strip()
        if status == "skip":
            continue
        rows.append(
            _build_row(
                msg,
                company=info.get("company") or _company_from_sender(msg["from"]),
                role_title=info.get("role_title") or _role_from_subject(msg["subject"]),
                status=status or "rejected",
            )
        )
    return rows


def _classify_with_heuristics(messages: list[dict]) -> list[dict]:
    rows = []
    for msg in messages:
        if not _looks_like_rejection(f"{msg['subject']} {msg['snippet']}"):
            continue
        rows.append(
            _build_row(
                msg,
                company=_company_from_sender(msg["from"]),
                role_title=_role_from_subject(msg["subject"]),
                status="rejected",
            )
        )
    return rows


def _build_row(msg: dict, company: str, role_title: str, status: str) -> dict:
    return {
        "id": f"gmail_{msg['id'][:12]}",
        "company": company,
        "role_title": role_title,
        "status": status,
        "applied_date": "",  # unknown from a rejection email; user can backfill
        "responded_date": _iso_date(msg["date"]),
        "required_skills": [],
        "salary_range": "",
        "source": "Gmail",
        "notes": msg["subject"][:160],
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def extract_rejections(query: str | None = None, max_results: int = 50, use_ai: bool = True) -> list[dict]:
    """Search Gmail and return classified application rows (mostly rejections).

    Each row matches the Sheets/Coral `applications` schema so it can be written
    straight to the tracker sheet.
    """
    svc = _service()
    q = query or os.getenv("GMAIL_REJECTION_QUERY") or DEFAULT_QUERY
    ids = _list_message_ids(svc, q, max_results)
    messages = [_fetch_message(svc, mid) for mid in ids]
    if not messages:
        return []

    rows = None
    if use_ai:
        rows = _classify_with_llm(messages)
    if rows is None:
        rows = _classify_with_heuristics(messages)

    # De-dupe by (company, role, responded_date).
    seen = set()
    unique = []
    for row in rows:
        key = (row["company"].lower(), row["role_title"].lower(), row["responded_date"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique
