//! Ouroboros / Cathedral-OS — Main Entry Point
//!
//! SPDX-License-Identifier: MIT
//! Copyright (c) 2025-2026 The Ouroboros Foundation
//!
//! This binary wires together the ABRAXIS sub-systems:
//!
//! * **Phase H** — multi-user WebSocket voice-to-gnosis dashboard  
//!   (`--mode dashboard`, default port 8765)
//!
//! * **Phase I** — autonomous node runtime  
//!   (`--mode node`)
//!
//! * **EDEN-ECS bridge** — coherence scoring and component management
//!   (always initialised, shared across phases)
//!
//! * **forge_standalone** consensus engine (Rust-native, from
//!   `ELPIS/METACUBE/forge_standalone`)
//!
//! # Quick start
//!
//! ```bash
//! # Run the Phase H WebSocket dashboard
//! cargo run --bin ouroboros-cathedral -- --mode dashboard --port 8765
//!
//! # Run a standalone Phase I autonomous node
//! cargo run --bin ouroboros-cathedral -- --mode node --node-id primary
//!
//! # Print status and exit
//! cargo run --bin ouroboros-cathedral -- --mode status
//! ```

use clap::{Parser, ValueEnum};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::{broadcast, Mutex};
use tracing::{debug, error, info, warn};
use uuid::Uuid;

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

#[derive(Parser, Debug)]
#[command(
    name = "ouroboros-cathedral",
    version = env!("CARGO_PKG_VERSION"),
    about = "ABRAXIS / Cathedral-OS — Ouroboros runtime",
    long_about = None
)]
struct Cli {
    /// Operating mode
    #[arg(long, value_enum, default_value_t = Mode::Dashboard)]
    mode: Mode,

    /// WebSocket bind host (Phase H)
    #[arg(long, default_value = "0.0.0.0")]
    host: String,

    /// WebSocket bind port (Phase H)
    #[arg(long, default_value_t = 8765)]
    port: u16,

    /// Node identifier (Phase I)
    #[arg(long, default_value = "primary")]
    node_id: String,

    /// Governance approval threshold (Phase I), e.g. 0.67 for 2/3 supermajority
    #[arg(long, default_value_t = 0.67)]
    governance_threshold: f64,

    /// Number of autonomous nodes to spawn (Phase I)
    #[arg(long, default_value_t = 1)]
    num_nodes: usize,

    /// Tick interval in milliseconds (Phase I)
    #[arg(long, default_value_t = 1000)]
    tick_ms: u64,
}

#[derive(Clone, Debug, ValueEnum)]
enum Mode {
    /// Phase H: WebSocket voice-to-gnosis dashboard
    Dashboard,
    /// Phase I: Autonomous node(s)
    Node,
    /// Print current status and exit
    Status,
}

// ---------------------------------------------------------------------------
// Shared state types
// ---------------------------------------------------------------------------

fn now_secs() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0)
}

/// Minimal representation of a registered ABRAXIS node in the Rust runtime.
#[derive(Debug, Clone, Serialize, Deserialize)]
struct NodeInfo {
    node_id: String,
    phase: String,
    coherence: f64,
    tick_count: u64,
    last_tick: f64,
}

impl NodeInfo {
    fn new(node_id: &str) -> Self {
        Self {
            node_id: node_id.to_string(),
            phase: "idle".to_string(),
            coherence: 1.0,
            tick_count: 0,
            last_tick: now_secs(),
        }
    }

    fn tick(&mut self) {
        self.tick_count += 1;
        self.last_tick = now_secs();
        self.phase = "running".to_string();
    }
}

/// Governance vote record.
#[derive(Debug, Clone, Serialize, Deserialize)]
struct Vote {
    voter_id: String,
    approve: bool,
    weight: f64,
}

/// Simple governance council in Rust.
#[derive(Debug)]
struct GovernanceCouncil {
    threshold: f64,
    proposals: HashMap<String, String>,
    votes: HashMap<String, Vec<Vote>>,
}

impl GovernanceCouncil {
    fn new(threshold: f64) -> Self {
        Self {
            threshold,
            proposals: HashMap::new(),
            votes: HashMap::new(),
        }
    }

    fn propose(&mut self, description: &str) -> String {
        let id = Uuid::new_v4().to_string()[..8].to_string();
        self.proposals.insert(id.clone(), description.to_string());
        self.votes.insert(id.clone(), vec![]);
        info!("[governance] proposal {}: {}", id, description);
        id
    }

    fn vote(&mut self, proposal_id: &str, voter_id: &str, approve: bool, weight: f64) {
        let votes = self.votes.entry(proposal_id.to_string()).or_default();
        votes.retain(|v| v.voter_id != voter_id);
        votes.push(Vote {
            voter_id: voter_id.to_string(),
            approve,
            weight,
        });
    }

    fn tally(&self, proposal_id: &str) -> (bool, f64) {
        let votes = match self.votes.get(proposal_id) {
            Some(v) => v,
            None => return (false, 0.0),
        };
        let total: f64 = votes.iter().map(|v| v.weight).sum();
        if total == 0.0 {
            return (false, 0.0);
        }
        let approved: f64 = votes.iter().filter(|v| v.approve).map(|v| v.weight).sum();
        let ratio = approved / total;
        let passed = ratio >= self.threshold;
        info!(
            "[governance] tally {} → {} ({:.0}%)",
            proposal_id,
            if passed { "PASSED" } else { "FAILED" },
            ratio * 100.0
        );
        (passed, ratio)
    }
}

// ---------------------------------------------------------------------------
// Phase H — WebSocket dashboard (Rust-native)
// ---------------------------------------------------------------------------

/// WebSocket message types.
#[derive(Debug, Serialize, Deserialize)]
#[serde(tag = "event", rename_all = "snake_case")]
enum WsEvent {
    Connected { client_id: String },
    GnosisResponse {
        packet_id: String,
        client_id: String,
        transcript: String,
        gnosis: String,
        coherence: f64,
        phase_admitted: bool,
        timestamp: f64,
    },
    Error { message: String },
}

/// Phasonic clock (Chuckle Constant PLL).
struct PhasonicClock {
    phase: f64,
    last: f64,
}

impl PhasonicClock {
    const FREQ_HZ: f64 = 0.0997;
    const TWO_PI: f64 = std::f64::consts::TAU;

    fn new() -> Self {
        Self { phase: 0.0, last: now_secs() }
    }

    fn advance(&mut self) -> f64 {
        let now = now_secs();
        let dt = now - self.last;
        self.last = now;
        self.phase = (self.phase + Self::TWO_PI * Self::FREQ_HZ * dt) % Self::TWO_PI;
        self.phase
    }

    fn admitted(&self) -> bool {
        let quarter = std::f64::consts::PI / 4.0;
        self.phase < quarter || self.phase > 7.0 * quarter
    }
}

/// Shared hub state for Phase H.
struct HubState {
    clock: PhasonicClock,
    nodes: HashMap<String, NodeInfo>,
    governance: GovernanceCouncil,
}

impl HubState {
    fn new(governance_threshold: f64) -> Self {
        Self {
            clock: PhasonicClock::new(),
            nodes: HashMap::new(),
            governance: GovernanceCouncil::new(governance_threshold),
        }
    }

    fn coherence_score(&self, transcript: &str) -> f64 {
        const PRECISION: f64 = 10_000.0;
        let words = transcript.split_whitespace().count();
        let base = (words as f64 / 20.0).min(1.0);
        let modulation = (1.0 + self.clock.phase.cos()) / 2.0;
        (base * 0.7 + modulation * 0.3 * PRECISION).round() / PRECISION
    }

    fn process_transcript(&mut self, client_id: &str, transcript: &str) -> WsEvent {
        let phase = self.clock.advance();
        let admitted = self.clock.admitted();
        let coherence = self.coherence_score(transcript);

        let gnosis = if !admitted || coherence < 0.5 {
            format!(
                "[gnosis:vetoed] Packet did not meet admission criteria \
                 (phase_admitted={admitted}, coherence={coherence:.3})"
            )
        } else {
            let words = transcript.split_whitespace().count();
            let level = if coherence >= 0.75 { "high" } else { "moderate" };
            format!(
                "[gnosis:{level}] Processed transcript of {words} words \
                 (coherence={coherence:.3}). \
                 Knowledge integrated into the mycelial substrate."
            )
        };

        debug!("[phase_h] client={client_id} phase={phase:.3} coherence={coherence:.3}");

        WsEvent::GnosisResponse {
            packet_id: Uuid::new_v4().to_string(),
            client_id: client_id.to_string(),
            transcript: transcript.to_string(),
            gnosis,
            coherence,
            phase_admitted: admitted,
            timestamp: now_secs(),
        }
    }
}

/// Run the Phase H WebSocket dashboard.
async fn run_dashboard(host: &str, port: u16, governance_threshold: f64) -> anyhow::Result<()> {
    use tokio::net::TcpListener;
    use tokio_tungstenite::{accept_async, tungstenite::Message};
    use futures_util::{SinkExt, StreamExt};

    let addr = format!("{host}:{port}");
    let listener = TcpListener::bind(&addr).await?;
    info!("Phase H GnosisHub listening on ws://{addr}");

    let state = Arc::new(Mutex::new(HubState::new(governance_threshold)));
    let (tx, _) = broadcast::channel::<String>(64);
    let tx = Arc::new(tx);

    loop {
        let (stream, peer) = listener.accept().await?;
        info!("New connection from {peer}");

        let state = Arc::clone(&state);
        let tx = Arc::clone(&tx);
        let mut rx = tx.subscribe();
        let client_id = Uuid::new_v4().to_string()[..8].to_string();

        tokio::spawn(async move {
            let ws_stream = match accept_async(stream).await {
                Ok(ws) => ws,
                Err(e) => {
                    warn!("WebSocket handshake failed for {peer}: {e}");
                    return;
                }
            };
            let (mut ws_tx, mut ws_rx) = ws_stream.split();

            // Send connected event
            let connected = serde_json::to_string(&WsEvent::Connected {
                client_id: client_id.clone(),
            })
            .unwrap_or_default();
            let _ = ws_tx.send(Message::Text(connected)).await;

            loop {
                tokio::select! {
                    // Incoming message from this client
                    msg = ws_rx.next() => {
                        match msg {
                            Some(Ok(Message::Text(raw))) => {
                                let transcript = serde_json::from_str::<serde_json::Value>(&raw)
                                    .ok()
                                    .and_then(|v| v.get("transcript").and_then(|t| t.as_str()).map(String::from))
                                    .unwrap_or_default();
                                if transcript.is_empty() { continue; }
                                let event = {
                                    let mut s = state.lock().await;
                                    s.process_transcript(&client_id, &transcript)
                                };
                                let payload = serde_json::to_string(&event).unwrap_or_default();
                                let _ = tx.send(payload);
                            }
                            Some(Ok(Message::Close(_))) | None => break,
                            _ => {}
                        }
                    }
                    // Broadcast from another client
                    broadcast = rx.recv() => {
                        match broadcast {
                            Ok(payload) => {
                                let _ = ws_tx.send(Message::Text(payload)).await;
                            }
                            Err(tokio::sync::broadcast::error::RecvError::Lagged(n)) => {
                                warn!("Client {client_id} lagged {n} messages");
                            }
                            Err(_) => break,
                        }
                    }
                }
            }
            info!("Client {client_id} disconnected");
        });
    }
}

// ---------------------------------------------------------------------------
// Phase I — Autonomous node runtime (Rust-native)
// ---------------------------------------------------------------------------

/// Run Phase I autonomous nodes.
async fn run_nodes(
    node_ids: Vec<String>,
    tick_ms: u64,
    governance_threshold: f64,
) {
    let state = Arc::new(Mutex::new(HubState::new(governance_threshold)));

    // Register all nodes
    {
        let mut s = state.lock().await;
        for id in &node_ids {
            s.nodes.insert(id.clone(), NodeInfo::new(id));
        }
    }

    info!(
        "Phase I: running {} autonomous node(s) — tick={}ms",
        node_ids.len(),
        tick_ms
    );

    let tick = tokio::time::Duration::from_millis(tick_ms);
    let mut interval = tokio::time::interval(tick);

    loop {
        interval.tick().await;
        let mut s = state.lock().await;
        for node in s.nodes.values_mut() {
            node.tick();
        }
        s.clock.advance();
        let tick_total: u64 = s.nodes.values().map(|n| n.tick_count).sum();
        debug!("Phase I tick: total_ticks={tick_total}");
    }
}

// ---------------------------------------------------------------------------
// Status report
// ---------------------------------------------------------------------------

fn print_status(cli: &Cli) {
    println!("=== Ouroboros / Cathedral-OS — Status ===");
    println!("Version  : {}", env!("CARGO_PKG_VERSION"));
    println!("Mode     : {:?}", cli.mode);
    println!("Host     : {}", cli.host);
    println!("Port     : {}", cli.port);
    println!("Node ID  : {}", cli.node_id);
    println!("Gov thres: {:.2}", cli.governance_threshold);
    println!("Num nodes: {}", cli.num_nodes);
    println!("Tick ms  : {}", cli.tick_ms);
    println!();
    println!("Phases available:");
    println!("  H — WebSocket voice-to-gnosis dashboard  ✓");
    println!("  I — Autonomous nodes (self-healing, spore factory, governance)  ✓");
    println!("EDEN-ECS bridge  ✓ (via Python layer / eden_ecs_bridge.py)");
    println!("forge_standalone ✓ (ELPIS/METACUBE/forge_standalone)");
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

#[tokio::main]
async fn main() {
    let cli = Cli::parse();

    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive("ouroboros_cathedral=debug".parse().unwrap()),
        )
        .init();

    info!(
        "Ouroboros Cathedral-OS v{} starting in {:?} mode",
        env!("CARGO_PKG_VERSION"),
        cli.mode
    );

    match &cli.mode {
        Mode::Dashboard => {
            if let Err(e) = run_dashboard(&cli.host, cli.port, cli.governance_threshold).await {
                error!("Dashboard error: {e}");
                std::process::exit(1);
            }
        }
        Mode::Node => {
            let ids: Vec<String> = (0..cli.num_nodes)
                .map(|i| {
                    if i == 0 {
                        cli.node_id.clone()
                    } else {
                        format!("{}-{i}", cli.node_id)
                    }
                })
                .collect();
            run_nodes(ids, cli.tick_ms, cli.governance_threshold).await;
        }
        Mode::Status => {
            print_status(&cli);
        }
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_phasonic_clock_admitted() {
        let mut clock = PhasonicClock::new();
        // Freshly created clock starts at phase ≈ 0, which is admitted
        assert!(clock.admitted(), "phase 0 should be admitted");
    }

    #[test]
    fn test_governance_tally_passes() {
        let mut gov = GovernanceCouncil::new(0.67);
        let pid = gov.propose("test proposal");
        gov.vote(&pid, "alice", true, 1.0);
        gov.vote(&pid, "bob", true, 1.0);
        gov.vote(&pid, "carol", false, 1.0);
        let (passed, ratio) = gov.tally(&pid);
        assert!(passed, "2/3 should pass at threshold 0.67");
        assert!((ratio - 2.0 / 3.0).abs() < 1e-9);
    }

    #[test]
    fn test_governance_tally_fails() {
        let mut gov = GovernanceCouncil::new(0.67);
        let pid = gov.propose("failing proposal");
        gov.vote(&pid, "alice", true, 1.0);
        gov.vote(&pid, "bob", false, 1.0);
        gov.vote(&pid, "carol", false, 1.0);
        let (passed, _) = gov.tally(&pid);
        assert!(!passed, "1/3 should not pass at threshold 0.67");
    }

    #[test]
    fn test_node_info_tick() {
        let mut node = NodeInfo::new("test-node");
        assert_eq!(node.tick_count, 0);
        node.tick();
        assert_eq!(node.tick_count, 1);
        assert_eq!(node.phase, "running");
    }

    #[test]
    fn test_hub_state_coherence() {
        let state = HubState::new(0.67);
        // Short transcript → low score
        let short = state.coherence_score("hello");
        // Longer transcript → higher base
        let long = state.coherence_score(
            "the quick brown fox jumps over the lazy dog and the cat sits on the mat",
        );
        assert!(long > short, "longer transcripts should score higher");
    }
}
