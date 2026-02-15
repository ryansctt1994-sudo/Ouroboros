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
    forge_engine_update_agent_array,
    forge_engine_get_agent_gamma,
    forge_engine_get_consensus_agreement,
};

/// Main Forge engine combining synchronization and consensus
pub struct ForgeEngine {
    sync: SyncEngine,
    consensus: ForgeConsensus,
    rounds: AtomicU64,
    last_agreement_ratio: std::sync::Mutex<f64>,
}

impl ForgeEngine {
    /// Create new Forge engine
    pub fn new(num_agents: usize) -> Self {
        Self {
            sync: SyncEngine::new(num_agents),
            consensus: ForgeConsensus::new(num_agents),
            rounds: AtomicU64::new(0),
            last_agreement_ratio: std::sync::Mutex::new(0.0),
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
        
        // Compute per-agent gamma values
        let gammas = self.sync.agent_gammas();
        
        // Use ForgeConsensus for the actual consensus check (replaces hardcoded 0.7)
        let (consensus_achieved, agreement_ratio) = self.consensus.check_epsilon_consensus(&gammas);
        
        // Store agreement ratio for FFI access
        if let Ok(mut ratio) = self.last_agreement_ratio.lock() {
            *ratio = agreement_ratio;
        }
        
        // Compute network-level gamma
        let network_gamma = if gammas.is_empty() {
            0.0
        } else {
            gammas.iter().sum::<f64>() / gammas.len() as f64
        };
        
        ConsensusResult {
            round: self.rounds.load(Ordering::Relaxed),
            consensus_achieved,
            network_gamma,
            num_agents: gammas.len(),
            agreement_ratio,
        }
    }

    /// Get current network metrics
    pub fn network_metrics(&self) -> NetworkMetrics {
        self.sync.network_metrics()
    }

    /// Get unified metric (gamma) for a specific agent
    pub fn get_agent_gamma(&self, agent_id: usize) -> Result<f64, String> {
        self.sync.get_agent_gamma(agent_id)
            .map_err(|e| format!("{:?}", e))
    }

    /// Get the agreement ratio from the last consensus round
    /// 
    /// Returns 0.0 if the mutex is poisoned (due to a panic while the lock was held).
    /// This is a safe fallback that indicates no consensus.
    pub fn get_consensus_agreement(&self) -> f64 {
        self.last_agreement_ratio.lock()
            .map(|r| *r)
            .unwrap_or_else(|e| {
                eprintln!("Warning: agreement_ratio mutex poisoned: {}", e);
                0.0
            })
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
