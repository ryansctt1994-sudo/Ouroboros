"""Geodesic Mycelium Agent — core agent loop.

Extension points
----------------
LLM provider
    Subclass :class:`LLMProvider` and pass an instance to :class:`GeodesicMyceliumAgent`.

Tool-calling / MCP
    Subclass :class:`ToolRegistry` and register tool handlers.  The agent calls
    ``registry.dispatch(tool_name, payload)`` at each tool-call step.

Persistent memory backend
    Subclass :class:`MemoryBackend` and pass an instance to the agent.  The
    default :class:`InMemoryBackend` stores everything in a plain Python list.
"""

from __future__ import annotations

import json
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any, Iterator

# ---------------------------------------------------------------------------
# Extension point 1 — LLM provider
# ---------------------------------------------------------------------------

class LLMProvider:
    """Base class for LLM providers.

    Subclass this to connect a real language-model backend.

    Example::

        class OpenAIProvider(LLMProvider):
            def __init__(self, api_key: str, model: str = "gpt-4o"):
                import openai
                self._client = openai.OpenAI(api_key=api_key)
                self._model = model

            def complete(self, messages: list[dict], **kwargs) -> str:
                resp = self._client.chat.completions.create(
                    model=self._model, messages=messages, **kwargs
                )
                return resp.choices[0].message.content
    """

    def complete(self, messages: list[dict], **kwargs: Any) -> str:
        """Return a completion string for the given message list.

        The default implementation is a dry-run stub that echoes the last
        user message back with a ``[DRY-RUN]`` prefix.
        """
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "(no user message)",
        )
        return f"[DRY-RUN] echo: {last_user}"


# ---------------------------------------------------------------------------
# Extension point 2 — Tool-calling / MCP
# ---------------------------------------------------------------------------

class ToolRegistry:
    """Registry of callable tools exposed to the agent.

    Register tools with :meth:`register`::

        registry = ToolRegistry()

        @registry.register("search_docs")
        def search_docs(query: str) -> str:
            ...

    Subclass and override :meth:`dispatch` to integrate an MCP server or
    WebSocket-based tool router.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, Any] = {}

    def register(self, name: str):
        """Decorator to register a tool handler under *name*."""
        def decorator(fn):
            self._handlers[name] = fn
            return fn
        return decorator

    def list_tools(self) -> list[str]:
        """Return names of all registered tools."""
        return list(self._handlers.keys())

    def dispatch(self, name: str, payload: dict) -> Any:
        """Invoke tool *name* with *payload*.

        Raises :class:`KeyError` if *name* is not registered.

        Override this method to forward calls to an MCP server::

            class MCPToolRegistry(ToolRegistry):
                def dispatch(self, name, payload):
                    import websockets, asyncio, json
                    async def _call():
                        async with websockets.connect(self._ws_url) as ws:
                            await ws.send(json.dumps({"tool": name, **payload}))
                            return json.loads(await ws.recv())
                    return asyncio.run(_call())
        """
        if name not in self._handlers:
            raise KeyError(f"Unknown tool: {name!r}")
        return self._handlers[name](**payload)


# ---------------------------------------------------------------------------
# Extension point 3 — Persistent memory backend
# ---------------------------------------------------------------------------

@dataclass
class MemoryEntry:
    role: str
    content: str
    metadata: dict = field(default_factory=dict)


class MemoryBackend:
    """Base class for memory backends.

    Subclass to plug in Qdrant, Neo4j/KyuGraph, or any other store::

        class QdrantMemoryBackend(MemoryBackend):
            def __init__(self, url: str, collection: str):
                from qdrant_client import QdrantClient
                self._client = QdrantClient(url=url)
                self._collection = collection

            def append(self, entry):
                # upsert vector embedding ...
                pass

            def recent(self, n):
                # scroll last n entries ...
                return []
    """

    def append(self, entry: MemoryEntry) -> None:
        raise NotImplementedError

    def recent(self, n: int = 10) -> list[MemoryEntry]:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class InMemoryBackend(MemoryBackend):
    """Simple in-process list-based memory (default)."""

    def __init__(self) -> None:
        self._entries: list[MemoryEntry] = []

    def append(self, entry: MemoryEntry) -> None:
        self._entries.append(entry)

    def recent(self, n: int = 10) -> list[MemoryEntry]:
        return self._entries[-n:]

    def clear(self) -> None:
        self._entries.clear()


# ---------------------------------------------------------------------------
# Docs loader
# ---------------------------------------------------------------------------

_REPO_ROOT = pathlib.Path(__file__).parent.parent


def load_canonical_progression() -> str:
    """Return the text of ABRAXIS/CANONICAL_PROGRESSION.md, or an empty string."""
    path = _REPO_ROOT / "ABRAXIS" / "CANONICAL_PROGRESSION.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def load_docs_index() -> str:
    """Return the text of ABRAXIS/INDEX.md, or an empty string."""
    path = _REPO_ROOT / "ABRAXIS" / "INDEX.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def load_knowledge_base() -> dict:
    """Return the parsed knowledge_base.json at the repo root, or empty dict."""
    path = _REPO_ROOT / "knowledge_base.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

@dataclass
class AgentConfig:
    """Configuration for :class:`GeodesicMyceliumAgent`."""
    max_iterations: int = 10
    system_prompt: str = (
        "You are the Geodesic Mycelium Agent, an orchestrator operating within the "
        "Abraxis/Cathedral-OS framework.  You reason through problems step-by-step, "
        "call registered tools when needed, and persist conclusions to memory."
    )
    dry_run: bool = True
    canonical_doc_excerpt_chars: int = 2000
    docs_index_excerpt_chars: int = 500
    memory_window: int = 8


class GeodesicMyceliumAgent:
    """Minimal agent loop with pluggable LLM, tools, and memory.

    Parameters
    ----------
    config:
        Runtime configuration.
    llm:
        LLM provider instance.  Defaults to the dry-run stub.
    tools:
        Tool registry.  Defaults to an empty registry.
    memory:
        Memory backend.  Defaults to :class:`InMemoryBackend`.
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        llm: LLMProvider | None = None,
        tools: ToolRegistry | None = None,
        memory: MemoryBackend | None = None,
    ) -> None:
        self.config = config or AgentConfig()
        self.llm = llm or LLMProvider()
        self.tools = tools or ToolRegistry()
        self.memory = memory or InMemoryBackend()

        # Load canonical docs into system context on start-up
        self._canonical_doc = load_canonical_progression()
        self._docs_index = load_docs_index()
        self._knowledge_base = load_knowledge_base()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, user_input: str) -> Iterator[str]:
        """Run a single agent turn, yielding incremental output lines.

        The loop follows a simplified ReAct pattern:
        1. Build context (system prompt + docs + recent memory + user input)
        2. Call LLM
        3. Parse any tool calls from the response
        4. Dispatch tools and append results to memory
        5. Yield final assistant response
        """
        self.memory.append(MemoryEntry(role="user", content=user_input))

        messages = self._build_messages(user_input)

        for iteration in range(self.config.max_iterations):
            response = self.llm.complete(messages)
            yield response

            tool_calls = self._extract_tool_calls(response)
            if not tool_calls:
                # No tool calls — we are done
                self.memory.append(MemoryEntry(role="assistant", content=response))
                return

            for tool_name, payload in tool_calls:
                tool_result = self._safe_dispatch(tool_name, payload)
                result_text = f"[tool:{tool_name}] {tool_result}"
                yield result_text
                messages.append({"role": "tool", "content": result_text})

            # Feed tool results back for next iteration
            messages.append({"role": "assistant", "content": response})

        # Max iterations reached
        yield "[agent] max_iterations reached — stopping."

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_messages(self, user_input: str) -> list[dict]:
        system_parts = [self.config.system_prompt]

        if self._canonical_doc:
            excerpt = self._canonical_doc[:self.config.canonical_doc_excerpt_chars]
            system_parts.append(f"\n\n--- Canonical Progression (excerpt) ---\n{excerpt}")

        if self._docs_index:
            excerpt = self._docs_index[:self.config.docs_index_excerpt_chars]
            system_parts.append(f"\n\n--- Docs Index (excerpt) ---\n{excerpt}")

        messages: list[dict] = [{"role": "system", "content": "\n".join(system_parts)}]

        for entry in self.memory.recent(self.config.memory_window):
            messages.append({"role": entry.role, "content": entry.content})

        messages.append({"role": "user", "content": user_input})
        return messages

    def _extract_tool_calls(self, response: str) -> list[tuple[str, dict]]:
        """Parse ``TOOL_CALL: <name> <json_payload>`` directives from the response."""
        calls = []
        pattern = re.compile(r"TOOL_CALL:\s*(\w+)\s+(\{.*?\})", re.DOTALL)
        for match in pattern.finditer(response):
            name = match.group(1)
            try:
                payload = json.loads(match.group(2))
            except json.JSONDecodeError:
                payload = {}
            calls.append((name, payload))
        return calls

    def _safe_dispatch(self, name: str, payload: dict) -> str:
        if self.config.dry_run:
            return f"[dry-run] would call {name!r} with {payload}"
        try:
            result = self.tools.dispatch(name, payload)
            return str(result)
        except KeyError as exc:
            return f"[error] {exc}"
        except Exception as exc:  # noqa: BLE001
            return f"[error] tool raised {type(exc).__name__}: {exc}"
