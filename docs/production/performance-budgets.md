# Performance Budgets — AIOS: Ouroboros

Budgets are **hard limits**, not targets. A scene that exceeds a budget is a
regression, not a style choice. Profiling runs weekly; regressions block
promotion to beta.

---

## Frame Time Targets

| Platform | Target FPS | Frame Budget | Max Sustained Hitch |
|----------|-----------|--------------|---------------------|
| PC — Recommended spec | 60 | 16.6 ms | < 33 ms, < 1 per 10 s |
| PC — Minimum spec | 30 | 33.3 ms | < 66 ms, < 1 per 10 s |
| Steam Deck (preset: SteamDeck) | 40 | 25.0 ms | < 50 ms, < 1 per 10 s |

Recommended spec (provisional):
- CPU: Intel Core i7-8700 / AMD Ryzen 5 3600
- GPU: NVIDIA GTX 1070 / AMD RX 5700
- RAM: 16 GB

Minimum spec (provisional):
- CPU: Intel Core i5-6600K / AMD Ryzen 5 1600
- GPU: NVIDIA GTX 970 / AMD RX 480
- RAM: 8 GB

---

## Thread Budgets (Recommended Spec, 60 fps target)

| Thread | Budget |
|--------|--------|
| Game thread | ≤ 8 ms |
| Render thread | ≤ 8 ms |
| GPU frame | ≤ 14 ms |
| Rust/ECS simulation tick | ≤ 2 ms (async, never blocks game thread) |

---

## Memory Budgets

| Resource | PC Recommended | PC Minimum | Steam Deck |
|----------|---------------|-----------|------------|
| Total process RAM | 4 GB | 2.5 GB | 3 GB |
| Texture streaming pool | 2048 MB | 768 MB | 1024 MB |
| GPU VRAM (render targets + assets) | 4 GB | 2 GB | 2.5 GB (shared) |

---

## Shader Compilation

- **Goal**: zero stutter from shader compilation during normal gameplay.
- **Strategy**: PSO cache warm-up pass on first boot (with progress messaging).
- **Budget**: first-boot warm-up ≤ 90 seconds on recommended spec.
- **User messaging**: "Preparing shaders — this runs once and makes gameplay smoother."

---

## Streaming Hitch Budget

| Event | Maximum allowed hitch |
|-------|-----------------------|
| Level streaming transition | 100 ms (one time, with fade) |
| Async asset load during traversal | 16 ms |
| Rust/ECS IPC round-trip | 5 ms (99th percentile) |

---

## Graphics Preset Definitions

| Setting | Ultra | High | Medium | Low | Steam Deck |
|---------|-------|------|--------|-----|------------|
| Shadow quality | 4 | 3 | 2 | 1 | 2 |
| AA quality | TAA 4 | TAA 3 | TAA 2 | FXAA | TAA 2 |
| Post-process | 4 | 3 | 2 | 1 | 2 |
| Texture quality | 4 | 3 | 2 | 1 | 2 |
| Effects quality | 4 | 3 | 2 | 1 | 1 |
| Foliage quality | 4 | 3 | 2 | 1 | 1 |
| Lumen GI | On | On | On | Off | Off |
| Lumen Reflections | On | On | Off | Off | Off |
| Screen % | 100 | 100 | 90 | 80 | 80 |

---

## Profiling Cadence

- **Weekly**: Game thread + GPU frame on the benchmark scene.
- **Pre-promotion**: Full pass on all platform tiers.
- **Tool**: Unreal Insights (session saved to `Saved/Profiling/`).
- **Regression threshold**: > 10% regression from last baseline = must fix before promotion.
