"""
EDEN ECS Mycelial Sync System - The Bridge Between Python and Rust
===================================================================

MycelialSyncSystem orchestrates the flow between Python consciousness
evolution, Rust consensus engine, and PLL synchronization.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import math
import time
import warnings
from typing import Set, Dict
from .core import System, World
from .components import Consciousness7D
from .mycelial_components import HyphalNodeComponent
from .forge_bridge import ForgeBridge, SlotAllocator, MAX_AGENTS


# Golden ratio for topology scaling
PHI = 1.618033988749895


class MycelialSyncSystem(System):
    """
    Mycelial synchronization system - the bridge between consciousness layers.
    
    Runs at priority 45 (after MemorySystem=40, before ValidationSystem=50).
    
    Responsibilities:
    - Topology management: Auto-create HyphalNodeComponents for conscious entities
    - State pushing: Push Consciousness7D states to Forge engine
    - Consensus rounds: Run consensus and tag entities
    - PLL propagation: Phase-locked loop synchronization across network
    - Slot reconciliation: Track entity lifecycle and free unused slots
    """
    
    def __init__(self, priority: int = 45, use_rust: bool = None):
        super().__init__(priority)
        
        # Initialize Forge bridge and slot allocator
        self.bridge = ForgeBridge(num_agents=MAX_AGENTS, use_rust=use_rust)
        self.allocator = SlotAllocator(max_slots=MAX_AGENTS)
        
        # Track known entities for slot reconciliation
        self._known_entity_ids: Set[str] = set()
        
        # Metrics
        self.total_syncs = 0
        self.total_consensus_achieved = 0
        self.avg_sync_latency_us = 0.0
        self._latency_samples = []
        self._max_latency_samples = 100
    
    def update(self, world: World, dt: float) -> None:
        """
        Main update loop for mycelial synchronization.
        
        Args:
            world: ECS world
            dt: Time delta in seconds
        """
        sync_start = time.perf_counter()
        
        # 1. Ensure topology (auto-create HyphalNodeComponents)
        self._ensure_topology(world)
        
        # 2. Push all states to Forge engine
        self._push_states(world)
        
        # 3. Run consensus round
        self._run_consensus_round(world)
        
        # 4. PLL phase propagation
        self._propagate_pll(world, dt)
        
        # 5. Update metrics
        sync_end = time.perf_counter()
        latency_us = (sync_end - sync_start) * 1_000_000
        self._record_latency(latency_us)
        self.total_syncs += 1
    
    def _ensure_topology(self, world: World) -> None:
        """
        Ensure all conscious entities have HyphalNodeComponents and Forge slots.
        
        Also handles entity removal and slot reconciliation.
        """
        # Get current conscious entities
        conscious_entities = world.query_entities(None, Consciousness7D)
        current_entity_ids = {e.entity_id for e in conscious_entities}
        
        # Detect removed entities
        removed = self._known_entity_ids - current_entity_ids
        for entity_id in removed:
            # Release forge slot
            slot = self.allocator.release(entity_id)
            if slot is not None:
                # Push neutral state to freed slot using the slot directly
                neutral_state = [0.5] * 7
                self.bridge.update_agent(entity_id, neutral_state, slot=slot)
        
        # Update known set
        self._known_entity_ids = current_entity_ids
        
        # Ensure each entity has HyphalNodeComponent
        for entity in conscious_entities:
            hyphal = entity.get_component(HyphalNodeComponent)
            
            if hyphal is None:
                # Create new hyphal node with uninitialized phase marker
                hyphal = HyphalNodeComponent(
                    node_id=entity.entity_id,
                    phase=-1.0,  # Sentinel value for uninitialized
                    frequency=0.0997,
                    synchronized=False,
                    avg_latency_us=0.0,
                    neighbor_ids=[],
                    forge_slot=-1,
                    consensus_participant=False,
                    last_gamma=0.0,
                    last_agreement_ratio=0.0
                )
                entity.add_component(hyphal)
            
            # Ensure forge slot allocation
            if hyphal.forge_slot == -1:
                try:
                    slot = self.allocator.allocate(entity.entity_id)
                    hyphal.forge_slot = slot
                except RuntimeError as e:
                    warnings.warn(f"Forge slot allocation failed: {e}", RuntimeWarning)
                    continue
        
        # Build Φ-scaled mycelial connectivity
        self._build_topology(conscious_entities)
    
    def _build_topology(self, entities) -> None:
        """
        Build mycelial ring topology with Φ-scaled connectivity.
        
        Each entity connects to max(2, N/φ) neighbors in a ring.
        Initial phases are distributed evenly around unit circle.
        """
        n = len(entities)
        if n == 0:
            return
        
        # Calculate neighbors per node: max(2, N/φ)
        neighbors_per_node = max(2, int(n / PHI))
        
        # Distribute initial phases evenly around circle
        for i, entity in enumerate(entities):
            hyphal = entity.get_component(HyphalNodeComponent)
            if hyphal:
                # Initial phase: evenly spaced around [0, 2π)
                # Only set if not already initialized (phase == -1.0)
                if hyphal.phase == -1.0:
                    hyphal.phase = (2.0 * math.pi * i) / n
                
                # Build neighbor list (ring topology)
                hyphal.neighbor_ids = []
                for offset in range(1, neighbors_per_node + 1):
                    neighbor_idx = (i + offset) % n
                    neighbor = entities[neighbor_idx]
                    hyphal.neighbor_ids.append(neighbor.entity_id)
    
    def _push_states(self, world: World) -> None:
        """Push all Consciousness7D states to Forge engine."""
        conscious_entities = world.query_entities(None, Consciousness7D, HyphalNodeComponent)
        
        for entity in conscious_entities:
            c7d = entity.get_component(Consciousness7D)
            hyphal = entity.get_component(HyphalNodeComponent)
            if c7d and hyphal and hyphal.forge_slot >= 0:
                state_array = c7d.to_array()
                self.bridge.update_agent(entity.entity_id, state_array, slot=hyphal.forge_slot)
    
    def _run_consensus_round(self, world: World) -> None:
        """
        Run consensus round and update entity tags.
        
        Emits warning if num_active_agents < 4.
        """
        snapshot = self.bridge.consensus_round()
        
        # Warn if too few agents
        if snapshot.num_active_agents < 4:
            warnings.warn(
                f"Consensus round with {snapshot.num_active_agents} agents (< 4 minimum for BFT)",
                RuntimeWarning,
                stacklevel=2
            )
        
        # Update consensus achieved count
        if snapshot.consensus_achieved:
            self.total_consensus_achieved += 1
        
        # Update per-agent gamma in HyphalNodeComponent
        conscious_entities = world.query_entities(None, Consciousness7D, HyphalNodeComponent)
        for entity in conscious_entities:
            hyphal = entity.get_component(HyphalNodeComponent)
            if hyphal:
                # Get gamma for this agent's slot (if available in snapshot)
                if hyphal.forge_slot in snapshot.per_agent_gammas:
                    hyphal.last_gamma = snapshot.per_agent_gammas[hyphal.forge_slot]
                else:
                    # If per_agent_gammas not available (Rust mode without extended FFI),
                    # use network gamma as approximation
                    hyphal.last_gamma = snapshot.network_gamma
                
                hyphal.last_agreement_ratio = snapshot.agreement_ratio
                hyphal.consensus_participant = True
        
        # Tag entities based on consensus
        all_entities = world.entities.values()
        if snapshot.consensus_achieved:
            for entity in all_entities:
                entity.add_tag("forge_consensus")
        else:
            for entity in all_entities:
                entity.remove_tag("forge_consensus")
    
    def _propagate_pll(self, world: World, dt: float) -> None:
        """
        PLL (Phase-Locked Loop) propagation across mycelial network.
        
        Two-pass algorithm:
        1. Advance all phases by dt
        2. For each node, compute circular mean of neighbor phases and correct
        """
        entities = world.query_entities(None, HyphalNodeComponent)
        
        if not entities:
            return
        
        # Pass 1: Advance all phases
        for entity in entities:
            hyphal = entity.get_component(HyphalNodeComponent)
            if hyphal:
                hyphal.advance_phase(dt)
        
        # Pass 2: Phase correction based on neighbors
        for entity in entities:
            hyphal = entity.get_component(HyphalNodeComponent)
            if not hyphal or not hyphal.neighbor_ids:
                continue
            
            # Collect neighbor phases
            neighbor_phases = []
            for neighbor_id in hyphal.neighbor_ids:
                if neighbor_id in world.entities:
                    neighbor = world.entities[neighbor_id]
                    neighbor_hyphal = neighbor.get_component(HyphalNodeComponent)
                    if neighbor_hyphal:
                        neighbor_phases.append(neighbor_hyphal.phase)
            
            if not neighbor_phases:
                continue
            
            # Compute circular mean of neighbor phases using atan2(mean_sin, mean_cos)
            mean_sin = sum(math.sin(p) for p in neighbor_phases) / len(neighbor_phases)
            mean_cos = sum(math.cos(p) for p in neighbor_phases) / len(neighbor_phases)
            target_phase = math.atan2(mean_sin, mean_cos)
            
            # Normalize to [0, 2π)
            if target_phase < 0:
                target_phase += 2.0 * math.pi
            
            # Apply phase correction
            hyphal.correct_phase(target_phase)
    
    def _record_latency(self, latency_us: float) -> None:
        """Record sync latency and update rolling average."""
        self._latency_samples.append(latency_us)
        if len(self._latency_samples) > self._max_latency_samples:
            self._latency_samples.pop(0)
        
        self.avg_sync_latency_us = sum(self._latency_samples) / len(self._latency_samples)
    
    def get_metrics(self) -> dict:
        """
        Get mycelial sync metrics.
        
        Returns:
            Dictionary with metrics
        """
        consensus_rate = 0.0
        if self.total_syncs > 0:
            consensus_rate = self.total_consensus_achieved / self.total_syncs
        
        return {
            'total_syncs': self.total_syncs,
            'total_consensus_achieved': self.total_consensus_achieved,
            'consensus_rate': consensus_rate,
            'avg_sync_latency_us': self.avg_sync_latency_us,
        }
