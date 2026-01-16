"""
Comprehensive Test Suite for Advanced AI-Enabled Systems

Tests for memory management, command system, prioritization engine, and file system.
"""

import pytest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory_management import ARIMAMemoryPredictor, LSTMMemoryPredictor, AdvancedMemoryManager, PredictionStrategy
from src.command_system import NLPCommandParser, CommandValidator, CommandExecutor, MultiLayeredCommandSystem
from src.command_system.nlp_parser import CommandIntent
from src.command_system.command_validator import PermissionLevel, ValidationResult
from src.command_system.command_executor import ExecutionPriority
from src.prioritization_engine import QLearningAgent, State, Action, MultiLevelPriorityManager, RewardCalculator
from src.prioritization_engine.reward_system import TaskOutcome
from src.prioritization_engine.priority_manager import Task
from src.file_system import ContentDeduplicator, LShardedIndex, EnhancedFileManager


# ============================================================================
# Memory Management Tests
# ============================================================================

class TestARIMAPredictor:
    """Tests for ARIMA memory predictor."""
    
    def test_initialization(self):
        """Test ARIMA predictor initialization."""
        predictor = ARIMAMemoryPredictor(p=3, d=1, q=2)
        assert predictor.p == 3
        assert predictor.d == 1
        assert predictor.q == 2
    
    def test_update_and_predict(self):
        """Test updating predictor with data and making predictions."""
        predictor = ARIMAMemoryPredictor()
        
        # Add some data
        for i in range(20):
            predictor.update(1000.0 + i * 10)
        
        # Make prediction
        predictions = predictor.predict(steps=3)
        
        assert len(predictions) == 3
        assert all(p >= 0 for p in predictions)
    
    def test_confidence_intervals(self):
        """Test confidence interval calculation."""
        predictor = ARIMAMemoryPredictor()
        
        for i in range(20):
            predictor.update(1000.0 + i * 10)
        
        predictions = predictor.predict(steps=3)
        intervals = predictor.get_confidence_interval()
        
        assert len(intervals) == 3
        for lower, upper in intervals:
            assert lower <= upper


class TestLSTMPredictor:
    """Tests for LSTM memory predictor."""
    
    def test_initialization(self):
        """Test LSTM predictor initialization."""
        predictor = LSTMMemoryPredictor(hidden_size=16, num_layers=2)
        assert predictor.hidden_size == 16
        assert predictor.num_layers == 2
    
    def test_update_and_predict(self):
        """Test updating predictor and making predictions."""
        predictor = LSTMMemoryPredictor(hidden_size=8, num_layers=1, sequence_length=5)
        
        # Add training data
        for i in range(15):
            predictor.update(1000.0 + i * 5)
        
        # Make prediction
        predictions = predictor.predict(steps=3)
        
        assert len(predictions) == 3
        assert all(p >= 0 for p in predictions)
    
    def test_online_learning(self):
        """Test online learning updates."""
        predictor = LSTMMemoryPredictor(hidden_size=8, num_layers=1, sequence_length=5)
        
        for i in range(15):
            predictor.update(1000.0 + i * 5)
        
        # Perform online updates
        losses = predictor.online_update(num_steps=3)
        
        assert len(losses) > 0


class TestAdvancedMemoryManager:
    """Tests for advanced memory manager."""
    
    def test_initialization(self):
        """Test memory manager initialization."""
        manager = AdvancedMemoryManager(max_memory_mb=4096)
        assert manager.max_memory_mb == 4096
    
    def test_update_and_predict(self):
        """Test updating manager and making predictions."""
        manager = AdvancedMemoryManager(max_memory_mb=4096)
        
        # Update with memory values
        for i in range(20):
            manager.update(1000.0 + i * 50)
        
        # Predict
        predictions = manager.predict(steps=5)
        
        assert len(predictions) == 5
        assert all(p >= 0 for p in predictions)
    
    def test_allocation_recommendation(self):
        """Test memory allocation recommendation."""
        manager = AdvancedMemoryManager(max_memory_mb=4096)
        
        manager.update(2000.0)
        
        # Request allocation
        recommendation = manager.recommend_allocation(500.0)
        
        assert 'approve' in recommendation
        assert 'usage_ratio' in recommendation
    
    def test_ensemble_strategy(self):
        """Test ensemble prediction strategy."""
        manager = AdvancedMemoryManager(
            max_memory_mb=4096,
            strategy=PredictionStrategy.ENSEMBLE_WEIGHTED
        )
        
        for i in range(20):
            manager.update(1000.0 + i * 50)
        
        predictions = manager.predict(steps=3)
        assert len(predictions) == 3


# ============================================================================
# Command System Tests
# ============================================================================

class TestNLPCommandParser:
    """Tests for NLP command parser."""
    
    def test_parse_allocate_memory(self):
        """Test parsing memory allocation command."""
        parser = NLPCommandParser()
        
        parsed = parser.parse("allocate 500 MB")
        
        assert parsed.intent == CommandIntent.ALLOCATE_MEMORY
        assert parsed.confidence > 0.3
        mem_entity = parsed.get_entity('memory_size')
        assert mem_entity is not None
        assert abs(mem_entity.value - 500.0) < 1.0
    
    def test_parse_get_status(self):
        """Test parsing status command."""
        parser = NLPCommandParser()
        
        parsed = parser.parse("show status")
        
        assert parsed.intent == CommandIntent.GET_STATUS
    
    def test_parse_optimize(self):
        """Test parsing optimization command."""
        parser = NLPCommandParser()
        
        parsed = parser.parse("optimize resources")
        
        assert parsed.intent == CommandIntent.OPTIMIZE_RESOURCES


class TestCommandValidator:
    """Tests for command validator."""
    
    def test_validate_approved(self):
        """Test validation of approved command."""
        validator = CommandValidator(max_memory_allocation_mb=1024)
        parser = NLPCommandParser()
        
        parsed = parser.parse("allocate 500 MB")
        result = validator.validate(parsed, PermissionLevel.USER)
        
        assert result['status'] == ValidationResult.APPROVED
    
    def test_validate_rejected_permission(self):
        """Test rejection due to insufficient permissions."""
        validator = CommandValidator()
        parser = NLPCommandParser()
        
        parsed = parser.parse("optimize resources")
        result = validator.validate(parsed, PermissionLevel.PUBLIC)
        
        assert result['status'] == ValidationResult.REJECTED
    
    def test_validate_rejected_size_limit(self):
        """Test rejection due to size limit."""
        validator = CommandValidator(max_memory_allocation_mb=100)
        parser = NLPCommandParser()
        
        parsed = parser.parse("allocate 500 MB")
        result = validator.validate(parsed, PermissionLevel.ADMIN)
        
        assert result['status'] == ValidationResult.REJECTED


class TestCommandExecutor:
    """Tests for command executor."""
    
    def test_synchronous_execution(self):
        """Test synchronous command execution."""
        executor = CommandExecutor(enable_async=False)
        parser = NLPCommandParser()
        
        parsed = parser.parse("get status")
        result = executor.execute_sync(parsed)
        
        assert result['success'] == True
    
    def test_asynchronous_submission(self):
        """Test asynchronous command submission."""
        executor = CommandExecutor(enable_async=True)
        parser = NLPCommandParser()
        
        parsed = parser.parse("allocate 100 MB")
        exec_id = executor.submit(parsed, ExecutionPriority.MEDIUM)
        
        assert exec_id.startswith('exec_')


class TestMultiLayeredCommandSystem:
    """Tests for multi-layered command system."""
    
    def test_process_command(self):
        """Test processing complete command."""
        system = MultiLayeredCommandSystem()
        
        result = system.process("show status", execute_async=False)
        
        assert 'success' in result
        assert result.get('parse_result') is not None
        assert result.get('validation_result') is not None
    
    def test_batch_processing(self):
        """Test batch command processing."""
        system = MultiLayeredCommandSystem()
        
        commands = [
            "show status",
            "allocate 100 MB",
            "get info"
        ]
        
        results = system.process_batch(commands)
        
        assert len(results) == 3


# ============================================================================
# Prioritization Engine Tests
# ============================================================================

class TestQLearningAgent:
    """Tests for Q-learning agent."""
    
    def test_initialization(self):
        """Test Q-learning agent initialization."""
        agent = QLearningAgent(learning_rate=0.1, discount_factor=0.9)
        assert agent.learning_rate == 0.1
        assert agent.discount_factor == 0.9
    
    def test_action_selection(self):
        """Test action selection."""
        agent = QLearningAgent()
        
        state = State(
            memory_usage_ratio=0.5,
            cpu_usage_ratio=0.6,
            queue_depth=10,
            task_urgency=0.8,
            task_complexity=0.5
        )
        
        action = agent.select_action(state)
        assert action in agent.actions
    
    def test_q_learning_update(self):
        """Test Q-learning update."""
        agent = QLearningAgent()
        
        state = State(0.5, 0.5, 10, 0.8, 0.5)
        next_state = State(0.6, 0.5, 9, 0.7, 0.5)
        action = Action.PRIORITY_HIGH
        reward = 10.0
        
        agent.update(state, action, reward, next_state)
        
        assert agent.total_updates == 1


class TestRewardCalculator:
    """Tests for reward calculator."""
    
    def test_calculate_reward(self):
        """Test reward calculation."""
        calculator = RewardCalculator()
        
        outcome = TaskOutcome(
            task_id="test_task",
            completed=True,
            execution_time=1.0,
            deadline_met=True,
            resource_efficiency=0.9,
            user_satisfaction=0.8
        )
        
        reward = calculator.calculate_reward(outcome)
        
        assert reward > 0
    
    def test_failed_task_penalty(self):
        """Test penalty for failed task."""
        calculator = RewardCalculator()
        
        outcome = TaskOutcome(
            task_id="test_task",
            completed=False,
            execution_time=1.0,
            deadline_met=False,
            resource_efficiency=0.5,
            user_satisfaction=0.3
        )
        
        reward = calculator.calculate_reward(outcome)
        
        assert reward < 0


class TestMultiLevelPriorityManager:
    """Tests for multi-level priority manager."""
    
    def test_add_task(self):
        """Test adding task to manager."""
        manager = MultiLevelPriorityManager(enable_rl=False)
        
        task = Task(
            task_id="task1",
            urgency=0.8,
            complexity=0.5
        )
        
        priority = manager.add_task(task)
        
        assert 0 <= priority <= 3
        assert task.task_id in manager.pending_tasks
    
    def test_get_next_task(self):
        """Test getting next task."""
        manager = MultiLevelPriorityManager(enable_rl=False)
        
        task1 = Task("task1", urgency=0.9, complexity=0.5)
        task2 = Task("task2", urgency=0.5, complexity=0.5)
        
        manager.add_task(task1)
        manager.add_task(task2)
        
        next_task = manager.get_next_task()
        
        assert next_task is not None


# ============================================================================
# File System Tests
# ============================================================================

class TestContentDeduplicator:
    """Tests for content deduplicator."""
    
    def test_store_and_retrieve(self):
        """Test storing and retrieving file."""
        deduplicator = ContentDeduplicator(block_size=1024)
        
        content = b"Hello, World! " * 1000
        metadata = deduplicator.store_file("file1", content)
        
        retrieved = deduplicator.retrieve_file("file1")
        
        assert retrieved == content
        assert metadata.original_size == len(content)
    
    def test_deduplication(self):
        """Test deduplication of identical content."""
        deduplicator = ContentDeduplicator(block_size=1024)
        
        content = b"Duplicate content " * 1000
        
        metadata1 = deduplicator.store_file("file1", content)
        metadata2 = deduplicator.store_file("file2", content)
        
        # Second file should have better compression due to shared blocks
        stats = deduplicator.get_statistics()
        assert stats['space_savings_ratio'] > 0
    
    def test_delete_file(self):
        """Test file deletion and cleanup."""
        deduplicator = ContentDeduplicator()
        
        content = b"Test content"
        deduplicator.store_file("file1", content)
        
        success = deduplicator.delete_file("file1")
        
        assert success == True
        retrieved = deduplicator.retrieve_file("file1")
        assert retrieved is None


class TestLShardedIndex:
    """Tests for L-sharded index."""
    
    def test_put_and_get(self):
        """Test putting and getting values."""
        index = LShardedIndex(num_shards=8)
        
        index.put("key1", "value1")
        value = index.get("key1")
        
        assert value == "value1"
    
    def test_shard_distribution(self):
        """Test shard distribution."""
        index = LShardedIndex(num_shards=4)
        
        # Add many entries
        for i in range(100):
            index.put(f"key_{i}", f"value_{i}")
        
        distribution = index.get_shard_distribution()
        
        # Should have some entries in each shard
        assert len(distribution) == 4
        assert sum(distribution) == 100
    
    def test_prefix_search(self):
        """Test prefix-based search."""
        index = LShardedIndex()
        
        index.put("user_1", "Alice")
        index.put("user_2", "Bob")
        index.put("admin_1", "Charlie")
        
        user_keys = index.find_by_prefix("user_")
        
        assert len(user_keys) == 2


class TestEnhancedFileManager:
    """Tests for enhanced file manager."""
    
    def test_store_and_retrieve(self):
        """Test storing and retrieving files."""
        manager = EnhancedFileManager(enable_deduplication=True)
        
        content = b"Test file content"
        result = manager.store_file("file1", content)
        
        assert result['success'] == True
        
        retrieved = manager.retrieve_file("file1")
        assert retrieved == content
    
    def test_file_exists(self):
        """Test file existence check."""
        manager = EnhancedFileManager()
        
        manager.store_file("file1", b"content")
        
        assert manager.file_exists("file1") == True
        assert manager.file_exists("nonexistent") == False
    
    def test_delete_file(self):
        """Test file deletion."""
        manager = EnhancedFileManager()
        
        manager.store_file("file1", b"content")
        success = manager.delete_file("file1")
        
        assert success == True
        assert manager.file_exists("file1") == False
    
    def test_statistics(self):
        """Test getting statistics."""
        manager = EnhancedFileManager()
        
        for i in range(5):
            manager.store_file(f"file_{i}", b"content" * 100)
        
        stats = manager.get_statistics()
        
        assert stats['total_files'] == 5
        assert 'index_stats' in stats


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for all systems."""
    
    def test_memory_manager_with_commands(self):
        """Test memory manager integrated with command system."""
        memory_manager = AdvancedMemoryManager(max_memory_mb=4096)
        command_system = MultiLayeredCommandSystem()
        
        # Simulate memory usage
        for i in range(10):
            memory_manager.update(1000.0 + i * 100)
        
        # Get recommendation
        recommendation = memory_manager.recommend_allocation(500.0)
        
        # Process command
        result = command_system.process("allocate 500 MB", execute_async=False)
        
        assert recommendation is not None
        assert result is not None
    
    def test_full_workflow(self):
        """Test complete workflow with all systems."""
        # Initialize all systems
        memory_mgr = AdvancedMemoryManager()
        cmd_system = MultiLayeredCommandSystem()
        priority_mgr = MultiLevelPriorityManager()
        file_mgr = EnhancedFileManager()
        
        # Update memory
        memory_mgr.update(2000.0)
        
        # Process command
        cmd_result = cmd_system.process("allocate 100 MB", execute_async=False)
        assert cmd_result['success'] == True
        
        # Add task to priority queue
        task = Task("task1", urgency=0.8, complexity=0.5)
        priority_mgr.add_task(task)
        
        # Store file
        file_result = file_mgr.store_file("test_file", b"content")
        assert file_result['success'] == True
        
        # Get statistics
        mem_stats = memory_mgr.get_state()
        priority_stats = priority_mgr.get_statistics()
        file_stats = file_mgr.get_statistics()
        
        assert mem_stats is not None
        assert priority_stats is not None
        assert file_stats is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
