"""Tests for ampro.priority — v0.1.5 message priority enum."""

import pytest

from ampro.core.priority import Priority


class TestPriorityEnum:
    def test_five_values(self):
        """Priority enum has exactly 5 members."""
        assert len(Priority) == 5

    def test_batch_value(self):
        assert Priority.BATCH == "batch"
        assert Priority.BATCH.value == "batch"

    def test_all_values(self):
        """All five levels exist with correct string values."""
        expected = {
            "BATCH": "batch",
            "NORMAL": "normal",
            "PRIORITY": "priority",
            "URGENT": "urgent",
            "CRITICAL": "critical",
        }
        for name, value in expected.items():
            member = Priority[name]
            assert member.value == value

    def test_from_string(self):
        """Priority('urgent') constructs the correct member."""
        assert Priority("urgent") is Priority.URGENT
        assert Priority("batch") is Priority.BATCH

    def test_invalid_value(self):
        """Unknown string raises ValueError."""
        with pytest.raises(ValueError):
            Priority("unknown")
