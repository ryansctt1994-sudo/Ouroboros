#!/usr/bin/env python3
"""
EDEN AI Service
===============

Multi-provider LLM router with local Ollama fallback.
Tries free cloud APIs first for speed, falls back to local Ollama.

Provider order: Groq → Together → Mistral → Local Ollama
All API keys via environment variables. No keys = local only.

Author: AIOSPANDORA Development Team
License: MIT
Version: 3.0.0 - Multi-Provider Router
"""

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

import requests

from performance import LRUCache

logger = logging.getLogger("eden_ai")


def resolve_ollama_host() -> str:
    """Return the Ollama base URL to use.

    Priority:
    1. ``OLLAMA_HOST`` environment variable — used as-is, no probing.
    2. ``http://host.lima.internal:11434`` — works inside a Lima VM.
    3. ``http://localhost:11434`` — macOS directly / Linux / Docker.

    Each candidate is probed with a 1-second timeout so startup is never
    delayed by more than ~2 seconds when Ollama is absent.
    """
    if "OLLAMA_HOST" in os.environ:
        return os.environ["OLLAMA_HOST"]

    candidates = [
        "http://host.lima.internal:11434",
        "http://localhost:11434",
    ]
    for host in candidates:
        try:
            r = requests.get(f"{host}/api/tags", timeout=1)
            if r.status_code == 200:
                logger.info(f"Ollama reachable at {host}")
                return host
        except Exception:
            pass

    logger.warning(
        "Ollama not reachable at any candidate host; defaulting to http://localhost:11434"
    )
    return "http://localhost:11434"


# Resolved once at import time — no per-request overhead.
OLLAMA_HOST = resolve_ollama_host()
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "deepseek-coder:6.7b")

SYSTEM_PROMPT = (
    "You are EDEN, an AI assistant integrated into the Ouroboros framework. "
    "You help with code understanding, system monitoring, and development tasks. "
    "Be concise and helpful."
)


@dataclass
class ProviderConfig:
    name: str
    api_base: str
    api_key_env: str
    model: str
    rate_limit_rpm: int
    request_timestamps: list = field(default_factory=list)


class LLMRouter:
    """
    Routes to the fastest available free provider.
    Falls back to local Ollama when cloud APIs are exhausted.
    """

    def __init__(self):
        self.providers: List[ProviderConfig] = []
        self._init_providers()
        self.last_provider = None

    def _init_providers(self):
        """Register providers that have API keys set."""
        configs = [
            ("Groq", "https://api.groq.com/openai/v1/chat/completions",
             "GROQ_API_KEY", "llama-3.3-70b-versatile", 30),
            ("Together", "https://api.together.xyz/v1/chat/completions",
             "TOGETHER_API_KEY", "mistralai/Mixtral-8x7B-Instruct-v0.1", 60),
            ("Mistral", "https://api.mistral.ai/v1/chat/completions",
             "MISTRAL_API_KEY", "mistral-small-latest", 1),
        ]
        for name, base, env, model, rpm in configs:
            if os.getenv(env):
                self.providers.append(ProviderConfig(
                    name=name, api_base=base, api_key_env=env,
                    model=model, rate_limit_rpm=rpm
                ))
                logger.info(f"Router: {name} provider registered")

        if not self.providers:
            logger.info("Router: No cloud API keys found, using Ollama only")

    def _check_rate_limit(self, provider: ProviderConfig) -> bool:
        """Return True if we can make a request (token bucket by minute)."""
        now = time.time()
        cutoff = now - 60
        provider.request_timestamps = [
            t for t in provider.request_timestamps if t > cutoff
        ]
        return len(provider.request_timestamps) < provider.rate_limit_rpm

    def _call_cloud(self, provider: ProviderConfig, messages: list,
                    max_tokens: int, temperature: float) -> Optional[str]:
        """Call an OpenAI-compatible cloud API."""
        if not self._check_rate_limit(provider):
            logger.info(f"Router: {provider.name} rate limited, skipping")
            return None

        headers = {
            "Authorization": f"Bearer {os.getenv(provider.api_key_env)}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": provider.model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            r = requests.post(provider.api_base, headers=headers,
                              json=payload, timeout=30)
            if r.status_code == 200:
                provider.request_timestamps.append(time.time())
                text = r.json()["choices"][0]["message"]["content"]
                self.last_provider = provider.name
                logger.info(f"Router: Response from {provider.name}")
                return text.strip()
            elif r.status_code == 429:
                logger.info(f"Router: {provider.name} returned 429, skipping")
                return None
            else:
                logger.warning(f"Router: {provider.name} error {r.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.warning(f"Router: {provider.name} timed out")
            return None
        except Exception as e:
            logger.warning(f"Router: {provider.name} exception: {e}")
            return None

    def _call_ollama(self, messages: list, max_tokens: int,
                     temperature: float) -> Optional[str]:
        """Call local Ollama as final fallback. Returns None if unreachable."""
        parts = [f"System: {SYSTEM_PROMPT}"]
        for m in messages:
            role = m["role"].capitalize()
            parts.append(f"{role}: {m['content']}")
        parts.append("Assistant:")
        full_prompt = "\n\n".join(parts)

        try:
            r = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                        "stop": ["User:", "System:"]
                    }
                },
                timeout=300  # local can be slow
            )
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            return None

        self.last_provider = f"Ollama ({OLLAMA_MODEL})"
        return r.json().get("response", "").strip()

    def query(self, messages: list, max_tokens: int = 512,
              temperature: float = 0.7) -> str:
        """Try cloud providers in order, fall back to Ollama."""
        for provider in self.providers:
            result = self._call_cloud(provider, messages, max_tokens, temperature)
            if result:
                return result

        logger.info("Router: Using local Ollama")
        return self._call_ollama(messages, max_tokens, temperature)


class EdenAI:
    """
    AI service for EDEN. Uses LLMRouter for multi-provider support.
    Maintains full API compatibility with eden_daemon.py.
    """

    def __init__(self, model_path: Optional[str] = None, cache_size: int = 100):
        self.model_loaded = False
        self.vectors_data = None
        self.model_path = model_path
        self._cache_enabled = cache_size > 0
        self._max_cache = cache_size
        self._cache = LRUCache(max_size=cache_size) if cache_size > 0 else None
        self.router = LLMRouter()

        # Test Ollama connection
        try:
            r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                if any(OLLAMA_MODEL in m for m in models):
                    self.model_loaded = True
                    logger.info(f"Ollama connected. Model: {OLLAMA_MODEL}")
                else:
                    logger.warning(f"Ollama running but {OLLAMA_MODEL} not found")
            # Even without Ollama, cloud providers may work
            if self.router.providers:
                self.model_loaded = True
        except Exception as e:
            logger.warning(f"Cannot connect to Ollama: {e}")
            if self.router.providers:
                self.model_loaded = True
                logger.info("Cloud providers available as fallback")

    def load_vectors(self, vectors_path: str = "vectors.json") -> bool:
        try:
            if os.path.exists(vectors_path):
                with open(vectors_path, 'r') as f:
                    self.vectors_data = json.load(f)
                logger.info(f"Loaded {len(self.vectors_data.get('vectors', []))} code vectors")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to load vectors.json: {e}")
            return False

    def search_vectors(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.vectors_data:
            return []
        keywords = set(query.lower().split())
        results = []
        for vector in self.vectors_data.get('vectors', []):
            score = 0
            name_lower = vector.get('name', '').lower()
            docstring_lower = vector.get('docstring', '').lower()
            module_lower = vector.get('module', '').lower()
            name_matches = keywords & set(name_lower.split())
            if name_matches:
                score += 2 * len(name_matches)
            for kw in keywords:
                if kw in docstring_lower:
                    score += 1
            if any(kw in module_lower for kw in keywords):
                score += 1
            if score > 0:
                results.append({'vector': vector, 'score': score})
        results.sort(key=lambda x: x['score'], reverse=True)
        return [r['vector'] for r in results[:limit]]

    def _build_context(self, user_message: str) -> str:
        if not self.vectors_data:
            return ""
        relevant = self.search_vectors(user_message, limit=3)
        if not relevant:
            return ""
        parts = ["Relevant code context:"]
        for v in relevant:
            parts.append(f"- {v.get('name', '?')} in {v.get('file_path', '?')}")
            if sig := v.get('signature', ''):
                parts.append(f"  Signature: {sig}")
            if doc := v.get('docstring', ''):
                parts.append(f"  Description: {doc}")
        return "\n".join(parts)

    def generate(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> str:
        if not self.model_loaded:
            raise RuntimeError("No LLM provider available")

        # Check cache
        if self._cache_enabled:
            cache_key = self._generate_cache_key(messages, temperature, max_tokens)
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        # Build context from last user message and prepend if available
        last_user_msg = next(
            (m['content'] for m in reversed(messages) if m['role'] == 'user'), ""
        )
        context = self._build_context(last_user_msg)

        # Inject context into the conversation
        enriched = list(messages)
        if context:
            enriched.insert(0, {"role": "system", "content": context})

        # Route through providers with full conversation
        text = self.router.query(enriched, max_tokens, temperature)

        if text is None:
            raise RuntimeError("All LLM providers failed")

        # Cache
        if self._cache_enabled:
            self._cache.put(cache_key, text)

        return text

    def is_available(self) -> bool:
        return self.model_loaded

    def _generate_cache_key(self, messages, temperature, max_tokens):
        key_data = json.dumps({
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get_status(self) -> Dict[str, Any]:
        cache_size = self._cache.get_stats()['size'] if self._cache_enabled else 0
        return {
            "backend": "multi-provider-router",
            "ollama_host": OLLAMA_HOST,
            "ollama_model": OLLAMA_MODEL,
            "cloud_providers": [p.name for p in self.router.providers],
            "last_provider": self.router.last_provider,
            "model_loaded": self.model_loaded,
            "vectors_loaded": self.vectors_data is not None,
            "vector_count": len(self.vectors_data.get('vectors', [])) if self.vectors_data else 0,
            "cache_size": cache_size
        }

    def get_performance_report(self) -> str:
        providers = ", ".join(p.name for p in self.router.providers) or "none"
        return (f"Router: cloud=[{providers}], "
                f"local=Ollama@{OLLAMA_HOST} ({OLLAMA_MODEL}), "
                f"last_used={self.router.last_provider}")
