"""
ECS Orchestrator Module

Coordinates and manages all ECS integration components,
providing a unified interface for consciousness computation.
"""

from typing import Dict, List, Any, Optional
from .runtime_vectorizer import RuntimeVectorizer
from .manuscript_validator import ManuscriptValidator, ValidationResult
from .adapters.quantum_adapter import QuantumAdapter
from .adapters.sync_adapter import SyncAdapter
from .adapters.teleport_adapter import TeleportAdapter
import time


class ECSOrchestrator:
    """
    Orchestrator for ECS integration layer.
    
    Manages vectorization, validation, quantum operations, synchronization,
    and teleportation in a coordinated manner.
    """
    
    def __init__(self, 
                 node_id: str = "default",
                 dimensions: int = 7,
                 num_qubits: int = 3,
                 tick_rate: float = 60.0):
        """
        Initialize the ECS orchestrator.
        
        Args:
            node_id: Unique identifier for this node
            dimensions: Vector space dimensions (default: 7 for METACUBE)
            num_qubits: Number of qubits for quantum operations
            tick_rate: Synchronization tick rate in Hz
        """
        self.node_id = node_id
        
        # Initialize components
        self.vectorizer = RuntimeVectorizer(dimensions=dimensions)
        self.validator = ManuscriptValidator(strict_mode=False)
        self.quantum = QuantumAdapter(num_qubits=num_qubits)
        self.sync = SyncAdapter(node_id=node_id, tick_rate=tick_rate)
        self.teleport = TeleportAdapter(use_encryption=True)
        
        # State tracking
        self.active = False
        self.start_time = 0.0
        self.tick_count = 0
        self.entity_registry: Dict[str, Dict[str, Any]] = {}
        
    def start(self) -> None:
        """Start the orchestrator."""
        if not self.active:
            self.active = True
            self.start_time = time.time()
            self.tick_count = 0
            self.quantum.reset()
    
    def stop(self) -> None:
        """Stop the orchestrator."""
        self.active = False
    
    def tick(self) -> None:
        """Execute a single orchestration tick."""
        if not self.active:
            return
        
        # Wait for synchronized tick
        self.sync.wait_for_tick()
        self.tick_count += 1
    
    def register_entity(self, entity_id: str, entity_data: Dict[str, Any]) -> bool:
        """
        Register an entity with the orchestrator.
        
        Args:
            entity_id: Unique identifier for the entity
            entity_data: Entity data including type and components
            
        Returns:
            True if registration successful
        """
        # Validate entity manuscript
        validation = self.validator.validate(entity_data)
        if not validation.is_valid():
            return False
        
        # Vectorize entity
        vector = self.vectorizer.vectorize(entity_data)
        self.vectorizer.cache_vector(entity_id, vector)
        
        # Store in registry
        self.entity_registry[entity_id] = {
            'data': entity_data,
            'vector': vector.tolist(),
            'registered_at': time.time()
        }
        
        return True
    
    def unregister_entity(self, entity_id: str) -> bool:
        """
        Unregister an entity.
        
        Args:
            entity_id: Entity to unregister
            
        Returns:
            True if unregistration successful
        """
        if entity_id in self.entity_registry:
            del self.entity_registry[entity_id]
            return True
        return False
    
    def teleport_entity(self, entity_id: str, 
                       target_orchestrator: 'ECSOrchestrator') -> bool:
        """
        Teleport an entity to another orchestrator.
        
        Args:
            entity_id: Entity to teleport
            target_orchestrator: Destination orchestrator
            
        Returns:
            True if teleport successful
        """
        if entity_id not in self.entity_registry:
            return False
        
        # Prepare teleport package
        entity_state = self.entity_registry[entity_id]
        package = self.teleport.prepare_teleport(entity_state['data'])
        
        # Execute teleport on target
        try:
            reconstructed = self.teleport.execute_teleport(package)
            target_orchestrator.register_entity(entity_id, reconstructed)
            
            # Optionally remove from source
            # self.unregister_entity(entity_id)
            
            return True
        except Exception:
            return False
    
    def apply_quantum_operation(self, operation: str, *args) -> Any:
        """
        Apply a quantum operation.
        
        Args:
            operation: Name of the quantum operation
            *args: Arguments for the operation
            
        Returns:
            Result of the operation
        """
        if not self.active:
            return None
        
        if operation == "hadamard":
            self.quantum.apply_hadamard(*args)
        elif operation == "phase":
            self.quantum.apply_phase_gate(*args)
        elif operation == "entangle":
            self.quantum.entangle(*args)
        elif operation == "measure":
            return self.quantum.measure(*args)
        
        return None
    
    def sync_with_peer(self, peer_id: str, peer_address: str) -> None:
        """
        Synchronize with a peer orchestrator.
        
        Args:
            peer_id: Peer orchestrator ID
            peer_address: Network address of peer
        """
        self.sync.register_peer(peer_id, peer_address)
    
    def broadcast_state(self) -> None:
        """Broadcast current state to all peers."""
        state_data = {
            'tick': self.tick_count,
            'entities': len(self.entity_registry),
            'active': self.active
        }
        self.sync.broadcast_state(state_data)
    
    def get_entity_similarity(self, entity1_id: str, entity2_id: str) -> float:
        """
        Calculate similarity between two registered entities.
        
        Args:
            entity1_id: First entity ID
            entity2_id: Second entity ID
            
        Returns:
            Cosine similarity score
        """
        vector1 = self.vectorizer.get_cached_vector(entity1_id)
        vector2 = self.vectorizer.get_cached_vector(entity2_id)
        
        if vector1 is None or vector2 is None:
            return 0.0
        
        return self.vectorizer.compute_similarity(vector1, vector2)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive orchestrator status.
        
        Returns:
            Status dictionary
        """
        uptime = time.time() - self.start_time if self.active else 0.0
        
        return {
            'node_id': self.node_id,
            'active': self.active,
            'uptime': uptime,
            'tick_count': self.tick_count,
            'entities': len(self.entity_registry),
            'vectorizer': {
                'dimensions': self.vectorizer.dimensions,
                'cached_vectors': len(self.vectorizer.vectors_cache)
            },
            'quantum': {
                'num_qubits': self.quantum.num_qubits,
                'dimension': self.quantum.dimension
            },
            'sync': self.sync.get_sync_status(),
            'teleport': self.teleport.get_teleport_stats()
        }
    
    def validate_manuscript(self, manuscript: Dict[str, Any]) -> ValidationResult:
        """
        Validate a manuscript.
        
        Args:
            manuscript: Manuscript to validate
            
        Returns:
            ValidationResult object
        """
        return self.validator.validate(manuscript)
