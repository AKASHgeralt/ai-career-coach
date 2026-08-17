"""Tests for the Career Readiness scoring maths.

compute_readiness is a pure function, so these run with no database, no network
and no model loading.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app.services.readiness import (
    COMPONENT_WEIGHTS,
    compute_readiness,
    weakest_component,
)


def component(result, key):
    return next(c for c in result["components"] if c["key"] == key)


class TestAllComponentsPresent:
    def test_weighted_average_is_correct(self):
        r = compute_readiness(resume=80, skills=60, interview=70, github=90)
        expected = (80 * 25 + 60 * 35 + 70 * 20 + 90 * 20) / 100
        assert r["score"] == pytest.approx(round(expected, 1))

    def test_identical_scores_average_to_themselves(self):
        r = compute_readiness(resume=72, skills=72, interview=72, github=72)
        assert r["score"] == 72.0

    def test_effective_weights_match_base_weights(self):
        r = compute_readiness(resume=50, skills=50, interview=50, github=50)
        for key, weight in COMPONENT_WEIGHTS.items():
            assert component(r, key)["effective_weight"] == pytest.approx(weight)

    def test_nothing_reported_missing(self):
        r = compute_readiness(resume=50, skills=50, interview=50, github=50)
        assert r["missing"] == []
        assert r["available_count"] == 4


class TestMissingComponents:
    def test_missing_github_does_not_drag_score_down(self):
        """The whole point: absent data must not act like a zero."""
        without = compute_readiness(resume=80, skills=80, interview=80)
        as_zero = compute_readiness(resume=80, skills=80, interview=80, github=0)
        assert without["score"] == 80.0
        assert as_zero["score"] < without["score"]

    def test_weights_renormalise_to_100(self):
        r = compute_readiness(resume=80, skills=80, interview=80)
        total = sum(
            c["effective_weight"] for c in r["components"] if c["available"]
        )
        assert total == pytest.approx(100.0, abs=0.2)

    def test_missing_component_is_reported_with_an_action(self):
        r = compute_readiness(resume=80, skills=80, interview=80)
        gh = component(r, "github")
        assert gh["available"] is False
        assert gh["score"] is None
        assert gh["effective_weight"] == 0.0
        assert "Connect GitHub" in gh["action"]

    def test_single_component_scores_to_that_component(self):
        r = compute_readiness(resume=64)
        assert r["score"] == 64.0
        assert component(r, "resume")["effective_weight"] == pytest.approx(100.0)
        assert r["available_count"] == 1

    def test_no_data_yields_none_not_zero(self):
        r = compute_readiness()
        assert r["score"] is None
        assert r["available_count"] == 0
        assert len(r["missing"]) == 4
        assert "No readiness score yet" in r["explanation"]


class TestClamping:
    def test_out_of_range_values_are_clamped(self):
        r = compute_readiness(resume=150, skills=-20, interview=50, github=50)
        assert component(r, "resume")["score"] == 100.0
        assert component(r, "skills")["score"] == 0.0
        assert 0 <= r["score"] <= 100


class TestExplanation:
    def test_names_strongest_and_weakest(self):
        r = compute_readiness(resume=90, skills=30, interview=70, github=60)
        assert "Skill Match" in r["explanation"]   # weakest
        assert "Resume / ATS" in r["explanation"]  # strongest

    def test_mentions_rebalancing_when_data_is_missing(self):
        r = compute_readiness(resume=80, skills=70)
        assert "rebalanced" in r["explanation"]


class TestWeakestComponent:
    def test_picks_lowest_scoring_available_component(self):
        r = compute_readiness(resume=90, skills=30, interview=70, github=60)
        assert weakest_component(r)["key"] == "skills"

    def test_ignores_missing_components(self):
        """A missing component must never be reported as the weak spot."""
        r = compute_readiness(resume=90, interview=70)
        assert weakest_component(r)["key"] == "interview"

    def test_returns_none_when_nothing_measured(self):
        assert weakest_component(compute_readiness()) is None
