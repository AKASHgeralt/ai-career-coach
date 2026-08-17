"""Tests for resume versioning and comparison."""
import os
import sys
from datetime import datetime, timedelta
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.resume_versions import (
    build_version_history,
    compare_resumes,
    next_version_for,
)

BASE_DATE = datetime(2026, 8, 1)

# Enough prose to clear the ATS length bands, so category deltas are meaningful.
FILLER = " ".join(["Delivered production services and measurable improvements."] * 30)


def resume(version, text, ats=0, days=0, name=None):
    return SimpleNamespace(
        id=f"00000000-0000-0000-0000-00000000000{version}",
        version=version,
        file_name=name or f"cv_v{version}.pdf",
        parsed_text=text,
        ats_score=ats,
        uploaded_at=BASE_DATE + timedelta(days=days),
    )


class TestNextVersion:
    def test_first_upload_is_v1(self):
        assert next_version_for([]) == 1

    def test_increments_from_highest(self):
        assert next_version_for([1, 2, 3]) == 4

    def test_survives_a_deleted_middle_version(self):
        """Deleting v2 must not cause v3 to be reissued."""
        assert next_version_for([1, 3]) == 4


class TestSkillComparison:
    def test_detects_gained_skills(self):
        out = compare_resumes(
            resume(1, f"python sql {FILLER}"),
            resume(2, f"python sql docker aws {FILLER}", days=5),
        )
        assert out["skills_gained"] == ["aws", "docker"]
        assert out["skills_lost"] == []

    def test_detects_dropped_skills(self):
        out = compare_resumes(
            resume(1, f"python sql docker {FILLER}"),
            resume(2, f"python sql {FILLER}", days=5),
        )
        assert out["skills_lost"] == ["docker"]
        assert "No longer detected" in out["summary"]

    def test_reports_kept_skills(self):
        out = compare_resumes(
            resume(1, f"python sql {FILLER}"),
            resume(2, f"python docker {FILLER}", days=5),
        )
        assert out["skills_kept"] == ["python"]

    def test_still_missing_uses_the_target_role_baseline(self):
        out = compare_resumes(
            resume(1, f"python {FILLER}"),
            resume(2, f"python docker {FILLER}", days=5),
            role_skills=["python", "docker", "kubernetes", "aws"],
        )
        assert out["still_missing"] == ["aws", "kubernetes"]

    def test_no_role_means_no_missing_claims(self):
        out = compare_resumes(
            resume(1, f"python {FILLER}"), resume(2, f"python {FILLER}", days=1)
        )
        assert out["still_missing"] == []


class TestAtsComparison:
    def test_improvement_is_reported(self):
        out = compare_resumes(
            resume(1, "python"),
            resume(2, f"python docker aws sql react {FILLER} "
                      "bachelor of engineering, university. worked at Acme. "
                      "a@b.com 555-123-4567 experience education skills projects summary",
                   days=5),
        )
        assert out["ats_delta"] > 0
        assert out["ats_status"] == "improved"
        assert "rose" in out["summary"]

    def test_decline_is_reported_honestly(self):
        out = compare_resumes(
            resume(1, f"python docker aws sql react {FILLER}"),
            resume(2, "python", days=5),
        )
        assert out["ats_delta"] < 0
        assert out["ats_status"] == "declined"
        assert "fell" in out["summary"]

    def test_identical_versions_show_no_change(self):
        text = f"python sql {FILLER}"
        out = compare_resumes(resume(1, text), resume(2, text, days=5))
        assert out["ats_delta"] == 0
        assert out["ats_status"] == "unchanged"
        assert out["skills_gained"] == [] and out["skills_lost"] == []

    def test_every_category_is_compared(self):
        out = compare_resumes(resume(1, "python"), resume(2, "python sql", days=1))
        keys = {c["key"] for c in out["categories"]}
        assert keys == {"skills", "length", "education", "experience", "contact", "sections"}
        for c in out["categories"]:
            assert c["delta"] == c["after"] - c["before"]

    def test_handles_empty_text(self):
        out = compare_resumes(resume(1, ""), resume(2, "", days=1))
        assert out["ats_delta"] == 0
        assert out["skills_gained"] == []


class TestVersionHistory:
    def test_orders_by_version(self):
        history = build_version_history([
            resume(3, "x", ats=86, days=10),
            resume(1, "x", ats=61, days=0),
            resume(2, "x", ats=74, days=5),
        ])
        assert [v["version"] for v in history["versions"]] == [1, 2, 3]
        assert [v["ats_score"] for v in history["versions"]] == [61, 74, 86]

    def test_improvement_is_first_to_last(self):
        history = build_version_history([
            resume(1, "x", ats=61), resume(2, "x", ats=74, days=5),
            resume(3, "x", ats=86, days=10),
        ])
        assert history["improvement"] == 25
        assert history["latest_version"] == 3

    def test_single_version_has_no_improvement(self):
        """One resume is a data point, not progress."""
        history = build_version_history([resume(1, "x", ats=61)])
        assert history["improvement"] is None
        assert history["count"] == 1

    def test_empty_history(self):
        history = build_version_history([])
        assert history == {
            "versions": [], "count": 0, "improvement": None, "latest_version": None
        }

    def test_regression_is_reported_as_negative(self):
        history = build_version_history([
            resume(1, "x", ats=80), resume(2, "x", ats=65, days=5),
        ])
        assert history["improvement"] == -15
