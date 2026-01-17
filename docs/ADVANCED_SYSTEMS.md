# Advanced AI-Enabled Systems - Documentation

This document describes the advanced AI-enabled systems implemented in the Ouroboros framework.

## Overview

The advanced systems replace simplistic implementations with cutting-edge AI and machine learning solutions:

1. **Memory Management**: ARIMA and LSTM-based predictive analytics
2. **Command System**: NLP-powered multi-layered command processing
3. **Prioritization Engine**: Reinforcement learning-based task scheduling
4. **File System**: Content deduplication and L-sharded indexing

## 1. Memory Management System

### Features

- **ARIMA Predictor**: Time-series forecasting using Auto-Regressive Integrated Moving Average
- **LSTM Predictor**: Neural network-based prediction with online learning
- **Ensemble Prediction**: Multiple strategies for optimal accuracy
- **Predictive Allocation**: Recommends memory allocations based on forecasts
- **Optimization Suggestions**: Proactive resource optimization recommendations

### Usage

```python
from src.memory_management import AdvancedMemoryManager, PredictionStrategy

# Initialize manager
manager = AdvancedMemoryManager(
    max_memory_mb=4096,
    strategy=PredictionStrategy.ENSEMBLE_WEIGHTED
)

# Update with current memory usage
manager.update(2000.0)

# Predict future usage
predictions = manager.predict(steps=5)

# Request allocation recommendation
recommendation = manager.recommend_allocation(500.0)
print(f"Approved: {recommendation['approve']}")
```

### Key Classes

- `ARIMAMemoryPredictor`: ARIMA-based forecasting with (p, d, q) parameters
- `LSTMMemoryPredictor`: LSTM neural network with online learning
- `AdvancedMemoryManager`: Integrated manager with ensemble prediction

## 2. Multi-Layered Command System

### Features

- **NLP Parsing**: Natural language command interpretation
- **Intent Recognition**: Automatic detection of command intent
- **Entity Extraction**: Extract parameters like memory sizes, names, values
- **Security Validation**: Permission checking and input sanitization
- **Priority Execution**: Asynchronous execution with priority queuing
- **Analytics**: Command tracking and success rate analysis

### Usage

```python
from src.command_system import MultiLayeredCommandSystem
from src.command_system.command_validator import PermissionLevel

# Initialize system
system = MultiLayeredCommandSystem()

# Process natural language command
result = system.process(
    "allocate 500 MB",
    permission=PermissionLevel.USER,
    execute_async=False
)

print(f"Success: {result['success']}")
print(f"Intent: {result['parse_result']['intent']}")
```

### Key Classes

- `NLPCommandParser`: Natural language parsing with pattern matching
- `CommandValidator`: Security and permission validation
- `CommandExecutor`: Async/sync execution with priority queuing
- `MultiLayeredCommandSystem`: Integrated command pipeline

### Supported Intents

- `ALLOCATE_MEMORY`: Memory allocation requests
- `DEALLOCATE_MEMORY`: Memory deallocation
- `OPTIMIZE_RESOURCES`: Resource optimization
- `GET_STATUS`: Status queries
- `SET_PARAMETER`: Parameter configuration
- `EXECUTE_TASK`: Task execution
- `QUERY_DATA`: Data queries

## 3. RL-Based Prioritization Engine

### Features

- **Q-Learning Agent**: Reinforcement learning for task prioritization
- **State Representation**: Multi-dimensional state space (memory, CPU, queue, urgency, complexity)
- **Reward System**: Multi-factor reward calculation
- **Online Learning**: Continuous policy improvement
- **Multi-Level Queues**: Priority-based task scheduling

### Usage

```python
from src.prioritization_engine import MultiLevelPriorityManager
from src.prioritization_engine.priority_manager import Task

# Initialize manager
manager = MultiLevelPriorityManager(enable_rl=True)

# Create task
task = Task(
    task_id="important_task",
    urgency=0.8,
    complexity=0.6
)

# Add to queue (RL agent determines priority)
priority = manager.add_task(task)

# Get next task to execute
next_task = manager.get_next_task()

# Record execution outcome
manager.record_outcome(
    task,
    completed=True,
    execution_time=1.5,
    deadline_met=True,
    resource_efficiency=0.85,
    user_satisfaction=0.9
)
```

### Key Classes

- `QLearningAgent`: Q-learning implementation with epsilon-greedy policy
- `State`: Multi-dimensional state representation
- `Action`: Prioritization actions (CRITICAL, HIGH, MEDIUM, LOW, DEFER, BATCH)
- `RewardCalculator`: Multi-factor reward computation
- `MultiLevelPriorityManager`: RL-integrated priority manager

### Reward Factors

- Task completion (1.0 weight)
- Deadline adherence (0.8 weight)
- Resource efficiency (0.6 weight)
- User satisfaction (0.7 weight)
- System stability (0.5 weight)

## 4. Enhanced File System

### Features

- **Content Deduplication**: Block-level deduplication with SHA-256 hashing
- **Reference Counting**: Automatic cleanup of unreferenced blocks
- **L-Sharded Index**: Distributed hash table for fast lookups
- **Prefix Search**: Fast key prefix-based queries
- **Access Tracking**: File access statistics and patterns

### Usage

```python
from src.file_system import EnhancedFileManager

# Initialize manager
manager = EnhancedFileManager(
    block_size=4096,
    num_shards=16,
    enable_deduplication=True
)

# Store file with deduplication
content = b"Hello, World! " * 1000
result = manager.store_file("file1.txt", content)
print(f"Space saved: {result['compression_ratio']:.1%}")

# Retrieve file
retrieved = manager.retrieve_file("file1.txt")

# Find similar files (shared blocks)
similar = manager.find_similar_files("file1.txt")

# Get statistics
stats = manager.get_statistics()
print(f"Space savings: {stats['deduplication_stats']['space_savings_ratio']:.1%}")
```

### Key Classes

- `ContentDeduplicator`: Block-level deduplication engine
- `LShardedIndex`: Sharded hash index for fast lookups
- `EnhancedFileManager`: Integrated file management with deduplication

### Deduplication Algorithm

1. Split content into fixed-size blocks (default: 4KB)
2. Compute SHA-256 hash for each block
3. Check if block exists in store
4. If exists: increment reference count
5. If new: store block with reference count = 1
6. Track block-to-file mappings for similarity detection

## Testing

### Running Tests

```bash
# Run all advanced systems tests
pytest tests/test_advanced_systems.py -v

# Run specific test class
pytest tests/test_advanced_systems.py::TestARIMAPredictor -v

# Run all tests
pytest tests/ -v
```

### Test Coverage

- **Memory Management**: 10 tests
- **Command System**: 10 tests
- **Prioritization Engine**: 7 tests
- **File System**: 10 tests
- **Integration**: 2 tests
- **Total**: 39 new tests, 95 total tests

## Examples

See `examples/advanced_systems_demo.py` for comprehensive usage examples:

```bash
python examples/advanced_systems_demo.py
```

## Performance Characteristics

### Memory Management

- **ARIMA**: O(p²) per prediction for AR coefficient fitting
- **LSTM**: O(hidden_size²) per forward pass
- **Prediction Time**: < 10ms for 5-step forecast

### Command System

- **NLP Parsing**: O(n) where n = number of intent patterns
- **Validation**: O(1) for permission checks
- **Execution**: Async with O(log n) priority queue operations

### Prioritization Engine

- **Q-Learning Update**: O(1) per update
- **State Discretization**: O(d) where d = number of dimensions
- **Task Retrieval**: O(log n) from priority queue

### File System

- **Deduplication**: O(b) where b = number of blocks
- **Lookup**: O(1) average with sharding
- **Space Savings**: 50-90% for duplicate-heavy workloads

## Security

All systems include security measures:

1. **Input Validation**: Sanitization of all user inputs
2. **Permission Checking**: Role-based access control
3. **Blacklist Filtering**: Prevention of dangerous operations
4. **Resource Limits**: Enforcement of allocation limits
5. **Audit Logging**: Complete history of operations

## Future Enhancements

Potential improvements:

1. **Memory Management**: Add SARIMA for seasonal patterns
2. **Command System**: Add GPT-based intent recognition
3. **Prioritization**: Implement Deep Q-Networks (DQN)
4. **File System**: Add encryption and compression
5. **Monitoring**: Real-time dashboards and alerts

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Advanced AI-Enabled Systems                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Memory     │  │   Command    │  │ Prioritization│      │
│  │  Management  │  │   System     │  │    Engine     │      │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤      │
│  │ ARIMA Pred.  │  │ NLP Parser   │  │ Q-Learning   │      │
│  │ LSTM Pred.   │  │ Validator    │  │ Reward Calc. │      │
│  │ Ensemble     │  │ Executor     │  │ Multi-Level  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────────────────────────────────────────┐       │
│  │              Enhanced File System                 │       │
│  ├──────────────────────────────────────────────────┤       │
│  │  Content Dedup  │  L-Sharded Index  │  Manager   │       │
│  └──────────────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Enhanced File System                 │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  Content Dedup  │  L-Sharded Index  │  Manager   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## License

MIT License - See LICENSE file for details.

## Contributors

Implemented as part of the Ouroboros Advanced AI Enhancement initiative.
