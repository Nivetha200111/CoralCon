"""Deterministic portfolio URL inspection."""

from __future__ import annotations

import os
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx


SKILL_KEYWORDS = {
    "aws": ["aws", "amazon web services", "lambda", "ec2", "s3"],
    "angular": ["angular"],
    "azure": ["azure"],
    "ci/cd": ["ci/cd", "github actions", "gitlab ci", "continuous integration"],
    "cassandra": ["cassandra"],
    "cobol": ["cobol"],
    "db2": ["db2"],
    "docker": ["docker"],  # "container" matched Tailwind's `container` class
    "figma": ["figma"],
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "flutter": ["flutter"],
    "gcp": ["gcp", "google cloud"],
    "git": ["git", "github"],
    "gliderecord": ["gliderecord"],
    "graphql": ["graphql"],
    "jcl": ["jcl"],
    "java": ["java", "spring boot"],
    "javascript": ["javascript", "node.js", "nodejs"],
    "kubernetes": ["kubernetes", "k8s"],
    "llm": ["llm", "llama", "llama3"],
    "machine learning": ["machine learning", "tensorflow", "pytorch"],  # bare "ml" hit `ml-4`
    "mysql": ["mysql"],
    "next.js": ["next.js", "nextjs"],
    "nlp": ["nlp"],
    "node.js": ["node.js", "nodejs"],
    "openai": ["openai", "openai api"],
    "pandas": ["pandas"],
    "postman": ["postman"],
    "power bi": ["power bi", "powerbi"],
    "postgresql": ["postgresql", "postgres", "sql"],
    "python": ["python", "django", "flask"],
    "react": ["react", "react.js", "reactjs"],
    "redis": ["redis"],
    "rest apis": ["rest api", "rest apis", "restful"],  # bare "api" is too noisy
    "servicenow": ["servicenow"],
    "sql": ["sql"],
    "system design": ["system design", "distributed system", "distributed systems"],
    "terraform": ["terraform"],
    "typescript": ["typescript"],  # bare "ts" is too noisy
    "vercel": ["vercel"],
}

MAX_HTML_BYTES = 500_000
MAX_TEXT_CHARS = 18_000


def inspect_portfolio(url: str | None = None) -> dict:
    """Fetch and summarize a public portfolio page without using AI."""
    raw_url = (url or os.getenv("PORTFOLIO_URL") or "").strip()
    if not raw_url:
        return {
            "url": None,
            "configured": False,
            "reachable": False,
            "status_code": None,
            "title": "",
            "description": "",
            "detected_skills": [],
            "project_links": [],
            "github_links": [],
            "external_links": [],
            "text_sample": "",
            "error": "Set PORTFOLIO_URL or pass --portfolio-url.",
        }

    normalized_url = _normalize_url(raw_url)
    try:
        with httpx.Client(
            timeout=httpx.Timeout(8.0, connect=4.0),
            follow_redirects=True,
            headers={"User-Agent": "CoralCon portfolio inspector/0.1"},
        ) as client:
            response = client.get(normalized_url)
    except httpx.HTTPError as exc:
        return _error_result(normalized_url, str(exc))

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        return _error_result(
            str(response.url),
            f"Expected HTML, received {content_type or 'unknown content type'}.",
            response.status_code,
        )

    html = response.content[:MAX_HTML_BYTES].decode(response.encoding or "utf-8", errors="replace")
    parser = _PortfolioHTMLParser()
    parser.feed(html)

    visible_text = _clean_text(" ".join(parser.text_parts))[:MAX_TEXT_CHARS]
    embedded_text = _extract_embedded_text(" ".join(parser.embedded_parts))[:MAX_TEXT_CHARS]
    searchable_text = " ".join([parser.title, parser.description, visible_text, embedded_text]).lower()
    links = _classify_links(str(response.url), parser.links)
    embedded_links = _classify_links(str(response.url), _extract_embedded_links(" ".join(parser.embedded_parts)))
    links = {
        "project_links": _merge_links(links["project_links"], embedded_links["project_links"]),
        "github_links": _merge_links(links["github_links"], embedded_links["github_links"]),
        "external_links": _merge_links(links["external_links"], embedded_links["external_links"]),
    }

    return {
        "url": str(response.url),
        "configured": True,
        "reachable": response.is_success,
        "status_code": response.status_code,
        "title": parser.title,
        "description": parser.description,
        "detected_skills": _detect_skills(searchable_text),
        "project_links": links["project_links"],
        "github_links": links["github_links"],
        "external_links": links["external_links"],
        "text_sample": (visible_text or embedded_text)[:900],
        "error": "" if response.is_success else f"HTTP {response.status_code}",
    }


class _PortfolioHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.links: list[dict] = []
        self.text_parts: list[str] = []
        self.embedded_parts: list[str] = []
        self._skip_depth = 0
        self._script_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        tag = tag.lower()
        if tag in {"style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag == "script":
            self._script_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            name = (attrs_dict.get("name") or attrs_dict.get("property") or "").lower()
            if name in {"description", "og:description", "twitter:description"} and not self.description:
                self.description = _clean_text(attrs_dict.get("content", ""))
        if tag == "a" and attrs_dict.get("href"):
            self.links.append(
                {
                    "href": attrs_dict["href"],
                    "label": _clean_text(attrs_dict.get("aria-label") or attrs_dict.get("title", "")),
                }
            )

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "script" and self._script_depth:
            self._script_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._script_depth:
            self.embedded_parts.append(data[:120_000])
            return
        if self._skip_depth:
            return
        text = _clean_text(data)
        if not text:
            return
        if self._in_title:
            self.title = _clean_text(f"{self.title} {text}")[:180]
        else:
            self.text_parts.append(text)

    def handle_comment(self, data: str) -> None:
        self.embedded_parts.append(data[:120_000])


def _normalize_url(url: str) -> str:
    if not urlparse(url).scheme:
        return f"https://{url}"
    return url


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _extract_embedded_text(value: str) -> str:
    quoted = re.findall(r"""["'`]([^"'`]{2,160})["'`]""", value)
    useful = [
        item
        for item in quoted
        if not item.startswith(("http", "data:", "#", "./", "../"))
        and not re.search(r"[{}<>;=]", item)
    ]
    return _clean_text(" ".join(useful))


def _extract_embedded_links(value: str) -> list[dict]:
    links = []
    for url in re.findall(r"https?://[^\s\"'`<>]+", value):
        links.append({"href": url.rstrip("),]};"), "label": ""})
    return links


def _detect_skills(text: str) -> list[str]:
    detected = []
    padded = f" {text} "
    for skill, aliases in SKILL_KEYWORDS.items():
        if any(_contains_alias(padded, alias) for alias in aliases):
            detected.append(skill)
    return sorted(detected, key=str.casefold)


def _contains_alias(text: str, alias: str) -> bool:
    escaped = re.escape(alias.lower())
    return re.search(rf"(?<![a-z0-9+#]){escaped}(?![a-z0-9+#])", text) is not None


def _classify_links(base_url: str, links: list[dict]) -> dict:
    base_host = urlparse(base_url).netloc.lower()
    project_links = []
    github_links = []
    external_links = []
    seen: set[str] = set()

    for link in links:
        href = link.get("href", "")
        if href.startswith(("mailto:", "tel:", "#", "javascript:")):
            continue
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"} or absolute in seen:
            continue
        seen.add(absolute)
        item = {"url": absolute, "label": link.get("label", "")[:80]}
        host = parsed.netloc.lower()
        path = parsed.path.lower()
        is_github = "github.com" in host
        is_project_host = host.endswith("vercel.app") or host.endswith("netlify.app") or host.endswith("github.io")
        if is_github:
            github_links.append(item)
        elif host != base_host:
            external_links.append(item)
        if (
            any(marker in f"{path} {item['label'].lower()}" for marker in ("project", "work", "case-study", "case study", "portfolio"))
            or is_project_host
            or (is_github and len([part for part in path.split("/") if part]) >= 2)
        ):
            project_links.append(item)

    return {
        "project_links": project_links[:12],
        "github_links": github_links[:12],
        "external_links": external_links[:12],
    }


def _merge_links(*groups: list[dict]) -> list[dict]:
    merged = []
    seen = set()
    for group in groups:
        for item in group:
            url = item.get("url")
            if url and url not in seen:
                seen.add(url)
                merged.append(item)
    return merged[:12]


def _error_result(url: str, error: str, status_code: int | None = None) -> dict:
    return {
        "url": url,
        "configured": True,
        "reachable": False,
        "status_code": status_code,
        "title": "",
        "description": "",
        "detected_skills": [],
        "project_links": [],
        "github_links": [],
        "external_links": [],
        "text_sample": "",
        "error": error,
    }
