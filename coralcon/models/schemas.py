from pydantic import BaseModel
from typing import Optional
from datetime import date


class Application(BaseModel):
    id: str
    company: str
    role_title: str
    applied_date: str
    status: str  # applied | interviewing | rejected | ghosted | offer
    required_skills: list[str] = []
    salary_range: Optional[str] = None
    days_since_applied: Optional[int] = None
    source: Optional[str] = None


class GitHubActivity(BaseModel):
    week: str
    commits_count: int
    active_repos: int
    languages: list[str] = []
    stars_earned: int = 0


class GitHubProfile(BaseModel):
    username: str
    total_repos: int
    total_stars: int
    languages: list[str]
    top_language: str
    commit_streak: int
    last_active: str


class LinkedInSkill(BaseModel):
    name: str
    endorsements: int = 0


class LinkedInProfile(BaseModel):
    headline: str
    summary: str
    location: str
    skills: list[LinkedInSkill] = []
    positions: list[dict] = []


class RejectionPattern(BaseModel):
    role_title: str
    total: int
    rejected: int
    ghosted: int
    interviewed: int
    offers: int
    rejection_rate: float
    ghost_rate: float
    response_rate: float


class SkillGap(BaseModel):
    skill: str
    times_required: int
    in_github: bool
    in_linkedin: bool
    priority: str  # critical | high | medium


class FollowUp(BaseModel):
    company: str
    role_title: str
    applied_date: str
    days_waiting: int
    priority: str  # hot | warm | cold
    recommended_action: str


class InsightReport(BaseModel):
    total_applications: int
    response_rate: float
    interview_rate: float
    offer_rate: float
    rejection_patterns: list[RejectionPattern]
    skill_gaps: list[SkillGap]
    follow_ups: list[FollowUp]
    github_signal: dict
    action_items: list[str]
    llm_insights: Optional[str] = None
