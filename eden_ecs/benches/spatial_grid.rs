//! Criterion benchmarks for EDEN-ECS hot paths.
//!
//! Run with:
//! ```sh
//! cargo bench --manifest-path eden_ecs/Cargo.toml
//! ```
//!
//! # Targets
//!
//! | Benchmark              | Target   |
//! |------------------------|----------|
//! | `grid_rebuild_1m`      | ≤ 5 ms   |
//! | `grid_neighbor_query`  | < 50 ns  |
//! | `weaver_policy_1m`     | ≤ 1.2 ms |

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use eden_ecs::{
    spatial_grid::{GridConfig, PackedEntityRef, SpatialGrid},
    weaver::{
        ComposePolicy, FlowNormalisation, PolicyContext, RedundancyDecay, SelectiveReinforcement,
        WeaverSandbox,
    },
};

// ── Spatial grid benchmarks ───────────────────────────────────────────────────

fn bench_grid_rebuild(c: &mut Criterion) {
    let mut group = c.benchmark_group("spatial_grid");

    for &n_entities in &[100_000usize, 1_000_000] {
        group.throughput(Throughput::Elements(n_entities as u64));
        group.bench_with_input(
            BenchmarkId::new("rebuild", n_entities),
            &n_entities,
            |b, &n| {
                let cfg = GridConfig {
                    nx: 256,
                    ny: 256,
                    nz: 64,
                    cell_size: 1.0,
                };
                let mut grid = SpatialGrid::new(cfg.clone());
                grid.reserve(n);

                b.iter(|| {
                    // Simulate one frame: insert all entities then build.
                    for i in 0u32..(n as u32) {
                        let x = (i % 256) as f32 + 0.5;
                        let y = ((i / 256) % 256) as f32 + 0.5;
                        let z = (i / (256 * 256)) as f32 + 0.5;
                        grid.insert(
                            black_box([x, y, z]),
                            PackedEntityRef::new(i & PackedEntityRef::MAX_ENTITY_ID, 0),
                        );
                    }
                    grid.build();
                    black_box(grid.total_entities())
                });
            },
        );
    }
    group.finish();
}

fn bench_grid_neighbor_query(c: &mut Criterion) {
    // Pre-build a grid with 100 k entities.
    let cfg = GridConfig {
        nx: 128,
        ny: 128,
        nz: 64,
        cell_size: 1.0,
    };
    let mut grid = SpatialGrid::new(cfg);
    grid.reserve(100_000);
    for i in 0u32..100_000 {
        let x = (i % 128) as f32 + 0.5;
        let y = ((i / 128) % 128) as f32 + 0.5;
        let z = (i / (128 * 128)) as f32 + 0.5;
        grid.insert([x, y, z], PackedEntityRef::new(i, 0));
    }
    grid.build();

    c.bench_function("grid_neighbor_query", |b| {
        b.iter(|| {
            let mut sum = 0usize;
            grid.query_neighbors(black_box(64), black_box(64), black_box(32), |refs| {
                sum += refs.len();
            });
            black_box(sum)
        });
    });
}

// ── Weaver policy benchmarks ──────────────────────────────────────────────────

fn bench_weaver_policy(c: &mut Criterion) {
    let mut group = c.benchmark_group("weaver_policy");

    for &n_edges in &[100_000usize, 1_000_000] {
        group.throughput(Throughput::Elements(n_edges as u64));
        group.bench_with_input(
            BenchmarkId::new("compose_policy", n_edges),
            &n_edges,
            |b, &n| {
                let mut sandbox = WeaverSandbox::new(Box::new(ComposePolicy::new(vec![
                    Box::new(SelectiveReinforcement {
                        alpha: 0.05,
                        threshold: 0.6,
                    }),
                    Box::new(RedundancyDecay {
                        decay_rate: 0.02,
                        min_weight: 0.01,
                    }),
                    Box::new(FlowNormalisation { target_mean: 0.5 }),
                ])));

                let mut weights: Vec<f32> = (0..n).map(|i| (i % 100) as f32 / 100.0).collect();
                let flow_rates: Vec<f32> = (0..n).map(|i| (i % 100) as f32 / 100.0).collect();

                b.iter(|| {
                    let mut ctx = PolicyContext {
                        edge_weights: &mut weights,
                        flow_rates: &flow_rates,
                    };
                    sandbox.execute(black_box(&mut ctx));
                    black_box(sandbox.tick_count())
                });
            },
        );
    }
    group.finish();
}

criterion_group!(
    benches,
    bench_grid_rebuild,
    bench_grid_neighbor_query,
    bench_weaver_policy
);
criterion_main!(benches);
