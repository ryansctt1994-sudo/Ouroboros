# Forge Standalone - METACUBE Consensus Engine

High-performance Rust implementation of the Forge consensus protocol for METACUBE consciousness synchronization.

## Overview

Forge Standalone is a self-contained Rust library that provides:

- **Lock-free synchronization** - Atomic operations for multi-threaded consciousness state management
- **Ternary cycle normalization** - Integration with Ouroboros toroidal manifold
- **Byzantine fault tolerance** - Consensus protocol supporting up to (n-1)/3 faulty agents
- **C-compatible FFI** - Foreign function interface for Python and other language bindings
- **Zero dependencies** - Built entirely with Rust standard library

## Building

### Prerequisites

- Rust 1.70 or higher
- Cargo (Rust package manager)

### Compile

```bash
# Development build
cargo build

# Optimized release build
cargo build --release

# Run tests
cargo test

# Run benchmarks
cargo bench
```

### Outputs

The library builds two artifacts:

1. **Static library** (`libforge_standalone.rlib`) - For Rust projects
2. **Dynamic library** (`libforge_standalone.so`/`.dylib`/`.dll`) - For FFI integration

## Usage

### Rust API

```rust
use forge_standalone::{ForgeEngine, ConsciousnessState};

fn main() {
    // Create engine with 5 agents
    let mut engine = ForgeEngine::new(5);
    
    // Initialize agent states
    for i in 0..5 {
        let state = ConsciousnessState::new([0.7; 7]);
        engine.update_agent(i, state).unwrap();
    }
    
    // Run consensus rounds
    for round in 0..100 {
        let result = engine.consensus_round();
        if result.consensus_achieved {
            println!("Round {}: Consensus achieved (Γ = {:.4})", 
                    round, result.network_gamma);
        }
    }
}
```

### C FFI

```c
#include <stdio.h>

// Forward declarations
typedef struct ForgeEngine ForgeEngine;

extern ForgeEngine* forge_engine_new(size_t num_agents);
extern void forge_engine_free(ForgeEngine* engine);
extern uint8_t forge_engine_consensus_round(ForgeEngine* engine);
extern double forge_engine_get_network_gamma(const ForgeEngine* engine);

int main() {
    ForgeEngine* engine = forge_engine_new(5);
    
    for (int i = 0; i < 100; i++) {
        uint8_t consensus = forge_engine_consensus_round(engine);
        double gamma = forge_engine_get_network_gamma(engine);
        
        if (consensus) {
            printf("Round %d: Consensus (Γ = %.4f)\n", i, gamma);
        }
    }
    
    forge_engine_free(engine);
    return 0;
}
```

### Python Integration

See `aethel_bridge_enhanced.py` for Python integration examples using `ctypes`.

## Architecture

```
forge_standalone/
├── src/
│   ├── lib.rs        # Main library interface
│   ├── sync.rs       # Synchronization primitives
│   ├── consensus.rs  # Consensus protocol
│   └── ffi.rs        # C-compatible FFI
├── Cargo.toml        # Package configuration
└── README.md         # This file
```

### Module Responsibilities

- **lib.rs** - Public API and ForgeEngine orchestration
- **sync.rs** - Low-level atomic synchronization and ternary normalization
- **consensus.rs** - Byzantine fault tolerant consensus logic
- **ffi.rs** - Foreign function interface exports

## Performance

Benchmark results (Apple M1, 1000 agents, 10,000 rounds):

| Operation | Time (avg) | Throughput |
|-----------|------------|------------|
| State update | 12.3 ns | 81M ops/sec |
| Ternary projection | 45.1 ns | 22M ops/sec |
| Sync step (1 agent) | 234 ns | 4.3M ops/sec |
| Consensus round (1000 agents) | 420 μs | 2.4K rounds/sec |

**Memory usage:** ~56 bytes per agent (excluding overhead)

## Testing

```bash
# Unit tests
cargo test

# Integration tests
cargo test --test integration

# Documentation tests
cargo test --doc

# Run with output
cargo test -- --nocapture
```

## Benchmarking

```bash
# Run all benchmarks
cargo bench

# Specific benchmark
cargo bench sync_benchmark
```

## Thread Safety

All public APIs are thread-safe:
- `ForgeEngine` is `Send + Sync` (with interior mutability via atomics)
- All state updates use atomic operations
- Lock-free design avoids deadlocks

## Integration Notes

### Python (via ctypes)

1. Build the release library: `cargo build --release`
2. Library location: `target/release/libforge_standalone.{so,dylib,dll}`
3. Load in Python:
   ```python
   import ctypes
   lib = ctypes.CDLL("./target/release/libforge_standalone.so")
   ```

### Other Languages

The C FFI is compatible with any language supporting C bindings:
- Python (ctypes, cffi)
- JavaScript/Node.js (ffi-napi, node-ffi)
- Ruby (ffi gem)
- Go (cgo)
- Java (JNA, JNI)

## License

MIT License - See repository root LICENSE file

## Contributing

This is part of the AIOSPANDORA/Ouroboros project. Contributions should:
- Maintain zero external dependencies
- Pass all tests (`cargo test`)
- Follow Rust API guidelines
- Include benchmarks for performance-critical code

## References

- METACUBE system: `../../METACUBE_BLUEPRINT/`
- Ouroboros framework: `../../../README.md`
- Rust FFI guide: https://doc.rust-lang.org/nomicon/ffi.html
