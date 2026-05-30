"""Tests for role-title -> required-skills inference.

This is what gives the flagship cross-source skill-gap query real data to join
on, so guard the mapping against regressions.
"""

from coralcon.enrich.skill_inference import (
    enrich_rows,
    infer_required_skills,
)


def test_react_role_infers_react_stack():
    skills = infer_required_skills("Software Engineer - React JS")
    assert "React" in skills
    assert "JavaScript" in skills


def test_java_token_does_not_fire_on_javascript():
    # "javascript" must not be mistaken for "java".
    skills = infer_required_skills("Senior JavaScript Developer")
    assert "Java" not in skills
    assert "JavaScript" in skills


def test_ml_role_infers_ml_stack():
    skills = infer_required_skills("ML Engineer")
    assert "Machine Learning" in skills
    assert "Python" in skills


def test_generic_software_role_gets_fundamentals():
    skills = infer_required_skills("Software Engineer")
    assert skills, "a generic engineering role should still infer fundamentals"
    assert "SQL" in skills


def test_empty_title_returns_nothing():
    assert infer_required_skills("") == []
    assert infer_required_skills("   ") == []


def test_skills_are_deduped_and_capped():
    skills = infer_required_skills(
        "Staff Fullstack Engineer (Python/Vue.js), AI/ML Backend"
    )
    assert len(skills) == len(set(skills))  # no duplicates
    assert len(skills) <= 6  # capped


def test_enrich_rows_fills_missing_only():
    rows = [
        {"role_title": "Java Developer", "required_skills": []},
        {"role_title": "Data Analyst", "required_skills": ["Existing"]},
    ]
    enriched = enrich_rows(rows)
    assert enriched == 1  # only the empty one
    assert "Java" in rows[0]["required_skills"]
    assert rows[1]["required_skills"] == ["Existing"]  # untouched


def test_enrich_rows_overwrite():
    rows = [{"role_title": "Java Developer", "required_skills": ["Stale"]}]
    enriched = enrich_rows(rows, overwrite=True)
    assert enriched == 1
    assert "Java" in rows[0]["required_skills"]
