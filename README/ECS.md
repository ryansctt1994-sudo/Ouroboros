# Eden ECS — Architecture & Module Reference

Eden ECS is a **biologically-inspired, RAM-bound, mycelial Entity-Component-System**
written in Rust.  It models cognition as a fungal routing network where edge
weights (synaptic conductances) are shaped by Hebbian learning, competitive
inhibition, and Polyak smoothing.

---

## Table of contents

1. [Conceptual model](#1-conceptual-model)
2. [Crate layout](#2-crate-layout)
3. [Module reference](#3-module-reference)
   - [weaver — fungal routing policies](#31-weaver--fungal-routing-policies)
   - [diagnostics — graph-structure metrics](#32-diagnostics--graph-structure-metrics)
   - [polyak — slow/fast weight averaging](#33-polyak--slowfast-weight-averaging)
   - [spatial_grid — packed entity grid](#34-spatial_grid--packed-entity-grid)
   - [telemetry_ffi — Python bridge](#35-telemetry_ffi--python-bridge)
   - [tracy — profiling & Sakib Index](#36-tracy--profiling--sakib-index)
   - [ffi_f16 — GPU diffusion buffers](#37-ffi_f16--gpu-diffusion-buffers)
   - [logger — CSV experiment logger](#38-logger--csv-experiment-logger)
   - [graph_perturb — robustness testing](#39-graph_perturb--robustness-testing)
   - [analysis/probes — representation analysis](#310-analysisprobes--representation-analysis)
4. [Weaver policies in depth](#4-weaver-policies-in-depth)
5. [Diagnostics metrics in depth](#5-diagnostics-metrics-in-depth)
6. [Data-flow diagram](#6-data-flow-diagram)
7. [Feature flags](#7-feature-flags)
8. [Performance targets](#8-performance-targets)

---

## 1. Conceptual model

```
                 ┌──────────────────────────────────────────┐
                 │               Mycelial Graph              │
                 │                                           │
                 │  nodes = entities (fungal hyphae tips)    │
                 │  edges = conductance channels (w ∈ [0,1]) │
                 └────────────────────┬─────────────────────┘
                                      │ flow_rates (read-only)
                                      ▼
                 ┌──────────────────────────────────────────┐
                 │              WeaverSandbox                │
                 │   hot-swappable WeaverPolicy              │
                 │   ┌─────────────────────────────────┐    │
                 │   │ active_policy.apply(ctx)         │    │
                 │   │   modifies edge_weights in-place │    │
                 │   └─────────────────────────────────┘    │
                 └────────────────────┬─────────────────────┘
                                      │ updated weights
                     ┌────────────────┴──────────────────┐
                     │                                   │
              ┌──────▼──────┐                   ┌───────▼──────┐
              │ diagnostics │                   │ telemetry_ffi│
              │  (metrics)  │                   │ (Python FFI) │
              └─────────────┘                   └──────────────┘
```

At each simulation **tick**:

1. A flow-propagation step computes `flow_rates` for each edge given the
   current activation pattern.
2. The active `WeaverPolicy` reads `flow_rates` and updates `edge_weights`
   in-place.
3. Diagnostic functions can be called on the updated weights to measure
   graph health.
4. The `telemetry_ffi` bridge writes the updated buffers for Python observers.

---

## 2. Crate layout

```
eden_ecs/src/
├── lib.rs               ← crate root; re-exports public symbols
├── weaver.rs            ← WeaverPolicy trait + all policy implementations
├── diagnostics.rs       ← graph-structure diagnostic functions
├── polyak.rs            ← PolyakAverager (slow/fast weight EMA)
├── spatial_grid.rs      ← PackedEntityRef ultra-dense spatial grid
├── telemetry_ffi.rs     ← ECSStateBuffer + C-ABI export functions
├── tracy.rs             ← Tracy profiling macros + Sakib Index / flow entropy
├── ffi_f16.rs           ← f16 buffer helpers for GPU / Unreal Engine 5
├── logger.rs            ← CsvLogger for experiment result persistence
├── graph_perturb.rs     ← edge rewiring and node shuffling utilities
└── analysis/
    └── probes.rs        ← LinearProbe + PCA variance helpers
```

---

## 3. Module reference

### 3.1 `weaver` — fungal routing policies

The Weaver is the hot-swappable policy engine.  Everything revolves around two
types:

#### `PolicyContext<'a>`

Passed by mutable reference to every policy tick.

| Field | Type | Description |
|-------|------|-------------|
| `edge_weights` | `&mut Vec<f32>` | Conductance of each edge (0 = blocked, 1 = max). Modified in-place. |
| `flow_rates` | `&[f32]` | Instantaneous flow magnitude through each edge. Read-only. |

#### `WeaverPolicy` trait

```rust
pub trait WeaverPolicy: Send + Sync {
    fn apply(&mut self, ctx: &mut PolicyContext<'_>);
    fn name(&self) -> &'static str;
}
```

All implementations must be `Send + Sync` so the sandbox can be shared across
worker threads.

#### `WeaverSandbox`

Owns one `Box<dyn WeaverPolicy>` and wraps it with Tracy zone instrumentation:

```rust
let mut sandbox = WeaverSandbox::new(culture_policy("engramum", 0.3, n_edges));
sandbox.execute(&mut ctx);
```

#### Built-in policies (see [Section 4](#4-weaver-policies-in-depth) for full details)

| Struct / function | Description |
|-------------------|-------------|
| `SelectiveReinforcement` | Reinforce edges above a flow threshold |
| `RedundancyDecay` | Prune edges below a flow threshold |
| `FlowNormalisation` | Homeostatic mean-clamping |
| `ComposePolicy` | Sequential composition of policies |
| `Hebbium` | Simple Hebbian potentiation |
| `Engramum` | EMA-traced Hebbian potentiation |
| `EngramumCompetitive` | EMA + L∞-competitive normalisation |
| `Polyakum` | Dual slow/fast weight system via Polyak averaging |
| `sakibium_policy(threshold)` | Factory: baseline competition + normalisation |
| `culture_policy(name, threshold, n)` | Factory: named culture selector |

---

### 3.2 `diagnostics` — graph-structure metrics

All functions are pure and `Send + Sync`.  They operate on weight slices and
adjacency information and return `0.0` on empty input.

| Function | Returns | Description |
|----------|---------|-------------|
| `weight_distribution_stats(weights)` | `(mean, std_dev, sparsity, gini)` | Weight spread and inequality |
| `dominant_eigenvalues(adj, n, k, iters)` | `Vec<f32>` | Top-k eigenvalues via power iteration |
| `clustering_coefficient(adj, weights, n)` | `f32` | Weighted local clustering coefficient |
| `modularity(adj, weights, n, communities)` | `f32` | Newman's modularity Q |
| `shannon_entropy(weights)` | `f32` | Shannon entropy of the weight distribution |
| `path_diversity(adj, weights, n)` | `f32` | Effective number of independent routing paths |
| `eigenvalue_gap(adj, n, iters)` | `f32` | Gap between first and second eigenvalue (spectral gap) |

---

### 3.3 `polyak` — slow/fast weight averaging

Implements **Polyak–Ruppert averaging** for stabilising learning dynamics.
Fast weights are updated by the learner; slow weights are updated via EMA and
used as the output representation.

```rust
use eden_ecs::polyak::PolyakAverager;

let mut averager = PolyakAverager::new(n_edges, 0.005); // tau = 0.005
// After each Weaver tick:
averager.update(&fast_weights);
// Slow weights are the stable output:
let slow: &[f32] = averager.slow_weights();
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `n_edges` | `usize` | Number of edges (pre-allocates buffers) |
| `tau` | `f32` | EMA step size (small = slow, stable; e.g. 0.005) |

The `Polyakum` Weaver policy wraps a `PolyakAverager` alongside an inner
learning policy so that the Weaver tick simultaneously updates fast weights
(via the inner policy) and slow weights (via the averager).

---

### 3.4 `spatial_grid` — packed entity grid

An ultra-dense linearised spatial grid using `PackedEntityRef` — a 24-bit
entity index packed with an 8-bit component tag into a single `u32`.  Designed
for cache-coherent iteration over entities in spatial proximity.

Key operations:

```rust
use eden_ecs::spatial_grid::{SpatialGrid, PackedEntityRef};

let mut grid = SpatialGrid::new(width, height, cell_size);
grid.insert(PackedEntityRef::new(entity_id, component_tag), x, y);
let neighbours = grid.query_radius(x, y, radius);
```

---

### 3.5 `telemetry_ffi` — Python bridge

Exports a zero-copy `f64` telemetry buffer over a C ABI so that the Python
observer (`cosmic_coder.py` / EngramObservatory) can read live state via
`ctypes` without a serialisation round-trip.

#### Buffer layout

| Buffer | Capacity | Semantics |
|--------|----------|-----------|
| `prediction_errors` | `MAX_ENTITIES` (100 000) | Per-entity Hebbian residual |
| `activations` | `MAX_ENTITIES` | Per-entity activation magnitude |
| `connectivity_weights` | `MAX_EDGES` (800 000) | Edge conductances |

#### C-ABI functions

```c
ECSStateBuffer* ecs_state_buffer_new(void);
void            ecs_state_buffer_free(ECSStateBuffer*);
void            ecs_state_buffer_flush(ECSStateBuffer*, uint32_t entity_count, uint32_t edge_count);
double*         ecs_state_buffer_activations_ptr(ECSStateBuffer*);
double*         ecs_state_buffer_connectivity_weights_ptr(ECSStateBuffer*);
double*         ecs_state_buffer_prediction_errors_ptr(ECSStateBuffer*);
uint32_t        ecs_state_buffer_entity_count(const ECSStateBuffer*);
uint32_t        ecs_state_buffer_edge_count(const ECSStateBuffer*);
```

Epoch-based synchronisation (`WRITE_EPOCH` atomic) prevents torn reads on the
Python side.

---

### 3.6 `tracy` — profiling & Sakib Index

#### Tracy macros (no-ops when `tracy` feature is off)

```rust
eden_ecs::tracy::frame_mark();           // tick boundary
eden_ecs::tracy::plot_f64("name", val);  // named scalar plot
```

#### Sakib Index

The **Sakib Index** measures routing quality:

```
sakib_index = mean(w[i] for i where flow[i] > threshold)
            / mean(w[all])
```

Values near **1.0** indicate uniform weights; values **> 1.0** indicate that
high-flow paths have been selectively reinforced; values near **0.0** indicate
network collapse.

```rust
use eden_ecs::tracy::{sakib_index, flow_entropy};

let s = sakib_index(&weights, &flows, 0.3);
let h = flow_entropy(&flows);
```

#### Flow entropy

Shannon entropy of the flow distribution, measured in bits.  High entropy
means flows are spread evenly; low entropy means routing has collapsed to a
few dominant channels.

---

### 3.7 `ffi_f16` — GPU diffusion buffers

Provides `f16` (IEEE 754 binary16) helper types and a C-ABI buffer for
transferring diffusion tensors to GPU shaders or Unreal Engine 5 Niagara
particle systems with minimal bandwidth overhead.

---

### 3.8 `logger` — CSV experiment logger

A simple, reusable CSV writer for centralising experiment results.

```rust
use eden_ecs::logger::CsvLogger;

let mut log = CsvLogger::new("results/run_001.csv",
    &["tick", "culture", "sakib", "entropy"])?;
log.write_row(&[tick.to_string(), culture.into(),
                format!("{:.6}", sakib), format!("{:.4}", entropy)])?;
log.flush()?;
```

The logger buffers writes and flushes on `drop`.  All rows must have the same
number of columns as the header; a mismatch is caught at write time.

---

### 3.9 `graph_perturb` — robustness testing

Provides controlled perturbations for stress-testing learned weight structures.

```rust
use eden_ecs::graph_perturb::{rewire_edges, shuffle_nodes};

// Randomly rewire `fraction` of edges (Watts–Strogatz-style)
rewire_edges(&mut edges, fraction, &mut rng);

// Shuffle node identities while preserving the edge structure
shuffle_nodes(&mut edges, n_nodes, &mut rng);
```

| Function | Description |
|----------|-------------|
| `rewire_edges(edges, fraction, rng)` | Replace `fraction` of edge destinations with uniformly random nodes |
| `shuffle_nodes(edges, n, rng)` | Apply a random permutation to all node indices |

Use these functions before re-running an experiment to measure how quickly
the network re-learns structure (transfer robustness metric).

---

### 3.10 `analysis/probes` — representation analysis

Tools for inspecting the geometry of learned representations.

```rust
use eden_ecs::analysis::probes::{LinearProbe, pca_explained_variance};

// Train a linear probe on (weights, labels) pairs
let probe = LinearProbe::fit(&feature_matrix, &labels, regularisation)?;
let accuracy = probe.eval(&test_features, &test_labels);

// PCA: fraction of variance explained by the top-k principal components
let variance_ratio = pca_explained_variance(&weight_matrix, k);
```

| Item | Description |
|------|-------------|
| `LinearProbe` | Logistic regression probe for evaluating linear separability of learned weight embeddings |
| `LinearProbe::fit(X, y, λ)` | Fit probe using gradient descent + L2 regularisation |
| `LinearProbe::eval(X, y)` | Return classification accuracy on a held-out set |
| `pca_explained_variance(X, k)` | Fraction of total variance captured by the top-k PCA components |

---

## 4. Weaver policies in depth

### SelectiveReinforcement

**Biological analogue:** *Physarum polycephalum* tube-diameter adaptation
(Tero et al. 2010).

```
Δw[i] = +α   if flow[i] > threshold
         0    otherwise
w[i] = clamp(w[i] + Δw[i], 0, 1)
```

| Parameter | Typical value | Effect |
|-----------|--------------|--------|
| `alpha` | 0.05 | Reinforcement step size per tick |
| `threshold` | 0.3 | Flow rate above which edges are reinforced |

---

### RedundancyDecay

**Biological analogue:** Hyphal autolysis in nutrient-depleted regions.

```
w[i] = max(min_weight, w[i] × (1 − decay_rate))   if flow[i] < min_weight
```

| Parameter | Typical value | Effect |
|-----------|--------------|--------|
| `decay_rate` | 0.02 | Proportional conductance loss per tick |
| `min_weight` | 0.01 | Conductance floor (edges never fully silenced) |

---

### FlowNormalisation

Homeostatic rescaling: keeps the mean conductance equal to `target_mean`.
Applied *after* reinforcement/decay to prevent runaway growth or collapse.

```
scale = target_mean / mean(w)
w[i]  = clamp(w[i] × scale, 0, 1)
```

---

### Hebbium

Simple Hebbian rule with saturation prevention:

```
w[i] = clamp(w[i] + α × flow[i] × (1 − w[i]), 0, 1)
```

The `(1 − w[i])` multiplicative term naturally bounds weights at 1.0 without
an explicit clamp in most operating regimes.

---

### Engramum

EMA-traced Hebbian rule.  The `trace` acts as a short-term synaptic memory:

```
trace[i] = β × trace[i] + (1 − β) × flow[i]
w[i]     = clamp(w[i] + α × trace[i] × (1 − w[i]), 0, 1)
```

Higher `β` lengthens the effective memory window.  The trace is lazily grown
and never shrunk, preserving accumulated history if the graph temporarily
reports fewer edges.

---

### EngramumCompetitive

EMA + L∞-competitive normalisation.  After the EMA update, traces are divided
by their maximum value so that the most active edge always receives the full
`α` update — **scale-invariant** across graphs of any size.

```
trace[i]  ← β × trace[i] + (1 − β) × flow[i]
t[i]       = trace[i] / (max(trace) + ε)           ← competition
w[i]      ← clamp(w[i] + α × t[i] × (1 − w[i]), 0, 1)
```

Winner-take-most routing channels emerge naturally without `FlowNormalisation`.

---

### Polyakum

Dual slow/fast system:

```
fast[i]  ← inner_policy.apply(fast[i], flow[i])
slow[i]  ← (1 − τ) × slow[i] + τ × fast[i]
```

The slow weights are the **output** representation; the fast weights are the
**learner**.  This separates rapid adaptation (fast) from stable output
(slow), reducing noise in downstream consumers.  `τ ≪ 1` (e.g. 0.005) gives
the slow weights a multi-hundred-tick effective time constant.

---

### `culture_policy` factory

Selects a pre-configured policy composition by name:

| Name | Composition |
|------|-------------|
| `"baseline"` | `SelectiveReinforcement` → `RedundancyDecay` → `FlowNormalisation` |
| `"hebbium"` | `Hebbium` → `RedundancyDecay` → `FlowNormalisation` |
| `"engramum"` | `Engramum` → `RedundancyDecay` → `FlowNormalisation` |
| `"engramum_competitive"` | `EngramumCompetitive` (competition replaces normalisation) |
| `"polyakum"` | `Polyakum` wrapping `EngramumCompetitive` |
| *(unknown)* | Falls back to `"baseline"` |

---

## 5. Diagnostics metrics in depth

### `weight_distribution_stats`

Returns `(mean, std_dev, sparsity, gini)`:

- **sparsity** — fraction of weights below 0.01 (near-zero / pruned edges)
- **Gini coefficient** — 0.0 = all edges equal; ≈ 1.0 = one dominant edge.
  Computed on the sorted weight vector using the standard formula:
  `G = (2 × Σᵢ rank_i × w_i) / (n × Σw) − (n+1)/n`

### `dominant_eigenvalues`

Top-k eigenvalues of the weighted adjacency matrix, computed via deflated
power iteration.  A large **spectral gap** (λ₁ >> λ₂) indicates a single
dominant routing channel has emerged.

### `clustering_coefficient`

Weighted local clustering (Onnela method):

```
C(v) = (1 / (k(v) × (k(v)−1))) × Σ_{i,j ∈ N(v)} (w_vi × w_ij × w_vj)^(1/3)
```

High clustering indicates that high-weight edges form tightly connected
local communities (triangle motifs).

### `modularity` (Newman's Q)

```
Q = (1/2m) × Σ_{ij} [w_ij − k_i × k_j / 2m] × δ(c_i, c_j)
```

Q > 0.3 suggests meaningful community structure has emerged in the routing
graph.

### `shannon_entropy`

Entropy of the weight distribution (treated as a discrete probability
distribution after normalisation by the sum).  High entropy = uniform weights;
low entropy = selective routing.

### `path_diversity`

Effective number of routing paths, computed as `exp(H)` where `H` is the
Shannon entropy of the per-path flow distribution.  A diversity of 1.0 means
all flow routes through a single path.

### `eigenvalue_gap`

`λ₁ − λ₂` from the top-2 eigenvalues.  A large gap indicates the learned
graph has a dominant eigenvector — one strong routing "backbone".

---

## 6. Data-flow diagram

```
  Python observer (cosmic_coder.py)
          │ ctypes raw pointer read
          │ (lock-free, epoch-gated)
          ▼
  ┌───────────────────┐
  │  ECSStateBuffer   │  (telemetry_ffi)
  │  activations[]    │
  │  weights[]        │
  │  pred_errors[]    │
  └────────┬──────────┘
           │ ecs_state_buffer_flush()
           ▼
  ┌───────────────────────────────────────┐
  │          Simulation tick              │
  │                                       │
  │  1. compute_flows(graph, weights) → flows           │
  │  2. WeaverSandbox.execute(ctx)                      │
  │       └─ active_policy.apply(ctx)                   │
  │           ├─ fast weights updated                    │
  │           └─ PolyakAverager.update() → slow weights  │
  │  3. diagnostics::weight_distribution_stats(weights) │
  │  4. tracy::record_sakib_index(s)                    │
  │  5. CsvLogger.write_row(…)                          │
  └───────────────────────────────────────┘
```

---

## 7. Feature flags

| Flag | Effect | Activate with |
|------|--------|---------------|
| `tracy` | Enable live Tracy profiler integration | `--features eden_ecs/tracy` |

All instrumentation is **zero-overhead** when the flag is absent — macros
expand to empty blocks and the `tracy-client` crate is not linked.

---

## 8. Performance targets

| Operation | Target | Graph size |
|-----------|--------|-----------|
| Weaver policy tick | ≤ 1.2 ms at 60 Hz | ≤ 20 M edges |
| Spatial grid rebuild | ≤ 200 µs | ≤ 100 000 entities |
| Telemetry flush | ≤ 50 µs | MAX_EDGES = 800 000 |
| Diagnostic full pass | ≤ 5 ms | 50 000-edge graph |

Benchmarks are in `eden_ecs/benches/` and run with `cargo bench -p eden_ecs`.
