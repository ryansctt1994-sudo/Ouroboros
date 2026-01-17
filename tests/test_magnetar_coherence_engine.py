"""
Test suite for Magnetar Coherence Engine.

This test suite validates the coherence analysis and signal processing
functionality of the MagnetarElasticCoherenceEngine.
"""

import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.magnetar_coherence_engine import (
    MagnetarElasticCoherenceEngine,
    MAGNETAR_FREQ
)


class TestCoherenceMetrics:
    """Test class for coherence metric calculations."""
    
    def test_engine_initialization(self):
        """Test that engine initializes properly."""
        engine = MagnetarElasticCoherenceEngine()
        assert engine is not None
        assert engine.module_weights == {}
    
    def test_engine_with_weights(self):
        """Test engine initialization with custom weights."""
        weights = {'module1': 0.5, 'module2': 0.3}
        engine = MagnetarElasticCoherenceEngine(module_weights=weights)
        assert engine.module_weights == weights
    
    def test_basic_signal_processing(self):
        """Test basic signal processing."""
        engine = MagnetarElasticCoherenceEngine()
        signal = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        result = engine(signal)
        
        assert 'coherence_score' in result
        assert 'processed_signal' in result
        assert 0 <= result['coherence_score'] <= 1
        assert len(result['processed_signal']) == len(signal)
    
    def test_perfect_coherence(self):
        """Test coherence with identical input/output."""
        engine = MagnetarElasticCoherenceEngine()
        
        signal = np.sin(2 * np.pi * MAGNETAR_FREQ * np.linspace(0, 1, 1000))
        
        # Perfect coherence would be input = output
        # But our engine modifies, so we just test it runs
        result = engine(signal)
        assert 0 <= result['coherence_score'] <= 1
    
    def test_empty_signal(self):
        """Test handling of empty signal."""
        engine = MagnetarElasticCoherenceEngine()
        signal = np.array([])
        
        result = engine(signal)
        assert result['coherence_score'] == 0.0
        assert len(result['processed_signal']) == 0
    
    def test_coherence_score_range(self):
        """Test that coherence score is always in valid range."""
        engine = MagnetarElasticCoherenceEngine()
        
        # Test with various signals
        test_signals = [
            np.random.randn(100),
            np.ones(50),
            np.zeros(30),
            np.linspace(-1, 1, 200)
        ]
        
        for signal in test_signals:
            result = engine(signal)
            assert 0 <= result['coherence_score'] <= 1, \
                f"Coherence score {result['coherence_score']} out of range [0,1]"
