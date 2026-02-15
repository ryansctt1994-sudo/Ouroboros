//! Consensus module for Forge protocol
//!
//! Implements Byzantine fault tolerant consensus for METACUBE networks

/// Parameters for ε-consensus checking
#[derive(Debug, Clone, Copy)]
pub struct ConsensusParams {
    /// Maximum deviation from mean gamma for an agent to count as "agreeing"
    pub epsilon: f64,
}

impl Default for ConsensusParams {
    fn default() -> Self {
        Self { epsilon: 0.15 }
    }
}

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
    params: ConsensusParams,
}

impl ForgeConsensus {
    /// Create new consensus protocol
    /// 
    /// # Panics
    /// Panics if `num_agents` is 0 or less than 4 (minimum for BFT).
    /// This is intentional to catch configuration errors early.
    pub fn new(num_agents: usize) -> Self {
        // Validate inputs
        assert!(num_agents > 0, "ForgeConsensus: num_agents must be > 0");
        assert!(num_agents >= 4, "ForgeConsensus: BFT requires at least 4 agents (got {})", num_agents);
        
        let fault_tolerance = (num_agents - 1) / 3;  // Byzantine fault tolerance
        let consensus_threshold = (2.0 * fault_tolerance as f64 + 1.0) / num_agents as f64;
        
        Self {
            num_agents,
            fault_tolerance,
            consensus_threshold,
            params: ConsensusParams::default(),
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

    /// Check ε-consensus: what fraction of agents have gamma within epsilon of the mean?
    /// Returns true if that fraction meets or exceeds the BFT-derived consensus_threshold.
    pub fn check_epsilon_consensus(&self, gammas: &[f64]) -> bool {
        if gammas.is_empty() {
            return false;
        }
        let n = gammas.len() as f64;
        let mean = gammas.iter().sum::<f64>() / n;
        let agreeing = gammas.iter()
            .filter(|&&g| (g - mean).abs() <= self.params.epsilon)
            .count();
        let agreement_ratio = agreeing as f64 / n;
        agreement_ratio >= self.consensus_threshold
    }

    /// Get the BFT-derived consensus threshold
    pub fn threshold(&self) -> f64 {
        self.consensus_threshold
    }

    /// Set the epsilon parameter for consensus checking
    pub fn set_epsilon(&mut self, epsilon: f64) {
        self.params.epsilon = epsilon;
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

    #[test]
    #[should_panic(expected = "num_agents must be > 0")]
    fn test_consensus_zero_agents() {
        ForgeConsensus::new(0);
    }

    #[test]
    #[should_panic(expected = "BFT requires at least 4 agents")]
    fn test_consensus_too_few_agents() {
        ForgeConsensus::new(3);
    }

    #[test]
    fn test_epsilon_consensus_all_agree() {
        let consensus = ForgeConsensus::new(5);
        // All gammas very close to each other
        let gammas = vec![0.7, 0.71, 0.69, 0.7, 0.72];
        assert!(consensus.check_epsilon_consensus(&gammas));
    }

    #[test]
    fn test_epsilon_consensus_disagreement() {
        let consensus = ForgeConsensus::new(5);
        // Gammas spread far apart — agents disagree
        let gammas = vec![0.9, 0.1, 0.5, 0.3, 0.8];
        assert!(!consensus.check_epsilon_consensus(&gammas));
    }

    #[test]
    fn test_epsilon_consensus_empty() {
        let consensus = ForgeConsensus::new(4);
        assert!(!consensus.check_epsilon_consensus(&[]));
    }
}
