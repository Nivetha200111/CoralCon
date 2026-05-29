"""Dashboard agent: returns local dashboard guidance."""


class DashboardAgent:
    """Prepare dashboard results for the local web UI."""

    def __init__(self):
        pass

    def update(self, insights: dict, dry_run: bool | None = None) -> dict:
        return {
            "updated": False,
            "url": None,
            "message": "Use `coralcon serve` for the local dashboard.",
        }
