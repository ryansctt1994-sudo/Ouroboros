#!/usr/bin/env python3
"""
EDEN AI Service
===============

Local AI assistant using Ollama API for inference.

Author: AIOSPANDORA Development Team
License: MIT
Version: 2.0.0 - Ollama Backend
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

logger = logging.getLogger("eden_ai")

# Ollama API endpoint - use host.lima.internal when inside Lima VM
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://host.lima.internal:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "deepseek-coder:6.7b")


class EdenAI:
    """
    AI service for EDEN using Ollama API backend.
    """

    def __init__(self, model_path: Optional[str] = None, cache_size: int = 100):
        self.model_loaded = False
        self.vectors_data = None
        self.model_path = model_path
        self._cache = {}
        self._cache_enabled = cache_size > 0
        self._max_cache = cache_size

        # Test Ollama connection
        try:
            r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                if any(OLLAMA_MODEL in m for m in models):
                    self.model_loaded = True
                    logger.info(f"Connected to Ollama. Model: {OLLAMA_MODEL}")
                else:
                    logger.warning(f"Ollama running but model {OLLAMA_MODEL} not found. Available: {models}")
            else:
                logger.warning(f"Ollama returned status {r.status_code}")
        except Exception as e:
            logger.warning(f"Cannot connect to Ollama at {OLLAMA_HOST}: {e}")

    def load_vectors(self, vectors_path: str = "vectors.json") -> bool:
        try:
            if os.path.exists(vectors_path):
                with open(vectors_path, 'r') as f:
                    self.vectors_data = json.load(f)
                logger.info(f"Loaded {len(self.vectors_data.get('vectors', []))} code vectors")
                return True
            else:
                logger.warning(f"vectors.json not found at {vectors_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to load vectors.json: {e}")
            return False

    def search_vectors(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.vectors_data:
            return []

        keywords = query.lower().split()
        keyword_set = set(keywords)
        results = []
        vectors = self.vectors_data.get('vectors', [])

        if not vectors:
            return []

        for vector in vectors:
            score = 0
            name_lower = vector.get('name', '').lower()
            docstring_lower = vector.get('docstring', '').lower()
            module_lower = vector.get('module', '').lower()

            name_words = set(name_lower.split())
            name_matches = keyword_set & name_words
            if name_matches:
                score += 2 * len(name_matches)

            for keyword in keywords:
                if keyword in docstring_lower:
                    score += 1

            if any(keyword in module_lower for keyword in keywords):
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

        context_parts = ["Relevant code context:"]
        for vector in relevant:
            name = vector.get('name', 'unknown')
            file_path = vector.get('file_path', 'unknown')
            docstring = vector.get('docstring', '')
            signature = vector.get('signature', '')

            context_parts.append(f"- {name} in {file_path}")
            if signature:
                context_parts.append(f"  Signature: {signature}")
            if docstring:
                context_parts.append(f"  Description: {docstring}")

        return "\n".join(context_parts)

    def generate(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> str:
        if not self.model_loaded:
            raise RuntimeError(
                f"Ollama model {OLLAMA_MODEL} is not available. "
                f"Check that Ollama is running at {OLLAMA_HOST}"
            )

        # Check cache
        if self._cache_enabled:
            cache_key = self._generate_cache_key(messages, temperature, max_tokens)
            if cache_key in self._cache:
                logger.debug("Cache hit")
                return self._cache[cache_key]

        # Build system prompt
        system_msg = (
            "You are EDEN, an AI assistant integrated into the Ouroboros framework. "
            "You help with code understanding, system monitoring, and development tasks. "
            "Be concise and helpful."
        )

        # Add context from vectors if available
        if messages:
            last_user_msg = next(
                (m['content'] for m in reversed(messages) if m['role'] == 'user'), None
            )
            if last_user_msg:
                context = self._build_context(last_user_msg)
                if context:
                    system_msg += "\n\n" + context

        # Build Ollama API request
        prompt_parts = [f"System: {system_msg}"]
        for msg in messages:
            role = msg['role'].capitalize()
            content = msg['content']
            prompt_parts.append(f"{role}: {content}")
        prompt_parts.append("Assistant:")

        prompt = "\n\n".join(prompt_parts)

        logger.debug(f"Sending to Ollama: {prompt[:100]}...")

        try:
            r = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                        "stop": ["User:", "System:"]
                    }
                },
                timeout=120
            )
            r.raise_for_status()
            text = r.json().get("response", "").strip()
        except requests.exceptions.Timeout:
            raise RuntimeError("Ollama request timed out (120s)")
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")

        logger.debug(f"Generated response: {text[:100]}...")

        # Cache result
        if self._cache_enabled:
            if len(self._cache) >= self._max_cache:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
            self._cache[cache_key] = text

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
        return {
            "backend": "ollama",
            "ollama_host": OLLAMA_HOST,
            "ollama_model": OLLAMA_MODEL,
            "model_loaded": self.model_loaded,
            "vectors_loaded": self.vectors_data is not None,
            "vector_count": len(self.vectors_data.get('vectors', [])) if self.vectors_data else 0,
            "cache_size": len(self._cache) if self._cache_enabled else 0
        }

    def get_performance_report(self) -> str:
        return f"Ollama backend at {OLLAMA_HOST} using {OLLAMA_MODEL}"
