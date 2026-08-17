"""Tests for interview dimension analytics.

Key properties: dimensions are averaged only over answers that recorded them,
sessions graded before dimensions existed degrade gracefully, and the platform
never reports a dimension it did not measure.
"""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.interview_analytics import (
    DIMENSION_KEYS,
    PRACTICE_FOR,
    aggregate_dimensions,
    build_session_analytics,
)


def answer(score=7, technical=None, problem_solving=None, communication=None,
           strengths="", improvements=""):
    dims = None
    if technical is not None:
        dims = {
            "technical": technical,
            "problem_solving": problem_solving,
            "communication": communication,
        }
    return SimpleNamespace(
        score=score, dimensions=dims,
        strengths=strengths, improvements=improvements,
    )


SESSION = SimpleNamespace(
    id="11111111-1111-1111-1111-111111111111",
    job_role="Backend Developer", difficulty="medium", status="completed",
)


def by_key(dims, key):
    return next(d for d in dims if d["key"] == key)


class TestDimensions:
    def test_only_three_measurable_dimensions_exist(self):
        """Confidence is not graded — a typed answer cannot evidence it."""
        assert set(DIMENSION_KEYS) == {"technical", "problem_solving", "communication"}
        assert "confidence" not in DIMENSION_KEYS

    def test_averages_across_answers(self):
        dims = aggregate_dimensions([
            answer(technical=8, problem_solving=6, communication=4),
            answer(technical=6, problem_solving=8, communication=6),
        ])
        assert by_key(dims, "technical")["score"] == 7.0
        assert by_key(dims, "problem_solving")["score"] == 7.0
        assert by_key(dims, "communication")["score"] == 5.0

    def test_counts_how_many_answers_contributed(self):
        dims = aggregate_dimensions([
            answer(technical=8, problem_solving=8, communication=8),
            answer(),  # legacy answer, no dimensions
        ])
        assert by_key(dims, "technical")["answers_scored"] == 1

    def test_out_of_range_values_are_clamped(self):
        dims = aggregate_dimensions([
            answer(technical=50, problem_solving=-5, communication=5)
        ])
        assert by_key(dims, "technical")["score"] == 10.0
        assert by_key(dims, "problem_solving")["score"] == 0.0

    def test_non_numeric_values_are_ignored(self):
        dims = aggregate_dimensions([
            answer(technical="high", problem_solving=None, communication=6)
        ])
        assert by_key(dims, "technical")["score"] is None
        assert by_key(dims, "communication")["score"] == 6.0

    def test_no_dimensions_yields_none_not_zero(self):
        dims = aggregate_dimensions([answer(), answer()])
        assert all(d["score"] is None for d in dims)
        assert all(d["answers_scored"] == 0 for d in dims)


class TestSessionAnalytics:
    def test_overall_matches_the_answer_scores(self):
        """Overall must agree with the total the user already saw."""
        out = build_session_analytics(SESSION, [answer(score=8), answer(score=6)])
        assert out["overall"] == 7.0

    def test_identifies_weakest_and_strongest(self):
        out = build_session_analytics(SESSION, [
            answer(technical=9, problem_solving=7, communication=3)
        ])
        assert out["weakest_dimension"] == "communication"
        assert out["strongest_dimension"] == "technical"
        assert "Communication" in out["summary"]

    def test_practice_matches_the_weakest_dimension(self):
        out = build_session_analytics(SESSION, [
            answer(technical=3, problem_solving=9, communication=9)
        ])
        assert out["recommended_practice"] == PRACTICE_FOR["technical"]

    def test_legacy_session_degrades_gracefully(self):
        """Sessions graded before dimensions existed still return sensibly."""
        out = build_session_analytics(SESSION, [answer(score=6), answer(score=8)])
        assert out["overall"] == 7.0
        assert out["weakest_dimension"] is None
        assert out["recommended_practice"] == []
        assert "before dimension scoring" in out["summary"]

    def test_strengths_and_weaknesses_are_deduplicated(self):
        out = build_session_analytics(SESSION, [
            answer(strengths="Clear examples", improvements="Add detail"),
            answer(strengths="Clear examples", improvements="Add detail"),
            answer(strengths="Good structure", improvements="Explain trade-offs"),
        ])
        assert out["strengths"] == ["Good structure", "Clear examples"]
        assert len(out["weaknesses"]) == 2

    def test_blank_feedback_is_skipped(self):
        out = build_session_analytics(SESSION, [
            answer(strengths="", improvements="   "),
            answer(strengths="Solid", improvements="Be concise"),
        ])
        assert out["strengths"] == ["Solid"]
        assert out["weaknesses"] == ["Be concise"]

    def test_empty_session(self):
        out = build_session_analytics(SESSION, [])
        assert out["overall"] is None
        assert out["questions_answered"] == 0
        assert out["strengths"] == []
