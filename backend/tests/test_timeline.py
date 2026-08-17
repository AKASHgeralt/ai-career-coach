"""Tests for the career progress timeline.

The property that matters: the timeline reflects real recorded events only.
Nothing is interpolated, and a single measurement is never presented as a trend.
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.timeline import build_progress_series

BASE = datetime(2026, 8, 1)


def point(kind, days, value, label="Score"):
    return {
        "kind": kind,
        "at": BASE + timedelta(days=days),
        "title": "t",
        "detail": None,
        "metric_label": label,
        "metric_value": value,
    }


class TestProgressSeries:
    def test_groups_points_by_signal(self):
        series = build_progress_series([
            point("resume", 0, 60), point("resume", 5, 80),
            point("skills", 1, 40), point("skills", 6, 55),
        ])
        assert set(series) == {"resume", "skills"}
        assert [p["value"] for p in series["resume"]] == [60, 80]

    def test_points_are_chronological(self):
        series = build_progress_series([
            point("resume", 9, 90), point("resume", 0, 60), point("resume", 4, 75),
        ])
        assert [p["value"] for p in series["resume"]] == [60, 75, 90]

    def test_single_point_is_not_a_trend(self):
        """One measurement must not be plotted as a line."""
        series = build_progress_series([point("resume", 0, 60)])
        assert "resume" not in series

    def test_mixed_signals_only_include_those_with_history(self):
        series = build_progress_series([
            point("resume", 0, 60), point("resume", 3, 70),
            point("github", 1, 25),
        ])
        assert "resume" in series
        assert "github" not in series

    def test_events_without_a_metric_are_excluded(self):
        """Completed roadmap tasks are timeline entries but carry no value."""
        task = point("task", 0, None)
        task["metric_label"] = None
        series = build_progress_series([task, point("task", 1, None)])
        assert series == {}

    def test_empty_input(self):
        assert build_progress_series([]) == {}

    def test_metric_label_is_carried_through(self):
        series = build_progress_series([
            point("skills", 0, 40, "Match"), point("skills", 2, 60, "Match"),
        ])
        assert all(p["label"] == "Match" for p in series["skills"])
