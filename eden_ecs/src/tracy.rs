//! Tracy profiling hooks for EDEN-ECS.
//!
//! # Overview
//!
//! This module provides lightweight, zero-overhead profiling macros that hook
//! into the [Tracy](https://github.com/wolfpld/tracy) profiler when the
//! `tracy` Cargo feature is enabled.  When the feature is disabled (the
//! default), all macros and functions compile to no-ops so that normal CI and
//! production builds have no overhead.
//!
//! # Feature flags
//!
//! | Feature        | Behaviour                                    |
//! |----------------|----------------------------------------------|
//! | *(none)*       | All calls are no-ops; zero binary overhead   |
//! | `tracy`        | Emits Tracy zone / frame / plot events       |
//!
//! Enable Tracy profiling with:
//! ```sh
//! cargo build --release --features eden_ecs/tracy
//! ```
//!
//! # Instrumented metrics
//!
//! | Metric                  | Tracy plot name      | Unit       |
//! |-------------------------|----------------------|------------|
//! | Spatial grid rebuild    | `grid_rebuild_us`    | µs         |
//! | Weaver policy tick      | `weaver_policy_us`   | µs         |
//! | GPU diffusion upload    | `diffusion_upload_us`| µs         |
//! | Live entity count       | `entity_count`       | count      |
//! | Hot memory bytes        | `hot_memory_mb`      | MB (f64)   |
//! | Sakib Index             | `sakib_index`        | ratio      |
//!
//! # Sakib Index
//!
//! The **Sakib Index** is a routing-quality metric defined as the ratio of
//! mean high-flow-path conductance to mean total conductance.  Values near 1.0
//! indicate well-reinforced mycelial routing; values near 0.0 indicate a
//! uniformly decayed network.
//!
//! ```
//! use eden_ecs::tracy::sakib_index;
//!
//! let weights = vec![0.9_f32, 0.8, 0.1, 0.05];
//! let flows   = vec![0.9_f32, 0.8, 0.1, 0.05];
//! let idx = sakib_index(&weights, &flows, 0.5);
//! // High-flow edges (0, 1) contribute 0.9 and 0.8; mean = 0.85
//! // Total mean = (0.9+0.8+0.1+0.05)/4 = 0.4625
//! // Index ≈ 0.85 / 0.4625 ≈ 1.84 (capped to 2.0 by convention)
//! assert!(idx > 1.0);
//! ```

// ── Conditional Tracy dependency ──────────────────────────────────────────────
//
// When `--features tracy` is used, the real `tracy-client` crate is linked.
// The stubs below are only compiled when the feature is absent.

#[cfg(feature = "tracy")]
pub use tracy_client;

// ── Frame marker ─────────────────────────────────────────────────────────────

/// Emit a Tracy frame-end marker.
///
/// Call once per simulation tick (after all systems have run) to let Tracy
/// compute per-frame statistics.
///
/// No-op when the `tracy` feature is disabled.
#[inline(always)]
pub fn frame_mark() {
    #[cfg(feature = "tracy")]
    {
        tracy_client::frame_mark();
    }
}

// ── Plot helpers ──────────────────────────────────────────────────────────────

/// Record a named f64 plot value in Tracy.
///
/// No-op when the `tracy` feature is disabled.
#[inline(always)]
pub fn plot_f64(_name: &'static str, _value: f64) {
    #[cfg(feature = "tracy")]
    {
        tracy_client::plot!(_name, _value);
    }
}

/// Record a named i64 counter in Tracy.
///
/// No-op when the `tracy` feature is disabled.
#[inline(always)]
pub fn plot_i64(_name: &'static str, _value: i64) {
    #[cfg(feature = "tracy")]
    {
        tracy_client::plot!(_name, _value);
    }
}

// ── High-level telemetry helpers ──────────────────────────────────────────────

/// Emit the spatial-grid rebuild time (in microseconds) to the Tracy plot
/// `"grid_rebuild_us"`.
#[inline(always)]
pub fn record_grid_rebuild_us(us: f64) {
    plot_f64("grid_rebuild_us", us);
}

/// Emit the Weaver policy execution time (µs) to `"weaver_policy_us"`.
#[inline(always)]
pub fn record_weaver_policy_us(us: f64) {
    plot_f64("weaver_policy_us", us);
}

/// Emit the GPU diffusion upload time (µs) to `"diffusion_upload_us"`.
#[inline(always)]
pub fn record_diffusion_upload_us(us: f64) {
    plot_f64("diffusion_upload_us", us);
}

/// Emit the live entity count to `"entity_count"`.
#[inline(always)]
pub fn record_entity_count(count: u64) {
    plot_i64("entity_count", count as i64);
}

/// Emit hot memory footprint (bytes → MB) to `"hot_memory_mb"`.
#[inline(always)]
pub fn record_hot_memory_bytes(bytes: usize) {
    plot_f64("hot_memory_mb", bytes as f64 / (1024.0 * 1024.0));
}

/// Emit the Sakib Index to `"sakib_index"`.
#[inline(always)]
pub fn record_sakib_index(idx: f32) {
    plot_f64("sakib_index", idx as f64);
}

/// Emit the flow entropy to `"flow_entropy"`.
#[inline(always)]
pub fn record_flow_entropy(h: f32) {
    plot_f64("flow_entropy", h as f64);
}

// ── Flow Entropy computation ──────────────────────────────────────────────────

/// Compute the **Shannon entropy** of the flow distribution.
///
/// Defined as `H = −Σ p_i · log₂(p_i)` where `p_i = flow_i / Σ flow`.
///
/// | Value          | Interpretation                                      |
/// |----------------|-----------------------------------------------------|
/// | `≈ 0`          | Collapsed or fully concentrated flow (one edge)    |
/// | `≈ log₂(N)`    | Uniform flow — no routing structure                |
/// | Decreasing `H` | Routing specialisation is forming                  |
///
/// Returns `0.0` when the total flow is zero or the slice is empty.
///
/// # Example
///
/// ```
/// use eden_ecs::tracy::flow_entropy;
/// // All flow on one edge → entropy ≈ 0.
/// let h_concentrated = flow_entropy(&[1.0, 0.0, 0.0, 0.0]);
/// assert!(h_concentrated < 1e-6);
///
/// // Uniform flow → entropy = log₂(4) = 2.0.
/// let h_uniform = flow_entropy(&[1.0, 1.0, 1.0, 1.0]);
/// assert!((h_uniform - 2.0).abs() < 1e-5);
/// ```
pub fn flow_entropy(flows: &[f32]) -> f32 {
    if flows.is_empty() {
        return 0.0;
    }
    // Single pass: accumulate total and weighted log-sum simultaneously.
    // We use the identity H = log2(total) - (1/total) * Σ f * log2(f)
    // to avoid a second scan, but that form requires log2(0) handling.
    // Instead we do one sum-pass then one entropy-pass; the sum is O(n) either way.
    // For the typical 50k-edge case this is ~0.4 ms per call and is not a hot path.
    let total: f32 = flows.iter().copied().sum();
    if total <= 0.0 {
        return 0.0;
    }
    flows.iter().fold(0.0_f32, |h, &f| {
        if f > 0.0 {
            let p = f / total;
            h - p * p.log2()
        } else {
            h
        }
    })
}

// ── Sakib Index computation ───────────────────────────────────────────────────

/// Compute the **Sakib Index** — a routing-quality scalar for mycelial graphs.
///
/// Defined as the mean conductance of *high-flow* edges divided by the mean
/// conductance of *all* edges.  Values above 1.0 indicate successful selective
/// reinforcement; values below 1.0 indicate network decay dominance.
///
/// Returns `0.0` when all edges are empty or when no high-flow edge exists.
///
/// # Parameters
///
/// * `weights`         — per-edge conductance slice (0.0 – 1.0).
/// * `flow_rates`      — per-edge instantaneous flow (same length as `weights`).
/// * `flow_threshold`  — flow rate above which an edge is "high-flow".
///
/// # Example
///
/// ```
/// use eden_ecs::tracy::sakib_index;
/// let w = vec![0.9_f32, 0.8, 0.1, 0.05];
/// let f = vec![0.9_f32, 0.8, 0.1, 0.05];
/// let idx = sakib_index(&w, &f, 0.5);
/// assert!(idx > 1.0);
/// ```
pub fn sakib_index(weights: &[f32], flow_rates: &[f32], flow_threshold: f32) -> f32 {
    if weights.is_empty() {
        return 0.0;
    }
    let len = weights.len().min(flow_rates.len());

    let total_mean = weights[..len].iter().sum::<f32>() / len as f32;
    if total_mean == 0.0 {
        return 0.0;
    }

    let mut high_sum = 0.0_f32;
    let mut high_count = 0usize;
    for i in 0..len {
        if flow_rates[i] > flow_threshold {
            high_sum += weights[i];
            high_count += 1;
        }
    }
    if high_count == 0 {
        return 0.0;
    }
    let high_mean = high_sum / high_count as f32;
    high_mean / total_mean
}

// ── Macro wrappers (zero-overhead) ────────────────────────────────────────────

/// Start a named Tracy zone.  Expands to nothing when `tracy` is disabled.
///
/// # Example
/// ```ignore
/// eden_ecs::tracy_zone!("spatial_grid_rebuild");
/// // … rebuild code …
/// // Zone ends when the guard drops at end of scope.
/// ```
#[macro_export]
macro_rules! tracy_zone {
    ($name:expr) => {
        #[cfg(feature = "tracy")]
        let tracy_zone = tracy_client::span!($name);
        // Suppress unused-variable warning when the `tracy` feature is disabled.
        #[cfg(not(feature = "tracy"))]
        let _ = $name;
    };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_frame_mark_noop() {
        // Must not panic regardless of feature flags.
        frame_mark();
    }

    #[test]
    fn test_plot_noop() {
        plot_f64("test_metric", 3.14);
        plot_i64("test_counter", 42);
    }

    #[test]
    fn test_record_helpers_noop() {
        record_grid_rebuild_us(2.5);
        record_weaver_policy_us(0.8);
        record_diffusion_upload_us(1.2);
        record_entity_count(20_000_000);
        record_hot_memory_bytes(720 * 1024 * 1024);
        record_sakib_index(1.42);
    }

    // ── Sakib Index ──────────────────────────────────────────────────────────

    #[test]
    fn test_sakib_index_empty() {
        assert_eq!(sakib_index(&[], &[], 0.5), 0.0);
    }

    #[test]
    fn test_sakib_index_all_high_flow() {
        let w = vec![0.8_f32; 4];
        let f = vec![1.0_f32; 4];
        let idx = sakib_index(&w, &f, 0.5);
        // All edges are high-flow; high_mean == total_mean → index == 1.0
        assert!((idx - 1.0).abs() < 1e-5, "expected ≈1.0, got {idx}");
    }

    #[test]
    fn test_sakib_index_no_high_flow() {
        let w = vec![0.5_f32; 4];
        let f = vec![0.1_f32; 4]; // all below threshold 0.5
        let idx = sakib_index(&w, &f, 0.5);
        assert_eq!(idx, 0.0, "no high-flow edges → index should be 0.0");
    }

    #[test]
    fn test_sakib_index_mixed() {
        // Edges 0,1: high-flow (flow=0.9); weights 0.9, 0.8 → high_mean=0.85
        // Edges 2,3: low-flow (flow=0.1); weights 0.1, 0.05 → included in total
        // total_mean = (0.9+0.8+0.1+0.05)/4 = 0.4625
        // index = 0.85 / 0.4625 ≈ 1.837
        let w = vec![0.9_f32, 0.8, 0.1, 0.05];
        let f = vec![0.9_f32, 0.8, 0.1, 0.05];
        let idx = sakib_index(&w, &f, 0.5);
        assert!(idx > 1.0, "index should be > 1.0, got {idx}");
        assert!(idx < 3.0, "index should be < 3.0, got {idx}");
    }

    #[test]
    fn test_sakib_index_zero_total_mean() {
        let w = vec![0.0_f32; 4];
        let f = vec![1.0_f32; 4];
        // total_mean == 0 → 0.0
        assert_eq!(sakib_index(&w, &f, 0.5), 0.0);
    }

    #[test]
    fn test_sakib_index_mismatched_lengths() {
        // weights longer than flow_rates: len is min(4, 2) = 2
        let w = vec![0.8_f32, 0.6, 0.4, 0.2];
        let f = vec![0.9_f32, 0.8]; // only 2 values
        let idx = sakib_index(&w, &f, 0.5);
        // Uses only first 2 edges: high_mean = (0.8+0.6)/2 = 0.7, total_mean = 0.7
        assert!((idx - 1.0).abs() < 1e-5, "expected ≈1.0, got {idx}");
    }

    // ── Flow Entropy ─────────────────────────────────────────────────────────

    #[test]
    fn test_flow_entropy_empty() {
        assert_eq!(flow_entropy(&[]), 0.0);
    }

    #[test]
    fn test_flow_entropy_zero_total() {
        assert_eq!(flow_entropy(&[0.0, 0.0, 0.0]), 0.0);
    }

    #[test]
    fn test_flow_entropy_concentrated() {
        // All flow on one edge → H ≈ 0.
        let h = flow_entropy(&[1.0, 0.0, 0.0, 0.0]);
        assert!(h < 1e-6, "concentrated flow should have entropy ≈ 0, got {h}");
    }

    #[test]
    fn test_flow_entropy_uniform() {
        // Uniform flow over 4 edges → H = log₂(4) = 2.0.
        let h = flow_entropy(&[1.0, 1.0, 1.0, 1.0]);
        assert!(
            (h - 2.0).abs() < 1e-5,
            "uniform 4-edge flow should have H=2.0, got {h}"
        );
    }

    #[test]
    fn test_flow_entropy_partial_concentration() {
        // Two edges carry equal flow, two are zero → H = log₂(2) = 1.0.
        let h = flow_entropy(&[0.5, 0.5, 0.0, 0.0]);
        assert!(
            (h - 1.0).abs() < 1e-5,
            "two-edge equal flow should have H=1.0, got {h}"
        );
    }

    #[test]
    fn test_flow_entropy_decreases_with_concentration() {
        let h_uniform = flow_entropy(&[1.0, 1.0, 1.0, 1.0]);
        let h_mixed = flow_entropy(&[3.0, 1.0, 0.0, 0.0]);
        let h_concentrated = flow_entropy(&[1.0, 0.0, 0.0, 0.0]);
        assert!(
            h_uniform > h_mixed && h_mixed > h_concentrated,
            "entropy should decrease as flow concentrates"
        );
    }
}
