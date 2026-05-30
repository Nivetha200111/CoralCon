"""Data enrichment for the application tracker.

Gmail rejection emails tell you *which* role you were rejected from, but not the
skills that role demanded. This package infers a role's required skills from its
title so the cross-source skill-gap query (sheets x linkedin x github) has real
data to join on.
"""

from coralcon.enrich.skill_inference import (
    enrich_csv,
    enrich_rows,
    infer_required_skills,
)

__all__ = ["infer_required_skills", "enrich_rows", "enrich_csv"]
