//! Weaver policy sandbox — biologically-inspired adaptive routing for EDEN-ECS.
//!
//! # Overview
//!
//! The Weaver provides a **hot-swappable policy interface** that governs how
//! the mycelial ECS routes nutrients / signals between entities.  Policies are
//! modelled on real-world fungal network behaviour:
//!
//! | Policy                    | Biological analogue                          |
//! |---------------------------|----------------------------------------------|
//! | [`SelectiveReinforcement`] | Physarum polycephalum thickening high-flow   |
//! |                            | veins (Tero et al. 2010)                     |
//! | [`RedundancyDecay`]        | Hyphal pruning of rarely-used pathways        |
//! | [`FlowNormalisation`]      | Network-wide homeostasis / Fick diffusion    |
//! | [`ComposePolicy`]          | Sequential policy composition (chain of      |
//! |                            | responsibility)                              |
//!
//! # Architecture
//!
//! ```text
//!              ┌─────────────────────────────────────────┐
//!              │            WeaverSandbox                │
//!              │                                         │
//!  frame tick ─►  execute(edge_weights, flow_rates)      │
//!              │         │                               │
//!              │         ▼                               │
//!              │   active_policy.apply(ctx)              │
//!              │     ├── SelectiveReinforcement          │
//!              │     ├── RedundancyDecay                 │
//!              │     └── ComposePolicy(p1, p2, …)        │
//!              └─────────────────────────────────────────┘
//! ```
//!
//! ## WASM extension point
//!
//! When compiled with `--features wasmtime-weaver` (not yet stabilised — see
//! roadmap), an external `.wasm` module can be loaded at runtime and wrapped
//! as a `Box<dyn WeaverPolicy>` so that researchers can inject custom fungal
//! routing models without recompiling the Rust core.
//!
//! # Performance target
//!
//! Policy execution over a typical mycelial graph (≤ 20 M edges) must
//! complete in **≤ 1.2 ms** at 60 Hz.
//!
//! # Example
//!
//! ```
//! use eden_ecs::weaver::{
//!     WeaverSandbox, PolicyContext,
//!     SelectiveReinforcement, RedundancyDecay, ComposePolicy,
//! };
//!
//! let mut sandbox = WeaverSandbox::new(
//!     Box::new(ComposePolicy::new(vec![
//!         Box::new(SelectiveReinforcement { alpha: 0.1, threshold: 0.6 }),
//!         Box::new(RedundancyDecay { decay_rate: 0.05, min_weight: 0.01 }),
//!     ]))
//! );
//!
//! let mut weights = vec![0.4_f32, 0.8, 0.2, 0.9];
//! let flow_rates  = vec![0.3_f32, 0.9, 0.1, 0.85];
//! let mut ctx = PolicyContext { edge_weights: &mut weights, flow_rates: &flow_rates };
//! sandbox.execute(&mut ctx);
//! ```

// ── Policy context ────────────────────────────────────────────────────────────

/// Mutable context passed to every policy during a Weaver tick.
///
/// `edge_weights[i]` is the current conductance of edge `i` in the mycelial
/// graph.  `flow_rates[i]` is the instantaneous flow magnitude through that
/// edge (read-only).  Both slices are the same length.
pub struct PolicyContext<'a> {
    /// Mutable edge conductance / routing weight (0.0 = blocked, 1.0 = max).
    pub edge_weights: &'a mut Vec<f32>,
    /// Instantaneous flow rate through each edge (read-only).
    pub flow_rates: &'a [f32],
}

// ── WeaverPolicy trait ────────────────────────────────────────────────────────

/// A stateless or stateful policy that modifies `edge_weights` in-place.
///
/// Implementors must be `Send + Sync` so that the sandbox can be used from
/// worker threads.
pub trait WeaverPolicy: Send + Sync {
    /// Apply the policy for one simulation tick.
    fn apply(&mut self, ctx: &mut PolicyContext<'_>);

    /// Human-readable policy identifier (used in telemetry / Tracy zones).
    fn name(&self) -> &'static str;
}

// ── Built-in fungal policies ──────────────────────────────────────────────────

/// **Selective Reinforcement** — increase the conductance of high-flow edges.
///
/// Inspired by *Physarum polycephalum* tube-diameter adaptation:
/// edges whose flow rate exceeds `threshold` are reinforced by `alpha` per
/// tick.  Conductances are clamped to \[0, 1\].
///
/// Δw(i) = +α  if flow_rate(i) > threshold
///         else 0
pub struct SelectiveReinforcement {
    /// Reinforcement increment per tick (e.g. 0.05).
    pub alpha: f32,
    /// Flow rate above which an edge is reinforced (0.0 – 1.0).
    pub threshold: f32,
}

impl WeaverPolicy for SelectiveReinforcement {
    fn apply(&mut self, ctx: &mut PolicyContext<'_>) {
        let w = &mut *ctx.edge_weights;
        let f = ctx.flow_rates;
        let len = w.len().min(f.len());
        for i in 0..len {
            if f[i] > self.threshold {
                w[i] = (w[i] + self.alpha).min(1.0);
            }
        }
    }

    fn name(&self) -> &'static str {
        "SelectiveReinforcement"
    }
}

/// **Redundancy Decay** — reduce the conductance of low-flow (redundant) edges.
///
/// Edges with flow below `min_weight` are considered redundant and their
/// conductance decays towards zero at rate `decay_rate`.  This mimics hyphal
/// autolysis in nutrient-depleted regions.
///
/// w'(i) = max(min_weight, w(i) × (1 − decay_rate))  if flow_rate(i) < min_weight
pub struct RedundancyDecay {
    /// Proportional decay coefficient per tick (e.g. 0.02).
    pub decay_rate: f32,
    /// Minimum conductance floor — edges are never fully silenced.
    pub min_weight: f32,
}

impl WeaverPolicy for RedundancyDecay {
    fn apply(&mut self, ctx: &mut PolicyContext<'_>) {
        let w = &mut *ctx.edge_weights;
        let f = ctx.flow_rates;
        let len = w.len().min(f.len());
        for i in 0..len {
            if f[i] < self.min_weight {
                let decayed = w[i] * (1.0 - self.decay_rate);
                w[i] = decayed.max(self.min_weight);
            }
        }
    }

    fn name(&self) -> &'static str {
        "RedundancyDecay"
    }
}

/// **Flow Normalisation** — rescale all edge weights so that the mean equals
/// `target_mean`.
///
/// Implements network-wide homeostasis: the total "nutrient budget" is
/// conserved across routing changes.  Applied after reinforcement / decay to
/// prevent runaway growth or collapse.
pub struct FlowNormalisation {
    /// Target mean conductance across all edges (e.g. 0.5).
    pub target_mean: f32,
}

impl WeaverPolicy for FlowNormalisation {
    fn apply(&mut self, ctx: &mut PolicyContext<'_>) {
        let w = &mut *ctx.edge_weights;
        if w.is_empty() {
            return;
        }
        let mean: f32 = w.iter().copied().sum::<f32>() / w.len() as f32;
        if mean == 0.0 {
            return;
        }
        let scale = self.target_mean / mean;
        for wi in w.iter_mut() {
            *wi = (*wi * scale).clamp(0.0, 1.0);
        }
    }

    fn name(&self) -> &'static str {
        "FlowNormalisation"
    }
}

/// **Compose** — run a list of policies sequentially, left to right.
pub struct ComposePolicy {
    policies: Vec<Box<dyn WeaverPolicy>>,
}

impl ComposePolicy {
    /// Create a composed policy from a `Vec` of boxed policies.
    pub fn new(policies: Vec<Box<dyn WeaverPolicy>>) -> Self {
        Self { policies }
    }
}

impl WeaverPolicy for ComposePolicy {
    fn apply(&mut self, ctx: &mut PolicyContext<'_>) {
        for p in &mut self.policies {
            p.apply(ctx);
        }
    }

    fn name(&self) -> &'static str {
        "ComposePolicy"
    }
}

// ── Hebbian / engram policies ─────────────────────────────────────────────────

/// **Hebbium** — Hebbian-style weight potentiation.
///
/// Each edge weight is nudged towards 1.0 in proportion to the current flow
/// rate, scaled by the learning rate `alpha`.  The multiplicative `(1-w)`
/// term keeps weights bounded without an explicit clamp:
///
/// `w[i] = clamp(w[i] + alpha * flow[i] * (1 - w[i]), 0, 1)`
pub struct Hebbium {
    /// Learning rate (e.g. 0.05 – 0.2).
    pub alpha: f32,
}

impl WeaverPolicy for Hebbium {
    fn apply(&mut self, ctx: &mut PolicyContext<'_>) {
        let w = &mut *ctx.edge_weights;
        let f = ctx.flow_rates;
        let len = w.len().min(f.len());
        for i in 0..len {
            w[i] = (w[i] + self.alpha * f[i] * (1.0 - w[i])).clamp(0.0, 1.0);
        }
    }

    fn name(&self) -> &'static str {
        "Hebbium"
    }
}

/// **Engramum** — EMA-traced Hebbian potentiation.
///
/// Maintains an exponential moving average (engram trace) of the flow signal
/// and uses it instead of the raw flow, making the update smoother and
/// history-dependent:
///
/// `trace[i] = beta * trace[i] + (1 - beta) * flow[i]`
/// `w[i]     = clamp(w[i] + alpha * trace[i] * (1 - w[i]), 0, 1)`
///
/// The trace is lazily grown to `min(|weights|, |flows|)` so mismatched
/// slices never cause a panic.  The trace is never shrunk so accumulated
/// history is preserved if the graph temporarily reports fewer edges.
pub struct Engramum {
    /// Hebbian learning rate (e.g. 0.05 – 0.2).
    pub alpha: f32,
    /// EMA decay factor (0 < beta < 1; higher = longer memory).
    pub beta: f32,
    /// Per-edge EMA trace (initialised to zeros; grown automatically).
    pub trace: Vec<f32>,
}

impl Engramum {
    /// Create a new `Engramum` policy with a pre-allocated trace of length
    /// `num_edges`.  Prefer this constructor over struct-literal syntax when
    /// the edge count is known up-front.
    pub fn new(alpha: f32, beta: f32, num_edges: usize) -> Self {
        Self {
            alpha,
            beta,
            trace: vec![0.0; num_edges],
        }
    }

    /// Grow the internal trace to at least `n` elements.
    ///
    /// Never shrinks — accumulated trace state is preserved even when the
    /// active slice length temporarily decreases.
    fn ensure_len(&mut self, n: usize) {
        if self.trace.len() < n {
            self.trace.resize(n, 0.0);
        }
    }
}

impl WeaverPolicy for Engramum {
    fn apply(&mut self, ctx: &mut PolicyContext<'_>) {
        let w = &mut *ctx.edge_weights;
        let f = ctx.flow_rates;
        let len = w.len().min(f.len());
        self.ensure_len(len);
        for i in 0..len {
            self.trace[i] = self.beta * self.trace[i] + (1.0 - self.beta) * f[i];
            w[i] = (w[i] + self.alpha * self.trace[i] * (1.0 - w[i])).clamp(0.0, 1.0);
        }
    }

    fn name(&self) -> &'static str {
        "Engramum"
    }
}

// ── Policy factories ──────────────────────────────────────────────────────────

/// **Engramum Competitive** — EMA-traced Hebbian potentiation with competitive
/// (L∞-normalised) traces.
///
/// After the EMA update the trace is normalised by its maximum value so that
/// traces represent *relative routing salience* — the most active edge always
/// receives the full `alpha` update; all others receive a proportionally
/// smaller update.  This **L∞ normalisation** is scale-invariant: it behaves
/// identically on graphs with 32 or 50 000 edges, unlike L1 normalisation
/// (divide by sum) which degrades to zero updates on large graphs.
///
/// The three update steps that change the phase diagram:
///
/// ```text
/// trace[i]  ← beta * trace[i] + (1 - beta) * flow[i]   // EMA accumulate
/// t[i]       = trace[i] / (max(trace) + ε)               // L∞ competition
/// w[i]      ← clamp(w[i] + alpha * t[i] * (1 - w[i]), 0, 1)
/// ```
///
/// Unlike plain [`Engramum`], the competition step produces winner-take-most
/// routing channels and prevents the amplifier regime even without an external
/// [`FlowNormalisation`] pass.
pub struct EngramumCompetitive {
    /// Hebbian learning rate (e.g. 0.05 – 0.2).
    pub alpha: f32,
    /// EMA decay factor (0 < beta < 1; higher = longer memory).
    pub beta: f32,
    /// Per-edge EMA trace (initialised to zeros; grown automatically).
    pub trace: Vec<f32>,
}

impl EngramumCompetitive {
    /// Create a new `EngramumCompetitive` with a pre-allocated trace.
    pub fn new(alpha: f32, beta: f32, num_edges: usize) -> Self {
        Self {
            alpha,
            beta,
            trace: vec![0.0; num_edges],
        }
    }

    /// Grow the internal trace to at least `n` elements.
    ///
    /// Never shrinks — accumulated trace state is preserved even when the
    /// active slice length temporarily decreases.
    fn ensure_len(&mut self, n: usize) {
        if self.trace.len() < n {
            self.trace.resize(n, 0.0);
        }
    }
}

impl WeaverPolicy for EngramumCompetitive {
    fn apply(&mut self, ctx: &mut PolicyContext<'_>) {
        let w = &mut *ctx.edge_weights;
        let f = ctx.flow_rates;
        let len = w.len().min(f.len());
        self.ensure_len(len);

        // Step 1 — EMA trace update.
        for i in 0..len {
            self.trace[i] = self.beta * self.trace[i] + (1.0 - self.beta) * f[i];
        }

        // Step 2 — L∞-normalise (competition): relative salience, scale-invariant.
        // Step 3 — Hebbian weight update using the competitive trace.
        let max_trace: f32 = self.trace[..len].iter().cloned().fold(0.0_f32, f32::max) + 1e-8;
        for i in 0..len {
            let t = self.trace[i] / max_trace;
            w[i] = (w[i] + self.alpha * t * (1.0 - w[i])).clamp(0.0, 1.0);
        }
    }

    fn name(&self) -> &'static str {
        "EngramumCompetitive"
    }
}

/// Build the **Sakibium** composed policy used for baseline A/B experiments.
///
/// The returned policy applies `SelectiveReinforcement`, `RedundancyDecay`,
/// and `FlowNormalisation` in sequence — matching the classic sakib-index
/// optimisation strategy.
///
/// # Parameters
/// * `flow_threshold` — reinforcement threshold forwarded to
///   [`SelectiveReinforcement`] and used as `min_weight` for [`RedundancyDecay`].
pub fn sakibium_policy(flow_threshold: f32) -> Box<dyn WeaverPolicy> {
    Box::new(ComposePolicy::new(vec![
        Box::new(SelectiveReinforcement {
            alpha: 0.05,
            threshold: flow_threshold,
        }),
        Box::new(RedundancyDecay {
            decay_rate: 0.02,
            min_weight: flow_threshold,
        }),
        Box::new(FlowNormalisation { target_mean: 0.5 }),
    ]))
}

/// Build a culture-specific composed policy for A/B experiments.
///
/// | `culture`                 | Policy composition                                              |
/// |---------------------------|-----------------------------------------------------------------|
/// | `"baseline"`              | [`sakibium_policy`]                                             |
/// | `"hebbium"`               | [`Hebbium`] → [`RedundancyDecay`] → [`FlowNormalisation`]       |
/// | `"engramum"`              | [`Engramum`] → [`RedundancyDecay`] → [`FlowNormalisation`]      |
/// | `"engramum_competitive"`  | [`EngramumCompetitive`] (competition replaces FlowNormalisation)|
///
/// All non-baseline cultures include `RedundancyDecay` to prevent unbounded
/// potentiation (amplifier regime).  Unrecognised culture strings fall back
/// to `"baseline"`.
///
/// # Parameters
/// * `culture`        — one of `"baseline"`, `"hebbium"`, `"engramum"`,
///                      `"engramum_competitive"`.
/// * `flow_threshold` — forwarded to the baseline policy if applicable.
/// * `num_edges`      — initial trace capacity for engram policies.
pub fn culture_policy(
    culture: &str,
    flow_threshold: f32,
    num_edges: usize,
) -> Box<dyn WeaverPolicy> {
    match culture {
        "hebbium" => Box::new(ComposePolicy::new(vec![
            Box::new(Hebbium { alpha: 0.1 }),
            Box::new(RedundancyDecay {
                decay_rate: 0.01,
                min_weight: 0.01,
            }),
            Box::new(FlowNormalisation { target_mean: 0.5 }),
        ])),
        "engramum" => Box::new(ComposePolicy::new(vec![
            Box::new(Engramum::new(0.1, 0.9, num_edges)),
            Box::new(RedundancyDecay {
                decay_rate: 0.01,
                min_weight: 0.01,
            }),
            Box::new(FlowNormalisation { target_mean: 0.5 }),
        ])),
        "engramum_competitive" => Box::new(ComposePolicy::new(vec![
            Box::new(EngramumCompetitive::new(0.1, 0.9, num_edges)),
            Box::new(RedundancyDecay {
                decay_rate: 0.01,
                min_weight: 0.01,
            }),
        ])),
        _ => sakibium_policy(flow_threshold),
    }
}

// ── WeaverSandbox ─────────────────────────────────────────────────────────────

/// Executes a [`WeaverPolicy`] each simulation tick.
///
/// The sandbox owns the active policy and records cumulative execution
/// statistics for the Tracy telemetry overlay.
pub struct WeaverSandbox {
    policy: Box<dyn WeaverPolicy>,
    /// Total number of ticks executed.
    tick_count: u64,
    /// Cumulative policy execution time in nanoseconds (monotonic).
    total_ns: u64,
}

impl WeaverSandbox {
    /// Create a new sandbox with the given initial policy.
    pub fn new(policy: Box<dyn WeaverPolicy>) -> Self {
        Self {
            policy,
            tick_count: 0,
            total_ns: 0,
        }
    }

    /// Hot-swap the active policy.  Safe to call between ticks.
    pub fn set_policy(&mut self, policy: Box<dyn WeaverPolicy>) {
        self.policy = policy;
    }

    /// Execute one policy tick.
    ///
    /// Records wall-clock time for the Tracy `"WeaverPolicy"` zone.
    pub fn execute(&mut self, ctx: &mut PolicyContext<'_>) {
        let t0 = monotonic_ns();
        self.policy.apply(ctx);
        let elapsed = monotonic_ns().saturating_sub(t0);
        self.tick_count += 1;
        self.total_ns = self.total_ns.saturating_add(elapsed);
        crate::tracy::frame_mark();
    }

    /// Mean policy execution time in nanoseconds over all ticks.
    pub fn mean_ns(&self) -> u64 {
        if self.tick_count == 0 {
            0
        } else {
            self.total_ns / self.tick_count
        }
    }

    /// Total ticks executed.
    pub fn tick_count(&self) -> u64 {
        self.tick_count
    }

    /// Name of the currently active policy.
    pub fn policy_name(&self) -> &'static str {
        self.policy.name()
    }
}

/// Portable monotonic clock in nanoseconds.  Uses `std::time::Instant`.
#[inline(always)]
fn monotonic_ns() -> u64 {
    use std::time::Instant;
    // Lazily initialise the epoch via a thread-local.  This avoids a syscall
    // to get absolute time; only the delta matters.
    thread_local! {
        static EPOCH: Instant = Instant::now();
    }
    EPOCH.with(|e| e.elapsed().as_nanos() as u64)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    fn make_ctx<'a>(w: &'a mut Vec<f32>, f: &'a [f32]) -> PolicyContext<'a> {
        PolicyContext {
            edge_weights: w,
            flow_rates: f,
        }
    }

    // ── SelectiveReinforcement ────────────────────────────────────────────────

    #[test]
    fn test_reinforcement_increases_high_flow_edges() {
        let mut w = vec![0.5_f32, 0.5, 0.5];
        let f = [0.9_f32, 0.1, 0.8]; // edges 0 and 2 exceed 0.6
        let mut policy = SelectiveReinforcement {
            alpha: 0.1,
            threshold: 0.6,
        };
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx);
        assert!((w[0] - 0.6).abs() < 1e-6, "edge 0 should be reinforced");
        assert!((w[1] - 0.5).abs() < 1e-6, "edge 1 should be unchanged");
        assert!((w[2] - 0.6).abs() < 1e-6, "edge 2 should be reinforced");
    }

    #[test]
    fn test_reinforcement_clamped_at_one() {
        let mut w = vec![0.95_f32];
        let f = [1.0_f32];
        let mut policy = SelectiveReinforcement {
            alpha: 0.2,
            threshold: 0.5,
        };
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx);
        assert!((w[0] - 1.0).abs() < 1e-6, "should be clamped to 1.0");
    }

    // ── RedundancyDecay ───────────────────────────────────────────────────────

    #[test]
    fn test_decay_reduces_low_flow_edges() {
        let mut w = vec![0.5_f32, 0.5];
        let f = [0.001_f32, 0.9]; // edge 0 below min_weight 0.01
        let mut policy = RedundancyDecay {
            decay_rate: 0.1,
            min_weight: 0.01,
        };
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx);
        // edge 0: decayed
        assert!(w[0] < 0.5, "edge 0 should decay");
        // edge 1: unchanged (flow >= min_weight)
        assert!((w[1] - 0.5).abs() < 1e-6, "edge 1 should be unchanged");
    }

    #[test]
    fn test_decay_floor_respected() {
        let mut w = vec![0.001_f32]; // already at floor
        let f = [0.0_f32];
        let mut policy = RedundancyDecay {
            decay_rate: 0.5,
            min_weight: 0.01,
        };
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx);
        assert!(
            w[0] >= 0.01 - 1e-6,
            "weight must not go below min_weight floor"
        );
    }

    // ── FlowNormalisation ─────────────────────────────────────────────────────

    #[test]
    fn test_normalisation_rescales_mean() {
        let mut w = vec![0.2_f32, 0.4, 0.6, 0.8];
        let f = vec![0.0_f32; 4];
        let mut policy = FlowNormalisation { target_mean: 0.5 };
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx);
        let mean = w.iter().sum::<f32>() / w.len() as f32;
        assert!(
            (mean - 0.5).abs() < 1e-5,
            "mean should be ≈ 0.5, got {mean}"
        );
    }

    #[test]
    fn test_normalisation_empty_noop() {
        let mut w: Vec<f32> = vec![];
        let f: Vec<f32> = vec![];
        let mut policy = FlowNormalisation { target_mean: 0.5 };
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx); // must not panic
    }

    // ── ComposePolicy ─────────────────────────────────────────────────────────

    #[test]
    fn test_compose_applies_in_order() {
        let mut w = vec![0.5_f32];
        let f = [1.0_f32];
        // First: reinforce (+0.1) → 0.6; Second: no decay (flow is not low)
        let mut policy = ComposePolicy::new(vec![
            Box::new(SelectiveReinforcement {
                alpha: 0.1,
                threshold: 0.5,
            }),
            Box::new(RedundancyDecay {
                decay_rate: 0.1,
                min_weight: 0.01,
            }),
        ]);
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx);
        assert!((w[0] - 0.6).abs() < 1e-6);
    }

    // ── WeaverSandbox ─────────────────────────────────────────────────────────

    #[test]
    fn test_sandbox_execute_runs_policy() {
        let mut sandbox = WeaverSandbox::new(Box::new(SelectiveReinforcement {
            alpha: 0.05,
            threshold: 0.5,
        }));
        let mut w = vec![0.5_f32, 0.5];
        let f = vec![1.0_f32, 0.0];
        let mut ctx = PolicyContext {
            edge_weights: &mut w,
            flow_rates: &f,
        };
        sandbox.execute(&mut ctx);
        assert_eq!(sandbox.tick_count(), 1);
        assert!(w[0] > 0.5, "edge 0 should be reinforced");
    }

    #[test]
    fn test_sandbox_hot_swap_policy() {
        let mut sandbox = WeaverSandbox::new(Box::new(SelectiveReinforcement {
            alpha: 0.1,
            threshold: 0.5,
        }));
        sandbox.set_policy(Box::new(RedundancyDecay {
            decay_rate: 0.1,
            min_weight: 0.01,
        }));
        assert_eq!(sandbox.policy_name(), "RedundancyDecay");
    }

    #[test]
    fn test_sandbox_mean_ns_zero_ticks() {
        let sandbox = WeaverSandbox::new(Box::new(SelectiveReinforcement {
            alpha: 0.1,
            threshold: 0.5,
        }));
        assert_eq!(sandbox.mean_ns(), 0);
    }

    // ── Hebbium ───────────────────────────────────────────────────────────────

    #[test]
    fn test_hebbium_increases_weight_with_flow() {
        let mut w = vec![0.5_f32];
        let f = [1.0_f32];
        let mut policy = Hebbium { alpha: 0.1 };
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx);
        // w[0] = 0.5 + 0.1 * 1.0 * (1.0 - 0.5) = 0.5 + 0.05 = 0.55
        assert!((w[0] - 0.55).abs() < 1e-6, "expected 0.55, got {}", w[0]);
    }

    #[test]
    fn test_hebbium_zero_flow_no_change() {
        let mut w = vec![0.4_f32];
        let f = [0.0_f32];
        let mut policy = Hebbium { alpha: 0.2 };
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx);
        assert!(
            (w[0] - 0.4).abs() < 1e-6,
            "zero flow should leave weight unchanged"
        );
    }

    #[test]
    fn test_hebbium_clamped_at_one() {
        let mut w = vec![0.99_f32];
        let f = [1.0_f32];
        let mut policy = Hebbium { alpha: 1.0 };
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx);
        assert!(w[0] <= 1.0, "weight must not exceed 1.0");
    }

    #[test]
    fn test_hebbium_mismatched_lengths() {
        let mut w = vec![0.5_f32, 0.5];
        let f = [0.8_f32]; // only 1 flow value
        let mut policy = Hebbium { alpha: 0.1 };
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx); // must not panic
        assert!(w[0] > 0.5, "first edge should be updated");
        assert!((w[1] - 0.5).abs() < 1e-6, "second edge should be untouched");
    }

    // ── Engramum ──────────────────────────────────────────────────────────────

    #[test]
    fn test_engramum_weight_increases_with_sustained_flow() {
        let mut w = vec![0.5_f32];
        let f = [1.0_f32];
        let mut policy = Engramum::new(0.1, 0.9, 1);
        let mut ctx = make_ctx(&mut w, &f);
        // Run for a few ticks so the trace accumulates.
        for _ in 0..10 {
            policy.apply(&mut ctx);
        }
        assert!(w[0] > 0.5, "weight should grow with sustained high flow");
    }

    #[test]
    fn test_engramum_trace_resizes() {
        // trace starts empty — must resize automatically without panicking.
        let mut w = vec![0.5_f32, 0.5];
        let f = [0.8_f32, 0.9];
        let mut policy = Engramum {
            alpha: 0.1,
            beta: 0.9,
            trace: vec![],
        };
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx); // must not panic
        assert_eq!(policy.trace.len(), 2);
    }

    #[test]
    fn test_engramum_zero_beta_equals_hebbium() {
        // With beta=0 the trace == current flow, so Engramum collapses to Hebbium.
        let mut w_e = vec![0.5_f32];
        let mut w_h = vec![0.5_f32];
        let f = [0.8_f32];
        let mut engramum = Engramum {
            alpha: 0.1,
            beta: 0.0,
            trace: vec![0.0],
        };
        let mut hebbium = Hebbium { alpha: 0.1 };
        engramum.apply(&mut make_ctx(&mut w_e, &f));
        hebbium.apply(&mut make_ctx(&mut w_h, &f));
        assert!(
            (w_e[0] - w_h[0]).abs() < 1e-6,
            "Engramum(beta=0) should equal Hebbium; e={} h={}",
            w_e[0],
            w_h[0]
        );
    }

    #[test]
    fn test_engramum_trace_accumulates() {
        // Second tick should potentiate more than the first because the EMA
        // trace has accumulated flow signal from tick 1.
        let mut w = vec![0.0_f32];
        let f = [1.0_f32];
        let mut policy = Engramum::new(1.0, 0.5, 1);
        // tick 1: trace = 0.5*0 + 0.5*1 = 0.5; w = 0.0 + 1.0*0.5*(1-0.0) = 0.5
        policy.apply(&mut make_ctx(&mut w, &f));
        let after1 = w[0];
        // tick 2: trace = 0.5*0.5 + 0.5*1 = 0.75; Δw = 1.0*0.75*(1-0.5) = 0.375
        policy.apply(&mut make_ctx(&mut w, &f));
        let after2 = w[0];
        assert!(
            after2 > after1,
            "second tick should potentiate more due to trace; after1={after1} after2={after2}"
        );
    }

    // ── Policy factories ──────────────────────────────────────────────────────

    #[test]
    fn test_sakibium_policy_runs_without_panic() {
        let mut policy = sakibium_policy(0.5);
        let mut w = vec![0.5_f32; 4];
        let f = vec![0.8_f32, 0.2, 0.9, 0.1];
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx); // must not panic
    }

    #[test]
    fn test_culture_policy_baseline() {
        let mut policy = culture_policy("baseline", 0.5, 4);
        let mut w = vec![0.5_f32; 4];
        let f = vec![0.8_f32; 4];
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx);
    }

    #[test]
    fn test_culture_policy_hebbium() {
        let mut policy = culture_policy("hebbium", 0.5, 4);
        let mut w = vec![0.5_f32; 4];
        let f = vec![1.0_f32; 4];
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx);
        // Hebbium with alpha=0.1: w = 0.5 + 0.1*1.0*0.5 = 0.55 → normalised
        // Just verify no panic and weights stay in [0,1].
        for &wi in &w {
            assert!(wi >= 0.0 && wi <= 1.0, "weight out of range: {wi}");
        }
    }

    #[test]
    fn test_culture_policy_engramum() {
        let mut policy = culture_policy("engramum", 0.5, 4);
        let mut w = vec![0.5_f32; 4];
        let f = vec![1.0_f32; 4];
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx);
        for &wi in &w {
            assert!(wi >= 0.0 && wi <= 1.0, "weight out of range: {wi}");
        }
    }

    #[test]
    fn test_culture_policy_unknown_falls_back_to_baseline() {
        // Unknown culture strings must not panic.
        let mut policy = culture_policy("unknown_culture", 0.5, 4);
        let mut w = vec![0.5_f32; 4];
        let f = vec![0.8_f32; 4];
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx);
    }

    // ── EngramumCompetitive ───────────────────────────────────────────────────

    #[test]
    fn test_engramum_competitive_weights_stay_in_range() {
        let mut w = vec![0.5_f32; 4];
        let f = [1.0_f32, 0.8, 0.2, 0.0];
        let mut policy = EngramumCompetitive::new(0.1, 0.9, 4);
        let mut ctx = make_ctx(&mut w, &f);
        for _ in 0..20 {
            policy.apply(&mut ctx);
        }
        for &wi in &w {
            assert!(wi >= 0.0 && wi <= 1.0, "weight out of range: {wi}");
        }
    }

    #[test]
    fn test_engramum_competitive_high_flow_edge_wins() {
        // Edge 0 gets all the flow; after many ticks it should dominate.
        let mut w = vec![0.5_f32; 4];
        let f = [1.0_f32, 0.0, 0.0, 0.0];
        let mut policy = EngramumCompetitive::new(0.2, 0.5, 4);
        let mut ctx = make_ctx(&mut w, &f);
        for _ in 0..30 {
            policy.apply(&mut ctx);
        }
        assert!(
            w[0] > w[1] && w[0] > w[2] && w[0] > w[3],
            "edge 0 should dominate; weights={w:?}"
        );
    }

    #[test]
    fn test_engramum_competitive_trace_resizes() {
        let mut w = vec![0.5_f32, 0.5];
        let f = [0.8_f32, 0.2];
        let mut policy = EngramumCompetitive::new(0.1, 0.9, 0);
        let mut ctx = make_ctx(&mut w, &f);
        policy.apply(&mut ctx); // must not panic
        assert_eq!(policy.trace.len(), 2);
    }

    #[test]
    fn test_engramum_competitive_linf_normalization() {
        // With L∞-norm, the max-flow edge always gets the full alpha update
        // regardless of graph size.  Verify on a 1-edge graph (trivial) and
        // compare to a 4-edge graph to confirm scale-invariance.
        let f = [1.0_f32, 0.0, 0.0, 0.0];

        // 1-edge version.
        let mut w1 = vec![0.0_f32];
        let mut policy1 = EngramumCompetitive::new(0.5, 0.0, 1); // beta=0 → trace=flow
        policy1.apply(&mut make_ctx(&mut w1, &f[..1]));
        // trace = flow = 1.0; max = 1.0; t = 1.0; Δw = 0.5 * 1.0 * 1.0 = 0.5
        assert!((w1[0] - 0.5).abs() < 1e-6, "expected 0.5, got {}", w1[0]);

        // 4-edge version — same edge 0 should also get Δw = 0.5.
        let mut w4 = vec![0.0_f32; 4];
        let mut policy4 = EngramumCompetitive::new(0.5, 0.0, 4);
        policy4.apply(&mut make_ctx(&mut w4, &f));
        assert!(
            (w4[0] - 0.5).abs() < 1e-6,
            "L∞ should be scale-invariant; 1-edge={} 4-edge={}",
            w1[0],
            w4[0]
        );
    }

    #[test]
    fn test_culture_policy_engramum_competitive() {
        let mut policy = culture_policy("engramum_competitive", 0.5, 4);
        let mut w = vec![0.5_f32; 4];
        let f = vec![1.0_f32, 0.5, 0.2, 0.0];
        let mut ctx = make_ctx(&mut w, &f);
        for _ in 0..10 {
            policy.apply(&mut ctx);
        }
        for &wi in &w {
            assert!(wi >= 0.0 && wi <= 1.0, "weight out of range: {wi}");
        }
    }
}
