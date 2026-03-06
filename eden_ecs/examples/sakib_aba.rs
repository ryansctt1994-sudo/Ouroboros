//! A→B→A engram persistence test.
//!
//! Tests whether a trained Weaver network can **recover** a previously learned
//! routing pattern faster than a freshly initialised network.  If it can, the
//! network has formed a persistent **engram** — the trace left by experience.
//!
//! # Protocol
//!
//! Three phases of equal length (`ticks_per_phase` ticks each):
//!
//! | Phase | Injection region | What we ask               |
//! |-------|-----------------|---------------------------|
//! | A     | nodes [0, N/3)  | baseline learning          |
//! | B     | nodes [N/3,2N/3)| interference / overwriting |
//! | A′    | nodes [0, N/3)  | recovery                  |
//!
//! Two networks run in parallel:
//! - **continuing**: weights evolve through all three phases (the engram network).
//! - **fresh**: reset to initial weights at the start of A′ (the null baseline).
//!
//! If the engram is real, the *continuing* network should reach the same
//! Sakib level as the *fresh* network at the end of A in fewer ticks during A′.
//!
//! # Output
//!
//! CSV to **stdout**:
//! ```text
//! phase,tick,sakib_continuing,sakib_fresh,culture
//! ```
//!
//! Diagnostics (entropy, weight percentiles, recovery ticks) go to **stderr**.
//!
//! # Usage
//!
//! ```sh
//! cargo run -p eden_ecs --example sakib_aba --release -- [culture] [ticks_per_phase] [flow_gain]
//! ```
//!
//! Defaults: `culture=engramum_competitive  ticks_per_phase=600  flow_gain=2.0`

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

// ── Flow computation (region-specific injection) ──────────────────────────────

/// Compute flows with injection restricted to `inject_range = (lo, hi)` nodes.
///
/// The injected node is chosen deterministically from `tick` and `seed`,
/// but only within the range `[lo, hi)`.  This creates phase-specific
/// activation patterns so that different graph regions specialise.
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

    graph
        .edges
        .iter()
        .map(|&(src, _)| (act[src] * flow_gain).clamp(0.0, 1.0))
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

// ── Phase runner ──────────────────────────────────────────────────────────────

/// Run a single phase, updating `weights` in-place if `learning=true`.
///
/// Returns the per-tick Sakib curve for the phase.
fn run_phase(
    graph: &Graph,
    weights: &mut Vec<f32>,
    sandbox: &mut WeaverSandbox,
    learning: bool,
    record_telemetry: bool,
    n_ticks: u32,
    flow_threshold: f32,
    seed: u32,
    steps: usize,
    flow_gain: f32,
    inject_lo: usize,
    inject_hi: usize,
) -> Vec<f32> {
    let mut curve = Vec::with_capacity(n_ticks as usize);
    for tick in 0..n_ticks {
        let flows = compute_flows(
            graph,
            weights,
            tick,
            seed,
            steps,
            flow_gain,
            inject_lo,
            inject_hi,
        );

        let s = sakib_index(weights, &flows, flow_threshold);
        curve.push(s);

        if record_telemetry {
            record_sakib_index(s);
            record_flow_entropy(flow_entropy(&flows));
        }

        if learning {
            let mut ctx = PolicyContext {
                edge_weights: weights,
                flow_rates: &flows,
            };
            sandbox.execute(&mut ctx);
        }
    }
    curve
}

// ── Main ──────────────────────────────────────────────────────────────────────

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let culture = args.get(1).map(String::as_str).unwrap_or("engramum_competitive");
    let ticks_per_phase: u32 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(600);
    let flow_gain: f32 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(2.0);

    eprintln!(
        "sakib_aba: culture={culture}  ticks_per_phase={ticks_per_phase}  flow_gain={flow_gain:.2}"
    );

    const N_NODES: usize = 10_000;
    const OUT_DEGREE: usize = 5;
    const FLOW_THRESHOLD: f32 = 0.3;
    const STEPS: usize = 6;
    const SEED: u32 = 12_345;

    // Injection regions for phases A and B.
    let region_a = (0, N_NODES / 3);
    let region_b = (N_NODES / 3, 2 * N_NODES / 3);

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

    // ── Continuing network (lives through A → B → A′) ────────────────────────
    let mut weights_cont = initial_weights.clone();
    let mut sandbox_cont = WeaverSandbox::new(culture_policy(
        culture,
        FLOW_THRESHOLD,
        weights_cont.len(),
    ));

    eprintln!("--- Phase A (continuing) ---");
    let curve_a_cont = run_phase(
        &graph,
        &mut weights_cont,
        &mut sandbox_cont,
        true,
        true, // record telemetry for continuing run only
        ticks_per_phase,
        FLOW_THRESHOLD,
        SEED,
        STEPS,
        flow_gain,
        region_a.0,
        region_a.1,
    );
    let sakib_end_a = *curve_a_cont.last().unwrap_or(&0.0);
    let (wp50, wp90, wp99) = percentiles(&weights_cont);
    eprintln!(
        "[continuing:A] Sakib_final={sakib_end_a:.4}  weights p50={wp50:.3} p90={wp90:.3} p99={wp99:.3}"
    );

    eprintln!("--- Phase B (continuing) ---");
    let curve_b_cont = run_phase(
        &graph,
        &mut weights_cont,
        &mut sandbox_cont,
        true,
        false, // don't mix B telemetry into learning series
        ticks_per_phase,
        FLOW_THRESHOLD,
        SEED ^ 0xBBBB_0000, // different seed for B injection
        STEPS,
        flow_gain,
        region_b.0,
        region_b.1,
    );
    let sakib_end_b = *curve_b_cont.last().unwrap_or(&0.0);
    let (wp50, wp90, wp99) = percentiles(&weights_cont);
    eprintln!(
        "[continuing:B] Sakib_final={sakib_end_b:.4}  weights p50={wp50:.3} p90={wp90:.3} p99={wp99:.3}"
    );

    eprintln!("--- Phase A′ (continuing) ---");
    let curve_a2_cont = run_phase(
        &graph,
        &mut weights_cont,
        &mut sandbox_cont,
        true,
        true,
        ticks_per_phase,
        FLOW_THRESHOLD,
        SEED,
        STEPS,
        flow_gain,
        region_a.0,
        region_a.1,
    );
    let sakib_end_a2_cont = *curve_a2_cont.last().unwrap_or(&0.0);
    let (wp50, wp90, wp99) = percentiles(&weights_cont);
    eprintln!(
        "[continuing:A′] Sakib_final={sakib_end_a2_cont:.4}  weights p50={wp50:.3} p90={wp90:.3} p99={wp99:.3}"
    );

    // ── Fresh network (reset to initial_weights at start of A′) ──────────────
    let mut weights_fresh = initial_weights.clone();
    let mut sandbox_fresh = WeaverSandbox::new(culture_policy(
        culture,
        FLOW_THRESHOLD,
        weights_fresh.len(),
    ));

    eprintln!("--- Phase A′ (fresh — starts from scratch) ---");
    let curve_a2_fresh = run_phase(
        &graph,
        &mut weights_fresh,
        &mut sandbox_fresh,
        true,
        false,
        ticks_per_phase,
        FLOW_THRESHOLD,
        SEED,
        STEPS,
        flow_gain,
        region_a.0,
        region_a.1,
    );
    let sakib_end_a2_fresh = *curve_a2_fresh.last().unwrap_or(&0.0);
    let (wp50, wp90, wp99) = percentiles(&weights_fresh);
    eprintln!(
        "[fresh:A′] Sakib_final={sakib_end_a2_fresh:.4}  weights p50={wp50:.3} p90={wp90:.3} p99={wp99:.3}"
    );

    assert_finite(&weights_cont, "weights_cont");
    assert_finite(&weights_fresh, "weights_fresh");

    // ── Recovery analysis ─────────────────────────────────────────────────────
    // How many A′ ticks for the continuing network to first match or exceed
    // the final Sakib level of Phase A?
    let target = sakib_end_a;
    let cont_recovery_tick = curve_a2_cont
        .iter()
        .position(|&s| s >= target)
        .map(|t| t as i64)
        .unwrap_or(-1);
    let fresh_recovery_tick = curve_a2_fresh
        .iter()
        .position(|&s| s >= target)
        .map(|t| t as i64)
        .unwrap_or(-1);

    eprintln!("--- Recovery analysis ---");
    eprintln!("Target Sakib (end of Phase A): {target:.4}");
    match (cont_recovery_tick, fresh_recovery_tick) {
        (-1, -1) => eprintln!("Neither network recovered to target within Phase A′."),
        (-1, t) => eprintln!(
            "Fresh recovered at tick {t}; continuing never recovered → no engram signal."
        ),
        (c, -1) => eprintln!(
            "Continuing recovered at tick {c}; fresh never recovered → strong engram signal!"
        ),
        (c, f) if c < f => eprintln!(
            "Continuing recovered {f_minus_c} ticks faster (continuing={c}, fresh={f}) → engram signal.",
            f_minus_c = f - c
        ),
        (c, f) if c > f => eprintln!(
            "Fresh recovered faster (fresh={f}, continuing={c}) → no engram advantage."
        ),
        (c, _) => eprintln!("Both recovered at same tick ({c}) → inconclusive."),
    }

    // ── CSV output ────────────────────────────────────────────────────────────
    println!("phase,tick,sakib_continuing,sakib_fresh,culture");
    for (t, (&sc, &sf)) in curve_a_cont
        .iter()
        .zip(std::iter::repeat(&f32::NAN))
        .enumerate()
    {
        println!("A,{t},{sc:.6},{:.6},{culture}", sf);
    }
    for (t, &sc) in curve_b_cont.iter().enumerate() {
        println!("B,{t},{sc:.6},NaN,{culture}");
    }
    for (t, (&sc, &sf)) in curve_a2_cont.iter().zip(curve_a2_fresh.iter()).enumerate() {
        println!("A2,{t},{sc:.6},{sf:.6},{culture}");
    }
}
