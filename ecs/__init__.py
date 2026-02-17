"""
ECS Integration Layer

This module provides the integration layer for the EDEN-ECS framework,
including runtime vectorization, manuscript validation, and system adapters.
"""

from .runtime_vectorizer import RuntimeVectorizer
from .manuscript_validator import ManuscriptValidator
from .orchestrator import ECSOrchestrator

__all__ = [
    'RuntimeVectorizer',
    'ManuscriptValidator',
    'ECSOrchestrator',
]

__version__ = '1.0.0'
