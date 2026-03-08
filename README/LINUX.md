# Linux Setup Guide — Eden ECS

This guide covers every step needed to build, test, and run the **Eden ECS**
crate on a Linux system.  All commands are for a standard `x86_64` host;
`aarch64` (Raspberry Pi 5, Ampere, etc.) works identically unless noted.

---

## Table of contents

1. [System dependencies](#1-system-dependencies)
2. [Rust toolchain](#2-rust-toolchain)
3. [Clone the repository](#3-clone-the-repository)
4. [Build](#4-build)
5. [Test](#5-test)
6. [Run examples](#6-run-examples)
7. [Benchmarks](#7-benchmarks)
8. [Tracy profiling](#8-tracy-profiling)
9. [Cross-compilation](#9-cross-compilation)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. System dependencies

### Debian / Ubuntu (22.04 LTS or later)

```sh
sudo apt update
sudo apt install -y \
    build-essential \
    pkg-config \
    libssl-dev \
    curl \
    git
```

### Fedora / RHEL / Rocky Linux

```sh
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y \
    openssl-devel \
    pkg-config \
    curl \
    git
```

### Arch Linux / Manjaro

```sh
sudo pacman -Syu --needed \
    base-devel \
    openssl \
    pkg-config \
    curl \
    git
```

> **Note:** `openssl-devel` / `libssl-dev` is required because the `reqwest`
> HTTP client (used by the telemetry bridge) links against OpenSSL when the
> `rustls-tls` feature is not fully tree-shaken.  If you see linker errors
> mentioning `ssl` or `crypto`, install this package.

---

## 2. Rust toolchain

Eden ECS requires **Rust 1.75 or later** (the `edition = "2021"` and the
`half` crate use stabilised features present from 1.75 onwards).

### Install via rustup (recommended)

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# Follow the on-screen prompts, then reload your shell:
source "$HOME/.cargo/env"
```

### Verify

```sh
rustc --version   # e.g. rustc 1.78.0 (9b00956e5 2024-04-29)
cargo --version   # e.g. cargo 1.78.0 (…)
```

### Keep up to date

```sh
rustup update stable
```

---

## 3. Clone the repository

```sh
git clone https://github.com/AIOSPANDORA/Ouroboros.git
cd Ouroboros
```

The workspace `Cargo.toml` at the repo root declares `eden_ecs` as a member,
so all `cargo` commands accept `-p eden_ecs` to scope them to the crate.

---

## 4. Build

### Debug build (fast to compile, includes debug info)

```sh
cargo build -p eden_ecs
```

### Release build (optimised, use for experiments and benchmarks)

```sh
cargo build --release -p eden_ecs
```

Compiled artefacts are placed in `target/debug/` and `target/release/`
respectively.  The shared library (`libeden_ecs.so`) is produced in the same
directory because the crate's `crate-type` includes `cdylib`.

### Build with Tracy profiling enabled

```sh
cargo build --release -p eden_ecs --features eden_ecs/tracy
```

See [Section 8](#8-tracy-profiling) for connecting the Tracy GUI.

---

## 5. Test

Run the full unit-and-integration test suite:

```sh
cargo test -p eden_ecs
```

Run only tests whose name contains a specific string (e.g. `weaver`):

```sh
cargo test -p eden_ecs weaver
```

Run tests with output visible (useful for debugging):

```sh
cargo test -p eden_ecs -- --nocapture
```

Run a single named test:

```sh
cargo test -p eden_ecs test_engramum_competitive_linf_normalization -- --exact
```

Expected result: **all tests pass** (the suite currently contains 81+ tests
across `weaver`, `diagnostics`, `spatial_grid`, and `telemetry_ffi`).

---

## 6. Run examples

Examples live in `eden_ecs/examples/` and are run with `cargo run --example`.

### A/B routing experiment

```sh
cargo run -p eden_ecs --example sakib_ab --release
# With named flags (preferred):
cargo run -p eden_ecs --example sakib_ab --release -- \
    --culture engramum_competitive --steps 6 --gain 2.0 --noise 0.05
# With diagnostics emitted to stderr every 100 ticks:
cargo run -p eden_ecs --example sakib_ab --release -- \
    --culture engramum --diagnostics
```

Outputs CSV to **stdout** (`tick,culture,sakib,entropy`) and diagnostics to
**stderr**.  Redirect to a file for later analysis:

```sh
cargo run -p eden_ecs --example sakib_ab --release 2>diag.log | tee results.csv
```

### A→B→A engram persistence experiment

```sh
cargo run -p eden_ecs --example sakib_aba --release
# optional args: [n_ticks] [flow_gain]
cargo run -p eden_ecs --example sakib_aba --release -- 2000 2.0
```

### Competing-paths experiment

```sh
cargo run -p eden_ecs --example competing_paths --release
```

Includes diagnostic logging for all policy variants including `polyakum`.

### Ablation harness

```sh
cargo run -p eden_ecs --example ablation --release
```

Isolates the contribution of each system component to overall learning
performance.

---

## 7. Benchmarks

The `spatial_grid` micro-benchmark uses [Criterion](https://github.com/bheisler/criterion.rs):

```sh
cargo bench -p eden_ecs
```

HTML reports are written to `target/criterion/`.

To run only the spatial-grid benchmark:

```sh
cargo bench -p eden_ecs --bench spatial_grid
```

---

## 8. Tracy profiling

[Tracy](https://github.com/wolfpld/tracy) is a real-time, sampling profiler.
The `tracy` Cargo feature enables zero-overhead instrumentation hooks.

### Step 1 — Build Tracy GUI

```sh
# Debian/Ubuntu dependencies
sudo apt install -y libcapstone-dev libdwarf-dev libtbb-dev \
                    libglfw3-dev libfreetype-dev

git clone https://github.com/wolfpld/tracy.git
cd tracy/profiler/build/unix
make -j$(nproc)
# Binary: ./Tracy-release
```

### Step 2 — Run Eden ECS with Tracy enabled

```sh
cargo run --release -p eden_ecs --example sakib_aba \
    --features eden_ecs/tracy
```

### Step 3 — Connect

Open the Tracy GUI and click **Connect**.  Plots recorded by eden_ecs include:

| Plot name | Unit | Description |
|-----------|------|-------------|
| `sakib_index` | ratio | Routing-quality metric (0 – 2) |
| `flow_entropy` | bits | Shannon entropy of flow distribution |
| `weaver_policy_us` | µs | Weaver policy tick duration |
| `grid_rebuild_us` | µs | Spatial grid rebuild latency |
| `entity_count` | count | Live entity count |
| `hot_memory_mb` | MB | Active memory usage |

---

## 9. Cross-compilation

### Target: `aarch64-unknown-linux-gnu` (ARM64 Linux)

```sh
rustup target add aarch64-unknown-linux-gnu
sudo apt install -y gcc-aarch64-linux-gnu

cargo build --release -p eden_ecs \
    --target aarch64-unknown-linux-gnu
```

Add to `.cargo/config.toml` if the linker is not found automatically:

```toml
[target.aarch64-unknown-linux-gnu]
linker = "aarch64-linux-gnu-gcc"
```

### Target: `wasm32-unknown-unknown` (experimental)

```sh
rustup target add wasm32-unknown-unknown
cargo build -p eden_ecs --target wasm32-unknown-unknown \
    --no-default-features
```

> WASM support is experimental.  The `telemetry_ffi` and `ffi_f16` modules
> disable their C-ABI exports under WASM to avoid ABI mismatches.

---

## 10. Troubleshooting

### `error: linker cc not found`

Install a C linker:

```sh
# Debian/Ubuntu
sudo apt install -y build-essential
# Fedora
sudo dnf groupinstall -y "Development Tools"
```

### `pkg-config: command not found`

```sh
sudo apt install -y pkg-config     # Debian/Ubuntu
sudo dnf install -y pkgconf        # Fedora
sudo pacman -S pkgconf             # Arch
```

### `cannot find -lssl` or `cannot find -lcrypto`

```sh
sudo apt install -y libssl-dev     # Debian/Ubuntu
sudo dnf install -y openssl-devel  # Fedora
sudo pacman -S openssl             # Arch
```

### `GLIBC_2.xx not found` (after cross-compiling)

The binary was built against a newer glibc than the target has.  Either:
- Build on a machine with the same (or older) glibc as the target, or
- Use `cargo build --target x86_64-unknown-linux-musl` for a fully static
  binary that embeds musl libc.

```sh
rustup target add x86_64-unknown-linux-musl
sudo apt install -y musl-tools
cargo build --release -p eden_ecs --target x86_64-unknown-linux-musl
```

### Tests fail with `stack overflow` on large graphs

Increase the stack size for the test runner:

```sh
RUST_MIN_STACK=8388608 cargo test -p eden_ecs
```

### `reqwest` TLS errors in CI (no root certificates)

```sh
sudo apt install -y ca-certificates
```

Or set:

```sh
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
```
