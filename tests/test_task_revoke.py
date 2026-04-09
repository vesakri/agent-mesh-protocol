"""Tests for ampro.task_revoke — v0.1.5 task revocation primitive."""

import pytest
from pydantic import ValidationError

from ampro.task_revoke import TaskRevokeBody
from ampro.body_schemas import validate_body


class TestTaskRevokeMinimal:
    def test_revoke_minimal(self):
        """Minimal revoke: task_id + reason only."""
        body = TaskRevokeBody(task_id="t-1", reason="no longer needed")
        assert body.task_id == "t-1"
        assert body.reason == "no longer needed"

    def test_revoke_defaults(self):
        """cascade and revoke_children both default to False."""
        body = TaskRevokeBody(task_id="t-2", reason="cancelled")
        assert body.cascade is False
        assert body.revoke_children is False


class TestTaskRevokeFlags:
    def test_revoke_cascade_true(self):
        body = TaskRevokeBody(task_id="t-3", reason="policy change", cascade=True)
        assert body.cascade is True
        assert body.revoke_children is False

    def test_revoke_children_true(self):
        body = TaskRevokeBody(task_id="t-4", reason="abort", revoke_children=True)
        assert body.cascade is False
        assert body.revoke_children is True

    def test_revoke_both_flags(self):
        body = TaskRevokeBody(
            task_id="t-5",
            reason="full teardown",
            cascade=True,
            revoke_children=True,
        )
        assert body.cascade is True
        assert body.revoke_children is True


class TestTaskRevokeBodyRegistry:
    def test_body_registry(self):
        """validate_body('task.revoke', ...) returns TaskRevokeBody."""
        body = validate_body("task.revoke", {
            "task_id": "t-99",
            "reason": "budget exceeded",
        })
        assert isinstance(body, TaskRevokeBody)
        assert body.task_id == "t-99"
        assert body.reason == "budget exceeded"


class TestTaskRevokeValidation:
    def test_missing_task_id(self):
        """task_id is required — omitting it raises ValidationError."""
        with pytest.raises(ValidationError):
            TaskRevokeBody(reason="no task id")

    def test_missing_reason(self):
        """reason is required — omitting it raises ValidationError."""
        with pytest.raises(ValidationError):
            TaskRevokeBody(task_id="t-6")
