# Memory Optimization Guide

## Overview

This guide covers memory optimization techniques for Ouroboros, including GPU memory management and tensor lifecycle optimization.

## GPU Memory Optimizer

### Features

The `GPUMemoryOptimizer` provides:
- Pinned memory pool management
- Zero-copy transfers between host and device
- Fragmentation monitoring and reduction
- Automatic memory pool resizing

### Basic Usage

```python
from src.performance import GPUMemoryOptimizer

# Initialize optimizer
optimizer = GPUMemoryOptimizer(
    pool_size_mb=1024,              # 1GB pool
    enable_zero_copy=True,
    fragmentation_threshold=0.3,
    consolidation_interval=60.0
)
```

### Memory Allocation

```python
# Allocate pinned memory
block_id = optimizer.allocate_pinned(
    size_mb=128,
    block_id='weights_block'  # Optional custom ID
)

# Check allocation
stats = optimizer.get_statistics()
print(f"Allocated: {stats.total_allocated_mb:.2f} MB")
print(f"Fragmentation: {stats.fragmentation_ratio:.2%}")
```

### Zero-Copy Transfers

```python
# Perform zero-copy transfer
success = optimizer.zero_copy_transfer(
    block_id,
    direction='host_to_device'
)

if success:
    print(f"Zero-copy transfers: {stats.zero_copy_transfers}")
```

### Memory Lifecycle

```python
# Free memory when done
optimizer.free(block_id)

# Or resize pool dynamically
optimizer.resize_pool(new_size_mb=2048)
```

### Fragmentation Management

```python
# Monitor fragmentation
fragmentation = optimizer.calculate_fragmentation()

if fragmentation > 0.3:
    # Consolidate memory
    consolidated = optimizer.consolidate_memory()
    print(f"Consolidated {consolidated} blocks")
```

## Tensor Warden

### Features

The `DynamicTensorWardenV2` provides:
- Predictive memory eviction
- LRU-based caching with criticality awareness
- Fragmentation handling
- Per-owner memory tracking

### Basic Usage

```python
from src.training import DynamicTensorWardenV2
import numpy as np

# Initialize warden
warden = DynamicTensorWardenV2(
    memory_limit_gb=16,
    eviction_threshold=0.85,
    fragmentation_threshold=0.3
)
```

### Tensor Registration

```python
# Register tensor
tensor = np.random.randn(1000, 1000)

success = warden.register_tensor(
    tensor_id='attention_weights',
    tensor=tensor,
    owner='model_a',
    size_mb=None,  # Auto-estimated
    critical=True  # Won't be evicted
)
```

### Tensor Access

```python
# Request tensor (updates access pattern)
tensor = warden.request_tensor('attention_weights', 'model_a')

if tensor is None:
    print("Tensor was evicted, need to recompute")
else:
    # Use tensor
    result = tensor @ input_data
```

### Memory Management

```python
# Release tensor when done
warden.release_tensor('attention_weights')

# Defragment memory
reclaimed = warden.defragment()

# Get statistics
stats = warden.get_statistics()
print(f"Utilization: {stats.utilization:.2%}")
print(f"Tensors: {stats.tensor_count}")
print(f"Evictions: {stats.eviction_count}")
```

## Best Practices

### 1. Pinned Memory Strategy

Use pinned memory for frequently transferred data:

```python
# Good: Pin frequently used tensors
model_weights = optimizer.allocate_pinned(size_mb=512)
optimizer.zero_copy_transfer(model_weights, 'host_to_device')

# Bad: Don't pin temporary buffers
temp_buffer = np.zeros((100, 100))  # Use regular memory
```

### 2. Critical Tensor Marking

Mark only truly critical tensors:

```python
# Critical: Model parameters
warden.register_tensor('model_params', params, critical=True)

# Not critical: Intermediate activations (can recompute)
warden.register_tensor('layer1_act', activations, critical=False)
```

### 3. Memory Budget Planning

```python
class MemoryBudget:
    def __init__(self, total_gb):
        self.total_mb = total_gb * 1024
        self.allocations = {
            'model_weights': 0.4,      # 40%
            'activations': 0.3,        # 30%
            'gradients': 0.2,          # 20%
            'optimizer_state': 0.1     # 10%
        }
    
    def get_limit(self, category):
        return self.total_mb * self.allocations[category]

budget = MemoryBudget(total_gb=16)
warden_activations = DynamicTensorWardenV2(
    memory_limit_gb=budget.get_limit('activations') / 1024
)
```

### 4. Eviction Strategy

```python
# Priority order for eviction:
# 1. Non-critical tensors with oldest access
# 2. Large infrequently-accessed tensors
# 3. Tensors from lower-priority owners

warden.register_tensor('cache_data', data, critical=False)
# Will be evicted first if memory pressure
```

### 5. Fragmentation Prevention

```python
# Monitor and defragment regularly
def maintenance_loop():
    while True:
        stats = warden.get_statistics()
        
        if stats.fragmentation_ratio > 0.3:
            warden.defragment()
        
        time.sleep(60)
```

## Performance Tuning

### GPU Memory Pool Sizing

```python
# Conservative: 50% of available GPU memory
gpu_info = get_gpu_info()
pool_size = gpu_info.total_memory_mb * 0.5

# Aggressive: 80% of available GPU memory
pool_size = gpu_info.total_memory_mb * 0.8

optimizer = GPUMemoryOptimizer(pool_size_mb=pool_size)
```

### Eviction Threshold Tuning

```python
# Low threshold: More aggressive eviction
warden = DynamicTensorWardenV2(eviction_threshold=0.7)

# High threshold: Less aggressive, may OOM
warden = DynamicTensorWardenV2(eviction_threshold=0.95)
```

## Monitoring and Debugging

### Memory Statistics

```python
def print_memory_stats():
    # GPU stats
    gpu_stats = optimizer.get_statistics()
    print("GPU Memory:")
    print(f"  Allocated: {gpu_stats.total_allocated_mb:.2f} MB")
    print(f"  Pinned: {gpu_stats.total_pinned_mb:.2f} MB")
    print(f"  Fragmentation: {gpu_stats.fragmentation_ratio:.2%}")
    
    # Tensor stats
    tensor_stats = warden.get_statistics()
    print("\nTensor Memory:")
    print(f"  Utilization: {tensor_stats.utilization:.2%}")
    print(f"  Tensors: {tensor_stats.tensor_count}")
    print(f"  Evictions: {tensor_stats.eviction_count}")
```

### Memory Leak Detection

```python
def check_memory_leaks():
    # Take snapshot
    initial_stats = warden.get_statistics()
    
    # Run workload
    run_training_iteration()
    
    # Release all tensors
    for tensor_id in list(warden._tensors.keys()):
        warden.release_tensor(tensor_id)
    
    # Check if memory was fully released
    final_stats = warden.get_statistics()
    
    if final_stats.total_allocated_mb > 0:
        print(f"WARNING: Memory leak detected!")
        print(f"Leaked: {final_stats.total_allocated_mb:.2f} MB")
```

## Common Issues

### Issue: Frequent Evictions

**Symptoms**: High eviction count, poor performance

**Solution**:
```python
# Increase memory limit
warden = DynamicTensorWardenV2(memory_limit_gb=32)

# Or mark more tensors as critical
warden.register_tensor(id, tensor, critical=True)
```

### Issue: Memory Fragmentation

**Symptoms**: High fragmentation ratio, failed allocations

**Solution**:
```python
# Lower fragmentation threshold
warden = DynamicTensorWardenV2(fragmentation_threshold=0.2)

# Or defragment more frequently
warden.defragment()
```

### Issue: Zero-Copy Failures

**Symptoms**: Zero-copy transfers return False

**Solution**:
```python
# Ensure memory is pinned
block_id = optimizer.allocate_pinned(size_mb=100)

# Check if zero-copy is enabled
if not optimizer.enable_zero_copy:
    optimizer.enable_zero_copy = True
```
