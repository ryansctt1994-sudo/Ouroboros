"""
Teleportation System Adapter
=============================

Adapter that connects TeleportationSystem to the ECS validation framework.
Enables entity state teleportation monitoring and validation.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import time
from typing import Dict, List, Any, Optional
from ..core import System, World, Entity
from ..components import SpatialLocation
from ..systems import TeleportationSystem


class TeleportationSystemAdapter:
    """
    Adapter for TeleportationSystem integration with ECS validation framework.
    
    Features:
    - Entity state teleportation monitoring
    - Cooldown tracking
    - Spatial validation
    - Realm transition tracking
    """
    
    def __init__(self, teleport_system: TeleportationSystem):
        """
        Initialize adapter with TeleportationSystem instance.
        
        Args:
            teleport_system: TeleportationSystem to adapt
        """
        self.system = teleport_system
        self.adapter_id = f"teleport_adapter_{id(self)}"
        
        # Metrics
        self.total_updates = 0
        self.total_teleports_attempted = 0
        self.total_teleports_succeeded = 0
        self.total_teleports_failed = 0
        self.last_update_time = 0.0
        
        # Validation state
        self.teleport_history = []
        self.validation_timestamp = 0.0
    
    def get_component_mapping(self) -> Dict[str, str]:
        """
        Get teleportation component to vector mapping.
        
        Returns:
            Dictionary mapping component names to vector IDs
        """
        return {
            "SpatialLocation": "eden_ecs.components.SpatialLocation",
            "TeleportationSystem": "eden_ecs.systems.TeleportationSystem",
            "teleport_cooldown": "field:teleport_cooldown",
        }
    
    def validate_spatial_state(self, entity: Entity) -> Dict[str, Any]:
        """
        Validate spatial state of an entity.
        
        Args:
            entity: Entity to validate
            
        Returns:
            Validation result dictionary
        """
        if not entity.has_component(SpatialLocation):
            return {
                "valid": False,
                "reason": "Missing SpatialLocation component",
                "entity_id": entity.entity_id
            }
        
        location = entity.get_component(SpatialLocation)
        
        # Validate coordinates (basic sanity checks)
        coords = [location.x, location.y, location.z]
        if any(abs(c) > 1e6 for c in coords):
            return {
                "valid": False,
                "reason": f"Coordinates out of range: ({location.x}, {location.y}, {location.z})",
                "entity_id": entity.entity_id
            }
        
        return {
            "valid": True,
            "entity_id": entity.entity_id,
            "position": (location.x, location.y, location.z),
            "realm": location.realm
        }
    
    def get_runtime_vectors(self, world: World) -> List[Dict[str, Any]]:
        """
        Extract runtime vectors from teleportable entities.
        
        Args:
            world: ECS world
            
        Returns:
            List of runtime vector dictionaries
        """
        vectors = []
        entities = world.query_entities(None, SpatialLocation)
        
        for entity in entities:
            location = entity.get_component(SpatialLocation)
            
            # Check if entity is on cooldown
            on_cooldown = entity.entity_id in self.system.cooldowns
            cooldown_remaining = self.system.cooldowns.get(entity.entity_id, 0.0)
            
            # Create runtime vector for this teleportable entity
            vector = {
                "vector_id": f"runtime.teleport.entity.{entity.entity_id}",
                "type": "teleportable_entity",
                "name": f"TeleportableEntity_{entity.entity_id[:8]}",
                "entity_id": entity.entity_id,
                "entity_name": entity.name,
                "position": {
                    "x": location.x,
                    "y": location.y,
                    "z": location.z
                },
                "realm": location.realm,
                "on_cooldown": on_cooldown,
                "cooldown_remaining": cooldown_remaining,
                "recently_teleported": entity.has_tag("recently_teleported"),
                "timestamp": time.time()
            }
            vectors.append(vector)
        
        self.validation_timestamp = time.time()
        
        return vectors
    
    def teleport_with_monitoring(
        self,
        entity: Entity,
        x: float,
        y: float,
        z: float,
        realm: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform teleport with integrated monitoring.
        
        Args:
            entity: Entity to teleport
            x, y, z: Target coordinates
            realm: Optional target realm
            
        Returns:
            Teleport result with metrics
        """
        start_time = time.perf_counter()
        
        # Get initial state
        location = entity.get_component(SpatialLocation)
        old_pos = (location.x, location.y, location.z) if location else None
        old_realm = location.realm if location else None
        
        # Attempt teleport
        self.total_teleports_attempted += 1
        success = self.system.teleport_entity(entity, x, y, z, realm)
        
        # Record result
        teleport_duration = time.perf_counter() - start_time
        
        if success:
            self.total_teleports_succeeded += 1
        else:
            self.total_teleports_failed += 1
        
        # Create history entry
        history_entry = {
            "timestamp": time.time(),
            "entity_id": entity.entity_id,
            "success": success,
            "old_position": old_pos,
            "new_position": (x, y, z),
            "old_realm": old_realm,
            "new_realm": realm,
            "duration_us": teleport_duration * 1_000_000
        }
        self.teleport_history.append(history_entry)
        
        # Keep history bounded
        if len(self.teleport_history) > 1000:
            self.teleport_history = self.teleport_history[-1000:]
        
        return {
            "success": success,
            "entity_id": entity.entity_id,
            "old_position": old_pos,
            "new_position": (x, y, z),
            "duration_us": teleport_duration * 1_000_000,
            "total_attempts": self.total_teleports_attempted,
            "total_succeeded": self.total_teleports_succeeded,
            "total_failed": self.total_teleports_failed
        }
    
    def update_with_monitoring(self, world: World, dt: float) -> Dict[str, Any]:
        """
        Update teleportation system with integrated monitoring.
        
        Args:
            world: ECS world
            dt: Time delta
            
        Returns:
            Monitoring metrics
        """
        start_time = time.perf_counter()
        
        # Get active cooldowns before update
        cooldowns_before = len(self.system.cooldowns)
        
        # Perform system update (cooldown management)
        self.system.update(world, dt)
        
        # Calculate metrics
        update_duration = time.perf_counter() - start_time
        self.total_updates += 1
        self.last_update_time = update_duration
        
        cooldowns_after = len(self.system.cooldowns)
        cooldowns_expired = max(0, cooldowns_before - cooldowns_after)
        
        return {
            "adapter_id": self.adapter_id,
            "system": "TeleportationSystem",
            "update_duration_us": update_duration * 1_000_000,
            "active_cooldowns": cooldowns_after,
            "cooldowns_expired": cooldowns_expired,
            "total_updates": self.total_updates
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get adapter metrics."""
        success_rate = 0.0
        if self.total_teleports_attempted > 0:
            success_rate = self.total_teleports_succeeded / self.total_teleports_attempted
        
        return {
            "adapter_id": self.adapter_id,
            "system": "TeleportationSystem",
            "priority": self.system.priority,
            "total_updates": self.total_updates,
            "total_teleports_attempted": self.total_teleports_attempted,
            "total_teleports_succeeded": self.total_teleports_succeeded,
            "total_teleports_failed": self.total_teleports_failed,
            "success_rate": success_rate,
            "active_cooldowns": len(self.system.cooldowns),
            "last_update_time_us": self.last_update_time * 1_000_000,
            "validation_timestamp": self.validation_timestamp,
            "history_size": len(self.teleport_history),
            "status": "CONNECTED" if self.total_updates > 0 else "IDLE"
        }
    
    def get_status(self) -> str:
        """Get adapter status string."""
        if self.total_updates == 0:
            return "IDLE"
        elif self.total_teleports_attempted == 0:
            return "MONITORING"
        else:
            return "ACTIVE"
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"TeleportationSystemAdapter("
            f"updates={self.total_updates}, "
            f"teleports={self.total_teleports_succeeded}/{self.total_teleports_attempted}, "
            f"status={self.get_status()})"
        )
