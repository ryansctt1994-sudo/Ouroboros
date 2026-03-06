//! A→B→A engram persistence test.
//!
//! Tests whether a Weaver network can **recover** a previously learned routing
//! pattern faster after interference than a freshly initialised network.  If
//! it can, the network has formed a **persistent engram**.
//!
//! # Protocol
//!
//! Three phases, each `n_ticks` ticks long:
//!
//! | Phase | Injection nodes | Question                          |
//! |-------|-----------------|-----------------------------------|
//! | A     | 0..8            | Build a routing pattern           |
//! | B     | 32..40          | Interfere / overwrite with new pattern |
//! | A₂    | 0..8            | Can the original pattern recover? |
//!
//! All cultures are run in a single invocation and compared side-by-side.
//! For each culture, the **continuing** network evolves through all three
//! phases; recovery speed in A₂ is the primary metric.
//!
//! # Recovery metric
//!
//! `recovery_ticks` = first tick in A₂ where Sakib ≥ 90% of peak Sakib
//! observed during phase A.  Printed as `recovery=never` when not reached.
//!
//! # Output
//!
//! CSV to **stdout**:
//! ```text
//! tick,phase,culture,sakib,entropy
//! ```
//!
//! `tick` is the global simulation tick (A: 0..n_ticks, B: n_ticks..2n_ticks,
//! A₂: 2n_ticks..3n_ticks).
//!
//! Diagnostics and recovery summary go to **stderr**.
//!
//! # Usage
//!
//! ```sh
//! cargo run -p eden_ecs --example sakib_aba --release -- [n_ticks] [flow_gain]
//! ```
//!
//! Defaults: `n_ticks=2000  flow_gain=2.0`

use eden_ecs::tracy::{flow_entropy, record_flow_entropy, record_sakib_index, sakib_index};
use eden_ecs::weaver::{culture_policy, PolicyContext, WeaverSandbox};

// ── LCG ──────────────────────────────────────────────────────────────────────

struct Lcg(u32);

impl Lcg {
    #[inline]
    fn next(&mut self) -> u32 {
        self.0 = self.0.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
        self.0
    }
    #[inline]
    fn next_f32(&mut self) -> f32 {
        (self.next() >> 8) as f32 / (1u32 << 24) as f32
    }
    #[inline]
    fn next_range(&mut self, lo: usize, hi: usize) -> usize {
        lo + (self.next() as usize) % (hi - lo)
    }
}

// ── Graph ─────────────────────────────────────────────────────────────────────

struct Graph {
    n_nodes: usize,
    edges: Vec<(usize, usize)>,
}

impl Graph {
    fn build_random(n_nodes: usize, out_degree: usize, seed: u32) -> Self {
        assert!(out_degree < n_nodes);
        let mut lcg = Lcg(seed ^ 0xA5A5_1234);
        let mut edges = Vec::with_capacity(n_nodes * out_degree);
        for src in 0..n_nodes {
            let mut chosen: Vec<usize> = Vec::with_capacity(out_degree);
            let mut guard = 0u32;
            while chosen.len() < out_degree {
                let dst = lcg.next_range(0, n_nodes);
                if dst != src && !chosen.contains(&dst) {
                    chosen.push(dst);
                }
                guard += 1;
                if guard > 100_000 {
                    break;
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

/// Compute flows with injection restricted to nodes `[inject_lo, inject_hi)`.
fn compute_flows(
    graph: &Graph,
    edge_weights: &[f32],
    tick: u32,
    seed: u32,
    steps: usize,
    flow_gain: f32,
    inject_lo: usize,
    inject_hi: usize,
) -> Vec<f32> {
    let n = graph.n_nodes;
    let mut lcg = Lcg(seed ^ tick.wrapping_mul(0x9E37_79B9));
    let inject = inject_lo + (lcg.next() as usize) % (inject_hi - inject_lo);

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

    // Flow = (act[src] / max_act) * flow_gain, clamped [0,1].
    // Max-normalization keeps threshold=0.3 meaningful as "top 30% of activation".
    let max_act: f32 = act.iter().cloned().fold(0.0_f32, f32::max).max(1e-9);
    graph
        .edges
        .iter()
        .map(|&(src, _)| (act[src] / max_act * flow_gain).clamp(0.0, 1.0))
        .collect()
}

// ── Diagnostics ───────────────────────────────────────────────────────────────

fn assert_finite(slice: &[f32], label: &str) {
    for (i, &v) in slice.iter().enumerate() {
        if !v.is_finite() {
            eprintln!("FATAL: {label}[{i}] = {v} (non-finite). Aborting.");
            std::process::exit(1);
        }
    }
}

fn percentiles(values: &[f32]) -> (f32, f32, f32) {
    let n = values.len();
    if n == 0 {
        return (0.0, 0.0, 0.0);
    }
    let mut sorted = values.to_vec();
    sorted.sort_unstable_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    (sorted[n / 2], sorted[(n * 9) / 10], sorted[(n * 99) / 100])
}

// ── Per-culture experiment ────────────────────────────────────────────────────

/// Holds per-tick (sakib, entropy) for one phase.
struct PhaseCurve {
    sakib: Vec<f32>,
    entropy: Vec<f32>,
}

/// Run one phase, returning per-tick (sakib, entropy).
/// Weights are updated in-place when `learning=true`.
fn run_phase(
    graph: &Graph,
    weights: &mut Vec<f32>,
    sandbox: &mut WeaverSandbox,
    learning: bool,
    emit_telemetry: bool,
    n_ticks: u32,
    flow_threshold: f32,
    seed: u32,
    steps: usize,
    flow_gain: f32,
    inject_lo: usize,
    inject_hi: usize,
) -> PhaseCurve {
    let mut sakib_vec = Vec::with_capacity(n_ticks as usize);
    let mut entropy_vec = Vec::with_capacity(n_ticks as usize);

    for tick in 0..n_ticks {
        let flows = compute_flows(
            graph, weights, tick, seed, steps, flow_gain, inject_lo, inject_hi,
        );

        let s = sakib_index(weights, &flows, flow_threshold);
        let h = flow_entropy(&flows);
        sakib_vec.push(s);
        entropy_vec.push(h);

        if emit_telemetry {
            record_sakib_index(s);
            record_flow_entropy(h);
        }

        if learning {
            let mut ctx = PolicyContext {
                edge_weights: weights,
                flow_rates: &flows,
            };
            sandbox.execute(&mut ctx);
        }
    }

    PhaseCurve {
        sakib: sakib_vec,
        entropy: entropy_vec,
    }
}

/// Run the full A→B→A protocol for one culture.
///
/// Returns `(curve_a, curve_b, curve_a2, recovery_ticks)` where
/// `recovery_ticks` is the first tick in A₂ where Sakib ≥ 90% of peak in A
/// (or `None` if never reached).
fn run_culture(
    graph: &Graph,
    initial_weights: &[f32],
    culture: &str,
    n_ticks: u32,
    flow_threshold: f32,
    steps: usize,
    flow_gain: f32,
    inject_a: (usize, usize),
    inject_b: (usize, usize),
) -> (PhaseCurve, PhaseCurve, PhaseCurve, Option<u32>) {
    const SEED: u32 = 12_345;
    const SEED_B: u32 = 12_345 ^ 0xBBBB_0000;

    let mut weights = initial_weights.to_vec();
    let mut sandbox =
        WeaverSandbox::new(culture_policy(culture, flow_threshold, weights.len()));

    // Phase A.
    eprintln!("[{culture}] Phase A …");
    let curve_a = run_phase(
        graph,
        &mut weights,
        &mut sandbox,
        true,
        true, // emit telemetry only for phase A learning
        n_ticks,
        flow_threshold,
        SEED,
        steps,
        flow_gain,
        inject_a.0,
        inject_a.1,
    );

    let peak_a = curve_a
        .sakib
        .iter()
        .cloned()
        .fold(f32::NEG_INFINITY, f32::max);
    let target_recovery = 0.9 * peak_a;
    let (wp50, wp90, wp99) = percentiles(&weights);
    eprintln!(
        "[{culture}] A done  peak_sakib={peak_a:.4}  target_90%={target_recovery:.4} \
         weights p50={wp50:.3} p90={wp90:.3} p99={wp99:.3}"
    );

    // Phase B (interference).
    eprintln!("[{culture}] Phase B …");
    let curve_b = run_phase(
        graph,
        &mut weights,
        &mut sandbox,
        true,
        false,
        n_ticks,
        flow_threshold,
        SEED_B,
        steps,
        flow_gain,
        inject_b.0,
        inject_b.1,
    );
    let (wp50, wp90, wp99) = percentiles(&weights);
    eprintln!(
        "[{culture}] B done  weights p50={wp50:.3} p90={wp90:.3} p99={wp99:.3}"
    );

    // Phase A₂ (recovery).
    eprintln!("[{culture}] Phase A₂ …");
    let curve_a2 = run_phase(
        graph,
        &mut weights,
        &mut sandbox,
        true,
        false,
        n_ticks,
        flow_threshold,
        SEED,
        steps,
        flow_gain,
        inject_a.0,
        inject_a.1,
    );
    let (wp50, wp90, wp99) = percentiles(&weights);
    let sakib_a2_final = curve_a2.sakib.last().cloned().unwrap_or(0.0);
    eprintln!(
        "[{culture}] A₂ done  sakib_final={sakib_a2_final:.4} \
         weights p50={wp50:.3} p90={wp90:.3} p99={wp99:.3}"
    );

    assert_finite(&weights, &format!("{culture}.weights"));

    // Recovery metric.
    let recovery = curve_a2
        .sakib
        .iter()
        .position(|&s| s >= target_recovery)
        .map(|t| t as u32);

    (curve_a, curve_b, curve_a2, recovery)
}

// ── Main ──────────────────────────────────────────────────────────────────────

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let n_ticks: u32 = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(2_000);
    let flow_gain: f32 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(2.0);

    eprintln!(
        "sakib_aba: n_ticks={n_ticks} (per phase)  flow_gain={flow_gain:.2}"
    );

    const N_NODES: usize = 10_000;
    const OUT_DEGREE: usize = 5;
    const FLOW_THRESHOLD: f32 = 0.3;
    const STEPS: usize = 6;
    const SEED: u32 = 12_345;

    // Injection node groups (spec-mandated small regions to force specialisation).
    let inject_a = (0_usize, 8_usize);   // nodes 0..8
    let inject_b = (32_usize, 40_usize); // nodes 32..40

    let graph = Graph::build_random(N_NODES, OUT_DEGREE, SEED);
    eprintln!(
        "graph: {N_NODES} nodes × {OUT_DEGREE} out-degree = {} edges",
        graph.n_edges()
    );

    // Initial weights: LCG in [0.2, 0.8].
    let mut lcg = Lcg(SEED ^ 0xC0FF_EE00);
    let initial_weights: Vec<f32> = (0..graph.n_edges())
        .map(|_| 0.2 + lcg.next_f32() * 0.6)
        .collect();

    // All four cultures — ranked by expected engram strength.
    let cultures = [
        "baseline",
        "hebbium",
        "engramum",
        "engramum_competitive",
    ];

    // CSV header.
    println!("tick,phase,culture,sakib,entropy");

    // Recovery summary accumulator (printed at end to stderr).
    let mut recovery_summary: Vec<(String, Option<u32>)> = Vec::new();

    for culture in cultures {
        eprintln!("\n=== {culture} ===");
        let (curve_a, curve_b, curve_a2, recovery) = run_culture(
            &graph,
            &initial_weights,
            culture,
            n_ticks,
            FLOW_THRESHOLD,
            STEPS,
            flow_gain,
            inject_a,
            inject_b,
        );

        // Emit CSV rows — global tick counter.
        for (i, (&s, &h)) in curve_a.sakib.iter().zip(&curve_a.entropy).enumerate() {
            println!("{},{},{},{:.6},{:.4}", i, "A", culture, s, h);
        }
        let b_offset = n_ticks as usize;
        for (i, (&s, &h)) in curve_b.sakib.iter().zip(&curve_b.entropy).enumerate() {
            println!("{},{},{},{:.6},{:.4}", b_offset + i, "B", culture, s, h);
        }
        let a2_offset = 2 * n_ticks as usize;
        // CSV uses "A2" (ASCII-safe phase token); docs use the subscript "A₂".
        for (i, (&s, &h)) in curve_a2.sakib.iter().zip(&curve_a2.entropy).enumerate() {
            println!("{},{},{},{:.6},{:.4}", a2_offset + i, "A2", culture, s, h);
        }

        recovery_summary.push((culture.to_string(), recovery));
    }

    // ── Recovery summary (stderr) ─────────────────────────────────────────────
    eprintln!("\n=== Recovery summary (ticks in A₂ to reach 90% of peak-A Sakib) ===");
    for (culture, ticks) in &recovery_summary {
        match ticks {
            Some(t) => eprintln!("culture={culture} recovery={t}"),
            None => eprintln!("culture={culture} recovery=never"),
        }
    }

    // Print expected ordering hint.
    eprintln!(
        "\nExpected ordering (fastest recovery): \
         engramum_competitive > engramum > hebbium > baseline"
    );
}
