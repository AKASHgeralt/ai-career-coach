"""Tests for the itemised ATS breakdown and skill classification.

The critical property for both: exposing detail must not change the numbers
that were already being produced.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app.services.nlp import (
    ATS_MAX,
    calculate_ats_breakdown,
    calculate_smart_ats_score,
    extract_skills,
)
from app.services.skill_gap_engine import (
    MATCH_THRESHOLD,
    PARTIAL_THRESHOLD,
    STATUS_MATCHED,
    STATUS_MISSING,
    STATUS_PARTIAL,
    classify_similarity,
)

FULL_RESUME = """
John Smith
john.smith@example.com
+1 555 123 4567

Summary
Backend engineer with 5 years of experience.

Education
B.Tech Computer Science, XYZ University

Experience
Backend Developer at Acme Corp. Built REST API services with Python and Django.
Worked at Globex as a software engineer.

Skills
python, java, sql, docker, kubernetes, aws, react, postgresql, git, fastapi

Projects
Built a distributed system using Redis and MongoDB.
""" + ("filler word " * 400)

SPARSE_RESUME = "Just some text with python in it."


def component(breakdown, key):
    return next(c for c in breakdown["components"] if c["key"] == key)


class TestScoreIsUnchanged:
    def test_breakdown_total_matches_the_public_score(self):
        for text in (FULL_RESUME, SPARSE_RESUME, ""):
            skills = extract_skills(text)
            assert calculate_ats_breakdown(text, skills)["total"] == \
                   calculate_smart_ats_score(text, skills)

    def test_components_sum_to_the_total(self):
        skills = extract_skills(FULL_RESUME)
        b = calculate_ats_breakdown(FULL_RESUME, skills)
        assert sum(c["earned"] for c in b["components"]) == b["total"]

    def test_maximums_sum_to_100(self):
        assert sum(ATS_MAX.values()) == 100
        b = calculate_ats_breakdown(FULL_RESUME, extract_skills(FULL_RESUME))
        assert sum(c["max"] for c in b["components"]) == 100

    def test_score_never_exceeds_100(self):
        skills = ["python"] * 50
        assert calculate_ats_breakdown(FULL_RESUME, skills)["total"] <= 100


class TestComponents:
    def test_strong_resume_maxes_most_categories(self):
        b = calculate_ats_breakdown(FULL_RESUME, extract_skills(FULL_RESUME))
        assert component(b, "contact")["earned"] == 10
        assert component(b, "education")["earned"] == 10
        assert component(b, "experience")["earned"] == 10
        assert component(b, "sections")["earned"] == 10

    def test_skills_award_four_points_each_up_to_the_cap(self):
        assert component(calculate_ats_breakdown("x", ["a", "b"]), "skills")["earned"] == 8
        assert component(calculate_ats_breakdown("x", ["a"] * 20), "skills")["earned"] == 40

    def test_empty_resume_scores_zero_without_crashing(self):
        b = calculate_ats_breakdown("", [])
        assert b["total"] == 0
        assert all(c["earned"] == 0 for c in b["components"])


class TestSuggestions:
    def test_maxed_category_has_no_suggestion(self):
        b = calculate_ats_breakdown(FULL_RESUME, extract_skills(FULL_RESUME))
        assert component(b, "contact")["suggestion"] is None

    def test_deficient_categories_explain_the_gap(self):
        b = calculate_ats_breakdown(SPARSE_RESUME, extract_skills(SPARSE_RESUME))
        for key in ("education", "experience", "contact", "length"):
            assert component(b, key)["suggestion"], f"{key} should suggest something"

    def test_missing_contact_names_what_is_absent(self):
        b = calculate_ats_breakdown("no contact details here", [])
        s = component(b, "contact")["suggestion"]
        assert "email" in s and "phone" in s

    def test_missing_sections_are_named(self):
        b = calculate_ats_breakdown("nothing structured here", [])
        s = component(b, "sections")["suggestion"]
        assert "experience" in s and "education" in s


class TestSkillClassification:
    def test_thresholds_map_to_the_right_status(self):
        assert classify_similarity(1.0) == STATUS_MATCHED
        assert classify_similarity(MATCH_THRESHOLD) == STATUS_MATCHED
        assert classify_similarity(MATCH_THRESHOLD - 0.01) == STATUS_PARTIAL
        assert classify_similarity(PARTIAL_THRESHOLD) == STATUS_PARTIAL
        assert classify_similarity(PARTIAL_THRESHOLD - 0.01) == STATUS_MISSING
        assert classify_similarity(0.0) == STATUS_MISSING

    def test_partial_sits_strictly_between_the_thresholds(self):
        assert PARTIAL_THRESHOLD < MATCH_THRESHOLD


class TestEmptyInputContract:
    def test_no_resume_skills_marks_everything_missing(self):
        from app.services.skill_gap_engine import compute_skill_gap
        r = compute_skill_gap([], ["python", "docker"])
        assert r["match_score"] == 0.0
        assert r["missing_skills"] == ["python", "docker"]
        assert [d["status"] for d in r["skill_details"]] == [STATUS_MISSING] * 2
        assert r["partial_skills"] == []

    def test_no_job_skills_yields_no_details(self):
        from app.services.skill_gap_engine import compute_skill_gap
        r = compute_skill_gap(["python"], [])
        assert r["skill_details"] == []
        assert r["match_score"] == 0.0
