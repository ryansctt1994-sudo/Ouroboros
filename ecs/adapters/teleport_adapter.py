"""
Teleport Adapter Module

Provides state teleportation for ECS entities,
enabling quantum-inspired state transfer across the system.
"""

import numpy as np
from typing import Dict, Any, Optional, List
import hashlib
import json


class TeleportAdapter:
    """
    Adapter for entity state teleportation in the ECS.
    
    Provides mechanisms for transferring entity states across different
    contexts, worlds, or system boundaries while maintaining coherence.
    """
    
    # Placeholder encryption key (replace with proper key management in production)
    _PLACEHOLDER_KEY = "OUROBOROS_TELEPORT_KEY"
    
    def __init__(self, use_encryption: bool = True):
        """
        Initialize the teleport adapter.
        
        Args:
            use_encryption: Whether to use state encryption during teleport
        """
        self.use_encryption = use_encryption
        self.teleport_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
    def prepare_teleport(self, entity_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare an entity state for teleportation.
        
        Args:
            entity_state: Complete state of the entity
            
        Returns:
            Prepared teleport package
        """
        # Create snapshot of current state
        state_snapshot = self._create_snapshot(entity_state)
        
        # Calculate state hash for verification
        state_hash = self._calculate_hash(state_snapshot)
        
        # Prepare teleport package
        package = {
            'snapshot': state_snapshot,
            'hash': state_hash,
            'metadata': {
                'timestamp': self._get_timestamp(),
                'encrypted': self.use_encryption
            }
        }
        
        # Encrypt if enabled
        if self.use_encryption:
            package['snapshot'] = self._encrypt_state(state_snapshot)
        
        return package
    
    def execute_teleport(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute teleportation and reconstruct entity state.
        
        Args:
            package: Teleport package from prepare_teleport
            
        Returns:
            Reconstructed entity state
        """
        # Verify package integrity
        if not self._verify_package(package):
            raise ValueError("Teleport package verification failed")
        
        # Decrypt if needed
        snapshot = package['snapshot']
        if package['metadata']['encrypted'] and self.use_encryption:
            snapshot = self._decrypt_state(snapshot)
        
        # Reconstruct entity state
        entity_state = self._reconstruct_state(snapshot)
        
        # Record teleport in history
        self._record_teleport(package, entity_state)
        
        return entity_state
    
    def teleport_component(self, component_data: Dict[str, Any],
                          source_entity_id: str,
                          target_entity_id: str) -> Dict[str, Any]:
        """
        Teleport a specific component between entities.
        
        Args:
            component_data: Component data to teleport
            source_entity_id: Source entity identifier
            target_entity_id: Target entity identifier
            
        Returns:
            Teleported component data
        """
        # Create component package
        package = {
            'component': component_data,
            'source': source_entity_id,
            'target': target_entity_id,
            'timestamp': self._get_timestamp()
        }
        
        # Transform component for target context
        transformed = self._transform_component(component_data)
        
        return transformed
    
    def batch_teleport(self, entity_states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Teleport multiple entities in batch.
        
        Args:
            entity_states: List of entity states to teleport
            
        Returns:
            List of teleport packages
        """
        packages = []
        for state in entity_states:
            package = self.prepare_teleport(state)
            packages.append(package)
        return packages
    
    def _create_snapshot(self, state: Dict[str, Any]) -> str:
        """Create a JSON snapshot of the state."""
        return json.dumps(state, sort_keys=True)
    
    def _reconstruct_state(self, snapshot: str) -> Dict[str, Any]:
        """Reconstruct state from JSON snapshot."""
        return json.loads(snapshot)
    
    def _calculate_hash(self, data: str) -> str:
        """Calculate SHA-256 hash of data."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _verify_package(self, package: Dict[str, Any]) -> bool:
        """Verify integrity of teleport package."""
        if 'hash' not in package or 'snapshot' not in package:
            return False
        
        # For encrypted snapshots, we can't verify until decryption
        if package['metadata']['encrypted']:
            return True
        
        # Verify hash for unencrypted
        calculated_hash = self._calculate_hash(package['snapshot'])
        return calculated_hash == package['hash']
    
    def _encrypt_state(self, state_snapshot: str) -> str:
        """
        Simple XOR-based encryption (placeholder for real encryption).
        In production, use proper encryption like AES.
        """
        # Simple XOR with key for demonstration
        encrypted = bytearray()
        for i, char in enumerate(state_snapshot.encode()):
            encrypted.append(char ^ ord(self._PLACEHOLDER_KEY[i % len(self._PLACEHOLDER_KEY)]))
        return encrypted.hex()
    
    def _decrypt_state(self, encrypted_data: str) -> str:
        """Decrypt state using XOR (placeholder)."""
        encrypted = bytearray.fromhex(encrypted_data)
        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            decrypted.append(byte ^ ord(self._PLACEHOLDER_KEY[i % len(self._PLACEHOLDER_KEY)]))
        return decrypted.decode()
    
    def _transform_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Transform component for target context."""
        # Create a deep copy and apply any necessary transformations
        transformed = component.copy()
        
        # Add teleport marker
        if 'metadata' not in transformed:
            transformed['metadata'] = {}
        transformed['metadata']['teleported'] = True
        transformed['metadata']['teleport_time'] = self._get_timestamp()
        
        return transformed
    
    def _record_teleport(self, package: Dict[str, Any], 
                        reconstructed_state: Dict[str, Any]) -> None:
        """Record teleport in history."""
        record = {
            'hash': package['hash'],
            'timestamp': package['metadata']['timestamp'],
            'encrypted': package['metadata']['encrypted']
        }
        
        self.teleport_history.append(record)
        
        # Limit history size
        if len(self.teleport_history) > self.max_history:
            self.teleport_history.pop(0)
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()
    
    def get_teleport_stats(self) -> Dict[str, Any]:
        """
        Get teleportation statistics.
        
        Returns:
            Dictionary with teleport statistics
        """
        return {
            'total_teleports': len(self.teleport_history),
            'encryption_enabled': self.use_encryption,
            'history_size': len(self.teleport_history),
            'max_history': self.max_history
        }
