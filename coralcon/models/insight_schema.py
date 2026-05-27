"""Evidence-backed insight schema."""

from pydantic import BaseModel, Field


class InsightEvidence(BaseModel):
    query_id: str
    rows_used: int
    sources: list[str]
    supporting_numbers: dict[str, int | float | str | bool]


class EvidenceBackedInsight(BaseModel):
    id: str
    title: str
    severity: str
    claim: str
    evidence: InsightEvidence
    root_cause: str
    recommended_action: str
    expected_impact: str
    confidence: float = Field(ge=0, le=1)
