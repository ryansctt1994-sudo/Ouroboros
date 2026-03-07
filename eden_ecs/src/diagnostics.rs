//! Graph-structure diagnostics for the Weaver learning system.
//!
//! # Overview
//!
//! This module provides four diagnostic functions that measure whether the
//! Weaver's Hebbian learning is producing useful structure or degenerating into
//! uniform saturation or chaotic drift.  All functions are pure, `Send + Sync`
//! safe, and handle empty graphs by returning `0.0`.
//!
//! # Metrics
//!
//! | Function                    | Measures                                           |
//! |-----------------------------|----------------------------------------------------|
//! | [`weight_distribution_stats`] | Mean, std-dev, sparsity, Gini — weight spread    |
//! | [`dominant_eigenvalues`]    | Top-k eigenvalues — global connectivity structure  |
//! | [`clustering_coefficient`]  | Weighted local clustering — triangle density       |
//! | [`modularity`]              | Newman's Q — has community structure emerged?      |
//!
//! # Signal vs Noise
//!
//! These metrics answer the same question the Weaver asks at the edge level,
//! but at the graph level: is the learned weight distribution carrying real
//! signal, or is it uniform noise?
//!
//! | Metric          | Noise regime          | Signal regime                  |
//! |-----------------|-----------------------|--------------------------------|
//! | Gini            | ≈ 0 (uniform mush)    | 0.3–0.7 (selective structure)  |
//! | Eigenvalue gap  | λ₁ ≈ λ₂ (no dominant)| λ₁ >> λ₂ (one dominant path)  |
//! | Clustering      | ≈ 0 (tree-like)       | > 0 (local communities)        |
//! | Modularity Q    | ≤ 0 (random)          | > 0.3 (clear communities)      |
//!
//! # Computational Complexity
//!
//! | Function                  | Complexity                        |
//! |---------------------------|-----------------------------------|
//! | `weight_distribution_stats` | O(n log n) for the sort         |
//! | `dominant_eigenvalues`    | O(k × iterations × \|E\|)        |
//! | `clustering_coefficient`  | O(\|E\| + n × d²) where d = mean degree |
//! | `modularity`              | O(\|E\| + n)                      |
//!
//! # Example
//!
//! ```
//! use eden_ecs::diagnostics::{weight_distribution_stats, dominant_eigenvalues,
//!                              clustering_coefficient, modularity};
//!
//! let weights = vec![0.9_f32, 0.8, 0.1, 0.05, 0.0];
//! let (mean, std, sparsity, gini) = weight_distribution_stats(&weights);
//! assert!(gini > 0.0, "skewed distribution should have Gini > 0");
//! assert!(sparsity > 0.0, "weights below 0.01 should increase sparsity");
//! ```

// ── Weight Distribution Stats ─────────────────────────────────────────────────

/// Returns `(mean, std_dev, sparsity, gini_coefficient)` of the weight vector.
///
/// - `sparsity` — fraction of weights strictly below `0.01` (near-zero edges)
/// - `gini` — Gini inequality measure: `0.0` = all equal, `≈1.0` = one edge
///   has everything.  Computed on the sorted weight vector using the standard
///   formula `G = (2 × Σᵢ i·wᵢ) / (n × Σwᵢ) − (n+1)/n` (1-indexed rank).
///
/// Returns `(0.0, 0.0, 0.0, 0.0)` when `weights` is empty.
///
/// # Example
///
/// ```
/// use eden_ecs::diagnostics::weight_distribution_stats;
///
/// // Uniform weights → Gini ≈ 0.
/// let (mean, std, sparsity, gini) = weight_distribution_stats(&[0.5, 0.5, 0.5]);
/// assert!((mean - 0.5).abs() < 1e-6);
/// assert!(gini < 1e-5);
/// ```
#[inline]
pub fn weight_distribution_stats(weights: &[f32]) -> (f32, f32, f32, f32) {
    if weights.is_empty() {
        // Vacuously all weights are sparse (nothing to measure), Gini undefined → 0.
        return (0.0, 0.0, 1.0, 0.0);
    }

    let n = weights.len() as f32;

    // Mean and variance in a single extra pass.
    let mean = weights.iter().sum::<f32>() / n;
    let variance = weights.iter().map(|&w| (w - mean).powi(2)).sum::<f32>() / n;
    let std_dev = variance.sqrt();

    // Sparsity: fraction of weights below epsilon.
    const EPSILON: f32 = 0.01;
    let sparsity = weights.iter().filter(|&&w| w < EPSILON).count() as f32 / n;

    // Gini coefficient on sorted values.
    // Formula (1-indexed): G = (2 × Σᵢ rank_i × y_i) / (n × total) − (n+1)/n
    let mut sorted = weights.to_vec();
    sorted.sort_unstable_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let total: f32 = sorted.iter().sum();

    let gini = if total <= 0.0 {
        0.0
    } else {
        let numerator: f32 = sorted
            .iter()
            .enumerate()
            .map(|(i, &w)| (i + 1) as f32 * w)
            .sum::<f32>();
        let raw = 2.0 * numerator / (n * total) - (n + 1.0) / n;
        // Clamp to [0, 1] to absorb floating-point rounding on uniform inputs.
        raw.clamp(0.0, 1.0)
    };

    (mean, std_dev, sparsity, gini)
}

// ── Dominant Eigenvalue Estimation ───────────────────────────────────────────

/// Estimate the top-k eigenvalues of the weighted adjacency matrix using
/// power iteration with Gram-Schmidt re-orthogonalization.
///
/// After each sparse matrix-vector multiply, the result is orthogonalized
/// against all previously found eigenvectors (pure Gram-Schmidt, not
/// Hotelling deflation).  This is more numerically stable for directed
/// (non-symmetric) graphs where eigenvalues may be close together.
///
/// **Complexity:** O(k × `iterations` × |E|) — no dense matrix allocation.
///
/// **Initialization strategy cascade** (per eigenvalue):
/// 1. All-ones vector — converges to the Perron-Frobenius positive eigenvector
///    for non-negative irreducible matrices.
/// 2. Alternating +1/−1 — orthogonal to all-ones; good for 2nd eigenvector.
/// 3. Standard basis vectors `eⱼ` — robust fallback when the above are in the
///    span of previously found eigenvectors.
///
/// # Parameters
///
/// * `n_nodes`    — number of nodes in the graph.
/// * `edges`      — `(src, dst)` pairs; must have the same length as `weights`.
/// * `weights`    — per-edge conductance (same indexing as `edges`).
/// * `k`          — number of eigenvalues to compute.
/// * `iterations` — power-iteration steps per eigenvalue (20–50 is typical).
///
/// Returns up to `k` eigenvalues in descending order.  Returns an empty
/// `Vec` when `n_nodes == 0`, `edges` is empty, or `k == 0`.
///
/// # Example
///
/// ```
/// use eden_ecs::diagnostics::dominant_eigenvalues;
///
/// // A symmetric 2-node graph (A=[[0,w],[w,0]]) has eigenvalues ±w.
/// let edges = vec![(0usize, 1usize), (1usize, 0usize)];
/// let weights = vec![0.5_f32, 0.5_f32];
/// let evs = dominant_eigenvalues(2, &edges, &weights, 1, 30);
/// assert_eq!(evs.len(), 1);
/// assert!((evs[0] - 0.5).abs() < 0.05, "dominant eigenvalue ≈ 0.5, got {}", evs[0]);
/// ```
pub fn dominant_eigenvalues(
    n_nodes: usize,
    edges: &[(usize, usize)],
    weights: &[f32],
    k: usize,
    iterations: usize,
) -> Vec<f32> {
    if n_nodes == 0 || edges.is_empty() || k == 0 {
        return Vec::new();
    }

    let len = edges.len().min(weights.len());
    let mut eigenvalues: Vec<f32> = Vec::with_capacity(k);
    let mut eigenvectors: Vec<Vec<f32>> = Vec::with_capacity(k);

    for ev_idx in 0..k {
        // Strategy cascade: find the first non-degenerate starting vector
        // (one that survives Gram-Schmidt against all found eigenvectors).
        //
        // Bound: (k + 3) strategies is always enough because the found
        // eigenvectors span a k-dimensional subspace, and at most k standard
        // basis vectors can lie exactly in that subspace.  In practice the
        // search terminates at strategy 0 or 1.
        let max_strategies = (k + 3).min(n_nodes + 2);
        let mut v = None;

        for s in 0..max_strategies {
            let mut candidate: Vec<f32> = match s {
                // 1. All-ones: converges to positive Perron eigenvector.
                0 => vec![1.0_f32; n_nodes],
                // 2. Alternating ±1: orthogonal to all-ones; good for 2nd eigenvector.
                1 => (0..n_nodes)
                    .map(|i| if i % 2 == 0 { 1.0_f32 } else { -1.0_f32 })
                    .collect(),
                // 3+. Standard basis vectors e_j (cycled by ev_idx to spread diversity).
                _ => {
                    let mut basis = vec![0.0_f32; n_nodes];
                    let basis_idx = (ev_idx + s - 2) % n_nodes;
                    basis[basis_idx] = 1.0;
                    basis
                }
            };

            gram_schmidt(&mut candidate, &eigenvectors);
            let norm = l2_norm(&candidate);
            if norm > 1e-6 {
                for x in candidate.iter_mut() {
                    *x /= norm;
                }
                v = Some(candidate);
                break;
            }
        }

        let mut v = match v {
            Some(v) => v,
            None => break, // all candidates span the found subspace — stop
        };

        // Power iteration with Gram-Schmidt re-orthogonalization every step.
        for _ in 0..iterations {
            // Sparse A-transposed × v  (note: `w[dst] += weight * v[src]`
            // computes (Aᵀv)[dst], same eigenvalues as Av for diagnostic use).
            let mut w = vec![0.0_f32; n_nodes];
            for (edge_idx, &(src, dst)) in edges[..len].iter().enumerate() {
                if src < n_nodes && dst < n_nodes {
                    w[dst] += weights[edge_idx] * v[src];
                }
            }

            // Gram-Schmidt: remove components in the direction of each
            // previously found eigenvector to prevent drift.
            gram_schmidt(&mut w, &eigenvectors);

            let norm = l2_norm(&w);
            if norm < 1e-9 {
                break; // converged to zero
            }
            for (v_i, w_i) in v.iter_mut().zip(w.iter()) {
                *v_i = w_i / norm;
            }
        }

        // Rayleigh quotient: λ = vᵀ (Aᵀ v) = vᵀ A v  (symmetric under same note above)
        let mut av = vec![0.0_f32; n_nodes];
        for (edge_idx, &(src, dst)) in edges[..len].iter().enumerate() {
            if src < n_nodes && dst < n_nodes {
                av[dst] += weights[edge_idx] * v[src];
            }
        }
        let eigenvalue: f32 = v.iter().zip(av.iter()).map(|(a, b)| a * b).sum();

        eigenvalues.push(eigenvalue);
        eigenvectors.push(v);
    }

    eigenvalues
}

/// Gram-Schmidt orthogonalisation: remove from `v` all components in the
/// direction of each `basis` vector.  Assumes each basis vector is unit-length.
///
/// This is applied after every power-iteration matrix-vector multiply to prevent
/// drift of the new eigenvector toward previously found ones.
#[inline]
fn gram_schmidt(v: &mut [f32], basis: &[Vec<f32>]) {
    for u in basis {
        let dot: f32 = u.iter().zip(v.iter()).map(|(a, b)| a * b).sum();
        for (v_i, u_i) in v.iter_mut().zip(u.iter()) {
            *v_i -= dot * u_i;
        }
    }
}

/// Euclidean norm of a slice.
#[inline]
fn l2_norm(v: &[f32]) -> f32 {
    v.iter().map(|x| x * x).sum::<f32>().sqrt()
}

// ── Clustering Coefficient ────────────────────────────────────────────────────

/// Which weighted clustering formula to apply.
///
/// | Variant          | Best for                                          |
/// |------------------|---------------------------------------------------|
/// | `WeightedRatio`  | Uniform-weight graphs; easy to interpret          |
/// | `Onnela`         | Heavy-tailed graphs (Hebbium saturation regime)   |
#[derive(Clone, Copy, Debug)]
pub enum ClusteringMethod {
    /// `Cᵢ = Σ closed_triplet_weights / Σ all_triplet_weights`.
    ///
    /// A "triplet weight" for the pair `(j, k)` of node `i`'s neighbours is
    /// `w(i,j) · w(i,k)`.  Simple to interpret but dominated by a single
    /// strong spoke edge in heavy-tailed weight distributions.
    WeightedRatio,

    /// Onnela (2005): `Cᵢ = (2 / kᵢ(kᵢ−1)) · Σ (w̃ᵢⱼ · w̃ᵢₖ · w̃ⱼₖ)^(1/3)`.
    ///
    /// All three triangle edges contribute equally via the geometric mean.
    /// `w̃` are weights normalised by the global maximum so that `w̃ ∈ [0, 1]`.
    /// More robust when weight distributions are heavy-tailed (as in Hebbium's
    /// `(1-w)` saturation regime where a few weights saturate near 1.0).
    Onnela,
}

/// Compute the mean weighted clustering coefficient of the graph.
///
/// Directed edges are treated as undirected (when both directions of an edge
/// exist, the maximum weight is used as the canonical undirected weight).
///
/// Returns the mean local coefficient over nodes with `kᵢ ≥ 2`.
/// Returns `0.0` when `n_nodes == 0`, no edges exist, or all weights are zero.
///
/// # Example
///
/// ```
/// use eden_ecs::diagnostics::{clustering_coefficient, ClusteringMethod};
///
/// // Triangle on 3 nodes → C = 1.0 with either method.
/// let edges = vec![(0usize,1usize),(1usize,2usize),(2usize,0usize)];
/// let weights = vec![1.0_f32, 1.0, 1.0];
/// let c = clustering_coefficient(3, &edges, &weights, ClusteringMethod::Onnela);
/// assert!((c - 1.0).abs() < 1e-5, "complete triangle: C=1.0, got {c}");
/// ```
pub fn clustering_coefficient(
    n_nodes: usize,
    edges: &[(usize, usize)],
    weights: &[f32],
    method: ClusteringMethod,
) -> f32 {
    if n_nodes == 0 || edges.is_empty() {
        return 0.0;
    }

    let len = edges.len().min(weights.len());

    // Global maximum weight — used for Onnela normalisation.
    let w_max = weights[..len].iter().cloned().fold(0.0_f32, f32::max);
    if w_max <= 0.0 {
        return 0.0;
    }

    // Build undirected weight map: (min, max) → max weight seen in either direction.
    let mut edge_map: std::collections::HashMap<(usize, usize), f32> =
        std::collections::HashMap::with_capacity(len);
    for (edge_idx, &(src, dst)) in edges[..len].iter().enumerate() {
        if src < n_nodes && dst < n_nodes && src != dst {
            let key = (src.min(dst), src.max(dst));
            let entry = edge_map.entry(key).or_insert(0.0);
            *entry = entry.max(weights[edge_idx]);
        }
    }

    // Build undirected adjacency list from the deduplicated edge_map.
    let mut adj: Vec<Vec<(usize, f32)>> = vec![Vec::new(); n_nodes];
    for (&(u, v), &w) in &edge_map {
        adj[u].push((v, w));
        adj[v].push((u, w));
    }

    let mut sum_cc = 0.0_f32;
    let mut node_count = 0usize;

    for nbrs in &adj {
        let ki = nbrs.len();
        if ki < 2 {
            continue;
        }

        match method {
            ClusteringMethod::Onnela => {
                // Cᵢ = (2 / kᵢ(kᵢ−1)) · Σ_{j<k: edge(j,k)} (w̃ᵢⱼ w̃ᵢₖ w̃ⱼₖ)^(1/3)
                let mut tri_sum = 0.0_f32;
                for a in 0..nbrs.len() {
                    let (j, w_ij) = nbrs[a];
                    for &(k, w_ik) in &nbrs[a + 1..] {
                        let key = (j.min(k), j.max(k));
                        if let Some(&w_jk) = edge_map.get(&key) {
                            let product =
                                (w_ij / w_max) * (w_ik / w_max) * (w_jk / w_max);
                            tri_sum += product.cbrt();
                        }
                    }
                }
                sum_cc += 2.0 * tri_sum / (ki * (ki - 1)) as f32;
                node_count += 1;
            }

            ClusteringMethod::WeightedRatio => {
                // Cᵢ = (Σ w_ij·w_ik for closed pairs) / (Σ w_ij·w_ik for all pairs)
                let mut closed = 0.0_f32;
                let mut total = 0.0_f32;
                for a in 0..nbrs.len() {
                    let (j, w_ij) = nbrs[a];
                    for &(k, w_ik) in &nbrs[a + 1..] {
                        let triplet = w_ij * w_ik;
                        total += triplet;
                        let key = (j.min(k), j.max(k));
                        if edge_map.contains_key(&key) {
                            closed += triplet;
                        }
                    }
                }
                if total > 0.0 {
                    sum_cc += closed / total;
                    node_count += 1;
                }
            }
        }
    }

    if node_count == 0 {
        0.0
    } else {
        sum_cc / node_count as f32
    }
}

// ── Modularity Score (Newman's Q) ─────────────────────────────────────────────

/// Compute Newman's modularity Q for a given community assignment.
///
/// Uses the undirected-graph form of Q, treating directed edges symmetrically
/// (each directed edge (i→j) contributes to both `kᵢ` and `kⱼ` so that
/// `Σᵢ kᵢ = 2m`):
///
/// ```text
/// Q = (1/2m) × Σᵢⱼ [wᵢⱼ_sym − kᵢ·kⱼ/(2m)] · δ(cᵢ, cⱼ)
/// ```
///
/// where `wᵢⱼ_sym = wᵢⱼ + wⱼᵢ`, `kᵢ = in-strength + out-strength`,
/// `2m = Σᵢ kᵢ`, and `cᵢ` is the community label of node `i`.
///
/// | Q    | Interpretation                                    |
/// |------|---------------------------------------------------|
/// | ≤ 0  | No community structure (random or one community) |
/// | 0.3+ | Meaningful community structure has emerged        |
/// | 0.7+ | Very strong modular structure                     |
///
/// Returns `0.0` when `n_nodes == 0`, no edges exist, `communities.len() < n_nodes`,
/// or all edge weights are zero.
///
/// # Parameters
///
/// * `n_nodes`     — number of nodes.
/// * `edges`       — `(src, dst)` pairs.
/// * `weights`     — per-edge conductance.
/// * `communities` — node index → community label (0-indexed, arbitrary labels).
///
/// # Example
///
/// ```
/// use eden_ecs::diagnostics::modularity;
///
/// // Two-clique graph: nodes 0,1 ↔ nodes 2,3 with no cross edges.
/// let edges = vec![(0,1),(1,0),(2,3),(3,2)];
/// let weights = vec![1.0_f32; 4];
/// let communities = vec![0, 0, 1, 1];
/// let q = modularity(4, &edges, &weights, &communities);
/// assert!(q > 0.3, "two separate cliques should have Q > 0.3, got {q}");
/// ```
pub fn modularity(
    n_nodes: usize,
    edges: &[(usize, usize)],
    weights: &[f32],
    communities: &[usize],
) -> f32 {
    if n_nodes == 0 || edges.is_empty() || communities.len() < n_nodes {
        return 0.0;
    }

    let len = edges.len().min(weights.len());

    // Compute weighted degree k_i = in-strength + out-strength, and total m.
    let mut k = vec![0.0_f32; n_nodes];
    let mut m = 0.0_f32;

    for (edge_idx, &(src, dst)) in edges[..len].iter().enumerate() {
        if src < n_nodes && dst < n_nodes {
            let w = weights[edge_idx];
            m += w;
            k[src] += w; // out-strength contribution
            k[dst] += w; // in-strength contribution
        }
    }

    if m <= 0.0 {
        return 0.0;
    }

    let two_m = 2.0 * m; // = Σᵢ kᵢ

    // Sum of directed within-community edge weights.
    let mut within = 0.0_f32;
    for (edge_idx, &(src, dst)) in edges[..len].iter().enumerate() {
        if src < n_nodes && dst < n_nodes && communities[src] == communities[dst] {
            within += weights[edge_idx];
        }
    }

    // Σ_c (Σ_{i ∈ c} kᵢ)² — use a HashMap to handle arbitrary community labels.
    let mut c_k: std::collections::HashMap<usize, f32> = std::collections::HashMap::new();
    for i in 0..n_nodes {
        *c_k.entry(communities[i]).or_insert(0.0) += k[i];
    }
    let sum_k_sq: f32 = c_k.values().map(|&x| x * x).sum();

    // Q = (1/2m) × [2·within − sum_k_sq / (2m)]
    // Derivation: treating directed edges as symmetric doubles 'within' in the
    // Σ_ij w_ij_sym sum, while k and 2m are already symmetric by construction.
    (2.0 * within - sum_k_sq / two_m) / two_m
}

// ── Tests ─────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    // ── weight_distribution_stats ────────────────────────────────────────────

    #[test]
    fn test_wds_empty() {
        // Empty → (mean=0, std=0, sparsity=1 [vacuous], gini=0)
        assert_eq!(weight_distribution_stats(&[]), (0.0, 0.0, 1.0, 0.0));
    }

    #[test]
    fn test_wds_single_weight() {
        let (mean, std, sparsity, gini) = weight_distribution_stats(&[0.5]);
        assert!((mean - 0.5).abs() < 1e-6, "mean should be 0.5, got {mean}");
        assert!(std < 1e-6, "std of a single value should be 0, got {std}");
        assert!((sparsity - 0.0).abs() < 1e-6, "0.5 is not sparse, got {sparsity}");
        assert!(gini < 1e-5, "gini of a single value should be 0, got {gini}");
    }

    #[test]
    fn test_wds_uniform_weights() {
        let weights = vec![0.5_f32; 8];
        let (mean, std, sparsity, gini) = weight_distribution_stats(&weights);
        assert!((mean - 0.5).abs() < 1e-5, "mean should be 0.5, got {mean}");
        assert!(std < 1e-5, "std should be 0 for uniform, got {std}");
        assert!((sparsity - 0.0).abs() < 1e-6, "no sparse weights, got {sparsity}");
        assert!(gini < 1e-5, "gini should be 0 for uniform, got {gini}");
    }

    #[test]
    fn test_wds_all_zero_weights() {
        let weights = vec![0.0_f32; 4];
        let (mean, std, sparsity, gini) = weight_distribution_stats(&weights);
        assert!((mean - 0.0).abs() < 1e-6);
        assert!((std - 0.0).abs() < 1e-6);
        // All weights < 0.01 → sparsity = 1.0
        assert!((sparsity - 1.0).abs() < 1e-6, "all zero → sparsity=1.0, got {sparsity}");
        assert!((gini - 0.0).abs() < 1e-6, "zero total → gini=0.0, got {gini}");
    }

    #[test]
    fn test_wds_sparsity_fraction() {
        // 2 out of 4 weights are below 0.01.
        let weights = vec![0.005_f32, 0.0, 0.5, 0.8];
        let (_, _, sparsity, _) = weight_distribution_stats(&weights);
        assert!(
            (sparsity - 0.5).abs() < 1e-5,
            "2/4 below epsilon → sparsity=0.5, got {sparsity}"
        );
    }

    #[test]
    fn test_wds_gini_skewed() {
        // One edge has nearly everything → Gini close to (n-1)/n.
        let weights = vec![0.0_f32, 0.0, 0.0, 1.0];
        let (_, _, _, gini) = weight_distribution_stats(&weights);
        // Expected: G = (n-1)/n = 3/4 = 0.75
        assert!(
            (gini - 0.75).abs() < 1e-5,
            "skewed distribution should have gini≈0.75, got {gini}"
        );
    }

    #[test]
    fn test_wds_gini_in_range() {
        // Arbitrary mixed weights — Gini must always be in [0, 1].
        let weights = vec![0.9_f32, 0.8, 0.1, 0.05, 0.3, 0.6];
        let (_, _, _, gini) = weight_distribution_stats(&weights);
        assert!(
            (0.0..=1.0).contains(&gini),
            "gini must be in [0,1], got {gini}"
        );
        assert!(gini > 0.0, "skewed distribution should have gini > 0");
    }

    #[test]
    fn test_wds_std_dev() {
        // Weights [0, 1] → mean=0.5, variance=0.25, std=0.5.
        let (mean, std, _, _) = weight_distribution_stats(&[0.0_f32, 1.0]);
        assert!((mean - 0.5).abs() < 1e-5, "mean should be 0.5, got {mean}");
        assert!((std - 0.5).abs() < 1e-5, "std should be 0.5, got {std}");
    }

    // ── dominant_eigenvalues ─────────────────────────────────────────────────

    #[test]
    fn test_eigenvalues_empty_nodes() {
        let evs = dominant_eigenvalues(0, &[], &[], 3, 20);
        assert!(evs.is_empty());
    }

    #[test]
    fn test_eigenvalues_empty_edges() {
        let evs = dominant_eigenvalues(5, &[], &[], 3, 20);
        assert!(evs.is_empty());
    }

    #[test]
    fn test_eigenvalues_k_zero() {
        let edges = vec![(0usize, 1usize)];
        let weights = vec![1.0_f32];
        let evs = dominant_eigenvalues(2, &edges, &weights, 0, 20);
        assert!(evs.is_empty());
    }

    #[test]
    fn test_eigenvalues_single_self_symmetric_edge() {
        // A symmetric 2-node graph (edges 0→1 and 1→0 with weight w) has
        // adjacency matrix [[0,w],[w,0]] with eigenvalues +w and −w.
        let w = 0.7_f32;
        let edges = vec![(0usize, 1usize), (1usize, 0usize)];
        let weights = vec![w, w];
        let evs = dominant_eigenvalues(2, &edges, &weights, 1, 50);
        assert_eq!(evs.len(), 1);
        assert!(
            (evs[0] - w).abs() < 0.05,
            "dominant eigenvalue should be ≈{w}, got {}",
            evs[0]
        );
    }

    #[test]
    fn test_eigenvalues_complete_graph_k3() {
        // Complete directed graph K₃ (all 6 directed edges, weight 1).
        // Adjacency matrix [[0,1,1],[1,0,1],[1,1,0]] has eigenvalues 2, -1, -1.
        let edges = vec![(0,1),(0,2),(1,0),(1,2),(2,0),(2,1)];
        let weights = vec![1.0_f32; 6];
        let evs = dominant_eigenvalues(3, &edges, &weights, 2, 50);
        assert_eq!(evs.len(), 2, "should return k=2 eigenvalues");
        assert!(
            (evs[0] - 2.0).abs() < 0.1,
            "dominant eigenvalue of K₃ should be ≈2.0, got {}",
            evs[0]
        );
        assert!(
            (evs[1] + 1.0).abs() < 0.2,
            "second eigenvalue of K₃ should be ≈-1.0, got {}",
            evs[1]
        );
    }

    #[test]
    fn test_eigenvalues_returns_k_values() {
        let edges: Vec<(usize, usize)> = (0..4)
            .flat_map(|i| (0..4).filter(move |&j| j != i).map(move |j| (i, j)))
            .collect();
        let weights = vec![1.0_f32; edges.len()];
        let evs = dominant_eigenvalues(4, &edges, &weights, 3, 30);
        assert_eq!(evs.len(), 3, "should return exactly k=3 eigenvalues");
    }

    #[test]
    fn test_eigenvalues_nonnegative_dominant() {
        // Symmetric undirected path 0--1--2--3 (both directed edges per pair).
        // For a non-negative symmetric matrix the dominant eigenvalue is positive
        // (Perron-Frobenius), and the all-ones init converges to it reliably.
        let edges = vec![(0usize,1),(1,0),(1,2),(2,1),(2,3),(3,2)];
        let weights = vec![0.5_f32, 0.5, 0.8, 0.8, 0.3, 0.3];
        let evs = dominant_eigenvalues(4, &edges, &weights, 1, 30);
        assert!(!evs.is_empty());
        assert!(
            evs[0] > 0.0,
            "dominant eigenvalue of a symmetric non-negative matrix must be > 0, got {}",
            evs[0]
        );
    }

    // ── clustering_coefficient ───────────────────────────────────────────────

    #[test]
    fn test_clustering_empty_nodes() {
        assert_eq!(
            clustering_coefficient(0, &[], &[], ClusteringMethod::Onnela),
            0.0
        );
    }

    #[test]
    fn test_clustering_empty_edges() {
        assert_eq!(
            clustering_coefficient(5, &[], &[], ClusteringMethod::WeightedRatio),
            0.0
        );
    }

    #[test]
    fn test_clustering_all_zero_weights() {
        let edges = vec![(0usize, 1usize), (1usize, 2usize), (2usize, 0usize)];
        let weights = vec![0.0_f32, 0.0, 0.0];
        // w_max = 0 → early return 0.0 for both methods.
        assert_eq!(
            clustering_coefficient(3, &edges, &weights, ClusteringMethod::Onnela),
            0.0
        );
        assert_eq!(
            clustering_coefficient(3, &edges, &weights, ClusteringMethod::WeightedRatio),
            0.0
        );
    }

    #[test]
    fn test_clustering_no_triangle_onnela() {
        // Linear path 0→1→2: no triangles → C = 0.
        let edges = vec![(0usize, 1usize), (1usize, 2usize)];
        let weights = vec![1.0_f32, 1.0];
        let c = clustering_coefficient(3, &edges, &weights, ClusteringMethod::Onnela);
        assert!(
            c < 1e-5,
            "linear path has no triangles; Onnela C should be 0, got {c}"
        );
    }

    #[test]
    fn test_clustering_no_triangle_ratio() {
        let edges = vec![(0usize, 1usize), (1usize, 2usize)];
        let weights = vec![1.0_f32, 1.0];
        let c = clustering_coefficient(3, &edges, &weights, ClusteringMethod::WeightedRatio);
        assert!(
            c < 1e-5,
            "linear path has no triangles; WeightedRatio C should be 0, got {c}"
        );
    }

    #[test]
    fn test_clustering_complete_triangle_onnela() {
        // Directed 3-cycle treated as undirected triangle.
        // Onnela: (1·1·1)^(1/3) = 1 per pair, C_i = 2*1/(2*1) = 1.0.
        let edges = vec![(0usize, 1usize), (1usize, 2usize), (2usize, 0usize)];
        let weights = vec![1.0_f32, 1.0, 1.0];
        let c = clustering_coefficient(3, &edges, &weights, ClusteringMethod::Onnela);
        assert!(
            (c - 1.0).abs() < 1e-5,
            "complete triangle Onnela should have C=1.0, got {c}"
        );
    }

    #[test]
    fn test_clustering_complete_triangle_ratio() {
        let edges = vec![(0usize, 1usize), (1usize, 2usize), (2usize, 0usize)];
        let weights = vec![1.0_f32, 1.0, 1.0];
        let c = clustering_coefficient(3, &edges, &weights, ClusteringMethod::WeightedRatio);
        assert!(
            (c - 1.0).abs() < 1e-5,
            "complete triangle WeightedRatio should have C=1.0, got {c}"
        );
    }

    #[test]
    fn test_clustering_range_onnela() {
        let edges = vec![(0, 1), (1, 2), (2, 0), (0, 3), (3, 4)];
        let weights = vec![0.8_f32, 0.6, 0.9, 0.4, 0.5];
        let c = clustering_coefficient(5, &edges, &weights, ClusteringMethod::Onnela);
        assert!((0.0..=1.0).contains(&c), "Onnela C must be in [0,1], got {c}");
    }

    #[test]
    fn test_clustering_isolated_nodes() {
        // Node 3 is isolated; result still 1.0 over nodes 0,1,2.
        let edges = vec![(0usize, 1usize), (1usize, 2usize), (2usize, 0usize)];
        let weights = vec![1.0_f32, 1.0, 1.0];
        let c = clustering_coefficient(4, &edges, &weights, ClusteringMethod::Onnela);
        assert!(
            (c - 1.0).abs() < 1e-5,
            "isolated node should not affect C; got {c}"
        );
    }

    #[test]
    fn test_clustering_onnela_depresses_weak_triangle() {
        // Triangle with one weak edge: Onnela gives C < 1 because w_jk^(1/3) is small.
        let edges = vec![(0usize, 1usize), (1usize, 2usize), (2usize, 0usize)];
        let weights = vec![1.0_f32, 1.0, 0.1]; // edge 2→0 is weak
        let c_onnela = clustering_coefficient(3, &edges, &weights, ClusteringMethod::Onnela);
        assert!(
            c_onnela > 0.0 && c_onnela < 1.0,
            "partially weak triangle: 0 < C_onnela < 1, got {c_onnela}"
        );
    }

    // ── modularity ───────────────────────────────────────────────────────────

    #[test]
    fn test_modularity_empty_nodes() {
        assert_eq!(modularity(0, &[], &[], &[]), 0.0);
    }

    #[test]
    fn test_modularity_empty_edges() {
        let communities = vec![0usize; 4];
        assert_eq!(modularity(4, &[], &[], &communities), 0.0);
    }

    #[test]
    fn test_modularity_mismatched_communities() {
        // communities shorter than n_nodes → 0.0.
        let edges = vec![(0usize, 1usize)];
        let weights = vec![1.0_f32];
        let communities = vec![0usize]; // only 1 element for 3 nodes
        assert_eq!(modularity(3, &edges, &weights, &communities), 0.0);
    }

    #[test]
    fn test_modularity_all_same_community() {
        // All nodes in one community → Q = 0 (null model is saturated).
        let edges = vec![(0, 1), (1, 0), (1, 2), (2, 1)];
        let weights = vec![1.0_f32; 4];
        let communities = vec![0usize; 3];
        let q = modularity(3, &edges, &weights, &communities);
        assert!(q.abs() < 1e-5, "all-one-community should give Q≈0, got {q}");
    }

    #[test]
    fn test_modularity_two_perfect_communities() {
        // Nodes {0,1} fully connected internally; nodes {2,3} fully connected
        // internally; no cross edges.  Q should be well above 0.
        let edges = vec![(0, 1), (1, 0), (2, 3), (3, 2)];
        let weights = vec![1.0_f32; 4];
        let communities = vec![0, 0, 1, 1];
        let q = modularity(4, &edges, &weights, &communities);
        assert!(q > 0.3, "two perfect communities should give Q > 0.3, got {q}");
    }

    #[test]
    fn test_modularity_zero_weights() {
        // All weights zero → 0.0.
        let edges = vec![(0, 1), (1, 0)];
        let weights = vec![0.0_f32; 2];
        let communities = vec![0, 1];
        assert_eq!(modularity(2, &edges, &weights, &communities), 0.0);
    }

    #[test]
    fn test_modularity_range_arbitrary() {
        // Q can be negative; it should be at most 1.0 in practice.
        let edges: Vec<(usize, usize)> = (0..5)
            .flat_map(|i| (0..5).filter(move |&j| j != i).map(move |j| (i, j)))
            .collect();
        let weights = vec![0.5_f32; edges.len()];
        // Bad community split (each node in its own community):
        let communities: Vec<usize> = (0..5).collect();
        let q = modularity(5, &edges, &weights, &communities);
        assert!(q <= 1.0, "Q must be ≤ 1.0, got {q}");
    }
}
