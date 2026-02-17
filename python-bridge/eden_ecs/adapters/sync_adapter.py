"""
Synchronization System Adapter
===============================

Adapter that connects MycelialSyncSystem to the ECS validation framework.
Enables mycelial node synchronization monitoring and validation.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import time
from typing import Dict, List, Any, Optional
from ..core import System, World, Entity
from ..components import Consciousness7D
from ..mycelial_components import HyphalNodeComponent
from ..mycelial_sync import MycelialSyncSystem


class SynchronizationSystemAdapter:
    """
    Adapter for MycelialSyncSystem integration with ECS validation framework.
    
    Features:
    - Mycelial node synchronization mapping
    - Consensus monitoring
    - PLL phase tracking
    - Slot allocation validation
    """
    
    def __init__(self, sync_system: MycelialSyncSystem):
        """
        Initialize adapter with MycelialSyncSystem instance.
        
        Args:
            sync_system: MycelialSyncSystem to adapt
        """
        self.system = sync_system
        self.adapter_id = f"sync_adapter_{id(self)}"
        
        # Metrics
        self.total_updates = 0
        self.total_syncs = 0
        self.total_consensus_achieved = 0
        self.last_update_time = 0.0
        
        # Validation state
        self.validated_nodes = []
        self.validation_timestamp = 0.0
    
    def get_component_mapping(self) -> Dict[str, str]:
        """
        Get synchronization component to vector mapping.
        
        Returns:
            Dictionary mapping component names to vector IDs
        """
        return {
            "Consciousness7D": "eden_ecs.components.Consciousness7D",
            "HyphalNodeComponent": "eden_ecs.mycelial_components.HyphalNodeComponent",
            "MycelialSyncSystem": "eden_ecs.mycelial_sync.MycelialSyncSystem",
            "ForgeBridge": "eden_ecs.forge_bridge.ForgeBridge",
        }
    
    def validate_sync_state(self, entity: Entity) -> Dict[str, Any]:
        """
        Validate synchronization state of an entity.
        
        Args:
            entity: Entity to validate
            
        Returns:
            Validation result dictionary
        """
        if not entity.has_component(Consciousness7D):
            return {
                "valid": False,
                "reason": "Missing Consciousness7D component",
                "entity_id": entity.entity_id
            }
        
        if not entity.has_component(HyphalNodeComponent):
            return {
                "valid": False,
                "reason": "Missing HyphalNodeComponent",
                "entity_id": entity.entity_id
            }
        
        consciousness = entity.get_component(Consciousness7D)
        hyphal = entity.get_component(HyphalNodeComponent)
        
        # Validate node state
        if hyphal.forge_slot < -1:
            return {
                "valid": False,
                "reason": f"Invalid forge_slot: {hyphal.forge_slot}",
                "entity_id": entity.entity_id
            }
        
        return {
            "valid": True,
            "entity_id": entity.entity_id,
            "forge_slot": hyphal.forge_slot,
            "phase": hyphal.phase,
            "coherence": consciousness.coherence()
        }
    
    def get_runtime_vectors(self, world: World) -> List[Dict[str, Any]]:
        """
        Extract runtime vectors from synchronized entities.
        
        Args:
            world: ECS world
            
        Returns:
            List of runtime vector dictionaries
        """
        vectors = []
        entities = world.query_entities(None, Consciousness7D, HyphalNodeComponent)
        
        for entity in entities:
            hyphal = entity.get_component(HyphalNodeComponent)
            consciousness = entity.get_component(Consciousness7D)
            
            # Create runtime vector for this sync node
            vector = {
                "vector_id": f"runtime.sync.node.{entity.entity_id}",
                "type": "sync_node",
                "name": f"MycelialNode_{entity.entity_id[:8]}",
                "entity_id": entity.entity_id,
                "entity_name": entity.name,
                "forge_slot": hyphal.forge_slot,
                "phase": hyphal.phase,
                "synchronized": hyphal.synchronized,
                "neighbors": hyphal.neighbor_ids,
                "coherence": consciousness.coherence(),
                "timestamp": time.time()
            }
            vectors.append(vector)
        
        self.validated_nodes = vectors
        self.validation_timestamp = time.time()
        
        return vectors
    
    def get_sync_metrics(self) -> Dict[str, Any]:
        """Get synchronization metrics from the system."""
        return {
            "total_syncs": self.system.total_syncs,
            "total_consensus_achieved": self.system.total_consensus_achieved,
            "avg_sync_latency_us": self.system.avg_sync_latency_us,
            "active_slots": len(self.system.allocator.entity_to_slot),
            "available_slots": len(self.system.allocator.available_slots),
        }
    
    def update_with_monitoring(self, world: World, dt: float) -> Dict[str, Any]:
        """
        Update sync system with integrated monitoring.
        
        Args:
            world: ECS world
            dt: Time delta
            
        Returns:
            Monitoring metrics
        """
        start_time = time.perf_counter()
        
        # Get metrics before update
        syncs_before = self.system.total_syncs
        consensus_before = self.system.total_consensus_achieved
        
        # Perform system update
        self.system.update(world, dt)
        
        # Calculate metrics
        update_duration = time.perf_counter() - start_time
        self.total_updates += 1
        self.last_update_time = update_duration
        
        # Track sync events
        syncs_delta = self.system.total_syncs - syncs_before
        consensus_delta = self.system.total_consensus_achieved - consensus_before
        
        self.total_syncs += syncs_delta
        self.total_consensus_achieved += consensus_delta
        
        return {
            "adapter_id": self.adapter_id,
            "system": "MycelialSyncSystem",
            "update_duration_us": update_duration * 1_000_000,
            "syncs_this_update": syncs_delta,
            "consensus_this_update": consensus_delta,
            "total_updates": self.total_updates,
            "avg_sync_latency_us": self.system.avg_sync_latency_us
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get adapter metrics."""
        sync_metrics = self.get_sync_metrics()
        
        return {
            "adapter_id": self.adapter_id,
            "system": "MycelialSyncSystem",
            "priority": self.system.priority,
            "total_updates": self.total_updates,
            "total_syncs": self.total_syncs,
            "total_consensus_achieved": self.total_consensus_achieved,
            "last_update_time_us": self.last_update_time * 1_000_000,
            "validated_nodes": len(self.validated_nodes),
            "validation_timestamp": self.validation_timestamp,
            "sync_metrics": sync_metrics,
            "status": "CONNECTED" if self.total_updates > 0 else "IDLE"
        }
    
    def get_status(self) -> str:
        """Get adapter status string."""
        if self.total_updates == 0:
            return "IDLE"
        elif self.total_syncs == 0:
            return "INITIALIZING"
        else:
            return "ACTIVE"
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SynchronizationSystemAdapter("
            f"updates={self.total_updates}, "
            f"syncs={self.total_syncs}, "
            f"status={self.get_status()})"
        )
