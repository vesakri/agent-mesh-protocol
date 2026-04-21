"""Tests for ampro-server CLI."""
from __future__ import annotations


def test_parse_app_string_module_attr():
    from ampro.server.cli import _parse_app_string
    module, attr = _parse_app_string("main:agent")
    assert module == "main"
    assert attr == "agent"


def test_parse_app_string_default_attr():
    from ampro.server.cli import _parse_app_string
    module, attr = _parse_app_string("main")
    assert module == "main"
    assert attr == "agent"


def test_parse_app_string_nested():
    from ampro.server.cli import _parse_app_string
    module, attr = _parse_app_string("my_app.agents:weather_agent")
    assert module == "my_app.agents"
    assert attr == "weather_agent"
