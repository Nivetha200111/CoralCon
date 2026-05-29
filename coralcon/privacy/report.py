"""Local-first privacy report generation."""

from pathlib import Path


def build_privacy_report() -> str:
    return "\n".join(
        [
            "# Local-First Privacy Report",
            "",
            "- CoralCon is designed to query raw source data locally through Coral SQL.",
            "- Reads from GitHub, Google Sheets, and LinkedIn should go through Coral in real mode.",
            "- The LinkedIn path uses user-provided GDPR export data; no scraping is required.",
            "- Credentials are read from environment variables or local config.",
            "- local dashboard outputs are optional and only publish dashboard/action outputs.",
            "- If LLM analysis is enabled, summarized query results may be sent to the configured LLM provider.",
            "- Sample mode works without API keys and keeps all data local.",
            "- Reports are written locally to `runs/latest` and `submission`.",
        ]
    )


def write_privacy_report() -> Path:
    path = Path("submission") / "PRIVACY_REPORT.md"
    path.parent.mkdir(exist_ok=True)
    path.write_text(build_privacy_report(), encoding="utf-8")
    return path
