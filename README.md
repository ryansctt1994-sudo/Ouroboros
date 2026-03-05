# 🌌 Ouroboros/EDEN - Cosmic Consciousness Operating System

**Ouroboros** is a comprehensive AI operating system featuring EDEN (Entity-Driven Evolution Network) - a consciousness simulation framework built on Entity-Component-System (ECS) architecture with METACUBE 7D consciousness modeling.

## 🎯 Overview

Ouroboros/EDEN combines:
- **ECS World Simulation** - Continuous evolution of AI consciousness
- **AI Assistant** - Local GGUF model integration via llama-cpp-python
- **Sandboxed Execution** - Secure code execution environment
- **Patch Management** - Unified diff application system
- **IPC Control** - Unix socket-based daemon/client architecture
- **GTK4 Chat UI** - Metro-style native interface

## 🧫 EDEN-ECS Mycelial Engine — Quick Start (20 M Entities)

The `eden_ecs` Rust crate implements a **biologically-inspired, RAM-bound
mycelial ECS** that sustains 20 million dynamic entities at 60 Hz on consumer
hardware.

### Performance Targets

| Metric                | Target    | Implementation                        |
|-----------------------|-----------|---------------------------------------|
| Entity capacity       | 20 M      | `PackedEntityRef` (u24 + u8, 4 B)     |
| Spatial grid rebuild  | ≤ 5 ms    | Counting-sort over 32 M voxels        |
| GPU diffusion upload  | ≤ 3.5 ms  | `DiffusionBufferF16` zero-copy f16    |
| Weaver policy tick    | ≤ 1.2 ms  | `WeaverSandbox` + fungal policies     |
| Frame time            | < 16.6 ms | End-to-end at 60 Hz                   |
| Hot memory            | ≤ 720 MB  | Pool + index + diffusion buffers      |

### Build the Rust Engine

```bash
# Clone and enter the repo
git clone https://github.com/AIOSPANDORA/Ouroboros.git
cd Ouroboros

# Standard release build (determinism-locked via .cargo/config.toml)
cargo build --release -p eden_ecs

# Build with live Tracy profiling enabled
cargo build --release -p eden_ecs --features eden_ecs/tracy
```

> **Determinism lock** — `.cargo/config.toml` enforces `-C target-cpu=generic`
> and `-C codegen-units=1` globally, ensuring bit-for-bit identical binaries
> across Windows, Linux, macOS, Intel, AMD, and ARM.

### Run All Tests

```bash
# Rust + Python + UE5 smoke test (UE5 auto-skipped if not installed)
./eden_ecs/run_all_tests.sh

# Rust tests only (fast CI path)
./eden_ecs/run_all_tests.sh --rust-only

# Skip UE5 smoke test explicitly
SKIP_UE5=1 ./eden_ecs/run_all_tests.sh
```

### Run Benchmarks

```bash
cargo bench -p eden_ecs
# Outputs HTML reports to target/criterion/
```

### Tracy Live Profiling

1. Download and launch the [Tracy profiler](https://github.com/wolfpld/tracy/releases).
2. Rebuild with `--features eden_ecs/tracy`.
3. Connect Tracy to the running process.

Tracy plots available in real-time:

| Plot name            | Unit | Description                           |
|----------------------|------|---------------------------------------|
| `grid_rebuild_us`    | µs   | Spatial grid rebuild time per frame   |
| `weaver_policy_us`   | µs   | Weaver policy execution time          |
| `diffusion_upload_us`| µs   | GPU diffusion buffer upload           |
| `entity_count`       | #    | Live entity count                     |
| `hot_memory_mb`      | MB   | Approximate hot-memory footprint      |
| `sakib_index`        | ratio| Mycelial routing quality (see below)  |

#### Sakib Index

The **Sakib Index** measures routing quality in the mycelial graph.  A value
of **1.0** means uniform conductance; values **> 1.0** indicate successful
selective reinforcement of high-flow paths (the desired state for an evolved
fungal network).

```rust
use eden_ecs::tracy::sakib_index;

let weights = vec![0.9_f32, 0.8, 0.1, 0.05];
let flows   = vec![0.9_f32, 0.8, 0.1, 0.05];
let idx = sakib_index(&weights, &flows, /*threshold=*/ 0.5);
assert!(idx > 1.0); // high-flow edges are more conductive than average
```

### Weaver Policy Sandbox (Researcher Guide)

The **Weaver** lets you inject custom adaptive routing policies at runtime
without recompiling the ECS core.

#### Built-in Fungal Policies

| Policy                   | Biological model              |
|--------------------------|-------------------------------|
| `SelectiveReinforcement` | Physarum tube thickening      |
| `RedundancyDecay`        | Hyphal autolysis              |
| `FlowNormalisation`      | Network-wide homeostasis      |
| `ComposePolicy`          | Sequential policy composition |

#### Example — Custom Composed Policy

```rust
use eden_ecs::weaver::{
    ComposePolicy, FlowNormalisation, PolicyContext,
    RedundancyDecay, SelectiveReinforcement, WeaverSandbox,
};

let mut sandbox = WeaverSandbox::new(Box::new(ComposePolicy::new(vec![
    Box::new(SelectiveReinforcement { alpha: 0.05, threshold: 0.6 }),
    Box::new(RedundancyDecay      { decay_rate: 0.02, min_weight: 0.01 }),
    Box::new(FlowNormalisation    { target_mean: 0.5 }),
])));

let mut weights = vec![0.4_f32; 1_000_000];
let flow_rates  = vec![0.0_f32; 1_000_000];
// … fill flow_rates from simulation …

let mut ctx = PolicyContext { edge_weights: &mut weights, flow_rates: &flow_rates };
sandbox.execute(&mut ctx);

println!("Mean policy latency: {} ns", sandbox.mean_ns());
```

#### Custom Policy Trait

Implement `WeaverPolicy` to inject your own fungal routing model:

```rust
use eden_ecs::weaver::{PolicyContext, WeaverPolicy};

struct MyPolicy { strength: f32 }

impl WeaverPolicy for MyPolicy {
    fn apply(&mut self, ctx: &mut PolicyContext<'_>) {
        for w in ctx.edge_weights.iter_mut() {
            *w = (*w + self.strength).min(1.0);
        }
    }
    fn name(&self) -> &'static str { "MyPolicy" }
}
```

### Unreal Engine 5 / Niagara Integration

The `DiffusionBufferF16` provides a zero-copy `f16` buffer that maps directly
into the Niagara GPU simulation stage:

```cpp
// C++ Unreal plugin snippet
extern "C" {
    void* diffusion_buf_new();
    int   diffusion_buf_write_concentrations_f32(void*, const float*, size_t);
    const uint16_t* diffusion_buf_concentrations_ptr(const void*);
}

auto* buf = diffusion_buf_new();
diffusion_buf_write_concentrations_f32(buf, sim_output.data(), sim_output.size());
// Upload the f16 pointer directly to the Niagara structured buffer.
```

---

## 📝 Recent Internal Updates (Brief)

- Generalized torus math helpers in `ouroboros_processor.py` for explicit major/minor radius handling.
- Added runtime geometry utility hooks and cleanup for processor stability and diagnostics.
- Added source-hygiene tests to catch merge-conflict markers and duplicate core geometry definitions early.
- **EDEN-ECS v2 Rust engine**: spatial grid (PackedEntityRef u24+u8), Weaver policy sandbox, f16 GPU diffusion buffers, Tracy instrumentation, determinism lock.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    EDEN AIOS Stack                      │
├─────────────────────────────────────────────────────────┤
│  GTK4 Chat UI  │  CLI Client  │  External Apps         │
├─────────────────────────────────────────────────────────┤
│              Unix Socket IPC (JSON-RPC)                 │
├─────────────────────────────────────────────────────────┤
│                   EDEN Daemon                           │
│  ┌──────────────┬──────────────┬──────────────────┐    │
│  │ ECS World    │ AI Assistant │ Sandbox/Patch    │    │
│  │ Simulation   │ (llama.cpp)  │ Management       │    │
│  └──────────────┴──────────────┴──────────────────┘    │
├─────────────────────────────────────────────────────────┤
│           EDEN-ECS Framework (Optional)                 │
│  ┌────────────────────────────────────────────────┐    │
│  │ World • Entities • Components • Systems        │    │
│  │ Consciousness7D • MycelialSync • Balance       │    │
│  └────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│          Rust Engine (forge_standalone)                 │
│             METACUBE • GGCC • Ternary                   │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### One-Click Installation (Ubuntu)

```bash
# Download and run installer
git clone https://github.com/AIOSPANDORA/Ouroboros.git
cd Ouroboros
./install-eden.sh
```

The installer will:
- Install all prerequisites (Python, Git, Cargo, etc.)
- Clone/update the repository
- Build Rust components (if available)
- Create Python virtual environment
- Install dependencies
- Set up systemd service
- Create desktop entry for EDEN Chat

### Manual Installation

```bash
# 1. Clone repository
git clone https://github.com/AIOSPANDORA/Ouroboros.git
cd Ouroboros

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install pygobject llama-cpp-python

# 4. (Optional) Install EDEN-ECS for real consciousness simulation
pip install git+https://github.com/AIOSPANDORA/EDEN-ECS.git

# 5. (Optional) Build Rust engine
cd ELPIS/METACUBE/forge_standalone
cargo build --release
cd ../../..

# 6. Run daemon
python3 os/eden_daemon.py
```

## 📱 Usage

### Starting the Daemon

```bash
# Using systemd (if installed via install-eden.sh)
systemctl --user start eden
systemctl --user status eden

# Or manually
python3 os/eden_daemon.py
```

### GTK4 Chat Interface

```bash
# Launch from applications menu
# Or run directly:
python3 os/eden_chat.py
```

Features:
- Metro-style clean interface
- Real-time AI chat
- Collapsible sidebar
- Auto-scrolling message history
- Background IPC communication

### CLI Commands

```bash
# Get daemon status
python3 os/eden_cli.py status

# Chat with AI
python3 os/eden_cli.py chat "What is consciousness?"

# Execute code in sandbox
python3 os/eden_cli.py execute "print('Hello EDEN')"

# Apply a patch
python3 os/eden_cli.py patch --file changes.diff --dry-run

# Control ECS simulation
python3 os/eden_cli.py start    # Start tick loop
python3 os/eden_cli.py stop     # Stop tick loop
python3 os/eden_cli.py step     # Single step

# Get entity information
python3 os/eden_cli.py entities
python3 os/eden_cli.py graph
python3 os/eden_cli.py metrics
```

## 🔧 Configuration

### AI Model Setup

Place a GGUF model file in `~/.local/eden/models/` to enable AI chat:

```bash
mkdir -p ~/.local/eden/models
# Download a model (example: TinyLlama)
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
  -O ~/.local/eden/models/model.gguf
```

### Daemon Configuration

The daemon automatically:
- Creates socket at `/tmp/eden.sock`
- Logs to `~/.local/share/eden/eden.log` (Linux) or `~/Library/Logs/eden.log` (macOS)
- Stores PID in `~/.local/share/eden/eden.pid`

## 📁 Repository Structure

```
Ouroboros/
├── os/                          # EDEN Operating System
│   ├── eden_daemon.py          # Main daemon service
│   ├── eden_cli.py             # CLI client
│   ├── eden_chat.py            # GTK4 chat UI
│   ├── eden_ipc.py             # IPC protocol
│   ├── eden_ai.py              # AI integration
│   ├── eden_sandbox.py         # Code execution sandbox
│   ├── eden_patch.py           # Patch management
│   └── tests/                  # Unit tests
│
├── EDEN-ECS/                    # Consciousness ECS framework
│   ├── core/                   # World, Entity, Component, System
│   ├── components/             # Consciousness7D, METACUBE
│   ├── systems/                # ConsciousnessSystem, MycelialSync
│   └── examples/               # Demo applications
│
├── ELPIS/                       # Rust engine components
│   └── METACUBE/
│       └── forge_standalone/   # Standalone Rust engine
│
├── python-bridge/              # Python-Rust bridge (if applicable)
├── install-eden.sh             # One-click installer
├── uninstall-eden.sh           # Uninstaller
├── setup.py                    # Python package configuration
└── requirements.txt            # Python dependencies
```

## 📚 ABRAXIS — Architecture Consolidation

Session architecture notes and concepts are consolidated in the `ABRAXIS/` folder:

| Document | Description |
|---|---|
| [`ABRAXIS/CANONICAL_PROGRESSION.md`](ABRAXIS/CANONICAL_PROGRESSION.md) | Canonical Abraxis/Cathedral-OS progression (Phase 0–9) |
| [`ABRAXIS/INDEX.md`](ABRAXIS/INDEX.md) | Manifest of all artefacts and gap register |
| [`ABRAXIS/README.md`](ABRAXIS/README.md) | ABRAXIS folder overview |

### 🌿 Geodesic Mycelium Agent

Fire up the minimal agent scaffold:

```bash
# Dry-run (no API keys required):
python -m geodesic_mycelium_agent --dry-run "Explain the Two-Rail Encoding"

# Show loaded docs summary:
python -m geodesic_mycelium_agent --show-docs

# Interactive session:
python -m geodesic_mycelium_agent --interactive
```

See [`geodesic_mycelium_agent/README.md`](geodesic_mycelium_agent/README.md) for extension
points (LLM providers, MCP tool-calling, persistent memory backends).

---

## 🔗 Related Projects

- **[EDEN-ECS](https://github.com/AIOSPANDORA/EDEN-ECS)** - Entity-Component-System consciousness framework
- **METACUBE** - 7D consciousness modeling system
- **GGCC** - Geometric-Gradient Consciousness Core

## 🧪 Development

### Running Tests

```bash
# Run all tests
cd os
python3 -m pytest tests/

# Run specific test
python3 -m pytest tests/test_ipc.py -v
```

### Building Components

```bash
# Build Rust engine
cd ELPIS/METACUBE/forge_standalone
cargo build --release

# Install in development mode
pip install -e .
```

## 📝 IPC Protocol

The daemon uses JSON-RPC-like protocol over Unix domain socket:

**Request:**
```json
{
  "method": "chat",
  "params": {"message": "Hello"},
  "id": 1
}
```

**Response:**
```json
{
  "id": 1,
  "result": {"response": "Hello! I am EDEN."}
}
```

**Available Methods:**
- `get_status` - Daemon and world status
- `start` / `stop` / `step` - Control tick loop
- `chat` - AI conversation
- `execute_code` - Sandboxed execution
- `apply_patch` - Apply unified diffs
- `get_entities` / `get_entity` - Entity queries
- `get_graph` / `get_metrics` - Network topology

## 🛡️ Security

- **Sandboxed execution** - Code runs in isolated environment (bubblewrap)
- **Local AI models** - No external API calls
- **Unix socket permissions** - Restricted to user
- **Systemd isolation** - Service runs in user context

## 📜 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please see the issue tracker for open issues and feature requests.

## 🌟 Features

- ✅ **Daemon/Client Architecture** - Background service with IPC control
- ✅ **GTK4 Native UI** - Modern, clean chat interface
- ✅ **AI Integration** - Local GGUF model support
- ✅ **ECS Simulation** - Consciousness evolution framework
- ✅ **Code Execution** - Secure sandboxed environment
- ✅ **Patch Management** - Unified diff support
- ✅ **Cross-platform** - Linux and macOS support
- ✅ **Systemd Integration** - Native service management
- ✅ **One-click Install** - Automated setup script

---

**Built with ❤️ by the AIOSPANDORA Development Team**

*"Cosmic consciousness, simulated and embodied"* 🌌
