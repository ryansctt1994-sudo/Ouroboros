"""
EDEN ECS Forge Bridge - FFI Integration with Rust ForgeEngine
==============================================================

Provides Python bindings to the Rust ForgeEngine for consensus and synchronization.
Includes pure-Python fallback when Rust library is unavailable.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import ctypes
import os
import platform
import warnings
from ctypes import c_void_p, c_size_t, c_uint8, c_double, c_int32, POINTER
from dataclasses import dataclass, field
from typing import Dict, List, Optional


MAX_AGENTS = 256  # Pre-allocated slot count


@dataclass
class ConsensusSnapshot:
    """Snapshot of consensus round results."""
    round: int
    consensus_achieved: bool
    network_gamma: float
    num_active_agents: int
    agreement_ratio: float
    per_agent_gammas: Dict[int, float] = field(default_factory=dict)


class SlotAllocator:
    """
    Maps entity UUIDs to fixed integer slots (0..MAX_AGENTS-1).
    
    Pre-allocates 256 slots with dynamic entity mapping. Freed slots
    are returned to a sorted free pool for deterministic reuse.
    """
    
    def __init__(self, max_slots: int = MAX_AGENTS):
        self.max_slots = max_slots
        self._entity_to_slot: Dict[str, int] = {}
        self._slot_to_entity: Dict[int, str] = {}
        self._free_slots: List[int] = list(range(max_slots))
    
    def allocate(self, entity_id: str) -> int:
        """
        Allocate a slot for an entity.
        
        Args:
            entity_id: UUID of the entity
            
        Returns:
            Slot index (0..MAX_AGENTS-1)
            
        Raises:
            RuntimeError: If all slots are exhausted
        """
        # If already allocated, return existing slot (idempotent)
        if entity_id in self._entity_to_slot:
            return self._entity_to_slot[entity_id]
        
        # Allocate new slot
        if not self._free_slots:
            raise RuntimeError(f"SlotAllocator exhausted: all {self.max_slots} slots in use")
        
        slot = self._free_slots.pop(0)  # Pop from front for deterministic order
        self._entity_to_slot[entity_id] = slot
        self._slot_to_entity[slot] = entity_id
        return slot
    
    def release(self, entity_id: str) -> Optional[int]:
        """
        Release a slot back to the free pool.
        
        Args:
            entity_id: UUID of the entity
            
        Returns:
            Released slot index, or None if entity had no slot
        """
        if entity_id not in self._entity_to_slot:
            return None
        
        slot = self._entity_to_slot[entity_id]
        del self._entity_to_slot[entity_id]
        del self._slot_to_entity[slot]
        
        # Insert back into free pool in sorted order
        self._free_slots.append(slot)
        self._free_slots.sort()
        
        return slot
    
    def get_slot(self, entity_id: str) -> Optional[int]:
        """Get the slot for an entity, or None if not allocated."""
        return self._entity_to_slot.get(entity_id)
    
    def get_entity(self, slot: int) -> Optional[str]:
        """Get the entity ID for a slot, or None if slot is free."""
        return self._slot_to_entity.get(slot)


class ForgeBridge:
    """
    FFI bridge to Rust ForgeEngine.
    
    Auto-discovers the Rust shared library and provides Python interface.
    Falls back to pure-Python consensus when Rust is unavailable.
    """
    
    def __init__(self, num_agents: int = MAX_AGENTS, use_rust: Optional[bool] = None):
        """
        Initialize the Forge bridge.
        
        Args:
            num_agents: Number of agent slots to allocate
            use_rust: None (auto-detect), True (require Rust), False (force Python)
        """
        self.num_agents = num_agents
        self.rust_available = False
        self._engine = None
        self._lib = None
        self._round_counter = 0
        
        # Python fallback state
        self._py_agents: Dict[int, List[float]] = {}
        self._py_epsilon = 0.15
        self._py_threshold = 0.67
        
        # Try to load Rust library
        if use_rust is not False:
            self._try_load_rust(require=use_rust is True)
        
        if not self.rust_available:
            if use_rust is True:
                raise RuntimeError("Rust library required but not found")
            warnings.warn(
                "Rust ForgeEngine not available, using Python fallback consensus",
                RuntimeWarning,
                stacklevel=2
            )
    
    def _try_load_rust(self, require: bool = False) -> None:
        """Attempt to load the Rust shared library."""
        # Platform-specific library names
        system = platform.system()
        if system == "Linux":
            lib_names = ["libforge_standalone.so"]
        elif system == "Darwin":
            lib_names = ["libforge_standalone.dylib"]
        elif system == "Windows":
            lib_names = ["forge_standalone.dll", "libforge_standalone.dll"]
        else:
            lib_names = ["libforge_standalone.so"]  # Fallback
        
        # Search paths
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        search_paths = [
            os.path.join(base_dir, "ELPIS", "METACUBE", "forge_standalone", "target", "release"),
            os.path.join(base_dir, "ELPIS", "METACUBE", "forge_standalone", "target", "debug"),
            os.path.join(base_dir, "target", "release"),
            os.path.join(base_dir, "target", "debug"),
            "/usr/local/lib",
            "/usr/lib",
        ]
        
        # Try to find and load library
        for search_path in search_paths:
            for lib_name in lib_names:
                lib_path = os.path.join(search_path, lib_name)
                if os.path.exists(lib_path):
                    try:
                        self._lib = ctypes.CDLL(lib_path)
                        self._setup_ffi()
                        self._engine = self._lib.forge_engine_new(self.num_agents)
                        self.rust_available = True
                        return
                    except Exception as e:
                        if require:
                            raise RuntimeError(f"Failed to load Rust library from {lib_path}: {e}")
                        continue
        
        if require:
            raise RuntimeError(f"Rust library not found in search paths: {search_paths}")
    
    def _setup_ffi(self) -> None:
        """Configure all FFI function signatures to prevent pointer truncation."""
        # forge_engine_new(num_agents: usize) -> *mut ForgeEngine
        self._lib.forge_engine_new.restype = c_void_p
        self._lib.forge_engine_new.argtypes = [c_size_t]
        
        # forge_engine_free(engine: *mut ForgeEngine)
        self._lib.forge_engine_free.restype = None
        self._lib.forge_engine_free.argtypes = [c_void_p]
        
        # forge_engine_consensus_round(engine: *mut ForgeEngine) -> u8
        self._lib.forge_engine_consensus_round.restype = c_uint8
        self._lib.forge_engine_consensus_round.argtypes = [c_void_p]
        
        # forge_engine_get_network_gamma(engine: *const ForgeEngine) -> f64
        self._lib.forge_engine_get_network_gamma.restype = c_double
        self._lib.forge_engine_get_network_gamma.argtypes = [c_void_p]
        
        # forge_engine_update_agent_array(engine, agent_id, values, len) -> i32
        self._lib.forge_engine_update_agent_array.restype = c_int32
        self._lib.forge_engine_update_agent_array.argtypes = [
            c_void_p,
            c_size_t,
            POINTER(c_double),
            c_size_t
        ]
    
    def update_agent(self, entity_id: str, state_7d: List[float], slot: int = None) -> bool:
        """
        Update agent state in the Forge engine.
        
        Args:
            entity_id: Entity UUID (for logging/tracking)
            state_7d: 7-element list [awareness, intention, emotion, cognition, memory, creativity, integration]
            slot: Pre-assigned slot index. If None, this method cannot be called.
            
        Returns:
            True if update succeeded
        """
        if len(state_7d) != 7:
            return False
        
        if slot is None:
            raise ValueError(
                "slot parameter is required. Use MycelialSyncSystem which manages slots via SlotAllocator."
            )
        
        if self.rust_available:
            # Call Rust FFI
            arr = (c_double * 7)(*state_7d)
            result = self._lib.forge_engine_update_agent_array(
                self._engine,
                slot,
                arr,
                7
            )
            return result == 0
        else:
            # Python fallback
            self._py_agents[slot] = list(state_7d)
            return True
    
    def consensus_round(self) -> ConsensusSnapshot:
        """
        Perform one consensus round.
        
        Returns:
            ConsensusSnapshot with results
        """
        self._round_counter += 1
        
        if self.rust_available:
            return self._rust_consensus_round()
        else:
            return self._python_consensus_round()
    
    def _rust_consensus_round(self) -> ConsensusSnapshot:
        """Consensus round using Rust engine."""
        consensus_achieved_u8 = self._lib.forge_engine_consensus_round(self._engine)
        consensus_achieved = bool(consensus_achieved_u8)
        network_gamma = self._lib.forge_engine_get_network_gamma(self._engine)
        
        # For now, we don't have per-agent gamma FFI, so use empty dict
        # This would require additional FFI functions (see #8 in requirements)
        # Track active agents via Python-side counter
        num_active = len(self._py_agents)
        
        return ConsensusSnapshot(
            round=self._round_counter,
            consensus_achieved=consensus_achieved,
            network_gamma=network_gamma,
            num_active_agents=num_active,
            agreement_ratio=1.0 if consensus_achieved else 0.0,
            per_agent_gammas={}
        )
    
    def _python_consensus_round(self) -> ConsensusSnapshot:
        """Pure-Python ε-consensus fallback."""
        if not self._py_agents:
            return ConsensusSnapshot(
                round=self._round_counter,
                consensus_achieved=False,
                network_gamma=0.0,
                num_active_agents=0,
                agreement_ratio=0.0,
                per_agent_gammas={}
            )
        
        # Compute per-agent gamma (coherence metric)
        per_agent_gammas = {}
        for slot, state in self._py_agents.items():
            gamma = self._compute_gamma(state)
            per_agent_gammas[slot] = gamma
        
        # Network gamma is mean of all agent gammas
        network_gamma = sum(per_agent_gammas.values()) / len(per_agent_gammas)
        
        # ε-consensus: count agents within epsilon of mean
        agreeing = 0
        for gamma in per_agent_gammas.values():
            if abs(gamma - network_gamma) <= self._py_epsilon:
                agreeing += 1
        
        agreement_ratio = agreeing / len(per_agent_gammas)
        consensus_achieved = agreement_ratio >= self._py_threshold
        
        return ConsensusSnapshot(
            round=self._round_counter,
            consensus_achieved=consensus_achieved,
            network_gamma=network_gamma,
            num_active_agents=len(self._py_agents),
            agreement_ratio=agreement_ratio,
            per_agent_gammas=per_agent_gammas
        )
    
    def _compute_gamma(self, state: List[float]) -> float:
        """
        Compute gamma (coherence) for a 7D state.
        
        Uses Rust-compatible formula: max(0, 1 - CV) where CV is coefficient of variation.
        """
        if len(state) != 7:
            return 0.0
        
        mean = sum(state) / 7.0
        if mean == 0.0:
            return 0.0
        
        variance = sum((v - mean) ** 2 for v in state) / 7.0
        std_dev = variance ** 0.5
        cv = std_dev / mean  # Coefficient of variation
        
        return max(0.0, 1.0 - cv)
    
    def __del__(self):
        """Clean up Rust engine on destruction."""
        if self.rust_available and self._engine is not None:
            try:
                self._lib.forge_engine_free(self._engine)
            except:
                pass  # Ignore errors during cleanup
