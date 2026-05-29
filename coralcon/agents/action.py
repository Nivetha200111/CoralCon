"""Action agent: converts insights into local action tasks."""

from datetime import date, timedelta


class ActionAgent:
    """Create or preview prioritized action tasks."""

    def __init__(self):
        pass

    def create_tasks(self, insights: dict, dry_run: bool | None = None) -> list[dict]:
        return self._build_tasks(insights)

    def _build_tasks(self, insights: dict) -> list[dict]:
        tasks = []
        for item in insights.get("action_items", []):
            tasks.append(
                {
                    "title": item,
                    "priority": "High",
                    "deadline": self._deadline(7),
                    "category": self._category_for(item),
                    "impact": self._impact_for(item),
                    "status": "Not Started",
                    "created": False,
                }
            )

        for followup in insights.get("followup_priorities", [])[:5]:
            if followup.get("priority") != "hot":
                continue
            tasks.append(
                {
                    "title": f"Follow up with {followup.get('company')} about {followup.get('role_title')}",
                    "priority": "High",
                    "deadline": self._deadline(1),
                    "category": "follow_up",
                    "impact": "Follow-ups in the 7-14 day window have the highest response odds.",
                    "status": "Not Started",
                    "created": False,
                }
            )

        return tasks[:10]

    @staticmethod
    def _deadline(days: int) -> str:
        return (date.today() + timedelta(days=days)).isoformat()

    @staticmethod
    def _category_for(text: str) -> str:
        lowered = text.lower()
        if "follow-up" in lowered or "follow up" in lowered:
            return "follow_up"
        if "github" in lowered or "commit" in lowered:
            return "profile_fix"
        if "project" in lowered or "skill" in lowered:
            return "skill_gap"
        return "application_strategy"

    @staticmethod
    def _impact_for(text: str) -> str:
        if "response rate" in text:
            return "Improves response-rate odds based on historical application outcomes."
        if "ghost rate" in text:
            return "Reduces ghosting risk by strengthening recruiter-visible signals."
        return "Targets the highest-impact weakness detected in the analysis."
