# macOS Setup Guide — Eden ECS

This guide covers installing dependencies, building the `eden_ecs` crate, and
running experiments natively on **macOS** (Intel and Apple Silicon).  If you
prefer a full Linux environment on your Mac, see [LIMA.md](LIMA.md) for the
Lima VM approach.

---

## Table of contents

1. [Supported macOS versions](#1-supported-macos-versions)
2. [Install Xcode Command Line Tools](#2-install-xcode-command-line-tools)
3. [Install Homebrew](#3-install-homebrew)
4. [Install system dependencies](#4-install-system-dependencies)
5. [Rust toolchain](#5-rust-toolchain)
6. [Clone the repository](#6-clone-the-repository)
7. [Build](#7-build)
8. [Test](#8-test)
9. [Run examples](#9-run-examples)
10. [Benchmarks](#10-benchmarks)
11. [Tracy profiling on macOS](#11-tracy-profiling-on-macos)
12. [Python terminal agent (cosmic_coder)](#12-python-terminal-agent-cosmic_coder)
13. [Apple Silicon notes](#13-apple-silicon-notes)
14. [Cross-compilation from macOS](#14-cross-compilation-from-macos)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. Supported macOS versions

| macOS version | Intel (x86_64) | Apple Silicon (aarch64) |
|---------------|----------------|------------------------|
| 14 Sonoma | ✅ | ✅ |
| 13 Ventura | ✅ | ✅ |
| 12 Monterey | ✅ | ✅ |
| 11 Big Sur | ✅ (Xcode 13+) | ✅ (Rosetta not needed) |
| 10.15 Catalina | ⚠ (may work) | N/A |

> **Apple Silicon:** Eden ECS compiles and runs natively as `aarch64-apple-darwin`.
> Rosetta 2 is **not** required.

---

## 2. Install Xcode Command Line Tools

Xcode CLT provides the C compiler and linker that Rust's build system requires.

```sh
xcode-select --install
```

A GUI dialog will appear asking you to install.  Accept and wait (~5 minutes).

Verify:

```sh
xcode-select -p
# /Library/Developer/CommandLineTools
cc --version
# Apple clang version 15.0.0 …
```

If you already have the full Xcode app installed:

```sh
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

---

## 3. Install Homebrew

[Homebrew](https://brew.sh) is the standard macOS package manager.

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the on-screen post-install instructions to add Homebrew to your `PATH`
(especially important on Apple Silicon where Homebrew installs to
`/opt/homebrew`).

Verify:

```sh
brew --version
# Homebrew 4.x.x
```

---

## 4. Install system dependencies

```sh
brew update
brew install openssl pkg-config git
```

**Why `openssl`?**  The `reqwest` HTTP client (used by the telemetry bridge)
links against OpenSSL.  Homebrew installs it to a non-standard prefix, so you
may also need to export the following (add to `~/.zshrc` or `~/.bash_profile`):

```sh
# Apple Silicon
export OPENSSL_DIR="$(brew --prefix openssl)"
export PKG_CONFIG_PATH="$(brew --prefix openssl)/lib/pkgconfig"

# Intel (same commands, different resolved path)
export OPENSSL_DIR="$(brew --prefix openssl)"
export PKG_CONFIG_PATH="$(brew --prefix openssl)/lib/pkgconfig"
```

Reload your shell:

```sh
source ~/.zshrc   # or ~/.bash_profile
```

---

## 5. Rust toolchain

### Install via rustup

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Accept the default installation.  Then reload your shell:

```sh
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

## 6. Clone the repository

```sh
git clone https://github.com/AIOSPANDORA/Ouroboros.git
cd Ouroboros
```

The workspace `Cargo.toml` at the root declares `eden_ecs` as a workspace
member.  All `cargo` commands accept `-p eden_ecs` to scope them to the crate.

---

## 7. Build

### Debug build

```sh
cargo build -p eden_ecs
```

### Release build (optimised — use for experiments)

```sh
cargo build --release -p eden_ecs
```

Compiled artefacts are placed in `target/debug/` and `target/release/`.
The shared library is named `libeden_ecs.dylib` on macOS (not `.so`).

### Build with Tracy profiling

```sh
cargo build --release -p eden_ecs --features eden_ecs/tracy
```

See [Section 11](#11-tracy-profiling-on-macos).

---

## 8. Test

```sh
# Full test suite (81+ tests)
cargo test -p eden_ecs

# Show output from passing tests
cargo test -p eden_ecs -- --nocapture

# Run only tests matching a pattern
cargo test -p eden_ecs weaver

# Single named test
cargo test -p eden_ecs test_engramum_competitive_linf_normalization -- --exact
```

All tests should pass.  If you see failures on a fresh checkout, verify that
`openssl` is discoverable (see [Section 4](#4-install-system-dependencies)).

---

## 9. Run examples

### A→B→A engram persistence (flagship experiment)

```sh
cargo run -p eden_ecs --example sakib_aba --release
# With custom parameters:
cargo run -p eden_ecs --example sakib_aba --release -- 2000 2.0
```

### A/B routing comparison

```sh
cargo run -p eden_ecs --example sakib_ab --release
cargo run -p eden_ecs --example sakib_ab --release -- \
    --culture engramum_competitive --diagnostics
```

### Competing-paths experiment

```sh
cargo run -p eden_ecs --example competing_paths --release
```

### Ablation harness

```sh
cargo run -p eden_ecs --example ablation --release
```

### Save results

```sh
# CSV to file, diagnostics to terminal
cargo run -p eden_ecs --example sakib_ab --release \
    2>/dev/null | tee results.csv

# Both streams to separate files
cargo run -p eden_ecs --example sakib_aba --release \
    > results.csv 2> diagnostics.log
```

---

## 10. Benchmarks

```sh
cargo bench -p eden_ecs
```

HTML reports are written to `target/criterion/`.  Open them in Safari or
Chrome:

```sh
open target/criterion/spatial_grid/report/index.html
```

---

## 11. Tracy profiling on macOS

[Tracy](https://github.com/wolfpld/tracy) provides a real-time sampling
profiler with a GUI front-end.

### Build the Tracy GUI on macOS

```sh
brew install cmake glfw freetype capstone

git clone https://github.com/wolfpld/tracy.git
cd tracy/profiler/build/unix

# Intel
make -j$(sysctl -n hw.logicalcpu)

# Apple Silicon (cross-compile is not needed; same Makefile works)
make -j$(sysctl -n hw.logicalcpu)
```

The binary is `./Tracy-release`.  Alternatively, download a pre-built release
from the [Tracy releases page](https://github.com/wolfpld/tracy/releases) if
available for macOS.

### Run Eden ECS with Tracy enabled

```sh
cargo run --release -p eden_ecs --example sakib_aba \
    --features eden_ecs/tracy
```

### Connect

Open `Tracy-release`, click **Connect** (default port 8765).

Plots emitted by Eden ECS:

| Plot | Unit | Description |
|------|------|-------------|
| `sakib_index` | ratio | Routing-quality metric |
| `flow_entropy` | bits | Shannon entropy of the flow distribution |
| `weaver_policy_us` | µs | Policy tick duration |
| `grid_rebuild_us` | µs | Spatial grid rebuild latency |
| `entity_count` | count | Live entity count |
| `hot_memory_mb` | MB | Active memory |

---

## 12. Python terminal agent (`cosmic_coder`)

macOS ships with Python 3 available via Homebrew or the system Python (Xcode
CLT).  The agent works with any Python ≥ 3.9 and has no required third-party
dependencies.

### Verify Python

```sh
python3 --version
# Python 3.11.x
```

### Run one-shot commands

```sh
# From the repository root:
python3 eden_ecs/tools/cosmic_coder.py test
python3 eden_ecs/tools/cosmic_coder.py ab engramum_competitive
python3 eden_ecs/tools/cosmic_coder.py aba 500 2.0
python3 eden_ecs/tools/cosmic_coder.py sweep
```

### Start the interactive REPL

```sh
python3 eden_ecs/tools/cosmic_coder.py
# or with a personality:
python3 eden_ecs/tools/cosmic_coder.py --personality zorel
```

### Optional: EngramObservatory (TensorBoard integration)

```sh
pip3 install torch tensorboard
# Then from the REPL:
# obs start runs/my_experiment
```

See [TERMINAL.md §10](TERMINAL.md#10-engramobservatory-telemetry-bridge) for
full details.

### macOS-specific shell tips

Zsh (the default macOS shell since Catalina) supports all the same redirect
patterns as Bash:

```zsh
# Capture CSV, print diagnostics
cargo run -p eden_ecs --example sakib_ab --release \
    2>&1 1>results.csv

# Tee CSV while watching live
cargo run -p eden_ecs --example sakib_ab --release \
    2>/dev/null | tee results.csv
```

---

## 13. Apple Silicon notes

### Native `aarch64-apple-darwin` target

rustup installs the `aarch64-apple-darwin` target automatically on Apple
Silicon Macs.  All `cargo build` commands work without any extra flags.

### Rosetta 2

Eden ECS does **not** require Rosetta 2.  Do not run `cargo` or `rustc`
under Rosetta — this will produce `x86_64` binaries and may cause subtle
performance issues.

Verify your Rust toolchain is native:

```sh
rustc -vV | grep host
# host: aarch64-apple-darwin   ← correct
# host: x86_64-apple-darwin    ← running under Rosetta (undesirable)
```

If you see `x86_64` on an Apple Silicon machine, reinstall rustup in a
native Terminal (not one opened via Rosetta):

```sh
rustup self uninstall
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Homebrew prefix

On Apple Silicon, Homebrew installs to `/opt/homebrew` (not `/usr/local`).
Always use `$(brew --prefix)` in scripts rather than hard-coding the path:

```sh
export OPENSSL_DIR="$(brew --prefix openssl)"
```

### Memory and performance

Apple Silicon's unified memory architecture makes Eden ECS especially
well-suited:

- The spatial grid and telemetry buffers fit entirely in L2/L3 cache for
  graphs up to ~50 000 edges on M1/M2.
- The release build consistently meets the ≤ 1.2 ms / tick policy target at
  60 Hz on M1 Pro and later.

---

## 14. Cross-compilation from macOS

### Target: `x86_64-apple-darwin` (from Apple Silicon)

```sh
rustup target add x86_64-apple-darwin
cargo build --release -p eden_ecs --target x86_64-apple-darwin
```

### Target: `aarch64-apple-darwin` (from Intel Mac)

```sh
rustup target add aarch64-apple-darwin
cargo build --release -p eden_ecs --target aarch64-apple-darwin
```

> Cross-compiling to macOS from macOS works natively because both targets
> use the same Xcode toolchain.  Signing / notarisation is only required for
> distribution.

### Target: Linux `x86_64-unknown-linux-musl` (from macOS)

```sh
brew install FiloSottile/musl-cross/musl-cross
rustup target add x86_64-unknown-linux-musl

# Tell Cargo to use the musl cross-linker
export CARGO_TARGET_X86_64_UNKNOWN_LINUX_MUSL_LINKER=x86_64-linux-musl-gcc

cargo build --release -p eden_ecs --target x86_64-unknown-linux-musl
```

---

## 15. Troubleshooting

### `error: linker 'cc' not found`

Install Xcode Command Line Tools:

```sh
xcode-select --install
```

### `cannot find -lssl` or OpenSSL-related linker errors

```sh
brew install openssl
export OPENSSL_DIR="$(brew --prefix openssl)"
export PKG_CONFIG_PATH="$(brew --prefix openssl)/lib/pkgconfig"
cargo build -p eden_ecs
```

### `pkg-config: command not found`

```sh
brew install pkg-config
```

### `error[E0463]: can't find crate for …` on aarch64

Your Rust installation may be using an x86_64 toolchain under Rosetta.
Reinstall rustup natively (see [Section 13](#13-apple-silicon-notes)).

### Slow first build

The first build downloads and compiles all dependencies from crates.io.  On a
typical MacBook Pro (M2) this takes ~2–3 minutes for a release build.
Subsequent builds are incremental.

Use `sccache` to persist the compiler cache across clean builds:

```sh
brew install sccache
export RUSTC_WRAPPER=sccache
cargo build --release -p eden_ecs
```

### `dyld: Library not loaded` at runtime

The `libeden_ecs.dylib` may not be on the dynamic linker search path.  Either:

```sh
export DYLD_LIBRARY_PATH="$PWD/target/release:$DYLD_LIBRARY_PATH"
```

Or link statically by changing `crate-type` in `Cargo.toml` to include only
`rlib` for your build.

### Test failures mentioning file descriptors or threads

macOS has a default file descriptor limit of 256.  Raise it for the test
session:

```sh
ulimit -n 4096
cargo test -p eden_ecs
```

### Gatekeeper blocks the Tracy binary

```sh
xattr -dr com.apple.quarantine ./Tracy-release
```
