"""Tests for roadmap task materialisation and progress.

build_tasks_from_roadmap / progress_for are pure, so no DB is needed.
"""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.roadmap_tasks import (
    MAX_TASKS_PER_WEEK,
    MAX_WEEKS,
    build_tasks_from_roadmap,
    progress_for,
)

USER = "11111111-1111-1111-1111-111111111111"
REC = "22222222-2222-2222-2222-222222222222"


def build(roadmap):
    return build_tasks_from_roadmap(roadmap, USER, REC)


class TestMaterialisation:
    def test_creates_one_row_per_task(self):
        rows = build([
            {"week": 1, "focus": "Python", "goal": "Basics",
             "tasks": ["NumPy revision", "Pandas revision"]},
            {"week": 2, "focus": "PyTorch", "goal": "Tensors",
             "tasks": ["Build an MLP"]},
        ])
        assert len(rows) == 3
        assert [r.title for r in rows] == ["NumPy revision", "Pandas revision", "Build an MLP"]
        assert [r.week for r in rows] == [1, 1, 2]

    def test_positions_are_sequential_within_a_week(self):
        rows = build([{"week": 1, "focus": "F", "tasks": ["a", "b", "c"]}])
        assert [r.position for r in rows] == [0, 1, 2]

    def test_week_goal_is_carried_as_detail(self):
        rows = build([{"week": 1, "focus": "Python", "goal": "Master basics", "tasks": ["x"]}])
        assert rows[0].detail == "Master basics"

    def test_tasks_start_incomplete(self):
        rows = build([{"week": 1, "focus": "Python", "tasks": ["x"]}])
        assert rows[0].completed is False


class TestLegacyAndMalformedInput:
    def test_week_without_tasks_falls_back_to_its_focus(self):
        """Roadmaps generated before tasks existed must still be checkable."""
        rows = build([{"week": 1, "focus": "Python for ML", "goal": "Basics"}])
        assert len(rows) == 1
        assert rows[0].title == "Python for ML"

    def test_empty_task_strings_are_dropped(self):
        rows = build([{"week": 1, "focus": "Python", "tasks": ["real", "  ", ""]}])
        assert [r.title for r in rows] == ["real"]

    def test_non_list_roadmap_yields_nothing(self):
        assert build(None) == []
        assert build({"week": 1}) == []
        assert build("nonsense") == []

    def test_non_dict_weeks_are_skipped(self):
        rows = build(["garbage", {"week": 1, "focus": "Python", "tasks": ["x"]}])
        assert len(rows) == 1

    def test_bad_week_number_falls_back_to_position(self):
        rows = build([
            {"week": "not a number", "focus": "A", "tasks": ["x"]},
            {"week": 999, "focus": "B", "tasks": ["y"]},
        ])
        assert rows[0].week == 1
        assert rows[1].week == 2

    def test_runaway_response_is_capped(self):
        roadmap = [
            {"week": i, "focus": f"W{i}", "tasks": [f"t{j}" for j in range(50)]}
            for i in range(1, 60)
        ]
        rows = build(roadmap)
        assert len(rows) <= MAX_WEEKS * MAX_TASKS_PER_WEEK

    def test_absurdly_long_title_is_truncated(self):
        rows = build([{"week": 1, "focus": "F", "tasks": ["x" * 5000]}])
        assert len(rows[0].title) <= 500


class TestProgress:
    def _tasks(self, flags):
        return [SimpleNamespace(completed=f) for f in flags]

    def test_empty_list_is_zero_not_a_crash(self):
        assert progress_for([]) == {"total": 0, "completed": 0, "percent": 0.0}

    def test_partial_completion(self):
        p = progress_for(self._tasks([True, True, False, False, False]))
        assert p == {"total": 5, "completed": 2, "percent": 40.0}

    def test_full_completion(self):
        assert progress_for(self._tasks([True, True]))["percent"] == 100.0

    def test_nothing_done(self):
        assert progress_for(self._tasks([False, False]))["percent"] == 0.0
