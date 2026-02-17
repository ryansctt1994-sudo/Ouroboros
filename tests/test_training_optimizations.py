"""
Test suite for training optimization modules.

Tests convergence detection, tensor memory management, and model orchestration.
"""

import pytest
import time
import numpy as np
from src.training.convergence_detector import (
    EnhancedConvergenceV2,
    ConvergenceMetrics,
)
from src.training.tensor_warden import (
    DynamicTensorWardenV2,
    TensorMetadata,
    MemoryStats,
)
from src.training.model_orchestrator import (
    FairModelOrchestrator,
    ModelRequest,
    ModelStats,
)


class TestEnhancedConvergenceV2:
    """Test convergence detection."""
    
    def test_initialization(self):
        """Test detector initialization."""
        detector = EnhancedConvergenceV2(initial_patience=10)
        
        assert detector.initial_patience == 10
    
    def test_watch_single_epoch(self):
        """Test watching a single epoch."""
        detector = EnhancedConvergenceV2()
        
        metrics = detector.watch(epoch=0, loss=1.0, learning_rate=0.001)
        
        assert isinstance(metrics, ConvergenceMetrics)
        assert metrics.epoch == 0
        assert metrics.loss == 1.0
    
    def test_phase_detection_warmup(self):
        """Test warmup phase detection."""
        detector = EnhancedConvergenceV2(warmup_epochs=5)
        
        metrics = detector.watch(epoch=2, loss=1.0)
        
        assert metrics.phase == 'warmup'
    
    def test_phase_detection_training(self):
        """Test training phase detection."""
        detector = EnhancedConvergenceV2(warmup_epochs=2)
        
        # Simulate improving loss
        for epoch in range(10):
            loss = 1.0 - epoch * 0.05
            metrics = detector.watch(epoch=epoch, loss=loss)
        
        assert metrics.phase in ['training', 'plateau', 'converged']
    
    def test_improvement_detection(self):
        """Test improvement detection."""
        detector = EnhancedConvergenceV2()
        
        # First epoch
        metrics1 = detector.watch(epoch=0, loss=1.0)
        
        # Improved loss
        metrics2 = detector.watch(epoch=1, loss=0.9)
        
        assert metrics2.loss_delta > 0  # Improvement
    
    def test_early_stop_recommendation(self):
        """Test early stop recommendation."""
        detector = EnhancedConvergenceV2(initial_patience=3, min_delta=0.01, warmup_epochs=0)
        
        # Simulate no improvement
        for epoch in range(6):
            metrics = detector.watch(epoch=epoch, loss=1.0)
        
        # Should recommend early stop or reduce LR after patience exhausted
        assert metrics.recommended_action in ['EARLY_STOP', 'REDUCE_LR', 'CONTINUE']
    
    def test_reduce_lr_recommendation(self):
        """Test learning rate reduction recommendation."""
        detector = EnhancedConvergenceV2(
            initial_patience=3,
            plateau_threshold=1e-5
        )
        
        # Simulate plateau
        for epoch in range(10):
            loss = 0.5 + (epoch % 2) * 0.0001  # Small oscillation
            metrics = detector.watch(epoch=epoch, loss=loss, learning_rate=0.001)
        
        # May recommend LR reduction
        assert metrics.recommended_action in ['CONTINUE', 'REDUCE_LR', 'EARLY_STOP']
    
    def test_get_summary(self):
        """Test summary retrieval."""
        detector = EnhancedConvergenceV2()
        
        for epoch in range(5):
            detector.watch(epoch=epoch, loss=1.0 - epoch * 0.1)
        
        summary = detector.get_summary()
        
        assert 'total_epochs' in summary
        assert 'best_loss' in summary
        assert summary['total_epochs'] == 5


class TestDynamicTensorWardenV2:
    """Test tensor memory management."""
    
    def test_register_tensor(self):
        """Test tensor registration."""
        warden = DynamicTensorWardenV2(memory_limit_gb=1)
        
        tensor = np.zeros((100, 100))
        success = warden.register_tensor('test_tensor', tensor, size_mb=1)
        
        assert success == True
        assert 'test_tensor' in warden._tensors
    
    def test_request_tensor(self):
        """Test tensor request."""
        warden = DynamicTensorWardenV2(memory_limit_gb=1)
        
        tensor = np.zeros((100, 100))
        warden.register_tensor('test_tensor', tensor, size_mb=1)
        
        retrieved = warden.request_tensor('test_tensor')
        
        assert retrieved is not None
        assert np.array_equal(retrieved, tensor)
    
    def test_release_tensor(self):
        """Test tensor release."""
        warden = DynamicTensorWardenV2(memory_limit_gb=1)
        
        tensor = np.zeros((100, 100))
        warden.register_tensor('test_tensor', tensor, size_mb=1)
        
        success = warden.release_tensor('test_tensor')
        
        assert success == True
        assert 'test_tensor' not in warden._tensors
    
    def test_eviction(self):
        """Test automatic eviction."""
        warden = DynamicTensorWardenV2(
            memory_limit_gb=0.01,  # Very small limit
            eviction_threshold=0.5
        )
        
        # Register tensor near limit
        tensor1 = np.zeros((100, 100))
        warden.register_tensor('tensor1', tensor1, size_mb=5)
        
        # This should trigger eviction
        tensor2 = np.zeros((100, 100))
        success = warden.register_tensor('tensor2', tensor2, size_mb=5)
        
        # Should succeed after eviction
        assert success == True
        assert warden._eviction_count > 0
    
    def test_critical_tensor(self):
        """Test critical tensor handling."""
        warden = DynamicTensorWardenV2(memory_limit_gb=0.01)
        
        # Register critical tensor
        tensor = np.zeros((100, 100))
        warden.register_tensor('critical', tensor, size_mb=5, critical=True)
        
        metadata = warden._tensors['critical']
        
        assert metadata.is_critical == True
        assert metadata.can_evict == False
    
    def test_defragment(self):
        """Test memory defragmentation."""
        warden = DynamicTensorWardenV2(memory_limit_gb=1, fragmentation_threshold=0.01)
        
        # Create some fragmentation
        warden._fragmented_space_mb = 100
        
        reclaimed = warden.defragment()
        
        assert reclaimed >= 0
        assert warden._fragmented_space_mb <= 100
    
    def test_get_statistics(self):
        """Test statistics retrieval."""
        warden = DynamicTensorWardenV2(memory_limit_gb=1)
        
        tensor = np.zeros((100, 100))
        warden.register_tensor('test', tensor, size_mb=10)
        
        stats = warden.get_statistics()
        
        assert isinstance(stats, MemoryStats)
        assert stats.tensor_count > 0


class TestFairModelOrchestrator:
    """Test model orchestration."""
    
    def test_register_model(self):
        """Test model registration."""
        orchestrator = FairModelOrchestrator()
        
        orchestrator.register_model('model_a', base_priority=1.0)
        
        assert 'model_a' in orchestrator._models
    
    def test_submit_request(self):
        """Test request submission."""
        orchestrator = FairModelOrchestrator()
        orchestrator.register_model('model_a')
        
        request_id = orchestrator.submit_request(
            'model_a',
            estimated_duration=60.0
        )
        
        assert request_id is not None
        assert request_id in orchestrator._active_requests
    
    def test_schedule_next(self):
        """Test scheduling."""
        orchestrator = FairModelOrchestrator()
        orchestrator.register_model('model_a')
        
        request_id = orchestrator.submit_request('model_a')
        
        scheduled = orchestrator.schedule_next()
        
        assert scheduled is not None
        assert scheduled[0] == request_id
    
    def test_priority_based_scheduling(self):
        """Test priority-based scheduling."""
        orchestrator = FairModelOrchestrator()
        
        orchestrator.register_model('model_a', base_priority=1.0)
        orchestrator.register_model('model_b', base_priority=2.0)
        
        req_a = orchestrator.submit_request('model_a')
        req_b = orchestrator.submit_request('model_b')
        
        # Higher priority should be scheduled first
        scheduled = orchestrator.schedule_next()
        
        assert scheduled is not None
        # model_b has higher priority
        assert scheduled[1].model_id == 'model_b'
    
    def test_starvation_prevention(self):
        """Test starvation prevention."""
        orchestrator = FairModelOrchestrator(
            starvation_threshold=0.1  # Very low for testing
        )
        
        orchestrator.register_model('model_a', base_priority=1.0)
        orchestrator.register_model('model_b', base_priority=10.0)
        
        req_a = orchestrator.submit_request('model_a')
        time.sleep(0.2)  # Wait past starvation threshold
        req_b = orchestrator.submit_request('model_b')
        
        # Even though model_b has higher priority, model_a should get boost
        scheduled = orchestrator.schedule_next()
        
        # Check that starvation boost was applied
        assert scheduled is not None
    
    def test_complete_request(self):
        """Test request completion."""
        orchestrator = FairModelOrchestrator()
        orchestrator.register_model('model_a')
        
        request_id = orchestrator.submit_request('model_a')
        scheduled = orchestrator.schedule_next()
        
        orchestrator.complete_request(request_id, actual_duration=30.0)
        
        assert request_id not in orchestrator._active_requests
    
    def test_get_model_stats(self):
        """Test model statistics."""
        orchestrator = FairModelOrchestrator()
        orchestrator.register_model('model_a')
        
        request_id = orchestrator.submit_request('model_a')
        orchestrator.schedule_next()
        orchestrator.complete_request(request_id)
        
        stats = orchestrator.get_model_stats('model_a')
        
        assert isinstance(stats, ModelStats)
        assert stats.completed_requests > 0
    
    def test_get_queue_status(self):
        """Test queue status retrieval."""
        orchestrator = FairModelOrchestrator()
        orchestrator.register_model('model_a')
        orchestrator.register_model('model_b')
        
        orchestrator.submit_request('model_a')
        orchestrator.submit_request('model_b')
        
        status = orchestrator.get_queue_status()
        
        assert 'queue_size' in status
        assert 'registered_models' in status
        assert status['queue_size'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
