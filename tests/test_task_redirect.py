"""Tests for ampro.task_redirect — v0.1.4 load-aware routing primitive."""

import pytest
from pydantic import ValidationError

from ampro.transport.task_redirect import TaskRedirectBody
from ampro.core.body_schemas import validate_body
from ampro.core.envelope import STANDARD_HEADERS


class TestTaskRedirectBodyRequired:
    """Test TaskRedirectBody required fields."""

    def test_required_fields(self):
        body = TaskRedirectBody(
            task_id="t-42",
            redirect_to="agent://backup.example.com",
            reason="overloaded",
        )
        assert body.task_id == "t-42"
        assert body.redirect_to == "agent://backup.example.com"
        assert body.reason == "overloaded"

    def test_missing_task_id_raises(self):
        with pytest.raises(ValidationError):
            TaskRedirectBody(
                redirect_to="agent://backup.example.com",
                reason="overloaded",
            )

    def test_missing_redirect_to_raises(self):
        with pytest.raises(ValidationError):
            TaskRedirectBody(
                task_id="t-1",
                reason="overloaded",
            )

    def test_missing_reason_raises(self):
        with pytest.raises(ValidationError):
            TaskRedirectBody(
                task_id="t-1",
                redirect_to="agent://backup.example.com",
            )


class TestTaskRedirectBodyOptionalDefaults:
    """Test that optional fields default to None."""

    def test_original_description_default_none(self):
        body = TaskRedirectBody(
            task_id="t-1",
            redirect_to="agent://b.example.com",
            reason="maintenance",
        )
        assert body.original_description is None

    def test_load_level_default_none(self):
        body = TaskRedirectBody(
            task_id="t-1",
            redirect_to="agent://b.example.com",
            reason="maintenance",
        )
        assert body.load_level is None

    def test_alternative_agents_default_none(self):
        body = TaskRedirectBody(
            task_id="t-1",
            redirect_to="agent://b.example.com",
            reason="maintenance",
        )
        assert body.alternative_agents is None

    def test_retry_after_seconds_default_none(self):
        body = TaskRedirectBody(
            task_id="t-1",
            redirect_to="agent://b.example.com",
            reason="maintenance",
        )
        assert body.retry_after_seconds is None


class TestTaskRedirectBodyAlternativeAgents:
    """Test TaskRedirectBody with alternative_agents list."""

    def test_with_alternative_agents(self):
        body = TaskRedirectBody(
            task_id="t-99",
            redirect_to="agent://primary-alt.example.com",
            reason="capability_mismatch",
            alternative_agents=[
                "agent://alt1.example.com",
                "agent://alt2.example.com",
                "agent://alt3.example.com",
            ],
        )
        assert len(body.alternative_agents) == 3
        assert "agent://alt2.example.com" in body.alternative_agents

    def test_with_all_optional_fields(self):
        body = TaskRedirectBody(
            task_id="t-100",
            redirect_to="agent://target.example.com",
            reason="overloaded",
            original_description="Summarize quarterly report",
            load_level=95,
            alternative_agents=["agent://fallback.example.com"],
            retry_after_seconds=30,
        )
        assert body.original_description == "Summarize quarterly report"
        assert body.load_level == 95
        assert body.retry_after_seconds == 30

    def test_empty_alternative_agents_list(self):
        body = TaskRedirectBody(
            task_id="t-1",
            redirect_to="agent://b.example.com",
            reason="overloaded",
            alternative_agents=[],
        )
        assert body.alternative_agents == []


class TestTaskRedirectValidateBody:
    """Test validate_body integration for task.redirect."""

    def test_validate_body_returns_task_redirect_body(self):
        body = validate_body("task.redirect", {
            "task_id": "t-500",
            "redirect_to": "agent://new-handler.example.com",
            "reason": "overloaded",
        })
        assert isinstance(body, TaskRedirectBody)
        assert body.task_id == "t-500"
        assert body.redirect_to == "agent://new-handler.example.com"
        assert body.reason == "overloaded"

    def test_validate_body_with_optional_fields(self):
        body = validate_body("task.redirect", {
            "task_id": "t-501",
            "redirect_to": "agent://alt.example.com",
            "reason": "maintenance",
            "load_level": 88,
            "alternative_agents": ["agent://spare.example.com"],
        })
        assert isinstance(body, TaskRedirectBody)
        assert body.load_level == 88

    def test_validate_body_missing_required_raises(self):
        with pytest.raises(ValidationError):
            validate_body("task.redirect", {"task_id": "t-1"})


class TestLoadLevelHeader:
    """Test X-Load-Level header presence in STANDARD_HEADERS."""

    def test_x_load_level_in_standard_headers(self):
        assert "X-Load-Level" in STANDARD_HEADERS

    def test_standard_headers_is_frozenset(self):
        assert isinstance(STANDARD_HEADERS, frozenset)


class TestRedirectLoopDetection:
    """Issue #35 — redirect loop + max-hops enforcement."""

    def test_visited_agents_defaults_to_empty_list(self):
        body = TaskRedirectBody(
            task_id="t-1",
            redirect_to="agent://b.example.com",
            reason="overloaded",
        )
        assert body.visited_agents == []
        assert body.max_hops == 5

    def test_visited_agents_capped_at_10(self):
        with pytest.raises(ValidationError):
            TaskRedirectBody(
                task_id="t-1",
                redirect_to="agent://b.example.com",
                reason="overloaded",
                visited_agents=[f"agent://a{i}.example.com" for i in range(11)],
            )

    def test_max_hops_bounds(self):
        with pytest.raises(ValidationError):
            TaskRedirectBody(
                task_id="t",
                redirect_to="agent://b.example.com",
                reason="r",
                max_hops=0,
            )
        with pytest.raises(ValidationError):
            TaskRedirectBody(
                task_id="t",
                redirect_to="agent://b.example.com",
                reason="r",
                max_hops=11,
            )

    def test_redirect_detects_cycle(self):
        from ampro.errors import RedirectLoopError
        from ampro.transport.task_redirect import check_redirect_chain

        body = TaskRedirectBody(
            task_id="t",
            redirect_to="agent://c.example.com",
            reason="overloaded",
            visited_agents=["agent://a.example.com", "agent://b.example.com"],
        )
        # Current agent already in visited → cycle
        with pytest.raises(RedirectLoopError) as excinfo:
            check_redirect_chain(body, "agent://a.example.com")
        assert "cycle" in str(excinfo.value).lower()

    def test_redirect_enforces_max_hops(self):
        from ampro.errors import RedirectLoopError
        from ampro.transport.task_redirect import check_redirect_chain

        body = TaskRedirectBody(
            task_id="t",
            redirect_to="agent://z.example.com",
            reason="overloaded",
            visited_agents=[f"agent://a{i}.example.com" for i in range(5)],
            max_hops=5,
        )
        # 5 visited >= max_hops=5 → must reject
        with pytest.raises(RedirectLoopError) as excinfo:
            check_redirect_chain(body, "agent://new.example.com")
        assert "max_hops" in str(excinfo.value)

    def test_redirect_chain_ok_when_under_limit(self):
        from ampro.transport.task_redirect import check_redirect_chain

        body = TaskRedirectBody(
            task_id="t",
            redirect_to="agent://z.example.com",
            reason="overloaded",
            visited_agents=["agent://a.example.com"],
            max_hops=5,
        )
        check_redirect_chain(body, "agent://b.example.com")  # no raise

    def test_redirect_loop_error_is_transport_error(self):
        from ampro.errors import RedirectLoopError, TransportError, AmpError

        assert issubclass(RedirectLoopError, TransportError)
        assert issubclass(RedirectLoopError, AmpError)
