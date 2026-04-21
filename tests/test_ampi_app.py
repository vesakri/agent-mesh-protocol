"""Tests for AgentApp."""
from __future__ import annotations


def test_agent_app_creation():
    from ampro.ampi.app import AgentApp
    agent = AgentApp("agent://test.example.com", "https://test.example.com")
    assert agent.agent_id == "agent://test.example.com"
    assert agent.endpoint == "https://test.example.com"


def test_register_handler():
    from ampro.ampi.app import AgentApp
    agent = AgentApp("agent://test.example.com", "https://test.example.com")

    @agent.on("task.create")
    async def handle(msg, ctx):
        return {"status": "ok"}

    assert "task.create" in agent.handlers


def test_register_streaming_handler():
    from ampro.ampi.app import AgentApp
    agent = AgentApp("agent://test.example.com", "https://test.example.com")

    @agent.on("task.create", streaming=True)
    async def handle(msg, ctx):
        yield {"type": "done"}

    assert "task.create" in agent.streaming_handlers


def test_register_middleware():
    from ampro.ampi.app import AgentApp
    agent = AgentApp("agent://test.example.com", "https://test.example.com")

    @agent.middleware
    async def mw(msg, ctx, next):
        return await next(msg, ctx)

    assert len(agent.middleware_chain) == 1


def test_register_tool():
    from ampro.ampi.app import AgentApp
    agent = AgentApp("agent://test.example.com", "https://test.example.com")

    @agent.tool("search")
    async def search(query, ctx):
        return {"results": []}

    assert "search" in agent.tools


def test_lifecycle_hooks():
    from ampro.ampi.app import AgentApp
    agent = AgentApp("agent://test.example.com", "https://test.example.com")

    @agent.on_startup
    async def startup():
        pass

    @agent.on_shutdown
    async def shutdown():
        pass

    assert len(agent.startup_hooks) == 1
    assert len(agent.shutdown_hooks) == 1


def test_error_handler():
    from ampro.ampi.app import AgentApp
    agent = AgentApp("agent://test.example.com", "https://test.example.com")

    @agent.on_error
    async def handle_error(exc, msg, ctx):
        return {"error": str(exc)}

    assert agent.error_handler is not None


def test_to_dict():
    from ampro.ampi.app import AgentApp
    agent = AgentApp("agent://test.example.com", "https://test.example.com")

    @agent.on("message")
    async def handle(msg, ctx):
        return {}

    d = agent.to_dict()
    assert d["agent_id"] == "agent://test.example.com"
    assert "message" in d["handlers"]


def test_state_dict():
    from ampro.ampi.app import AgentApp
    agent = AgentApp("agent://test.example.com", "https://test.example.com")
    agent.state["db"] = "connected"
    assert agent.state["db"] == "connected"


def test_agent_json_auto_generated():
    from ampro.ampi.app import AgentApp
    agent = AgentApp("agent://test.example.com", "https://test.example.com", capabilities=["messaging", "tools"])
    aj = agent.agent_json
    assert aj.endpoint == "https://test.example.com"
    assert "agent://test.example.com" in aj.identifiers


def test_session_start_hook():
    from ampro.ampi.app import AgentApp
    agent = AgentApp("agent://test.example.com", "https://test.example.com")

    @agent.on_session_start
    async def on_sess(session):
        pass

    assert len(agent.session_start_hooks) == 1
