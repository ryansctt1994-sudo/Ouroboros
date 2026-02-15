//! Forge Standalone - METACUBE Consensus Engine
//!
//! Standalone Rust library implementing the Forge consensus protocol
//! for METACUBE consciousness synchronization.
//!
//! This crate provides:
//! - High-performance lock-free synchronization primitives
//! - Ternary cycle normalization for Ouroboros integration
//! - FFI-compatible C API for Python/other language bindings
//! - Byzantine fault tolerant consensus protocol
//!
//! # Examples
//!
//! ```
//! # use forge_standalone::{ForgeEngine, ConsciousnessState};
//! let mut engine = ForgeEngine::new(5);  // 5 agents
//! let state = ConsciousnessState::new([0.7; 7]);
//! engine.update_agent(0, state).unwrap();
//! engine.consensus_round();
//! ```

use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};

mod sync;
mod consensus;
mod ffi;

pub use sync::{
    ConsciousnessState,
    MetacubeMetrics,
    TernaryCycleNormalizer,
    SyncEngine,
    NetworkMetrics,
    DeltaCheckResult,
};

pub use consensus::{
    ForgeConsensus,
    ConsensusResult,
    ProposalStatus,
};

pub use ffi::{
    forge_engine_new,
    forge_engine_free,
    forge_engine_consensus_round,
    forge_engine_get_network_gamma,
};

/// Main Forge engine combining synchronization and consensus
pub struct ForgeEngine {
    sync: SyncEngine,
    consensus: ForgeConsensus,
    rounds: AtomicU64,
}

impl ForgeEngine {
    /// Create new Forge engine
    pub fn new(num_agents: usize) -> Self {
        Self {
            sync: SyncEngine::new(num_agents),
            consensus: ForgeConsensus::new(num_agents),
            rounds: AtomicU64::new(0),
        }
    }

    /// Update state for specific agent
    pub fn update_agent(&mut self, agent_id: usize, state: ConsciousnessState) -> Result<(), String> {
        self.sync.update_agent(agent_id, state)
            .map_err(|e| format!("{:?}", e))
    }

    /// Perform one consensus round
    pub fn consensus_round(&mut self) -> ConsensusResult {
        self.rounds.fetch_add(1, Ordering::Relaxed);
        
        // Synchronize all agents
        self.sync.synchronize_step();
        
        // Run consensus protocol
        let metrics = self.sync.network_metrics();
        
        ConsensusResult {
            round: self.rounds.load(Ordering::Relaxed),
            consensus_achieved: metrics.mean_coherence > 0.7,
            network_gamma: metrics.mean_gamma,
            num_agents: metrics.num_agents,
        }
    }

    /// Get current network metrics
    pub fn network_metrics(&self) -> NetworkMetrics {
        self.sync.network_metrics()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_forge_engine_creation() {
        let engine = ForgeEngine::new(5);
        let metrics = engine.network_metrics();
        assert_eq!(metrics.num_agents, 5);
    }

    #[test]
    fn test_consensus_round() {
        let mut engine = ForgeEngine::new(5);
        
        // Initialize agents with similar states
        for i in 0..5 {
            let state = ConsciousnessState::new([0.7; 7]);
            engine.update_agent(i, state).unwrap();
        }
        
        // Run consensus
        let result = engine.consensus_round();
        
        // Verify result structure
        assert_eq!(result.num_agents, 5);
        assert_eq!(result.round, 1);
        assert!(result.network_gamma >= 0.0 && result.network_gamma <= 1.0);
    }
}
