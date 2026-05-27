"""Dashboard agent: publishes structured insights to Notion when configured."""

from coralcon.notion.client import NotionWriteClient


class DashboardAgent:
    """Update the Notion dashboard or return local dashboard guidance."""

    def __init__(self, notion_client: NotionWriteClient | None = None):
        self.notion = notion_client or NotionWriteClient()

    def update(self, insights: dict, dry_run: bool | None = None) -> dict:
        should_write = self.notion.is_configured("dashboard") if dry_run is None else not dry_run

        if not should_write:
            return {
                "updated": False,
                "url": None,
                "message": "Notion dashboard is not configured. Use `coralcon serve` for the local dashboard.",
            }

        try:
            result = self.notion.update_dashboard(insights)
            return {
                "updated": True,
                "url": result.get("url"),
                "message": "Notion dashboard updated.",
            }
        except Exception as exc:
            return {
                "updated": False,
                "url": None,
                "message": str(exc),
            }
