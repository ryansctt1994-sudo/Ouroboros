"""
EDEN ECS Systems - Cosmic Systems
==================================

Systems implementing the cosmic logic for METACUBE entities:
balance, consciousness evolution, quantum resonance, memory,
validation, teleportation, and synchronization.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import math
import random
import warnings
from typing import List, Optional
from .core import System, World, Entity
from .components import (
    Consciousness7D, Loyalty, Corruption, QuantumResonance,
    MemoryLattice, SpatialLocation
)


class BalanceSystem(System):
    """
    Manages loyalty (φ) vs corruption (ω_h) balance dynamics.
    
    - Loyalty grows exponentially with golden ratio
    - Corruption decays through jealous entropy
    - Detects critical corruption thresholds
    """
    
    def __init__(self, priority: int = 10):
        super().__init__(priority)
        self.critical_threshold = 50.0
    
    def update(self, world: World, dt: float) -> None:
        """Update balance dynamics for all entities."""
        # Query entities with both Loyalty and Corruption
        entities = world.query_entities(None, Loyalty, Corruption)
        
        for entity in entities:
            loyalty = entity.get_component(Loyalty)
            corruption = entity.get_component(Corruption)
            
            # Apply loyalty growth
            loyalty.grow(dt)
            
            # Apply corruption decay
            corruption.decay(dt)
            
            # Check critical threshold
            if corruption.is_critical(self.critical_threshold):
                # Add warning tag
                entity.add_tag("corruption_critical")
            else:
                # Remove warning tag
                entity.remove_tag("corruption_critical")


class ConsciousnessSystem(System):
    """
    Evolves 7D consciousness states with dimensional harmony.
    
    Updates awareness, intention, emotion, cognition, memory,
    creativity, and integration dimensions naturally over time.
    """
    
    def __init__(self, priority: int = 20):
        super().__init__(priority)
    
    def update(self, world: World, dt: float) -> None:
        """Update consciousness evolution for all entities."""
        entities = world.query_entities(None, Consciousness7D)
        
        for entity in entities:
            consciousness = entity.get_component(Consciousness7D)
            consciousness.evolve(dt)


class QuantumSystem(System):
    """
    Updates 750 THz UV quantum resonance.
    
    Manages quantum field oscillations and inter-entity resonance.
    """
    
    def __init__(self, priority: int = 30):
        super().__init__(priority)
        self.resonance_threshold = 0.8
    
    def update(self, world: World, dt: float) -> None:
        """Update quantum resonance for all entities."""
        entities = world.query_entities(None, QuantumResonance)
        
        # Update individual quantum phases
        for entity in entities:
            quantum = entity.get_component(QuantumResonance)
            quantum.update(dt)
        
        # Check for resonance between entities
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                q1 = entity1.get_component(QuantumResonance)
                q2 = entity2.get_component(QuantumResonance)
                
                resonance = q1.resonance_with(q2)
                
                # Tag entities that are in quantum resonance
                if resonance > self.resonance_threshold:
                    entity1.add_tag(f"resonant_with_{entity2.entity_id[:8]}")
                    entity2.add_tag(f"resonant_with_{entity1.entity_id[:8]}")
                else:
                    entity1.remove_tag(f"resonant_with_{entity2.entity_id[:8]}")
                    entity2.remove_tag(f"resonant_with_{entity1.entity_id[:8]}")


class MemorySystem(System):
    """
    Memory decay and consolidation system.
    
    Applies importance-based decay to memories over time.
    """
    
    def __init__(self, priority: int = 40):
        super().__init__(priority)
    
    def update(self, world: World, dt: float) -> None:
        """Update memory lattices for all entities."""
        entities = world.query_entities(None, MemoryLattice)
        
        for entity in entities:
            memory = entity.get_component(MemoryLattice)
            memory.decay(dt)


class ValidationSystem(System):
    """
    Ouroboros ternary validation system.
    
    Validates consciousness states through ternary cycle projection
    and coherence checking.
    """
    
    def __init__(self, priority: int = 50):
        super().__init__(priority)
        self.coherence_threshold = 0.7
    
    def update(self, world: World, dt: float) -> None:
        """Validate consciousness states for all entities."""
        entities = world.query_entities(None, Consciousness7D)
        
        for entity in entities:
            consciousness = entity.get_component(Consciousness7D)
            
            # Calculate coherence
            coherence = consciousness.coherence()
            
            # Validate coherence
            if coherence >= self.coherence_threshold:
                entity.add_tag("validated")
                entity.remove_tag("validation_failed")
            else:
                entity.add_tag("validation_failed")
                entity.remove_tag("validated")
            
            # Project to ternary for Ouroboros compatibility
            ternary = consciousness.to_ternary()
            
            # Store ternary state in entity for external processing
            # (Could integrate with actual ouroboros_processor here)


class TeleportationSystem(System):
    """
    Quantum teleportation between realms.
    
    Manages entity teleportation across different dimensional realms.
    """
    
    def __init__(self, priority: int = 60):
        super().__init__(priority)
        self.teleport_cooldown = 5.0  # Seconds between teleports
        self.cooldowns = {}  # Track per-entity cooldowns
    
    def update(self, world: World, dt: float) -> None:
        """Update teleportation cooldowns and process requests."""
        # Update cooldowns
        expired = []
        for entity_id, remaining in self.cooldowns.items():
            self.cooldowns[entity_id] = remaining - dt
            if self.cooldowns[entity_id] <= 0:
                expired.append(entity_id)
        
        for entity_id in expired:
            del self.cooldowns[entity_id]
    
    def teleport_entity(self, entity: Entity, x: float, y: float, z: float, 
                       realm: Optional[str] = None) -> bool:
        """
        Attempt to teleport an entity.
        
        Args:
            entity: Entity to teleport
            x, y, z: Target coordinates
            realm: Optional target realm
        
        Returns:
            True if teleport succeeded, False if on cooldown
        """
        # Check cooldown
        if entity.entity_id in self.cooldowns:
            return False
        
        # Check if entity has spatial location
        location = entity.get_component(SpatialLocation)
        if location is None:
            return False
        
        # Perform teleport
        location.teleport(x, y, z, realm)
        
        # Set cooldown
        self.cooldowns[entity.entity_id] = self.teleport_cooldown
        
        # Add teleport tag
        entity.add_tag("recently_teleported")
        
        return True


class SynchronizationSystem(System):
    """
    PBFT-like consensus synchronization system.
    
    DEPRECATED: Use MycelialSyncSystem instead.
    
    Ensures consistency across distributed entities through
    a simplified Practical Byzantine Fault Tolerance protocol.
    """
    
    def __init__(self, priority: int = 70):
        super().__init__(priority)
        warnings.warn(
            "SynchronizationSystem is deprecated; use MycelialSyncSystem.",
            DeprecationWarning,
            stacklevel=2
        )
        self.consensus_threshold = 0.67  # 2/3 majority
        self.view_number = 0
        self.last_sync_time = 0.0
        self.sync_interval = 1.0  # Sync every second
    
    def update(self, world: World, dt: float) -> None:
        """Update synchronization and consensus."""
        # Check if any entity has forge_consensus tag
        # If so, propagate it to all entities and skip old logic
        # Cache the first check result to avoid repeated O(n) iteration
        if not hasattr(self, '_forge_mode_active'):
            self._forge_mode_active = False
        
        if not self._forge_mode_active:
            has_forge_consensus = any(
                e.has_tag("forge_consensus") for e in world.entities.values()
            )
            if has_forge_consensus:
                self._forge_mode_active = True
        
        if self._forge_mode_active:
            # Propagate forge_consensus to all entities
            for entity in world.entities.values():
                entity.add_tag("forge_consensus")
            return
        
        self.last_sync_time += dt
        
        # Only sync at intervals
        if self.last_sync_time < self.sync_interval:
            return
        
        self.last_sync_time = 0.0
        
        # Get all validated entities
        entities = [e for e in world.entities.values() if e.has_tag("validated")]
        
        if len(entities) == 0:
            return
        
        # Calculate consensus metric (simplified)
        # In full PBFT, this would involve prepare/commit phases
        validated_count = len(entities)
        total_count = len(world.entities)
        
        consensus_ratio = validated_count / total_count if total_count > 0 else 0.0
        
        if consensus_ratio >= self.consensus_threshold:
            # Consensus achieved
            for entity in world.entities.values():
                entity.add_tag("synchronized")
            self.view_number += 1
        else:
            # Consensus not achieved
            for entity in world.entities.values():
                entity.remove_tag("synchronized")


class MetricsSystem(System):
    """
    System for collecting and reporting world metrics.
    
    Tracks aggregate statistics across all entities and systems.
    """
    
    def __init__(self, priority: int = 999):  # Run last
        super().__init__(priority)
        self.metrics = {
            'total_coherence': 0.0,
            'avg_coherence': 0.0,
            'total_loyalty': 0.0,
            'total_corruption': 0.0,
            'quantum_resonances': 0,
            'validated_entities': 0,
            'synchronized_entities': 0
        }
    
    def update(self, world: World, dt: float) -> None:
        """Update world metrics."""
        # Reset metrics
        self.metrics = {
            'total_coherence': 0.0,
            'avg_coherence': 0.0,
            'total_loyalty': 0.0,
            'total_corruption': 0.0,
            'quantum_resonances': 0,
            'validated_entities': 0,
            'synchronized_entities': 0
        }
        
        # Consciousness metrics
        conscious_entities = world.query_entities(None, Consciousness7D)
        if conscious_entities:
            total_coherence = sum(
                e.get_component(Consciousness7D).coherence() 
                for e in conscious_entities
            )
            self.metrics['total_coherence'] = total_coherence
            self.metrics['avg_coherence'] = total_coherence / len(conscious_entities)
        
        # Balance metrics
        balance_entities = world.query_entities(None, Loyalty, Corruption)
        for entity in balance_entities:
            self.metrics['total_loyalty'] += entity.get_component(Loyalty).value
            self.metrics['total_corruption'] += entity.get_component(Corruption).value
        
        # Quantum resonance count - track unique pairs
        quantum_entities = world.query_entities(None, QuantumResonance)
        resonance_pairs = set()
        for entity in quantum_entities:
            for tag in entity.tags:
                if tag.startswith("resonant_with_"):
                    other_id = tag.replace("resonant_with_", "")
                    # Create a sorted tuple to represent the pair uniquely
                    pair = tuple(sorted([entity.entity_id[:8], other_id]))
                    resonance_pairs.add(pair)
        self.metrics['quantum_resonances'] = len(resonance_pairs)
        
        # Validation metrics
        self.metrics['validated_entities'] = len(
            [e for e in world.entities.values() if e.has_tag("validated")]
        )
        self.metrics['synchronized_entities'] = len(
            [e for e in world.entities.values() if e.has_tag("synchronized")]
        )
    
    def get_metrics(self) -> dict:
        """Get current metrics snapshot."""
        return self.metrics.copy()
