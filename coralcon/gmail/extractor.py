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

from coralcon.enrich.skill_inference import infer_required_skills
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

# ATS / email-infra tokens that are never the hiring company.
_ATS_TOKENS = {
    "greenhouse", "lever", "workday", "myworkday", "myworkdayjobs", "ashby",
    "ashbyhq", "smartrecruiters", "icims", "taleo", "successfactors", "jobvite",
    "bamboohr", "rippling", "gem", "eightfold", "phenom", "avature", "teamtailor",
    "mail", "email", "mailer", "notifications", "notification", "noreply",
    "no-reply", "donotreply", "do-not-reply", "hello", "info", "talent",
    "careers", "recruiting", "jobs", "wd1", "wd3", "wd5", "us", "eu",
}

# Recruiting noise words to strip from a sender display name.
_COMPANY_NOISE = re.compile(
    r"\b(recruit(?:ing|ment)?|talent(?:s)?|acquisition|careers?|team|hiring|"
    r"no-?reply|do-?not-?reply|jobs?|hr|people|staffing|notifications?|mailer|"
    r"global|partners?|bootcamp|actions?|inc|llc|ltd|the)\b",
    flags=re.IGNORECASE,
)


def _is_ats_label(label: str) -> bool:
    low = label.lower()
    return any(tok in low for tok in _ATS_TOKENS)


def _titlecase_company(text: str) -> str:
    """Title-case, but keep short all-caps acronyms (IBM, SAP) intact."""
    out = []
    for word in text.split():
        if word.isupper() and len(word) <= 4:
            out.append(word)
        else:
            out.append(word[:1].upper() + word[1:])
    return " ".join(out)


def _clean_company(text: str) -> str:
    text = _COMPANY_NOISE.sub(" ", text)
    text = re.sub(r"[^A-Za-z0-9&.\- ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" ,-|.&")
    return _titlecase_company(text) if text else ""


def _company_from_sender(from_header: str) -> str:
    """Best-effort hiring-company name from a From header.

    'Stripe Recruiting <jobs@stripe.com>'        -> 'Stripe'
    'Logitech via Workday <no-reply@myworkday>'  -> 'Logitech'
    'careers@scale.com'                          -> 'Scale'
    Falls back to 'Unknown' rather than emitting an ATS vendor or noise.
    """
    name, addr = parseaddr(from_header)
    # "Logitech via Workday" / "Acme (Greenhouse)" -> take the company part.
    name = re.split(r"\s+via\s+|\s*\(", name or "", maxsplit=1)[0]
    cleaned = _clean_company(name)
    if cleaned and not _is_ats_label(cleaned):
        return cleaned

    # Fall back to the email domain, skipping ATS / infra labels.
    domain = addr.split("@")[-1].lower() if "@" in addr else ""
    tlds = {"com", "org", "net", "io", "co", "ai", "dev", "app", "us", "www"}
    labels = [l for l in domain.split(".") if l and l not in tlds]
    for label in labels:  # most-specific subdomain first (company.wd5.myworkday…)
        if not _is_ats_label(label):
            return _titlecase_company(label)
    # Nothing but ATS/infra signal anywhere — don't mislabel it as the vendor.
    return "Unknown"


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


_ROLE_KEYWORD = (
    r"(?:Engineer|Developer|Designer|Manager|Analyst|Scientist|Architect|"
    r"Consultant|Specialist|Administrator|Programmer|Researcher|Intern|"
    r"Internship|Associate|Trainee|Lead|Director|SDE|SDET)"
)
# Leading boilerplate to peel off a captured phrase.
_ROLE_PREFIX = re.compile(
    r"^(?:your|our|the|a|an|for|to|application|position|role|update|regarding|"
    r"thank|thanks|you|we|re)\s+",
    flags=re.IGNORECASE,
)


def _role_from_subject(subject: str) -> str:
    """Pull a concise role title from the subject line, else empty.

    Captures up to a few Capitalized words ending in a role keyword (so we get
    'Backend Engineer', not the whole 'Your application for our ...' sentence).
    Returns "" when nothing plausible is found — a blank role beats garbage.
    """
    s = re.sub(r"^(?:re|fw|fwd):\s*", "", subject or "", flags=re.IGNORECASE)
    m = re.search(rf"((?:[A-Z][A-Za-z0-9+/.#&-]*\s+){{0,4}}{_ROLE_KEYWORD})\b", s)
    if not m:
        return ""
    role = m.group(1).strip()
    # Drop any leading boilerplate words that slipped into the capture.
    prev = None
    while role != prev:
        prev = role
        role = _ROLE_PREFIX.sub("", role).strip(" ,-")
    role = re.sub(r"\s+", " ", role).strip(" ,-")
    return role if 0 < len(role) <= 50 else ""


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
        "For each email return:\n"
        "- company: the HIRING company in Title Case (e.g. 'Stripe', 'Louis Vuitton'). "
        "Never the ATS vendor or mail infra (Greenhouse, Lever, Workday, myworkday, "
        "Rippling, iCIMS, SmartRecruiters). If 'X via Workday', the company is X. "
        "If you genuinely cannot tell, use 'Unknown'.\n"
        "- role_title: a CONCISE job title only (e.g. 'Backend Engineer', 'Data "
        "Analyst Intern') — never a sentence or the email subject. Empty string if "
        "no specific role is named.\n"
        "- status: exactly one of rejected, interviewing, offer, applied.\n"
        "Most of these are rejections. If an email is clearly NOT a job-application "
        'outcome (newsletter, course ad, job alert digest), set status to "skip".\n\n'
        f"EMAILS:\n{json.dumps(compact, indent=2)}\n\n"
        'Respond with ONLY a JSON array, one object per email, like:\n'
        '[{"i":0,"company":"Stripe","role_title":"Backend Engineer","status":"rejected"}]'
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
    notes = msg["subject"][:160]
    return {
        "id": f"gmail_{msg['id'][:12]}",
        "company": company,
        "role_title": role_title,
        "status": status,
        "applied_date": "",  # unknown from a rejection email; user can backfill
        "responded_date": _iso_date(msg["date"]),
        # Rejection emails don't list the role's skills, so infer them from the
        # title; this is what the cross-source skill-gap query joins on.
        "required_skills": infer_required_skills(role_title, notes),
        "salary_range": "",
        "source": "Gmail",
        "notes": notes,
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
