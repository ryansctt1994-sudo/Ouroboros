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
//! CSV to **stdout** with header:
//! ```text
//! tick,sakib_learning,sakib_frozen,culture
//! ```
//!
//! Diagnostics (param summary, flow/weight percentiles, regime hint) go to **stderr**
//! so they never contaminate the CSV.
//!
//! # Graph
//!
//! A fixed sparse directed graph with 10 000 nodes and out-degree 5 (50 000 edges)
//! is generated deterministically via a 32-bit LCG.  Initial edge weights are in
//! \[0.2, 0.8\] (also LCG-derived).
//!
//! # A/B protocol
//!
//! Two independent episodes are run with **identical** initial weights and
//! deterministic per-tick flow injection:
//! - **learning** — the [`WeaverSandbox`] policy is applied each tick.
//! - **frozen**   — weights are never modified.
//!
//! `record_sakib_index` is called only for the learning run to keep Tracy
//! telemetry series clean.

use eden_ecs::tracy::{flow_entropy, record_flow_entropy, record_sakib_index, sakib_index};
use eden_ecs::weaver::{culture_policy, PolicyContext, WeaverSandbox};

// ── Deterministic LCG ────────────────────────────────────────────────────────

/// Minimal 32-bit LCG (Numerical Recipes constants).
struct Lcg(u32);

impl Lcg {
    #[inline]
    fn next(&mut self) -> u32 {
        self.0 = self.0.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
        self.0
    }

    /// Uniform float in [0, 1).
    #[inline]
    fn next_f32(&mut self) -> f32 {
        // Use top 24 bits for full mantissa coverage.
        (self.next() >> 8) as f32 / (1u32 << 24) as f32
    }

    /// Uniform integer in [0, n).
    #[inline]
    fn next_usize(&mut self, n: usize) -> usize {
        (self.next() as usize) % n
    }
}

// ── Graph ─────────────────────────────────────────────────────────────────────

/// Fixed sparse directed graph.
struct Graph {
    n_nodes: usize,
    /// (src, dst) for each edge, indexed 0..n_edges.
    edges: Vec<(usize, usize)>,
}

impl Graph {
    /// Build a random sparse directed graph with fixed out-degree per node.
    ///
    /// Guarantees: no self-loops; no duplicate (src, dst) pairs per node.
    fn build_random(n_nodes: usize, out_degree: usize, seed: u32) -> Self {
        assert!(out_degree < n_nodes, "out_degree must be < n_nodes");
        let mut lcg = Lcg(seed ^ 0xA5A5_1234);
        let mut edges = Vec::with_capacity(n_nodes * out_degree);
        for src in 0..n_nodes {
            let mut chosen: Vec<usize> = Vec::with_capacity(out_degree);
            let mut guard = 0u32;
            while chosen.len() < out_degree {
                let dst = lcg.next_usize(n_nodes);
                if dst != src && !chosen.contains(&dst) {
                    chosen.push(dst);
                }
                guard += 1;
                if guard > 100_000 {
                    break; // safety valve — should never trigger for n≥6
                }
            }
            for dst in chosen {
                edges.push((src, dst));
            }
        }
        Self { n_nodes, edges }
    }

    fn n_edges(&self) -> usize {
        self.edges.len()
    }
}

// ── Flow computation ──────────────────────────────────────────────────────────

/// Run `steps` rounds of message passing and return per-edge flow magnitudes.
///
/// A single unit pulse is injected into a node chosen deterministically from
/// `tick` and `seed` before propagation.  Each step L2-normalises the node
/// activations.  Flows are the source-node activation scaled by `flow_gain`,
/// clamped to \[0, 1\].
///
/// If `noise_sigma > 0`, additive Gaussian noise is approximated via a
/// Box-Muller step using the same LCG (no extra dependencies).
fn compute_flows(
    graph: &Graph,
    edge_weights: &[f32],
    tick: u32,
    seed: u32,
    steps: usize,
    flow_gain: f32,
    noise_sigma: f32,
) -> Vec<f32> {
    let n = graph.n_nodes;
    let mut lcg = Lcg(seed ^ tick.wrapping_mul(0x9E37_79B9));
    let inject = lcg.next_usize(n);

    let mut act = vec![0.0_f32; n];
    act[inject] = 1.0;

    for _ in 0..steps {
        let mut next = vec![0.0_f32; n];
        for (edge_idx, &(src, dst)) in graph.edges.iter().enumerate() {
            next[dst] += act[src] * edge_weights[edge_idx];
        }
        let norm: f32 = next.iter().map(|x| x * x).sum::<f32>().sqrt();
        if norm > 1e-9 {
            for v in next.iter_mut() {
                *v /= norm;
            }
        }
        act = next;
    }

    // Flow = source activation × flow_gain, clamped [0,1].
    let mut flows: Vec<f32> = graph
        .edges
        .iter()
        .map(|&(src, _)| (act[src] * flow_gain).clamp(0.0, 1.0))
        .collect();

    // Additive noise via Box-Muller (deterministic LCG, no extra deps).
    if noise_sigma > 0.0 {
        let mut i = 0;
        while i + 1 < flows.len() {
            let u1 = lcg.next_f32().max(1e-9);
            let u2 = lcg.next_f32();
            let mag = noise_sigma * (-2.0 * u1.ln()).sqrt();
            let angle = std::f32::consts::TAU * u2;
            flows[i] = (flows[i] + mag * angle.cos()).clamp(0.0, 1.0);
            flows[i + 1] = (flows[i + 1] + mag * angle.sin()).clamp(0.0, 1.0);
            i += 2;
        }
    }

    flows
}

// ── Diagnostics ───────────────────────────────────────────────────────────────

/// Abort with a clear message if any value in `slice` is non-finite (NaN or Inf).
fn assert_finite(slice: &[f32], label: &str) {
    for (i, &v) in slice.iter().enumerate() {
        if !v.is_finite() {
            eprintln!("FATAL: {label}[{i}] = {v} (non-finite). Aborting.");
            std::process::exit(1);
        }
    }
}

/// Compute (p50, p90, p99) from an unsorted slice by sorting a clone.
///
/// Allocation is intentional: called at most twice per episode, not per tick.
fn percentiles(values: &[f32]) -> (f32, f32, f32) {
    let n = values.len();
    if n == 0 {
        return (0.0, 0.0, 0.0);
    }
    let mut sorted = values.to_vec();
    sorted.sort_unstable_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let p50 = sorted[n / 2];
    let p90 = sorted[(n * 9) / 10];
    let p99 = sorted[(n * 99) / 100];
    (p50, p90, p99)
}

/// Classify the network regime based on final weight percentiles.
///
/// | Regime      | Signal                                                    |
/// |-------------|-----------------------------------------------------------|
/// | collapse    | p90 < 0.15 — decay dominates; network going inert        |
/// | amplifier   | p99 > 0.95 AND p50 < 0.4 — winner-take-all channels      |
/// | routing     | structured heterogeneity; Sakib gap learning > frozen     |
fn regime_hint(p50: f32, p90: f32, p99: f32) -> &'static str {
    if p90 < 0.15 {
        "collapse"
    } else if p99 > 0.95 && p50 < 0.4 {
        "amplifier"
    } else {
        "routing"
    }
}

// ── Episode ───────────────────────────────────────────────────────────────────

struct Episode {
    sakib_curve: Vec<f32>,
    final_weights: Vec<f32>,
}

fn run_episode(
    graph: &Graph,
    initial_weights: &[f32],
    learning: bool,
    n_ticks: u32,
    flow_threshold: f32,
    seed: u32,
    culture: &str,
    steps: usize,
    flow_gain: f32,
    noise_sigma: f32,
    // Ticks at which to log flow percentiles to stderr.
    diag_ticks: &[u32],
) -> Episode {
    let tag = if learning { "learning" } else { "frozen  " };
    let mut weights = initial_weights.to_vec();
    let mut sandbox = WeaverSandbox::new(culture_policy(culture, flow_threshold, weights.len()));
    let mut sakib_curve = Vec::with_capacity(n_ticks as usize);

    for tick in 0..n_ticks {
        let flows = compute_flows(graph, &weights, tick, seed, steps, flow_gain, noise_sigma);

        // Debug builds check every tick; release builds rely on final assert_finite.
        #[cfg(debug_assertions)]
        {
            assert_finite(&flows, "flows");
            assert_finite(&weights, "weights");
        }

        // Flow percentile + entropy snapshot at selected ticks.
        if diag_ticks.contains(&tick) {
            let (fp50, fp90, fp99) = percentiles(&flows);
            let h = flow_entropy(&flows);
            eprintln!(
                "[{tag}:{culture} tick={tick:4}] flows  p50={fp50:.3} p90={fp90:.3} p99={fp99:.3}  H={h:.3}"
            );
        }

        let s = sakib_index(&weights, &flows, flow_threshold);
        sakib_curve.push(s);

        if learning {
            record_sakib_index(s);
            record_flow_entropy(flow_entropy(&flows));
            let mut ctx = PolicyContext {
                edge_weights: &mut weights,
                flow_rates: &flows,
            };
            sandbox.execute(&mut ctx);
        }
    }

    // Final weight percentiles + regime hint.
    let (wp50, wp90, wp99) = percentiles(&weights);
    let regime = regime_hint(wp50, wp90, wp99);
    eprintln!(
        "[{tag}:{culture}] weights p50={wp50:.3} p90={wp90:.3} p99={wp99:.3} → {regime}"
    );

    Episode {
        sakib_curve,
        final_weights: weights,
    }
}

// ── Main ──────────────────────────────────────────────────────────────────────

fn main() {
    // ── CLI args ──────────────────────────────────────────────────────────────
    let args: Vec<String> = std::env::args().collect();
    let culture = args.get(1).map(String::as_str).unwrap_or("baseline");
    let steps: usize = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(6);
    let flow_gain: f32 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(2.0);
    let noise_sigma: f32 = args.get(4).and_then(|s| s.parse().ok()).unwrap_or(0.0);

    eprintln!(
        "sakib_ab: culture={culture}  steps={steps}  flow_gain={flow_gain:.2}  noise={noise_sigma:.3}"
    );

    // ── Graph ─────────────────────────────────────────────────────────────────
    const N_NODES: usize = 10_000;
    const OUT_DEGREE: usize = 5; // → 50 000 edges
    const N_TICKS: u32 = 2_000;
    const FLOW_THRESHOLD: f32 = 0.3;
    const SEED: u32 = 12_345;

    let graph = Graph::build_random(N_NODES, OUT_DEGREE, SEED);
    eprintln!("graph: {N_NODES} nodes × {OUT_DEGREE} out-degree = {} edges", graph.n_edges());

    // ── Initial weights via LCG in [0.2, 0.8] ────────────────────────────────
    let mut lcg = Lcg(SEED ^ 0xC0FF_EE00);
    let initial_weights: Vec<f32> = (0..graph.n_edges())
        .map(|_| 0.2 + lcg.next_f32() * 0.6)
        .collect();

    // Ticks at which to log flow percentiles (early and late).
    let diag_ticks = [100u32, N_TICKS - 100];

    // ── Run episodes ──────────────────────────────────────────────────────────
    let learn = run_episode(
        &graph,
        &initial_weights,
        true,
        N_TICKS,
        FLOW_THRESHOLD,
        SEED,
        culture,
        steps,
        flow_gain,
        noise_sigma,
        &diag_ticks,
    );

    let frozen = run_episode(
        &graph,
        &initial_weights,
        false,
        N_TICKS,
        FLOW_THRESHOLD,
        SEED,
        culture,
        steps,
        flow_gain,
        noise_sigma,
        &diag_ticks,
    );

    // ── Final NaN/Inf guard (release builds) ──────────────────────────────────
    assert_finite(&learn.final_weights, "learn.final_weights");
    assert_finite(&frozen.final_weights, "frozen.final_weights");

    // ── CSV output to stdout ──────────────────────────────────────────────────
    println!("tick,sakib_learning,sakib_frozen,culture");
    for t in 0..(N_TICKS as usize) {
        println!(
            "{t},{:.6},{:.6},{culture}",
            learn.sakib_curve[t], frozen.sakib_curve[t]
        );
    }
}
