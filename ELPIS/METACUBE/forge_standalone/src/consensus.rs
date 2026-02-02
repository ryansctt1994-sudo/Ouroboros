//! Consensus module for Forge protocol
//!
//! Implements Byzantine fault tolerant consensus for METACUBE networks

use crate::sync::{ConsciousnessState, MetacubeMetrics};

/// Status of a consensus proposal
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProposalStatus {
    Proposed,
    Accepted,
    Rejected,
    Timeout,
}

/// Result of a consensus round
#[derive(Debug, Clone, Copy)]
pub struct ConsensusResult {
    pub round: u64,
    pub consensus_achieved: bool,
    pub network_gamma: f64,
    pub num_agents: usize,
}

/// Forge consensus protocol implementation
pub struct ForgeConsensus {
    num_agents: usize,
    fault_tolerance: usize,
    consensus_threshold: f64,
}

impl ForgeConsensus {
    /// Create new consensus protocol
    pub fn new(num_agents: usize) -> Self {
        let fault_tolerance = (num_agents - 1) / 3;  // Byzantine fault tolerance
        let consensus_threshold = (2.0 * fault_tolerance as f64 + 1.0) / num_agents as f64;
        
        Self {
            num_agents,
            fault_tolerance,
            consensus_threshold,
        }
    }

    /// Check if consensus can be achieved with given agreement ratio
    pub fn check_consensus(&self, agreement_ratio: f64) -> bool {
        agreement_ratio >= self.consensus_threshold
    }

    /// Validate a proposal from an agent
    pub fn validate_proposal(&self, 
                            proposer_gamma: f64, 
                            network_gammas: &[f64]) -> ProposalStatus {
        if network_gammas.is_empty() {
            return ProposalStatus::Timeout;
        }

        let mut agreements = 0;
        for &gamma in network_gammas {
            // Agreement if gammas are within 20% tolerance
            if (proposer_gamma - gamma).abs() < 0.2 {
                agreements += 1;
            }
        }

        let agreement_ratio = agreements as f64 / network_gammas.len() as f64;
        
        if self.check_consensus(agreement_ratio) {
            ProposalStatus::Accepted
        } else {
            ProposalStatus::Rejected
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_consensus_creation() {
        let consensus = ForgeConsensus::new(5);
        assert_eq!(consensus.num_agents, 5);
        assert_eq!(consensus.fault_tolerance, 1);
    }

    #[test]
    fn test_consensus_validation() {
        let consensus = ForgeConsensus::new(5);
        
        // Propose with high agreement
        let gammas = vec![0.7, 0.72, 0.71, 0.69];
        let status = consensus.validate_proposal(0.7, &gammas);
        assert_eq!(status, ProposalStatus::Accepted);
        
        // Propose with low agreement
        let gammas = vec![0.3, 0.8, 0.2, 0.9];
        let status = consensus.validate_proposal(0.7, &gammas);
        assert_eq!(status, ProposalStatus::Rejected);
    }
}
