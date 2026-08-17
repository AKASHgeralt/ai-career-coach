"""Tests for the Next Best Action engine.

Pure function, no DB. The important properties: setup beats optimisation, the
weakest measured signal wins otherwise, and a missing signal is never reported
as the weak spot.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.next_action import determine_next_action
from app.services.readiness import compute_readiness

ROLE = "AI Engineer"


def decide(readiness, **kwargs):
    kwargs.setdefault("target_role_label", ROLE)
    kwargs.setdefault("role_scoped_gap", True)
    return determine_next_action(readiness=readiness, **kwargs)


class TestSetupTier:
    def test_no_target_role_comes_first(self):
        """Even with everything else measured, an unset role blocks personalisation."""
        r = compute_readiness(resume=80, skills=80, interview=80, github=80)
        a = decide(r, target_role_label=None)
        assert a["based_on"] == "target_role"
        assert a["target_section"] == "Settings"
        assert a["priority"] == "setup"

    def test_missing_resume_beats_optimising_a_weak_signal(self):
        r = compute_readiness(skills=10, interview=90, github=90)
        a = decide(r)
        assert a["based_on"] == "resume"
        assert a["target_section"] == "Resumes"

    def test_missing_skills_analysis_is_next(self):
        r = compute_readiness(resume=80, interview=90, github=90)
        a = decide(r)
        assert a["based_on"] == "skills"
        assert a["target_section"] == "Skill Gap"

    def test_missing_interview_then_github(self):
        r = compute_readiness(resume=80, skills=80, github=90)
        assert decide(r)["based_on"] == "interview"

        r2 = compute_readiness(resume=80, skills=80, interview=90)
        assert decide(r2)["based_on"] == "github"

    def test_nothing_measured_asks_for_a_resume(self):
        a = decide(compute_readiness())
        assert a["target_section"] == "Resumes"

    def test_gap_for_wrong_role_prompts_a_rerun(self):
        """A skill score measured against the wrong role isn't real readiness."""
        r = compute_readiness(resume=80, skills=90, interview=80, github=80)
        a = decide(r, role_scoped_gap=False)
        assert a["target_section"] == "Skill Gap"
        assert ROLE in a["action"]


class TestImproveTier:
    def _full(self, **scores):
        base = dict(resume=80, skills=80, interview=80, github=80)
        base.update(scores)
        return compute_readiness(**base)

    def test_targets_the_weakest_signal(self):
        assert decide(self._full(skills=20))["based_on"] == "skills"
        assert decide(self._full(resume=20))["based_on"] == "resume"
        assert decide(self._full(interview=20))["based_on"] == "interview"
        assert decide(self._full(github=20))["based_on"] == "github"

    def test_weak_skills_name_the_actual_missing_skill(self):
        a = decide(self._full(skills=20), top_missing_skill=("docker", 3), gap_count=4)
        assert "docker" in a["action"].lower()
        assert "3 of your 4 analyses" in a["why"]
        assert a["target_section"] == "Roadmap"

    def test_weak_skills_without_a_named_gap_still_works(self):
        a = decide(self._full(skills=20), top_missing_skill=None)
        assert a["based_on"] == "skills"
        assert a["target_section"] == "Roadmap"

    def test_everything_strong_still_returns_an_action(self):
        a = decide(self._full())
        assert a["action"] and a["why"] and a["priority"] == "improve"

    def test_reason_quotes_the_real_score(self):
        a = decide(self._full(interview=37))
        assert "37/100" in a["why"]


class TestNeverBlamesMissingData:
    def test_missing_signal_is_not_called_the_weakest(self):
        """GitHub absent must produce a setup action, never 'GitHub is weakest'."""
        r = compute_readiness(resume=90, skills=90, interview=90)
        a = decide(r)
        assert a["priority"] == "setup"
        assert "weakest" not in a["why"]
