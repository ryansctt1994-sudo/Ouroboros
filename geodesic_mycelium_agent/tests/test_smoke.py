"""Smoke tests for the Geodesic Mycelium Agent.

These tests exercise the agent in dry-run mode and require no external
dependencies (no network, no API keys).
"""

from __future__ import annotations

import pathlib
import sys

import pytest

# Ensure the repo root is on the path so the package is importable
_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from geodesic_mycelium_agent.agent import (
    AgentConfig,
    GeodesicMyceliumAgent,
    InMemoryBackend,
    LLMProvider,
    MemoryEntry,
    ToolRegistry,
    load_canonical_progression,
    load_docs_index,
    load_knowledge_base,
)
from geodesic_mycelium_agent.cli import build_parser, main


# ---------------------------------------------------------------------------
# Docs loader tests
# ---------------------------------------------------------------------------

def test_load_canonical_progression_returns_string():
    result = load_canonical_progression()
    assert isinstance(result, str)


def test_canonical_progression_file_exists():
    """The canonical doc must be present in the repository."""
    path = _REPO_ROOT / "ABRAXIS" / "CANONICAL_PROGRESSION.md"
    assert path.exists(), f"Missing file: {path}"


def test_load_docs_index_returns_string():
    result = load_docs_index()
    assert isinstance(result, str)


def test_docs_index_file_exists():
    path = _REPO_ROOT / "ABRAXIS" / "INDEX.md"
    assert path.exists(), f"Missing file: {path}"


def test_load_knowledge_base_returns_dict():
    result = load_knowledge_base()
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# InMemoryBackend tests
# ---------------------------------------------------------------------------

def test_in_memory_backend_append_and_recent():
    backend = InMemoryBackend()
    backend.append(MemoryEntry(role="user", content="hello"))
    backend.append(MemoryEntry(role="assistant", content="world"))
    entries = backend.recent(5)
    assert len(entries) == 2
    assert entries[0].content == "hello"


def test_in_memory_backend_recent_limit():
    backend = InMemoryBackend()
    for i in range(20):
        backend.append(MemoryEntry(role="user", content=str(i)))
    assert len(backend.recent(5)) == 5


def test_in_memory_backend_clear():
    backend = InMemoryBackend()
    backend.append(MemoryEntry(role="user", content="data"))
    backend.clear()
    assert backend.recent() == []


# ---------------------------------------------------------------------------
# ToolRegistry tests
# ---------------------------------------------------------------------------

def test_tool_registry_register_and_dispatch():
    registry = ToolRegistry()

    @registry.register("echo")
    def echo(message: str) -> str:
        return message

    result = registry.dispatch("echo", {"message": "ping"})
    assert result == "ping"


def test_tool_registry_list_tools():
    registry = ToolRegistry()
    registry.register("noop")(lambda: None)
    assert "noop" in registry.list_tools()


def test_tool_registry_unknown_tool_raises():
    registry = ToolRegistry()
    with pytest.raises(KeyError):
        registry.dispatch("nonexistent", {})


# ---------------------------------------------------------------------------
# LLMProvider dry-run stub tests
# ---------------------------------------------------------------------------

def test_default_llm_provider_returns_string():
    provider = LLMProvider()
    messages = [{"role": "user", "content": "hello"}]
    result = provider.complete(messages)
    assert isinstance(result, str)
    assert "DRY-RUN" in result


def test_default_llm_provider_echoes_last_user_message():
    provider = LLMProvider()
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "What is Two-Rail Encoding?"},
    ]
    result = provider.complete(messages)
    assert "Two-Rail Encoding" in result


# ---------------------------------------------------------------------------
# GeodesicMyceliumAgent tests
# ---------------------------------------------------------------------------

def test_agent_run_dry_run_produces_output():
    agent = GeodesicMyceliumAgent(config=AgentConfig(dry_run=True, max_iterations=3))
    outputs = list(agent.run("hello"))
    assert len(outputs) >= 1
    assert all(isinstance(o, str) for o in outputs)


def test_agent_run_populates_memory():
    backend = InMemoryBackend()
    agent = GeodesicMyceliumAgent(
        config=AgentConfig(dry_run=True),
        memory=backend,
    )
    list(agent.run("test input"))
    assert any(e.content == "test input" for e in backend.recent(20))


def test_agent_tool_call_dry_run_does_not_invoke_tool():
    """In dry-run mode, tool calls should not be dispatched for real."""
    invoked = []

    registry = ToolRegistry()

    @registry.register("real_tool")
    def real_tool(**kwargs):
        invoked.append(kwargs)
        return "should not be called"

    class ToolCallingLLM(LLMProvider):
        def complete(self, messages, **kwargs):
            # First call emits a tool directive; subsequent calls return normal text
            if not invoked and not any("TOOL_CALL" in m.get("content", "") for m in messages):
                return 'TOOL_CALL: real_tool {"key": "value"}'
            return "done"

    agent = GeodesicMyceliumAgent(
        config=AgentConfig(dry_run=True, max_iterations=3),
        llm=ToolCallingLLM(),
        tools=registry,
    )
    outputs = list(agent.run("trigger tool"))
    # The tool should NOT have been invoked because we are in dry-run mode
    assert invoked == []
    # But the dry-run message should appear in the output
    assert any("dry-run" in o for o in outputs)


def test_agent_tool_call_live_mode_invokes_tool():
    """In live mode, registered tools should be dispatched."""
    invoked = []

    registry = ToolRegistry()

    @registry.register("noop_tool")
    def noop_tool(**kwargs):
        invoked.append(kwargs)
        return "result"

    class ToolCallingLLM(LLMProvider):
        _called = False

        def complete(self, messages, **kwargs):
            if not self._called:
                self._called = True
                return 'TOOL_CALL: noop_tool {"x": 1}'
            return "final"

    agent = GeodesicMyceliumAgent(
        config=AgentConfig(dry_run=False, max_iterations=3),
        llm=ToolCallingLLM(),
        tools=registry,
    )
    list(agent.run("go"))
    assert len(invoked) == 1


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_cli_show_docs_exits_zero(capsys):
    exit_code = main(["--show-docs"])
    assert exit_code == 0


def test_cli_dry_run_single_prompt(capsys):
    exit_code = main(["--dry-run", "Explain the Silk damping tail"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "DRY-RUN" in captured.out


def test_cli_default_prompt(capsys):
    """Running with no prompt should use the default smoke-test prompt."""
    exit_code = main([])
    assert exit_code == 0


def test_cli_parser_dry_run_default():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.dry_run is True


def test_cli_parser_no_dry_run():
    parser = build_parser()
    args = parser.parse_args(["--no-dry-run"])
    assert args.dry_run is False


def test_cli_parser_iterations():
    parser = build_parser()
    args = parser.parse_args(["--iterations", "5"])
    assert args.iterations == 5
