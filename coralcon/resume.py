"""Resume upload parsing and local profile storage."""

from __future__ import annotations

import json
import re
import zipfile
from html import unescape
from io import BytesIO
from pathlib import Path

from coralcon.paths import runs_dir
from coralcon.portfolio.inspector import _detect_skills


MAX_RESUME_BYTES = 2_500_000
MAX_TEXT_CHARS = 80_000
SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}
PROFILE_PATH = "resume_profile.json"


def parse_resume_upload(filename: str, content: bytes) -> dict:
    """Parse a resume upload into structured profile signals.

    The parser is intentionally dependency-light so uploads work in serverless
    deployments. DOCX is read from its XML package. PDF support is best-effort
    text extraction from uncompressed text fragments; users get a clear warning
    if the file needs conversion to text.
    """
    safe_name = Path(filename or "resume").name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("Upload a .pdf, .docx, .txt, or .md resume.")
    if len(content) > MAX_RESUME_BYTES:
        raise ValueError("Resume is too large. Upload a file under 2.5 MB.")
    if not content:
        raise ValueError("Resume file is empty.")

    text, warnings = _extract_text(suffix, content)
    text = _clean_text(text)[:MAX_TEXT_CHARS]
    if len(text) < 40:
        warnings.append("Very little text could be extracted. Try uploading a DOCX or TXT version.")

    profile = {
        "filename": safe_name,
        "file_type": suffix.lstrip("."),
        "text": text,
        "summary": _summary(text),
        "name": _extract_name(text),
        "email": _extract_email(text),
        "phone": _extract_phone(text),
        "links": _extract_links(text),
        "skills": _detect_skills(text.lower()),
        "sections": _section_presence(text),
        "warnings": warnings,
    }
    save_resume_profile(profile)
    return profile


def save_resume_profile(profile: dict) -> Path:
    path = runs_dir() / PROFILE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return path


def load_resume_profile() -> dict | None:
    path = runs_dir() / PROFILE_PATH
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def public_resume_profile(profile: dict | None = None) -> dict | None:
    profile = profile if profile is not None else load_resume_profile()
    if not profile:
        return None
    return {
        "filename": profile.get("filename", ""),
        "fileType": profile.get("file_type", ""),
        "summary": profile.get("summary", ""),
        "name": profile.get("name", ""),
        "email": profile.get("email", ""),
        "phone": profile.get("phone", ""),
        "links": profile.get("links", []),
        "skills": profile.get("skills", []),
        "sections": profile.get("sections", {}),
        "warnings": profile.get("warnings", []),
    }


def _extract_text(suffix: str, content: bytes) -> tuple[str, list[str]]:
    if suffix in {".txt", ".md"}:
        return content.decode("utf-8", errors="replace"), []
    if suffix == ".docx":
        return _extract_docx_text(content), []
    return _extract_pdf_text(content)


def _extract_docx_text(content: bytes) -> str:
    with zipfile.ZipFile(BytesIO(content)) as docx:
        xml = docx.read("word/document.xml").decode("utf-8", errors="replace")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<[^>]+>", " ", xml)
    return unescape(xml)


def _extract_pdf_text(content: bytes) -> tuple[str, list[str]]:
    raw = content.decode("latin-1", errors="ignore")
    fragments = re.findall(r"\(([^()]{1,2000})\)\s*Tj", raw)
    fragments.extend(" ".join(parts) for parts in re.findall(r"\[((?:\([^()]*\)\s*)+)\]\s*TJ", raw))
    text = " ".join(re.sub(r"[()]", " ", fragment) for fragment in fragments)
    if not text.strip():
        # Last-resort scan for readable runs in simple PDFs.
        text = " ".join(re.findall(r"[A-Za-z0-9@:/.,+#&() -]{4,}", raw))
    warnings = []
    if len(text.strip()) < 120:
        warnings.append("PDF text extraction was limited; DOCX or TXT gives better resume parsing.")
    return text, warnings


def _clean_text(value: str) -> str:
    value = value.replace("\x00", " ")
    return re.sub(r"[ \t\r\f\v]+", " ", re.sub(r"\n{3,}", "\n\n", value)).strip()


def _summary(text: str) -> str:
    lines = [line.strip(" -|") for line in text.splitlines() if line.strip()]
    useful = [line for line in lines if len(line) >= 20 and not _extract_email(line)]
    return " ".join(useful[:3])[:420]


def _extract_name(text: str) -> str:
    for line in text.splitlines()[:8]:
        cleaned = line.strip()
        if not cleaned or _extract_email(cleaned) or _extract_phone(cleaned):
            continue
        if 2 <= len(cleaned.split()) <= 5 and not re.search(r"\d|@", cleaned):
            return cleaned[:80]
    return ""


def _extract_email(text: str) -> str:
    match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else ""


def _extract_phone(text: str) -> str:
    match = re.search(r"(?:\+?\d[\d ().-]{7,}\d)", text)
    return match.group(0).strip() if match else ""


def _extract_links(text: str) -> list[str]:
    links = re.findall(r"https?://[^\s,)]+", text)
    links.extend(f"https://{item}" for item in re.findall(r"\b(?:github|linkedin)\.com/[^\s,)]+", text, re.I))
    seen = []
    for link in links:
        cleaned = link.rstrip(".,;")
        if cleaned not in seen:
            seen.append(cleaned)
    return seen[:12]


def _section_presence(text: str) -> dict:
    lowered = text.lower()
    return {
        "experience": bool(re.search(r"\b(experience|employment|work history)\b", lowered)),
        "projects": bool(re.search(r"\b(projects?|portfolio)\b", lowered)),
        "education": "education" in lowered,
        "skills": bool(re.search(r"\b(skills?|technologies|tools)\b", lowered)),
        "links": bool(_extract_links(text)),
    }
