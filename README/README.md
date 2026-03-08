# Ouroboros / Eden ECS — Documentation Index

This folder contains focused reference guides for setting up, building, and
working with the **Eden ECS** crate inside the Ouroboros repository.

---

## Documents in this folder

| File | What it covers |
|------|----------------|
| [LINUX.md](LINUX.md) | Installing system dependencies, building the crate, and running tests on Linux (Debian/Ubuntu, Fedora/RHEL, Arch) |
| [MACOS.md](MACOS.md) | Native macOS setup (Intel and Apple Silicon) — Xcode CLT, Homebrew, OpenSSL, Tracy on macOS, and Apple Silicon notes |
| [LIMA.md](LIMA.md) | Running a full Linux environment on macOS via Lima — VM creation, port-forwarding, and working with the Rust toolchain inside the VM |
| [ECS.md](ECS.md) | Eden ECS architecture deep-dive: modules, Weaver policies, diagnostics, telemetry FFI, and the Polyak memory system |
| [TERMINAL.md](TERMINAL.md) | Full terminal integration: `cosmic_coder.py` REPL/CLI agent, example experiments, CSV output, profiling, and the Python↔Rust bridge |

---

## Quick-start (Linux / Lima)

```sh
# 1. Install Rust (if not already present)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

# 2. Clone the repository
git clone https://github.com/AIOSPANDORA/Ouroboros.git
cd Ouroboros

# 3. Build the eden_ecs crate
cargo build --release -p eden_ecs

# 4. Run the full test suite
cargo test -p eden_ecs

# 5. Run the flagship A→B→A engram experiment
cargo run -p eden_ecs --example sakib_aba --release
```

See **[LINUX.md](LINUX.md)** for platform-specific dependency instructions
and **[TERMINAL.md](TERMINAL.md)** for the Python terminal agent and
all available experiment flags.

---

## Repository layout (abridged)

```
Ouroboros/
├── eden_ecs/                  ← Rust crate (main focus of these docs)
│   ├── Cargo.toml
│   ├── src/
│   │   ├── lib.rs             ← crate root & public API
│   │   ├── weaver.rs          ← Weaver policies (Hebbium, Engramum, …)
│   │   ├── diagnostics.rs     ← graph metrics (Gini, eigenvalues, clustering)
│   │   ├── spatial_grid.rs    ← ultra-dense packed entity grid
│   │   ├── telemetry_ffi.rs   ← zero-copy f64 bridge to Python
│   │   ├── tracy.rs           ← Tracy profiling hooks & Sakib Index
│   │   ├── ffi_f16.rs         ← f16 buffers for GPU / UE5 diffusion
│   │   ├── polyak.rs          ← Polyak (slow/fast) weight averaging
│   │   ├── logger.rs          ← CSV experiment logger
│   │   ├── graph_perturb.rs   ← edge/node perturbation for robustness tests
│   │   └── analysis/
│   │       └── probes.rs      ← linear probes & PCA for representation analysis
│   ├── examples/
│   │   ├── sakib_ab.rs        ← A/B routing experiment
│   │   ├── sakib_aba.rs       ← A→B→A engram persistence experiment
│   │   ├── competing_paths.rs ← competing-path routing benchmark
│   │   └── ablation.rs        ← component ablation harness
│   ├── tools/
│   │   └── cosmic_coder.py    ← Python terminal agent
│   └── benches/
│       └── spatial_grid.rs    ← Criterion micro-benchmarks
├── README/                    ← ← you are here
└── README.md                  ← top-level project README
```

---

## Feature flags

| Flag | Effect | Enable with |
|------|--------|-------------|
| `tracy` | Live Tracy profiler integration | `--features eden_ecs/tracy` |

---

## Licence

MIT — see [LICENSE](../LICENSE).
