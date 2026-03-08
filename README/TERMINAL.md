# Full Terminal Integration — Eden ECS

This guide covers every way to interact with Eden ECS from the terminal:
the **`cosmic_coder.py` agent** (Python REPL + one-shot CLI), the **Cargo
example binaries**, CSV result analysis, and the optional
**EngramObservatory** telemetry bridge.

---

## Table of contents

1. [Requirements](#1-requirements)
2. [cosmic_coder.py overview](#2-cosmic_coderpy-overview)
3. [One-shot CLI reference](#3-one-shot-cli-reference)
4. [Interactive REPL](#4-interactive-repl)
5. [Personalities](#5-personalities)
6. [Cargo example binaries](#6-cargo-example-binaries)
7. [CSV output format](#7-csv-output-format)
8. [Parameter sweeps](#8-parameter-sweeps)
9. [Analyzing saved results](#9-analyzing-saved-results)
10. [EngramObservatory telemetry bridge](#10-engramobservatory-telemetry-bridge)
11. [Pre-build validation hook](#11-pre-build-validation-hook)
12. [Environment variables & paths](#12-environment-variables--paths)
13. [Tips and recipes](#13-tips-and-recipes)

---

## 1. Requirements

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | ≥ 3.9 | The agent uses `argparse`, `csv`, `subprocess`, `pathlib` |
| Rust / Cargo | ≥ 1.75 | Must be on `PATH` |
| `cargo` accessible from the same `PATH` as Python | — | The agent calls `cargo` as a subprocess |

No extra Python packages are required for the core agent.  The optional
**EngramObservatory** integration requires `torch` or `tensorboardX` (see
[Section 10](#10-engramobservatory-telemetry-bridge)).

---

## 2. `cosmic_coder.py` overview

`cosmic_coder.py` lives at `eden_ecs/tools/cosmic_coder.py`.  It is a
self-contained Python terminal agent that:

- **Builds and tests** the `eden_ecs` crate by invoking `cargo` as a
  subprocess.
- **Runs experiments** (`sakib_ab`, `sakib_aba`) and streams `stderr`
  diagnostics to your terminal while capturing `stdout` CSV for analysis.
- **Parses results** from CSV, classifies the learning regime, and prints a
  formatted summary.
- **Sweeps parameters** (cultures × steps × flow-gain) in a grid search and
  ranks configurations by tail-mean ΔSakib.
- **Saves outputs** to a directory of your choice as `.csv` or `.json` files.
- **Bridges** to the optional `EngramObservatory` for live TensorBoard-style
  metric logging.

```
eden_ecs/tools/
└── cosmic_coder.py
```

---

## 3. One-shot CLI reference

Run from the repository root:

```sh
python eden_ecs/tools/cosmic_coder.py [--personality PERS] [--no-color] \
    [--save-dir DIR] COMMAND [args…]
```

### Global flags

| Flag | Default | Description |
|------|---------|-------------|
| `--personality alice\|bunny\|zorel` | `alice` | Output verbosity/style (see [Section 5](#5-personalities)) |
| `--no-color` | off | Disable ANSI colour codes (useful when piping) |
| `--save-dir DIR` | *(none)* | Save CSV/JSON output to `DIR/` |

### `test` — run the test suite

```sh
python eden_ecs/tools/cosmic_coder.py test
```

Equivalent to `cargo test -p eden_ecs`.  Streams output live; exits with the
`cargo` return code.

### `build` — release build

```sh
python eden_ecs/tools/cosmic_coder.py build
```

Equivalent to `cargo build -p eden_ecs --release`.

### `ab` — A/B routing experiment

```sh
python eden_ecs/tools/cosmic_coder.py ab [culture] [steps] [gain] [noise]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `culture` | `engramum_competitive` | Weaver policy: `baseline`, `hebbium`, `engramum`, `engramum_competitive`, `polyakum` |
| `steps` | `6` | Message-passing depth per tick |
| `gain` | `2.0` | Flow gain multiplier |
| `noise` | `0.0` | Box-Muller noise σ added to flows |

**Examples:**

```sh
# Default (engramum_competitive, 6 steps, gain 2.0)
python eden_ecs/tools/cosmic_coder.py ab

# Hebbium with custom gain
python eden_ecs/tools/cosmic_coder.py ab hebbium 6 2.0

# With flow noise
python eden_ecs/tools/cosmic_coder.py ab engramum 6 2.0 0.05

# Compact output
python eden_ecs/tools/cosmic_coder.py --personality bunny ab hebbium
```

Output includes: final Sakib (learning vs frozen), ΔSakib, tail-mean ΔSakib,
max Sakib, and **regime classification**:

| Regime | Condition | Meaning |
|--------|-----------|---------|
| `routing` | Sustained positive ΔSakib | Healthy selective routing |
| `amplifier` | Max Sakib > 1.8, then falls | Runaway potentiation |
| `collapse` | Final Sakib < 0.3, ΔSakib < 0.05 | Network degenerated |

### `aba` — A→B→A engram persistence

```sh
python eden_ecs/tools/cosmic_coder.py aba [n_ticks] [gain]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `n_ticks` | `200` | Ticks per phase (total = 3 × n_ticks) |
| `gain` | `2.0` | Flow gain |

Output: per-culture recovery table (ticks in phase A₂ to reach 90% of peak-A
Sakib).  Faster recovery = stronger engram.

```sh
python eden_ecs/tools/cosmic_coder.py aba 500 2.5
```

### `sweep` — parameter grid search

```sh
python eden_ecs/tools/cosmic_coder.py sweep [culture1 culture2 …] \
    [--steps N …] [--gains F …]
```

```sh
# Default: all 4 cultures × steps {4,6,8} × gains {1.5,2.0,3.0} = 36 runs
python eden_ecs/tools/cosmic_coder.py sweep

# Custom cultures and gains
python eden_ecs/tools/cosmic_coder.py sweep engramum engramum_competitive \
    --steps 4 6 8 --gains 1.5 2.0 3.0

# Zorel personality → regime guidance for each result
python eden_ecs/tools/cosmic_coder.py --personality zorel sweep
```

Prints a ranked top-10 table sorted by tail-mean ΔSakib.  Saves
`sweep_results.json` if `--save-dir` is set.

### `analyze` — parse a saved CSV

```sh
python eden_ecs/tools/cosmic_coder.py analyze path/to/results.csv
```

Auto-detects A/B vs A→B→A format from the CSV header and prints the
appropriate summary.

### `validate` — pre-build integrity check

```sh
python eden_ecs/tools/cosmic_coder.py validate
```

Runs `tools/pre_build_hook.py`.

---

## 4. Interactive REPL

Start the REPL by running `cosmic_coder.py` with no subcommand:

```sh
python eden_ecs/tools/cosmic_coder.py
# or with a personality:
python eden_ecs/tools/cosmic_coder.py --personality zorel
```

You will see the banner:

```
╔══════════════════════════════════════════════════════════╗
║   🌌 COSMIC CODER — EDEN-ECS Terminal Agent             ║
╚══════════════════════════════════════════════════════════╝
Personality : Alice (528 Hz) — Analytical & Structured
Repo root   : /path/to/Ouroboros
…
🌌 Alice>
```

### REPL commands

| Command | Description |
|---------|-------------|
| `test` | `cargo test -p eden_ecs` |
| `build` | `cargo build --release` |
| `ab [culture] [steps] [gain] [noise]` | A/B experiment |
| `aba [n_ticks] [gain]` | A→B→A persistence experiment |
| `sweep [culture1 …]` | Parameter sweep |
| `analyze <file>` | Parse a CSV file |
| `validate` | Run pre-build hook |
| `obs start [log_dir]` | Start EngramObservatory |
| `obs stop` | Stop EngramObservatory |
| `help` | Show command list |
| `q` / `quit` / `exit` | Exit the REPL |

Press `Ctrl-C` or `Ctrl-D` to exit at any time.

---

## 5. Personalities

Personalities control output verbosity without changing the underlying
experiment logic.

| Name | Frequency | Style | Verbosity |
|------|-----------|-------|-----------|
| `alice` (default) | 528 Hz | Analytical & Structured | Full stats: all fields, percentile tables |
| `bunny` | 417 Hz | Quick & Practical | Compact: one-liner ΔSakib + regime |
| `zorel` | 852 Hz | Visionary & Strategic | Full stats + regime-specific guidance |

`zorel` additionally prints actionable guidance for each regime:

| Regime | Guidance |
|--------|----------|
| `collapse` | Try: raise `flow_gain`, reduce `decay_rate`, or increase `alpha` |
| `amplifier` | Try: lower `flow_gain`, reduce `alpha`, or enable noise σ > 0 |
| `routing` | Good: sustained learning gap. Try `engramum_competitive` next. |

---

## 6. Cargo example binaries

The Rust example binaries can also be invoked directly without the Python agent.

### `sakib_ab` — A/B routing comparison

```sh
cargo run -p eden_ecs --example sakib_ab --release -- \
    --culture engramum_competitive \
    --steps 6 \
    --gain 2.0 \
    --noise 0.0 \
    --diagnostics
```

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--culture NAME` | `baseline` | Policy culture |
| `--steps N` | `6` | Message-passing depth per tick |
| `--gain F` | `2.0` | Flow gain multiplier |
| `--noise F` | `0.0` | Box-Muller noise σ |
| `--diagnostics` | off | Emit eigenvalues, clustering, modularity, Gini, sparsity to stderr every 100 ticks |

**Output:** CSV to **stdout**, diagnostics to **stderr**.

```sh
# Capture CSV, show diagnostics live
cargo run -p eden_ecs --example sakib_ab --release -- \
    --culture engramum --diagnostics \
    2>&1 1>results_engramum.csv
```

### `sakib_aba` — A→B→A engram persistence

```sh
cargo run -p eden_ecs --example sakib_aba --release -- [n_ticks] [flow_gain]
# defaults: 2000 ticks/phase, gain 2.0
```

### `competing_paths` — competing-path routing benchmark

```sh
cargo run -p eden_ecs --example competing_paths --release
```

Tests all policy variants (including `polyakum`) on a graph with two
competing routing paths.  Outputs per-tick metrics and a path-dominance
summary to stderr.

### `ablation` — component ablation harness

```sh
cargo run -p eden_ecs --example ablation --release
```

Systematically disables individual policy components to measure their
individual contribution to overall learning performance.

### Redirect patterns

```sh
# CSV to file, diagnostics to terminal
cargo run -p eden_ecs --example sakib_ab --release 2>/dev/null > results.csv

# Both to separate files
cargo run -p eden_ecs --example sakib_ab --release \
    > results.csv 2> diagnostics.log

# Pipe CSV into analysis (e.g. Python)
cargo run -p eden_ecs --example sakib_ab --release 2>/dev/null \
    | python eden_ecs/tools/cosmic_coder.py analyze /dev/stdin
```

---

## 7. CSV output format

### `sakib_ab` CSV

```
tick,sakib_learning,sakib_frozen,culture
0,0.452134,0.452134,engramum_competitive
1,0.459821,0.452044,engramum_competitive
…
```

| Column | Type | Description |
|--------|------|-------------|
| `tick` | int | Simulation tick (0-indexed) |
| `sakib_learning` | f32 | Sakib Index for the learning run |
| `sakib_frozen` | f32 | Sakib Index for the frozen (control) run |
| `culture` | str | Policy name |

### `sakib_aba` CSV

```
tick,phase,culture,sakib,entropy
0,A,engramum,0.451230,2.8901
…
2000,B,engramum,0.382001,3.1204
…
4000,A2,engramum,0.440998,2.9102
```

| Column | Type | Description |
|--------|------|-------------|
| `tick` | int | Global tick (phase A: 0..n, B: n..2n, A₂: 2n..3n) |
| `phase` | str | `A`, `B`, or `A2` |
| `culture` | str | Policy name |
| `sakib` | f32 | Sakib Index |
| `entropy` | f32 | Flow entropy (bits) |

---

## 8. Parameter sweeps

The sweep command runs all combinations of cultures × steps × gains and
ranks by tail-mean ΔSakib.  Use `--save-dir` to persist results:

```sh
python eden_ecs/tools/cosmic_coder.py \
    --personality zorel \
    --save-dir ./runs/sweep_001 \
    sweep engramum engramum_competitive \
    --steps 4 6 8 \
    --gains 1.5 2.0 2.5 3.0
```

Output example:

```
#    Culture                   Stp   Gain   ΔSakib(tail)  Regime
─────────────────────────────────────────────────────────────────
1    engramum_competitive       8    3.0      +0.3812  routing
2    engramum_competitive       6    2.5      +0.3601  routing
3    engramum                   8    2.5      +0.2944  routing
…
```

The JSON file at `runs/sweep_001/sweep_results.json` contains all fields
including elapsed time per run.

---

## 9. Analyzing saved results

Any previously saved CSV can be re-analyzed without re-running the experiment:

```sh
# Auto-detect format
python eden_ecs/tools/cosmic_coder.py analyze runs/sweep_001/ab_engramum_competitive_s6_g2.0_n0.0.csv

# From the REPL
🌌 Alice> analyze runs/sweep_001/ab_engramum_competitive_s6_g2.0_n0.0.csv
```

---

## 10. EngramObservatory telemetry bridge

The `EngramObservatory` provides a TensorBoard-compatible live metric stream.
It is optional — the agent works fully without it.

### Requirements

```sh
pip install torch tensorboard       # or tensorboardX
```

The observatory module lives at `arc_agi_3/engram_observatory.py` in the
repository root.

### Start from the REPL

```sh
🌌 Alice> obs start runs/cosmic_coder
  ✓ EngramObservatory started (log_dir=runs/cosmic_coder)

🌌 Alice> ab engramum_competitive
  # … experiment runs, Sakib curve is pushed to the observatory …

🌌 Alice> obs stop
  ✓ EngramObservatory stopped
```

### View in TensorBoard

```sh
tensorboard --logdir runs/cosmic_coder
# Open http://localhost:6006 in a browser
```

### Observatory push protocol

After each `sakib_ab` run the agent pushes a downsampled (10×) version of
the learning Sakib curve:

```python
for step, val in enumerate(sakib_values[::10]):
    observatory.push(activations=np.array([val]), step=step)
```

---

## 11. Pre-build validation hook

The validation hook runs a series of integrity checks before a build to catch
configuration drift early:

```sh
python eden_ecs/tools/cosmic_coder.py validate
# or directly:
python eden_ecs/tools/pre_build_hook.py
```

---

## 12. Environment variables & paths

| Variable / Path | Default | Description |
|----------------|---------|-------------|
| `PATH` | system | Must contain `cargo` and `rustc` |
| `REPO_ROOT` | auto-detected from `cosmic_coder.py` location | Repository root |
| `EDEN_ECS_DIR` | `REPO_ROOT/eden_ecs` | Crate directory |
| `runs/` | `.gitignore`d | Default directory for local artefacts |
| `RUST_MIN_STACK` | system default | Increase for large-graph tests (e.g. `8388608`) |

---

## 13. Tips and recipes

### Run all four cultures back-to-back and save CSV

```sh
for culture in baseline hebbium engramum engramum_competitive; do
    python eden_ecs/tools/cosmic_coder.py \
        --save-dir ./runs/ab_all \
        ab "$culture"
done
```

### Quick sanity check (compact, no colour)

```sh
python eden_ecs/tools/cosmic_coder.py \
    --personality bunny --no-color \
    ab engramum_competitive
```

### Full engram persistence run with save

```sh
python eden_ecs/tools/cosmic_coder.py \
    --save-dir ./runs/aba_full \
    aba 2000 2.0
```

### Watch Sakib curve in real-time with `watch`

```sh
# Terminal 1: run and tee to file
cargo run -p eden_ecs --example sakib_ab --release 2>/dev/null \
    | tee /tmp/sakib_live.csv

# Terminal 2: watch tail
watch -n1 tail -20 /tmp/sakib_live.csv
```

### Use Tracy for live profiling alongside cosmic_coder

```sh
# Terminal 1: start Tracy GUI (see LINUX.md §8 or MACOS.md §8)
./Tracy-release

# Terminal 2: run with tracy feature
cargo run -p eden_ecs --example sakib_aba --release \
    --features eden_ecs/tracy
```

### Persist a sweep for later comparison

```sh
python eden_ecs/tools/cosmic_coder.py \
    --save-dir ./runs/sweep_$(date +%Y%m%d_%H%M%S) \
    sweep
```
