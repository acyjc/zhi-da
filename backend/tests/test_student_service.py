import pytest
from core.services.student_service import _diff_skills


class TestDiffSkills:
    def test_added_skill(self):
        diffs = _diff_skills({}, {"Python": 80}, "tech_skills")
        assert len(diffs) == 1
        assert "0→80" in diffs[0]

    def test_removed_skill(self):
        diffs = _diff_skills({"Python": 80}, {}, "tech_skills")
        assert len(diffs) == 1
        assert "80→0" in diffs[0]

    def test_changed_skill(self):
        diffs = _diff_skills({"Python": 70}, {"Python": 85}, "tech_skills")
        assert len(diffs) == 1
        assert "70→85" in diffs[0]

    def test_no_change(self):
        diffs = _diff_skills({"Python": 80}, {"Python": 80}, "tech_skills")
        assert len(diffs) == 0

    def test_multiple_changes(self):
        diffs = _diff_skills(
            {"Python": 70, "Java": 60},
            {"Python": 85, "Java": 65},
            "tech_skills",
        )
        assert len(diffs) == 2
