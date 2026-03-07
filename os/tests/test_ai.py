#!/usr/bin/env python3
"""
EDEN AI Service Tests
=====================

Unit tests for the v3.0 multi-provider router API.

Author: AIOSPANDORA Development Team
License: MIT
Version: 3.0.0
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path
SCRIPT_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

# Suppress the module-level resolve_ollama_host() probe on first import.
with patch("requests.get", side_effect=Exception("no network")):
    import eden_ai as _eden_ai_module  # noqa: F401

from eden_ai import resolve_ollama_host, LLMRouter, EdenAI


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(status_code: int, body: dict) -> MagicMock:
    """Build a fake requests.Response."""
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = body
    r.raise_for_status = MagicMock()
    return r


def _make_ai(**kwargs) -> EdenAI:
    """Return an EdenAI instance with the Ollama connectivity check suppressed."""
    with patch("requests.get", side_effect=Exception("no network")):
        return EdenAI(**kwargs)


# ---------------------------------------------------------------------------
# resolve_ollama_host
# ---------------------------------------------------------------------------

class TestResolveOllamaHost(unittest.TestCase):
    """Tests for the host-probing function."""

    def test_env_override_skips_probing(self):
        """When OLLAMA_HOST is set, resolve_ollama_host returns it immediately."""
        with patch.dict(os.environ, {"OLLAMA_HOST": "http://custom-host:9999"}):
            with patch("requests.get") as mock_get:
                result = resolve_ollama_host()
        self.assertEqual(result, "http://custom-host:9999")
        mock_get.assert_not_called()

    def test_lima_host_reachable(self):
        """When the Lima host responds 200, it is returned first."""
        ok = _make_response(200, {"models": []})
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OLLAMA_HOST", None)
            with patch("requests.get", return_value=ok):
                result = resolve_ollama_host()
        self.assertEqual(result, "http://host.lima.internal:11434")

    def test_fallback_to_localhost_when_lima_unreachable(self):
        """When Lima times out but localhost responds, localhost is returned."""
        import requests as req
        ok = _make_response(200, {"models": []})

        def side_effect(url, **kwargs):
            if "lima" in url:
                raise req.exceptions.ConnectionError("unreachable")
            return ok

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OLLAMA_HOST", None)
            with patch("requests.get", side_effect=side_effect):
                result = resolve_ollama_host()
        self.assertEqual(result, "http://localhost:11434")

    def test_default_when_neither_reachable(self):
        """When neither host responds, localhost is the safe default."""
        import requests as req
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OLLAMA_HOST", None)
            with patch("requests.get", side_effect=req.exceptions.ConnectionError):
                result = resolve_ollama_host()
        self.assertEqual(result, "http://localhost:11434")


# ---------------------------------------------------------------------------
# LLMRouter provider registration
# ---------------------------------------------------------------------------

class TestLLMRouterProviders(unittest.TestCase):
    """Test that LLMRouter registers only providers whose env vars are set."""

    def test_no_keys_registers_no_cloud_providers(self):
        env = {"GROQ_API_KEY": "", "TOGETHER_API_KEY": "", "MISTRAL_API_KEY": ""}
        with patch.dict(os.environ, env):
            router = LLMRouter()
        self.assertEqual(router.providers, [])

    def test_single_key_registers_one_provider(self):
        env = {"GROQ_API_KEY": "test-groq-key",
               "TOGETHER_API_KEY": "", "MISTRAL_API_KEY": ""}
        with patch.dict(os.environ, env):
            router = LLMRouter()
        self.assertEqual(len(router.providers), 1)
        self.assertEqual(router.providers[0].name, "Groq")

    def test_all_keys_registers_three_providers(self):
        env = {"GROQ_API_KEY": "g", "TOGETHER_API_KEY": "t", "MISTRAL_API_KEY": "m"}
        with patch.dict(os.environ, env):
            router = LLMRouter()
        names = [p.name for p in router.providers]
        self.assertIn("Groq", names)
        self.assertIn("Together", names)
        self.assertIn("Mistral", names)


# ---------------------------------------------------------------------------
# _call_ollama failure handling
# ---------------------------------------------------------------------------

class TestCallOllamaFailure(unittest.TestCase):
    """_call_ollama must return None on any RequestException."""

    def setUp(self):
        self.router = LLMRouter()

    def test_connection_error_returns_none(self):
        import requests as req
        with patch("requests.post", side_effect=req.exceptions.ConnectionError("refused")):
            result = self.router._call_ollama(
                [{"role": "user", "content": "hello"}], 64, 0.7
            )
        self.assertIsNone(result)

    def test_timeout_returns_none(self):
        import requests as req
        with patch("requests.post", side_effect=req.exceptions.Timeout("timeout")):
            result = self.router._call_ollama(
                [{"role": "user", "content": "hello"}], 64, 0.7
            )
        self.assertIsNone(result)

    def test_http_error_returns_none(self):
        import requests as req
        bad = _make_response(503, {})
        bad.raise_for_status.side_effect = req.exceptions.HTTPError("503")
        with patch("requests.post", return_value=bad):
            result = self.router._call_ollama(
                [{"role": "user", "content": "hello"}], 64, 0.7
            )
        self.assertIsNone(result)

    def test_successful_call_returns_text(self):
        ok = _make_response(200, {"response": "Hello from Ollama"})
        with patch("requests.post", return_value=ok):
            result = self.router._call_ollama(
                [{"role": "user", "content": "hello"}], 64, 0.7
            )
        self.assertEqual(result, "Hello from Ollama")


# ---------------------------------------------------------------------------
# EdenAI cache — LRU behaviour
# ---------------------------------------------------------------------------

class TestEdenAICacheLRU(unittest.TestCase):
    """Cache must evict the least-recently-used entry, not the oldest inserted."""

    def _cache_key(self, ai, text):
        return ai._generate_cache_key(
            [{"role": "user", "content": text}], 0.7, 512
        )

    def test_lru_eviction_not_fifo(self):
        """Access key1 after key2 so key2 is LRU; adding key4 must evict key2."""
        ai = _make_ai(cache_size=3)
        ai.model_loaded = True

        call_count = [0]
        responses = ["resp-1", "resp-2", "resp-3", "resp-4"]

        def fake_query(messages, max_tokens, temperature):
            r = responses[call_count[0]]
            call_count[0] += 1
            return r

        ai.router.query = fake_query
        msgs = lambda t: [{"role": "user", "content": t}]

        # Fill cache: key1, key2, key3
        self.assertEqual(ai.generate(msgs("key1")), "resp-1")
        self.assertEqual(ai.generate(msgs("key2")), "resp-2")
        self.assertEqual(ai.generate(msgs("key3")), "resp-3")

        # Touch key1 → key1 is now MRU, key2 is LRU
        ai.generate(msgs("key1"))

        # key4 must evict key2 (LRU), not key1 (MRU)
        self.assertEqual(ai.generate(msgs("key4")), "resp-4")

        self.assertEqual(ai.generate(msgs("key1")), "resp-1")          # still cached
        self.assertIsNone(ai._cache.get(self._cache_key(ai, "key2")))  # evicted
        self.assertEqual(ai.generate(msgs("key3")), "resp-3")          # still cached

    def test_cache_hit_does_not_call_router(self):
        ai = _make_ai(cache_size=10)
        ai.model_loaded = True
        ai.router.query = MagicMock(return_value="answer")

        msgs = [{"role": "user", "content": "repeat me"}]
        first = ai.generate(msgs)
        second = ai.generate(msgs)

        self.assertEqual(first, second)
        ai.router.query.assert_called_once()  # second call served from cache


# ---------------------------------------------------------------------------
# EdenAI.search_vectors
# ---------------------------------------------------------------------------

class TestEdenAISearchVectors(unittest.TestCase):

    def setUp(self):
        self.ai = _make_ai()
        self.ai.vectors_data = {
            "vectors": [
                {"name": "calculate_sum",
                 "docstring": "calculate the sum of numbers", "module": "math"},
                {"name": "calculate_product",
                 "docstring": "calculate the product of numbers", "module": "math"},
                {"name": "format_string",
                 "docstring": "format a string", "module": "text"},
            ]
        }

    def test_no_data_returns_empty(self):
        self.ai.vectors_data = None
        self.assertEqual(self.ai.search_vectors("anything"), [])

    def test_keyword_match(self):
        results = self.ai.search_vectors("calculate")
        self.assertEqual(len(results), 2)
        names = {r["name"] for r in results}
        self.assertIn("calculate_sum", names)
        self.assertIn("calculate_product", names)

    def test_limit_respected(self):
        results = self.ai.search_vectors("numbers", limit=1)
        self.assertEqual(len(results), 1)

    def test_no_match_returns_empty(self):
        results = self.ai.search_vectors("xyzzy")
        self.assertEqual(results, [])


# ---------------------------------------------------------------------------
# EdenAI.generate
# ---------------------------------------------------------------------------

class TestEdenAIGenerate(unittest.TestCase):

    def test_raises_when_no_provider_available(self):
        ai = _make_ai()
        ai.model_loaded = False
        with self.assertRaises(RuntimeError):
            ai.generate([{"role": "user", "content": "hello"}])

    def test_raises_when_all_providers_fail(self):
        ai = _make_ai()
        ai.model_loaded = True
        ai.router.query = MagicMock(return_value=None)
        with self.assertRaises(RuntimeError):
            ai.generate([{"role": "user", "content": "hello"}])

    def test_returns_string_from_router(self):
        ai = _make_ai()
        ai.model_loaded = True
        ai.router.query = MagicMock(return_value="Hello from AI")
        result = ai.generate([{"role": "user", "content": "hi"}])
        self.assertIsInstance(result, str)
        self.assertEqual(result, "Hello from AI")


# ---------------------------------------------------------------------------
# EdenAI.get_status
# ---------------------------------------------------------------------------

class TestEdenAIGetStatus(unittest.TestCase):

    def test_status_keys_present(self):
        ai = _make_ai()
        status = ai.get_status()
        for key in ("backend", "ollama_host", "ollama_model", "cloud_providers",
                    "last_provider", "model_loaded", "vectors_loaded",
                    "vector_count", "cache_size"):
            self.assertIn(key, status)

    def test_cache_size_reflects_entries(self):
        ai = _make_ai(cache_size=10)
        ai.model_loaded = True
        ai.router.query = MagicMock(return_value="hi")
        ai.generate([{"role": "user", "content": "test"}])
        self.assertEqual(ai.get_status()["cache_size"], 1)


if __name__ == "__main__":
    unittest.main()
