#!/usr/bin/env python3
"""
EDEN AI Service
===============

Local AI assistant using llama-cpp-python for CPU-only inference.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator

logger = logging.getLogger("eden_ai")


class EdenAI:
    """
    AI service for EDEN using local GGUF models via llama-cpp-python.
    
    Supports both streaming and non-streaming generation, with graceful
    degradation when llama-cpp-python is not available.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the AI service.
        
        Args:
            model_path: Path to GGUF model file. If None, uses default location.
        
        Raises:
            ImportError: If llama-cpp-python is not installed (with instructions)
            FileNotFoundError: If model file is not found
        """
        self.model = None
        self.model_loaded = False
        self.vectors_data = None
        
        # Determine model path
        if model_path is None:
            model_dir = Path.home() / ".local" / "eden" / "models"
            # Look for any .gguf file in the directory
            if model_dir.exists():
                gguf_files = list(model_dir.glob("*.gguf"))
                if gguf_files:
                    model_path = str(gguf_files[0])
        
        self.model_path = model_path
        
        # Try to import llama-cpp-python
        try:
            from llama_cpp import Llama
            self.Llama = Llama
            self._llama_available = True
        except ImportError:
            self._llama_available = False
            logger.warning(
                "llama-cpp-python not installed. AI features will be unavailable.\n"
                "To install: pip install llama-cpp-python"
            )
            return
        
        # Try to load model if path is provided
        if self.model_path and os.path.exists(self.model_path):
            try:
                logger.info(f"Loading model from {self.model_path}")
                self.model = self.Llama(
                    model_path=self.model_path,
                    n_ctx=2048,  # Context window
                    n_threads=4,  # CPU threads
                    n_gpu_layers=0,  # CPU-only
                    verbose=False
                )
                self.model_loaded = True
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self.model_loaded = False
        else:
            logger.warning(
                f"Model file not found at {self.model_path}. "
                "AI features will be unavailable until a model is loaded."
            )
    
    def load_vectors(self, vectors_path: str = "vectors.json") -> bool:
        """
        Load vectors.json for code context.
        
        Args:
            vectors_path: Path to vectors.json file
        
        Returns:
            True if loaded successfully, False otherwise
        """
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
        """
        Search vectors for relevant code units based on query.
        
        Simple keyword matching for MVP. Returns code units that match
        any of the query keywords.
        
        Args:
            query: Search query
            limit: Maximum number of results
        
        Returns:
            List of matching code vectors
        """
        if not self.vectors_data:
            return []
        
        # Extract keywords from query (simple tokenization)
        keywords = query.lower().split()
        
        # Search vectors
        results = []
        for vector in self.vectors_data.get('vectors', []):
            score = 0
            
            # Check name
            name = vector.get('name', '').lower()
            for keyword in keywords:
                if keyword in name:
                    score += 2
            
            # Check docstring
            docstring = vector.get('docstring', '').lower()
            for keyword in keywords:
                if keyword in docstring:
                    score += 1
            
            # Check module
            module = vector.get('module', '').lower()
            for keyword in keywords:
                if keyword in module:
                    score += 1
            
            if score > 0:
                results.append({
                    'vector': vector,
                    'score': score
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return [r['vector'] for r in results[:limit]]
    
    def _build_context(self, user_message: str) -> str:
        """
        Build context from vectors.json based on user message.
        
        Args:
            user_message: User's message
        
        Returns:
            Context string to prepend to conversation
        """
        if not self.vectors_data:
            return ""
        
        # Search for relevant code
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
        """
        Generate a response from the AI.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            stream: Whether to stream the response (not implemented in MVP)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated response text
        
        Raises:
            RuntimeError: If model is not loaded or llama-cpp-python not available
        """
        if not self._llama_available:
            raise RuntimeError(
                "llama-cpp-python is not installed. "
                "Install with: pip install llama-cpp-python"
            )
        
        if not self.model_loaded or self.model is None:
            raise RuntimeError(
                "No AI model is loaded. "
                f"Please place a GGUF model at {self.model_path} or specify a valid path."
            )
        
        # Build prompt from messages
        prompt_parts = []
        
        # Add system message (EDEN identity)
        system_msg = (
            "You are EDEN, an AI assistant integrated into the Ouroboros framework. "
            "You help with code understanding, system monitoring, and development tasks. "
            "Be concise and helpful."
        )
        prompt_parts.append(f"System: {system_msg}")
        
        # Add context from vectors if available
        if messages:
            last_user_msg = next((m['content'] for m in reversed(messages) if m['role'] == 'user'), None)
            if last_user_msg:
                context = self._build_context(last_user_msg)
                if context:
                    prompt_parts.append(context)
        
        # Add conversation messages
        for msg in messages:
            role = msg['role'].capitalize()
            content = msg['content']
            prompt_parts.append(f"{role}: {content}")
        
        # Add assistant prompt
        prompt_parts.append("Assistant:")
        
        prompt = "\n\n".join(prompt_parts)
        
        # Generate response
        logger.debug(f"Generating with prompt: {prompt[:100]}...")
        
        if stream:
            # Streaming not fully implemented in MVP
            logger.warning("Streaming not fully implemented, falling back to non-streaming")
        
        response = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["User:", "System:"],
            echo=False
        )
        
        # Extract text from response
        text = response['choices'][0]['text'].strip()
        
        logger.debug(f"Generated response: {text[:100]}...")
        
        return text
    
    def is_available(self) -> bool:
        """
        Check if AI service is available.
        
        Returns:
            True if model is loaded and ready, False otherwise
        """
        return self._llama_available and self.model_loaded
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get AI service status.
        
        Returns:
            Status dictionary
        """
        return {
            "llama_available": self._llama_available,
            "model_loaded": self.model_loaded,
            "model_path": self.model_path,
            "vectors_loaded": self.vectors_data is not None,
            "vector_count": len(self.vectors_data.get('vectors', [])) if self.vectors_data else 0
        }
