# Adapter Patterns Guide

## Overview

**System Adapters** are the bridge between existing systems and the ECS validation framework. They enable loose coupling while providing tight integration for monitoring, validation, and self-awareness.

## The Adapter Pattern

### Problem

You have existing systems (QuantumSystem, TeleportationSystem, etc.) that:
- Work independently
- Have their own update cycles
- Maintain internal state
- Need monitoring and validation

**But you want:**
- Unified monitoring
- Consistent validation
- Runtime state extraction
- Integration with vectorization

### Solution

Create adapters that:
1. **Wrap** existing systems without modifying them
2. **Monitor** system behavior through observation
3. **Validate** system state against vectors
4. **Extract** runtime vectors for validation
5. **Report** metrics and health status

```
┌────────────────────────────────────┐
│       Existing System              │
│   (QuantumSystem, etc.)            │
└────────────┬───────────────────────┘
             │
             │ wraps
             │
┌────────────▼───────────────────────┐
│       System Adapter               │
│  ┌──────────────────────────────┐  │
│  │  Monitoring                  │  │
│  │  Validation                  │  │
│  │  Vector Extraction           │  │
│  │  Metrics Collection          │  │
│  └──────────────────────────────┘  │
└────────────┬───────────────────────┘
             │
             │ integrates with
             │
┌────────────▼───────────────────────┐
│    ECS Validation Framework        │
│  (Runtime Validator, Orchestrator) │
└────────────────────────────────────┘
```

## Adapter Architecture

### Core Components

Each adapter implements:

```python
class SystemAdapter:
    """Base pattern for system adapters."""
    
    def __init__(self, system):
        self.system = system              # Wrapped system
        self.adapter_id = f"adapter_{id(self)}"
        self.metrics = {}                 # Performance metrics
        self.validation_state = {}        # Validation cache
    
    def get_component_mapping(self) -> Dict[str, str]:
        """Map components to vector IDs."""
        pass
    
    def validate_state(self, entity: Entity) -> Dict[str, Any]:
        """Validate entity state."""
        pass
    
    def get_runtime_vectors(self, world: World) -> List[Dict[str, Any]]:
        """Extract runtime vectors."""
        pass
    
    def update_with_monitoring(self, world: World, dt: float) -> Dict[str, Any]:
        """Update system with monitoring."""
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get adapter metrics."""
        pass
```

## Adapter Implementations

### 1. Quantum System Adapter

Connects `QuantumSystem` to validation framework.

**File:** `python-bridge/eden_ecs/adapters/quantum_adapter.py`

#### Component Mapping

Maps quantum components to vectors:

```python
def get_component_mapping(self) -> Dict[str, str]:
    return {
        "QuantumResonance": "eden_ecs.components.QuantumResonance",
        "quantum_phase": "field:quantum_phase",
        "coherence": "field:coherence",
        "frequency_hz": "field:frequency_hz",
    }
```

#### State Validation

Validates quantum state parameters:

```python
def validate_quantum_state(self, entity: Entity) -> Dict[str, Any]:
    if not entity.has_component(QuantumResonance):
        return {"valid": False, "reason": "Missing QuantumResonance"}
    
    quantum = entity.get_component(QuantumResonance)
    
    # Validate 750 THz frequency
    if quantum.frequency != 750e12:
        return {
            "valid": False,
            "reason": f"Invalid frequency: {quantum.frequency}"
        }
    
    # Validate amplitude range [0.0, 10.0]
    if not (0.0 <= quantum.amplitude <= 10.0):
        return {
            "valid": False,
            "reason": f"Amplitude out of range: {quantum.amplitude}"
        }
    
    return {"valid": True, "entity_id": entity.entity_id}
```

#### Runtime Vector Extraction

Extract live quantum state as vectors:

```python
def get_runtime_vectors(self, world: World) -> List[Dict[str, Any]]:
    vectors = []
    entities = world.query_entities(None, QuantumResonance)
    
    for entity in entities:
        quantum = entity.get_component(QuantumResonance)
        
        vector = {
            "vector_id": f"runtime.quantum.entity.{entity.entity_id}",
            "type": "component_instance",
            "name": f"QuantumResonance_{entity.entity_id[:8]}",
            "quantum_phase": quantum.phase,
            "coherence": quantum.coherence,
            "frequency_hz": quantum.frequency_hz,
            "timestamp": time.time()
        }
        vectors.append(vector)
    
    return vectors
```

#### Monitored Update

Update with performance tracking:

```python
def update_with_monitoring(self, world: World, dt: float) -> Dict[str, Any]:
    start_time = time.perf_counter()
    
    # Call wrapped system's update
    self.system.update(world, dt)
    
    # Calculate metrics
    update_duration = time.perf_counter() - start_time
    self.total_updates += 1
    
    # Update exponential moving average
    alpha = 0.1
    self.avg_update_duration = (
        alpha * update_duration + (1 - alpha) * self.avg_update_duration
    )
    
    return {
        "update_duration_us": update_duration * 1_000_000,
        "entities_processed": len(world.query_entities(None, QuantumResonance)),
        "total_updates": self.total_updates
    }
```

### 2. Synchronization System Adapter

Connects `MycelialSyncSystem` to validation framework.

**File:** `python-bridge/eden_ecs/adapters/sync_adapter.py`

#### Component Mapping

Maps sync components:

```python
def get_component_mapping(self) -> Dict[str, str]:
    return {
        "Consciousness7D": "eden_ecs.components.Consciousness7D",
        "HyphalNodeComponent": "eden_ecs.mycelial_components.HyphalNodeComponent",
        "MycelialSyncSystem": "eden_ecs.mycelial_sync.MycelialSyncSystem",
        "ForgeBridge": "eden_ecs.forge_bridge.ForgeBridge",
    }
```

#### Sync Metrics

Track synchronization events:

```python
def get_sync_metrics(self) -> Dict[str, Any]:
    return {
        "total_syncs": self.system.total_syncs,
        "total_consensus_achieved": self.system.total_consensus_achieved,
        "avg_sync_latency_us": self.system.avg_sync_latency_us,
        "active_slots": len(self.system.allocator.entity_to_slot),
        "available_slots": len(self.system.allocator.available_slots),
    }
```

#### Node Validation

Validate mycelial node state:

```python
def validate_sync_state(self, entity: Entity) -> Dict[str, Any]:
    if not entity.has_component(HyphalNodeComponent):
        return {"valid": False, "reason": "Missing HyphalNodeComponent"}
    
    hyphal = entity.get_component(HyphalNodeComponent)
    
    if hyphal.slot_id < 0:
        return {"valid": False, "reason": f"Invalid slot_id: {hyphal.slot_id}"}
    
    return {
        "valid": True,
        "entity_id": entity.entity_id,
        "slot_id": hyphal.slot_id,
        "pll_phase": hyphal.pll_phase
    }
```

### 3. Teleportation System Adapter

Connects `TeleportationSystem` to validation framework.

**File:** `python-bridge/eden_ecs/adapters/teleport_adapter.py`

#### Spatial Validation

Validate entity location:

```python
def validate_spatial_state(self, entity: Entity) -> Dict[str, Any]:
    if not entity.has_component(SpatialLocation):
        return {"valid": False, "reason": "Missing SpatialLocation"}
    
    location = entity.get_component(SpatialLocation)
    
    # Sanity check coordinates
    coords = [location.x, location.y, location.z]
    if any(abs(c) > 1e6 for c in coords):
        return {
            "valid": False,
            "reason": f"Coordinates out of range: {coords}"
        }
    
    return {
        "valid": True,
        "entity_id": entity.entity_id,
        "position": (location.x, location.y, location.z)
    }
```

#### Teleport Monitoring

Monitor teleport operations:

```python
def teleport_with_monitoring(
    self, entity: Entity, x: float, y: float, z: float
) -> Dict[str, Any]:
    start_time = time.perf_counter()
    
    # Attempt teleport
    success = self.system.teleport_entity(entity, x, y, z)
    duration = time.perf_counter() - start_time
    
    # Record metrics
    self.total_teleports_attempted += 1
    if success:
        self.total_teleports_succeeded += 1
    else:
        self.total_teleports_failed += 1
    
    # Create history entry
    self.teleport_history.append({
        "timestamp": time.time(),
        "entity_id": entity.entity_id,
        "success": success,
        "duration_us": duration * 1_000_000
    })
    
    return {"success": success, "duration_us": duration * 1_000_000}
```

## Design Patterns

### 1. Wrapper Pattern

**Don't modify original system:**

```python
# ❌ BAD: Modifying original system
class QuantumSystem(System):
    def update(self, world, dt):
        # Added monitoring code here - BAD!
        start = time.perf_counter()
        # ... original logic
        self.metrics["duration"] = time.perf_counter() - start

# ✅ GOOD: Wrap with adapter
class QuantumSystemAdapter:
    def __init__(self, quantum_system):
        self.system = quantum_system  # Wrap, don't modify
    
    def update_with_monitoring(self, world, dt):
        start = time.perf_counter()
        self.system.update(world, dt)  # Call original
        return {"duration": time.perf_counter() - start}
```

### 2. Observer Pattern

**Monitor without coupling:**

```python
class SystemAdapter:
    def observe_update(self, world, dt):
        """Observe system behavior without interference."""
        # Get state before
        entities_before = len(world.query_entities(None, QuantumResonance))
        
        # Let system update
        self.system.update(world, dt)
        
        # Observe changes
        entities_after = len(world.query_entities(None, QuantumResonance))
        
        return {
            "entities_added": entities_after - entities_before,
            "entities_removed": entities_before - entities_after
        }
```

### 3. Strategy Pattern

**Different validation strategies:**

```python
class ValidationStrategy:
    def validate(self, entity): pass

class StrictValidation(ValidationStrategy):
    def validate(self, entity):
        # Strict checks
        pass

class RelaxedValidation(ValidationStrategy):
    def validate(self, entity):
        # Lenient checks
        pass

class SystemAdapter:
    def __init__(self, system, validation_strategy):
        self.system = system
        self.validator = validation_strategy
    
    def validate_state(self, entity):
        return self.validator.validate(entity)
```

## Integration Workflow

### 1. Create Adapter

```python
from eden_ecs import QuantumSystem
from eden_ecs.adapters import QuantumSystemAdapter

# Create system
quantum_system = QuantumSystem(priority=30)

# Create adapter
quantum_adapter = QuantumSystemAdapter(quantum_system)
```

### 2. Add to World

```python
from eden_ecs import World

world = World()

# Add original system (for updates)
world.add_system(quantum_system)

# Adapter doesn't need to be in system list
# It's used for validation and monitoring separately
```

### 3. Update with Monitoring

```python
# During game loop
for dt in simulation_loop():
    # Update with monitoring
    metrics = quantum_adapter.update_with_monitoring(world, dt)
    
    # Log metrics
    logger.info(f"Quantum update: {metrics['update_duration_us']:.2f} μs")
```

### 4. Extract Runtime Vectors

```python
# Periodically extract runtime state
runtime_vectors = quantum_adapter.get_runtime_vectors(world)

# Validate against static vectors
from tools.runtime_validator import RuntimeVectorValidator

validator = RuntimeVectorValidator("vectors.json")
report = validator.validate_runtime_state(runtime_vectors)
```

### 5. Validate State

```python
# Validate individual entities
for entity in world.query_entities(None, QuantumResonance):
    validation = quantum_adapter.validate_quantum_state(entity)
    
    if not validation["valid"]:
        logger.warning(f"Invalid quantum state: {validation['reason']}")
```

## Best Practices

### 1. Minimal Interference

Adapters should not change system behavior:

```python
# ✅ GOOD: Non-invasive monitoring
def update_with_monitoring(self, world, dt):
    start = time.perf_counter()
    self.system.update(world, dt)  # Original behavior unchanged
    duration = time.perf_counter() - start
    return {"duration": duration}

# ❌ BAD: Changing behavior
def update_with_monitoring(self, world, dt):
    self.system.update(world, dt * 2)  # Changed dt - BAD!
```

### 2. Efficient Metrics

Use exponential moving averages for performance:

```python
def update_avg_metric(self, new_value, alpha=0.1):
    """Update exponential moving average."""
    self.avg_value = alpha * new_value + (1 - alpha) * self.avg_value
```

### 3. Bounded History

Keep history sizes bounded:

```python
def record_event(self, event):
    self.history.append(event)
    
    # Keep only last 1000 events
    if len(self.history) > 1000:
        self.history = self.history[-1000:]
```

### 4. Lazy Validation

Validate only when needed:

```python
def get_runtime_vectors(self, world):
    # Cache results
    if self.cache_valid():
        return self.cached_vectors
    
    # Recompute only if cache invalid
    vectors = self._extract_vectors(world)
    self.cached_vectors = vectors
    self.cache_timestamp = time.time()
    return vectors
```

## Advanced Features

### Custom Metrics

Add domain-specific metrics:

```python
class QuantumSystemAdapter(SystemAdapter):
    def collect_quantum_metrics(self, world):
        """Collect quantum-specific metrics."""
        entities = world.query_entities(None, QuantumResonance)
        
        coherences = [e.get_component(QuantumResonance).coherence for e in entities]
        
        return {
            "avg_coherence": sum(coherences) / len(coherences),
            "max_coherence": max(coherences),
            "min_coherence": min(coherences),
            "coherent_count": sum(1 for c in coherences if c > 0.8)
        }
```

### Health Scoring

Compute health scores:

```python
def get_health_score(self) -> float:
    """Compute adapter health score [0.0, 1.0]."""
    score = 1.0
    
    # Deduct for errors
    if self.total_errors > 0:
        score -= 0.3
    
    # Deduct for warnings
    if self.total_warnings > 0:
        score -= 0.1
    
    # Deduct for slow updates
    if self.avg_update_duration > 0.1:  # > 100ms
        score -= 0.2
    
    return max(0.0, score)
```

### Event Streaming

Stream events to external systems:

```python
class StreamingAdapter(SystemAdapter):
    def __init__(self, system, event_stream):
        super().__init__(system)
        self.event_stream = event_stream
    
    def update_with_monitoring(self, world, dt):
        metrics = super().update_with_monitoring(world, dt)
        
        # Stream event
        self.event_stream.publish({
            "type": "system_update",
            "adapter": self.adapter_id,
            "metrics": metrics,
            "timestamp": time.time()
        })
        
        return metrics
```

## Troubleshooting

### Issue: Adapter slowing down system

**Cause:** Too much monitoring overhead  
**Solution:** Reduce monitoring frequency or use sampling

```python
def should_monitor(self):
    # Monitor only 10% of updates
    return random.random() < 0.1
```

### Issue: Memory growth from history

**Cause:** Unbounded history storage  
**Solution:** Implement bounds and cleanup

```python
MAX_HISTORY = 1000

def record_event(self, event):
    self.history.append(event)
    if len(self.history) > MAX_HISTORY:
        self.history.pop(0)
```

### Issue: Validation too strict

**Cause:** Unrealistic validation rules  
**Solution:** Adjust validation thresholds

```python
# Instead of exact match
if quantum.frequency_hz != 750e12:  # Too strict

# Use tolerance
if abs(quantum.frequency_hz - 750e12) > 1e9:  # ±1 GHz tolerance
```

## Future Enhancements

- **Auto-Generated Adapters**: Generate adapters from system signatures
- **Machine Learning**: Predict system failures from metrics
- **Distributed Adapters**: Adapters across network boundaries
- **Quantum Adapters**: Quantum-ready adapter protocols

---

**Loose systems, tightly integrated through elegant adapters.**
