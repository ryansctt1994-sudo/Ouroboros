# Geodesic Mycelium Agent

A minimal, dependency-light Python agent scaffold for the Abraxis / Cathedral-OS framework.

## Quick start

```bash
# Dry-run (no API keys required):
python -m geodesic_mycelium_agent --dry-run "Explain the Two-Rail Encoding"

# Show loaded ABRAXIS docs summary:
python -m geodesic_mycelium_agent --show-docs

# Interactive REPL (dry-run):
python -m geodesic_mycelium_agent --interactive
```

## Structure

```
geodesic_mycelium_agent/
├── __init__.py      # Package metadata
├── __main__.py      # python -m entrypoint
├── agent.py         # Core agent loop + extension points
├── cli.py           # Argument parsing + REPL
└── tests/
    └── test_smoke.py  # Smoke tests (no external deps)
```

## Extension points

### 1. LLM provider

```python
from geodesic_mycelium_agent.agent import LLMProvider, GeodesicMyceliumAgent

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        import openai
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    def complete(self, messages, **kwargs):
        resp = self._client.chat.completions.create(
            model=self._model, messages=messages, **kwargs
        )
        return resp.choices[0].message.content

agent = GeodesicMyceliumAgent(llm=OpenAIProvider(api_key="sk-..."))
```

### 2. Tool-calling / MCP servers

```python
from geodesic_mycelium_agent.agent import ToolRegistry

registry = ToolRegistry()

@registry.register("search_docs")
def search_docs(query: str) -> str:
    # Local doc search, Qdrant, or MCP endpoint
    ...

# Or subclass ToolRegistry to forward calls over WebSocket / MCP:
class MCPToolRegistry(ToolRegistry):
    def dispatch(self, name, payload):
        import asyncio, json, websockets
        async def _call():
            async with websockets.connect("ws://localhost:8765") as ws:
                await ws.send(json.dumps({"tool": name, **payload}))
                return json.loads(await ws.recv())
        return asyncio.run(_call())
```

### 3. Persistent memory backend

```python
from geodesic_mycelium_agent.agent import MemoryBackend, MemoryEntry

class QdrantMemoryBackend(MemoryBackend):
    def __init__(self, url: str, collection: str):
        from qdrant_client import QdrantClient
        self._client = QdrantClient(url=url)
        self._collection = collection

    def append(self, entry: MemoryEntry):
        # encode and upsert
        ...

    def recent(self, n=10):
        # scroll latest vectors
        ...
```

## Running tests

```bash
pytest geodesic_mycelium_agent/tests/ -v
```

## Architecture notes

See [`ABRAXIS/CANONICAL_PROGRESSION.md`](../ABRAXIS/CANONICAL_PROGRESSION.md) for the full
conceptual context this agent is designed to operate within.
