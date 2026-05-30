"""Infer the skills a role demands from its title.

Rejection emails carry the role title but not its skill requirements, so the
flagship skill-gap join had nothing to match on. This module maps a job title to
a deterministic set of canonical skills (no LLM, fully reproducible) using the
same skill vocabulary that shows up in `linkedin.skills` and
`github.user_repos.language`, so the cross-source join produces a true signal:
"this skill is demanded by N rejected roles but absent from your profile."
"""

from __future__ import annotations

import re
from pathlib import Path

# Ordered most-specific -> most-generic. Each pattern is a compiled regex tested
# against the lower-cased role title; matches accumulate (deduped, order kept).
# Short/ambiguous tokens (java, go, ai, ml, bi, js, sre, c#) use word boundaries
# so "java" never fires on "javascript" and "go" never fires on "google".
_RULES: list[tuple[re.Pattern[str], list[str]]] = [
    (re.compile(r"\breact\b"), ["React", "JavaScript", "TypeScript"]),
    (re.compile(r"\bvue\b|vue\.js"), ["Vue.js", "JavaScript"]),
    (re.compile(r"\bangular\b"), ["Angular", "TypeScript"]),
    (re.compile(r"\bnode\b|node\.js"), ["Node.js", "JavaScript"]),
    (re.compile(r"front[\s-]?end"), ["JavaScript", "React", "CSS"]),
    (re.compile(r"full[\s-]?stack"), ["JavaScript", "React", "Node.js", "SQL"]),
    (re.compile(r"back[\s-]?end"), ["Python", "SQL", "API Design"]),
    (re.compile(r"\bjavascript\b|\bjs\b"), ["JavaScript", "TypeScript"]),
    (re.compile(r"typescript"), ["TypeScript", "JavaScript"]),
    (re.compile(r"\bjava\b"), ["Java", "Spring", "SQL"]),
    (re.compile(r"\bpython\b"), ["Python", "SQL"]),
    (re.compile(r"\bgo(?:lang)?\b"), ["Go"]),
    (re.compile(r"c#|\.net|dotnet"), ["C#", ".NET", "SQL"]),
    (re.compile(r"data engineer"), ["Python", "SQL", "ETL", "Spark"]),
    (re.compile(r"data scien"), ["Python", "Machine Learning", "SQL", "Statistics"]),
    (re.compile(r"data analy"), ["SQL", "Python", "Data Visualization", "Excel"]),
    (re.compile(r"business intelligence|\bbi\b|power bi"), ["SQL", "Power BI", "Data Visualization"]),
    (re.compile(r"business analy"), ["SQL", "Requirements Analysis", "Excel"]),
    (re.compile(r"machine learning|\bml\b|ai/ml|\bml/ai\b"), ["Python", "Machine Learning", "PyTorch", "TensorFlow"]),
    (re.compile(r"\bai\b|artificial intelligence|generative ai|\bgenai\b"), ["Python", "Machine Learning", "Generative AI"]),
    (re.compile(r"devops|\bsre\b|site reliability"), ["Docker", "Kubernetes", "CI/CD", "Linux"]),
    (re.compile(r"\bcloud\b|aws|azure|\bgcp\b"), ["AWS", "Docker", "Kubernetes"]),
    (re.compile(r"android|kotlin"), ["Kotlin", "Android"]),
    (re.compile(r"\bios\b|swift"), ["Swift", "iOS"]),
    (re.compile(r"flutter|\bmobile\b"), ["Dart", "Flutter"]),
    (re.compile(r"solution engineer|sales engineer|solutions architect"), ["SQL", "Cloud Computing", "Communication"]),
]

# Generic software roles that match nothing specific still demand fundamentals.
_GENERIC_SOFTWARE = re.compile(
    r"software|engineer|developer|\bsde\b|programmer|\bsystem\b|technology|\bit\b"
)
_GENERIC_SKILLS = ["Python", "Java", "SQL", "Data Structures"]

_MAX_SKILLS = 6


def infer_required_skills(role_title: str, notes: str = "") -> list[str]:
    """Return the canonical skills a role title implies (deterministic, deduped)."""
    text = f"{role_title or ''} {notes or ''}".lower()
    if not text.strip():
        return []

    skills: list[str] = []
    for pattern, mapped in _RULES:
        if pattern.search(text):
            for skill in mapped:
                if skill not in skills:
                    skills.append(skill)

    if not skills and _GENERIC_SOFTWARE.search(text):
        skills = list(_GENERIC_SKILLS)

    return skills[:_MAX_SKILLS]


def enrich_rows(rows: list[dict], *, overwrite: bool = False) -> int:
    """Fill `required_skills` on application rows in place from their titles.

    Skips rows that already have skills unless `overwrite=True`. `required_skills`
    is left as a list; the sheets client serializes it with ';' on write.
    Returns the number of rows that gained skills.
    """
    enriched = 0
    for row in rows:
        existing = row.get("required_skills")
        if isinstance(existing, str):
            has = bool(existing.strip())
        else:
            has = bool(existing)
        if has and not overwrite:
            continue
        inferred = infer_required_skills(row.get("role_title", ""), row.get("notes", ""))
        if inferred:
            row["required_skills"] = inferred
            enriched += 1
    return enriched


def enrich_csv(csv_path: Path | None = None, *, overwrite: bool = False) -> int:
    """Backfill required_skills in the applications CSV the Coral sheets source reads.

    Returns the number of rows enriched.
    """
    # Imported here to avoid a circular import at module load.
    from coralcon.sheets.client import read_csv, write_csv

    rows = read_csv(csv_path)
    enriched = enrich_rows(rows, overwrite=overwrite)
    if enriched:
        write_csv(rows, csv_path)
    return enriched
