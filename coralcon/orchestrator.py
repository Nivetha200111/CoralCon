"""Phase 2 orchestrator for the CoralCon multi-agent pipeline."""

from coralcon.agents.action import ActionAgent
from coralcon.agents.analyst import AnalystAgent
from coralcon.agents.dashboard import DashboardAgent
from coralcon.agents.recon import ReconAgent


class CoralConOrchestrator:
    """Coordinate Recon, Analyst, Dashboard, and Action agents."""

    def __init__(
        self,
        recon: ReconAgent | None = None,
        analyst: AnalystAgent | None = None,
        dashboard: DashboardAgent | None = None,
        action: ActionAgent | None = None,
    ):
        self.recon = recon or ReconAgent()
        self.analyst = analyst or AnalystAgent()
        self.dashboard = dashboard or DashboardAgent()
        self.action = action or ActionAgent()

    def run_recon(self) -> dict:
        return self.recon.fetch_all()

    def run_insights(self, use_ai: bool = True) -> dict:
        raw_data = self.run_recon()
        return self.analyst.analyze(raw_data, use_ai=use_ai)

    def run_dashboard(self, use_ai: bool = True, dry_run: bool | None = None) -> dict:
        insights = self.run_insights(use_ai=use_ai)
        dashboard = self.dashboard.update(insights, dry_run=dry_run)
        return {"insights": insights, "dashboard": dashboard}

    def run_actions(self, use_ai: bool = True, dry_run: bool | None = None) -> dict:
        insights = self.run_insights(use_ai=use_ai)
        tasks = self.action.create_tasks(insights, dry_run=dry_run)
        return {"insights": insights, "tasks": tasks}

    def run_full_analysis(
        self,
        use_ai: bool = True,
        write_dashboard: bool = True,
        create_actions: bool = True,
        dry_run: bool | None = None,
    ) -> dict:
        raw_data = self.run_recon()
        insights = self.analyst.analyze(raw_data, use_ai=use_ai)
        dashboard = (
            self.dashboard.update(insights, dry_run=dry_run)
            if write_dashboard
            else {"updated": False, "url": None, "message": "Skipped."}
        )
        tasks = (
            self.action.create_tasks(insights, dry_run=dry_run)
            if create_actions
            else []
        )

        return {
            "raw_data": raw_data,
            "insights": insights,
            "dashboard": dashboard,
            "tasks_created": sum(1 for task in tasks if task.get("created")),
            "tasks": tasks,
        }
