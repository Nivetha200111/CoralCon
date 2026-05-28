"""Analyst agent: turns raw Recon data into structured insights."""

import json
from pathlib import Path

from coralcon.agents import analyzer, recommender
from coralcon.agents.rule_based_analyst import build_evidence_insights
from coralcon.proof.query_logger import get_query_log


class AnalystAgent:
    """Generate rule-based insights, with optional Claude narrative analysis."""

    def analyze(self, raw_data: dict, use_ai: bool = True) -> dict:
        patterns = raw_data.get("rejection_patterns", [])
        github_rows = raw_data.get("github_correlation", [])
        gaps = raw_data.get("skill_gaps", [])
        timing = raw_data.get("timing", [])
        followups = raw_data.get("followups", [])
        portfolio = raw_data.get("portfolio", {})
        gaps = self._merge_portfolio_evidence(gaps, portfolio)

        totals = self._totals(patterns)
        github_signal = recommender.compute_github_signal(github_rows, github_rows)
        action_items = recommender.generate_action_items(
            patterns,
            gaps,
            github_signal,
            timing,
            len(followups),
            portfolio,
        )

        insights = {
            **totals,
            "rejection_patterns": patterns,
            "timing_insights": timing,
            "skill_gaps": gaps,
            "github_correlation": github_signal,
            "followup_priorities": recommender.prioritize_followups(followups),
            "action_items": action_items,
            "portfolio": portfolio,
            "overall_health_score": self._health_score(totals, gaps, github_signal, followups, portfolio),
            "evidence_insights": [],
            "llm_insights": None,
        }
        insights["evidence_insights"] = build_evidence_insights(insights)

        if use_ai:
            try:
                insights["llm_insights"] = analyzer.generate_full_analysis(
                    {
                        "rejections": patterns,
                        "github_signal": github_signal,
                        "skill_gaps": gaps,
                        "portfolio": {
                            "reachable": portfolio.get("reachable", False),
                            "detected_skills": portfolio.get("detected_skills", []),
                            "project_links": len(portfolio.get("project_links", [])),
                            "github_links": len(portfolio.get("github_links", [])),
                        },
                        "timing": timing,
                        "total_applications": totals["total_applications"],
                        "response_rate": totals["response_rate"],
                    }
                )
            except Exception as exc:
                insights["llm_error"] = str(exc)

        self._write_run_artifacts(insights)
        return insights

    @staticmethod
    def _totals(patterns: list[dict]) -> dict:
        total = sum(row.get("total", 0) for row in patterns)
        interviewed = sum(row.get("interviewed", 0) for row in patterns)
        offers = sum(row.get("offers", 0) for row in patterns)
        responded = interviewed + offers

        return {
            "total_applications": total,
            "response_rate": round(responded * 100 / total, 1) if total else 0,
            "interview_rate": round(interviewed * 100 / total, 1) if total else 0,
            "offer_rate": round(offers * 100 / total, 1) if total else 0,
        }

    @staticmethod
    def _health_score(
        totals: dict,
        gaps: list[dict],
        github_signal: dict,
        followups: list[dict],
        portfolio: dict | None = None,
    ) -> int:
        score = 45
        score += min(totals.get("response_rate", 0) * 1.2, 30)
        score += min(totals.get("offer_rate", 0) * 2, 10)

        critical_gaps = sum(1 for gap in gaps if gap.get("priority") == "critical")
        score -= min(critical_gaps * 5, 25)

        ghost_gap = (
            github_signal.get("ghost_rate_inactive_weeks", 0)
            - github_signal.get("ghost_rate_active_weeks", 0)
        )
        if ghost_gap > 20:
            score -= min((ghost_gap - 20) * 0.5, 15)

        hot_followups = sum(1 for item in followups if item.get("priority") == "hot")
        score -= min(hot_followups, 10)

        if portfolio and portfolio.get("configured"):
            if portfolio.get("reachable"):
                score += min(len(portfolio.get("detected_skills", [])), 8)
                if portfolio.get("github_links") or portfolio.get("project_links"):
                    score += 4
            else:
                score -= 8

        return max(0, min(100, round(score)))

    @staticmethod
    def _merge_portfolio_evidence(gaps: list[dict], portfolio: dict) -> list[dict]:
        detected = {str(skill).casefold() for skill in portfolio.get("detected_skills", [])}
        merged = []
        for gap in gaps:
            item = dict(gap)
            in_portfolio = str(item.get("skill", "")).casefold() in detected
            item["in_portfolio"] = in_portfolio
            if in_portfolio and item.get("priority") == "critical":
                item["priority"] = "high"
            elif in_portfolio and item.get("priority") == "high":
                item["priority"] = "medium"
            merged.append(item)
        return merged

    @staticmethod
    def _write_run_artifacts(insights: dict) -> None:
        run_dir = Path("runs") / "latest"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "insights.json").write_text(json.dumps(insights, indent=2), encoding="utf-8")
        (run_dir / "proof.json").write_text(json.dumps(get_query_log(), indent=2), encoding="utf-8")
        report = [
            "# CoralCon Latest Report",
            "",
            f"- Applications: {insights.get('total_applications', 0)}",
            f"- Response rate: {insights.get('response_rate', 0)}%",
            f"- Health score: {insights.get('overall_health_score', 0)}/100",
            "",
            "## Evidence-Backed Insights",
        ]
        for item in insights.get("evidence_insights", []):
            report.extend(
                [
                    f"### {item['title']}",
                    item["claim"],
                    f"Evidence query: {item['evidence']['query_id']}",
                    f"Action: {item['recommended_action']}",
                    "",
                ]
            )
        (run_dir / "report.md").write_text("\n".join(report), encoding="utf-8")
