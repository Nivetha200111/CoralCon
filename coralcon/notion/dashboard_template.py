"""Notion block templates for the CoralCon dashboard."""

from datetime import datetime


def build_dashboard_blocks(insights: dict) -> list[dict]:
    """Build compact Notion blocks from structured insights."""
    blocks = [
        _heading(f"CoralCon Career Dashboard - Last updated: {datetime.now().isoformat(timespec='minutes')}"),
        _paragraph(f"Career health score: {insights.get('overall_health_score', 0)}/100"),
        _heading("Key Metrics", level=2),
        _bullets(
            [
                f"Applications: {insights.get('total_applications', 0)}",
                f"Response rate: {insights.get('response_rate', 0)}%",
                f"Interview rate: {insights.get('interview_rate', 0)}%",
                f"Offer rate: {insights.get('offer_rate', 0)}%",
            ]
        ),
        _heading("Top Rejection Patterns", level=2),
        _bullets(
            [
                f"{row.get('role_title')}: {row.get('rejection_rate', 0)}% rejected across {row.get('total', 0)} applications"
                for row in insights.get("rejection_patterns", [])[:6]
            ]
        ),
        _heading("Skill Gaps", level=2),
        _bullets(
            [
                f"{row.get('skill')}: required in {row.get('times_required', 0)} rejections, priority {row.get('priority')}"
                for row in insights.get("skill_gaps", [])[:8]
            ]
        ),
        _heading("Follow-Up Priorities", level=2),
        _bullets(
            [
                f"{row.get('company')} - {row.get('role_title')}: {row.get('days_waiting')} days waiting ({row.get('priority')})"
                for row in insights.get("followup_priorities", [])[:8]
            ]
        ),
        _heading("Weekly Action Items", level=2),
        _bullets(insights.get("action_items", [])[:8]),
    ]

    if insights.get("llm_insights"):
        blocks.extend([_heading("AI Analysis", level=2), _paragraph(insights["llm_insights"])])

    return [block for block in blocks if block]


def _heading(text: str, level: int = 1) -> dict:
    block_type = "heading_1" if level == 1 else "heading_2"
    return {
        "object": "block",
        "type": block_type,
        block_type: {"rich_text": [_text(text)]},
    }


def _paragraph(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [_text(text[:1900])]},
    }


def _bullets(items: list[str]) -> list[dict] | None:
    cleaned = [str(item) for item in items if item]
    if not cleaned:
        return None
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [_text(cleaned[0][:1900])],
            "children": [
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [_text(item[:1900])]},
                }
                for item in cleaned[1:]
            ],
        },
    }


def _text(content: str) -> dict:
    return {"type": "text", "text": {"content": content}}
