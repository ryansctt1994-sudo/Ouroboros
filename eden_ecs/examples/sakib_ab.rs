//! A/B experiment harness — Sakib Index comparison across Weaver cultures.
//!
//! # Usage
//!
//! ```sh
//! cargo run -p eden_ecs --example sakib_ab --release -- [culture] [steps] [flow_gain]
//! ```
//!
//! Defaults: `culture=baseline  steps=6  flow_gain=2.0`
//!
//! # Output
//!
//! CSV to stdout with header:
//! ```text
//! tick,sakib_learning,sakib_frozen,culture
//! ```
//!
//! Two episodes are run for every tick:
//! * **learning** — the Weaver policy is applied each tick.
//! * **frozen**   — the policy is never applied (static weights).
//!
//! `record_sakib_index` is called only for the learning run to avoid mixing
//! telemetry series.

use eden_ecs::tracy::{record_sakib_index, sakib_index};
use eden_ecs::weaver::{culture_policy, PolicyContext, WeaverSandbox};

// ── Deterministic LCG ────────────────────────────────────────────────────────

/// Minimal 32-bit LCG (Numerical Recipes constants).
struct Lcg(u32);

impl Lcg {
    fn next_f32(&mut self) -> f32 {
        self.0 = self.0.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
        // Map high 24 bits to [0, 1).
        (self.0 >> 8) as f32 / (1u32 << 24) as f32
    }
}

// ── Graph topology ────────────────────────────────────────────────────────────

/// A fixed sparse directed graph with `n_nodes` nodes and `n_edges` edges.
struct Graph {
    n_nodes: usize,
    /// Each element is `(src, dst)`.
    edges: Vec<(usize, usize)>,
}

impl Graph {
    /// Build a deterministic sparse graph: each node gets exactly 2 out-edges
    /// pointing to `(node+1) % n` and `(node+3) % n`.
    fn build(n_nodes: usize) -> Self {
        let mut edges = Vec::with_capacity(n_nodes * 2);
        for i in 0..n_nodes {
            edges.push((i, (i + 1) % n_nodes));
            edges.push((i, (i + 3) % n_nodes));
        }
        Self { n_nodes, edges }
    }

    fn n_edges(&self) -> usize {
        self.edges.len()
    }
}

// ── Message-passing flow simulation ──────────────────────────────────────────

/// Perform `steps` rounds of message passing over `node_activations` using
/// `edge_weights` and return the resulting per-edge flow magnitudes.
///
/// Each round:
/// 1. Each node accumulates signals from in-edges weighted by `edge_weights`.
/// 2. Node activations are L2-normalised.
///
/// Edge flows are computed as the source-node activation scaled by
/// `flow_gain`, clamped to `[0, 1]`.  Using the steady-state source
/// activation (rather than a temporal gradient) gives stable, non-zero flows
/// throughout the simulation.
fn compute_flows(
    graph: &Graph,
    node_activations: &mut Vec<f32>,
    edge_weights: &[f32],
    steps: usize,
    flow_gain: f32,
) -> Vec<f32> {
    let n = graph.n_nodes;

    for _ in 0..steps {
        let mut next = vec![0.0_f32; n];
        for (edge_idx, &(src, dst)) in graph.edges.iter().enumerate() {
            next[dst] += node_activations[src] * edge_weights[edge_idx];
        }
        // L2 normalise.
        let norm: f32 = next.iter().map(|x| x * x).sum::<f32>().sqrt();
        if norm > 1e-9 {
            for v in next.iter_mut() {
                *v /= norm;
            }
        }
        *node_activations = next;
    }

    // Edge flow = source-node activation magnitude scaled by flow_gain.
    graph
        .edges
        .iter()
        .map(|&(src, _dst)| (node_activations[src] * flow_gain).clamp(0.0, 1.0))
        .collect()
}

// ── Main ──────────────────────────────────────────────────────────────────────

fn main() {
    // ── Parse CLI args ────────────────────────────────────────────────────────
    let args: Vec<String> = std::env::args().collect();
    let culture = args.get(1).map(String::as_str).unwrap_or("baseline");
    let steps: usize = args
        .get(2)
        .and_then(|s| s.parse().ok())
        .unwrap_or(6);
    let flow_gain: f32 = args
        .get(3)
        .and_then(|s| s.parse().ok())
        .unwrap_or(2.0);

    eprintln!(
        "sakib_ab: culture={culture}  steps={steps}  flow_gain={flow_gain:.2}"
    );

    // ── Build graph ───────────────────────────────────────────────────────────
    const N_NODES: usize = 16;
    const N_TICKS: usize = 40;
    const FLOW_THRESHOLD: f32 = 0.3;

    let graph = Graph::build(N_NODES);
    let n_edges = graph.n_edges();

    // ── Initial weights via LCG in [0.2, 0.8] ────────────────────────────────
    let mut lcg = Lcg(0xDEAD_BEEF);
    let initial_weights: Vec<f32> = (0..n_edges)
        .map(|_| 0.2 + lcg.next_f32() * 0.6)
        .collect();

    // ── Build policies ────────────────────────────────────────────────────────
    let policy_learning = culture_policy(culture, FLOW_THRESHOLD, n_edges);
    let mut sandbox_learning = WeaverSandbox::new(policy_learning);

    // ── Initialise node activations (deterministic) ───────────────────────────
    let mut activations_learning: Vec<f32> = (0..N_NODES)
        .map(|i| (i as f32 + 1.0) / N_NODES as f32)
        .collect();
    let mut activations_frozen = activations_learning.clone();

    let mut weights_learning = initial_weights.clone();
    let weights_frozen = initial_weights.clone();

    // ── CSV header ────────────────────────────────────────────────────────────
    println!("tick,sakib_learning,sakib_frozen,culture");

    for tick in 0..N_TICKS {
        // ── Learning run ─────────────────────────────────────────────────────
        let flows_learning = compute_flows(
            &graph,
            &mut activations_learning,
            &weights_learning,
            steps,
            flow_gain,
        );

        // Apply policy.
        let mut ctx = PolicyContext {
            edge_weights: &mut weights_learning,
            flow_rates: &flows_learning,
        };
        sandbox_learning.execute(&mut ctx);

        let s_learning = sakib_index(&weights_learning, &flows_learning, FLOW_THRESHOLD);
        record_sakib_index(s_learning);

        // ── Frozen run ────────────────────────────────────────────────────────
        let flows_frozen = compute_flows(
            &graph,
            &mut activations_frozen,
            &weights_frozen,
            steps,
            flow_gain,
        );
        let s_frozen = sakib_index(&weights_frozen, &flows_frozen, FLOW_THRESHOLD);

        println!("{tick},{s_learning:.6},{s_frozen:.6},{culture}");
    }
}
