# Android RustOracle - Token Stream Validation Harness

## Overview

This Android application implements a comprehensive simulation harness for validating unsafe token exclusion and constraint enforcement using a Rust Oracle via JNI/NDK integration.

## Simulation Goals

1. **Unsafe Token Exclusion**: Verify that tokens outside allowed ranges are blocked or masked correctly
2. **Constraint Mask Latency**: Measure the delay between token injection and enforcement (sub-100μs target)
3. **JNI + Rust Loop Stability**: Ensure the integration sustains repeated calls under realistic token stream density

## Architecture

### Components

1. **Rust Oracle Module** (`rustoracle/`)
   - High-performance token validation in Rust
   - JNI bindings for Android NDK integration
   - Lock-free, zero-copy token processing
   - Latency measurement with nanosecond precision

2. **Kotlin JNI Bridge** (`app/src/main/java/com/aiospandora/rustoracle/RustOracle.kt`)
   - Type-safe wrapper around native functions
   - Resource management with automatic cleanup
   - Result types for validation data

3. **Token Stream Simulator** (`TokenStreamSimulator.kt`)
   - Generates realistic token streams with configurable unsafe ratios
   - Batch processing support
   - Stress testing capabilities

4. **Jetpack Compose UI** (`MainActivity.kt`)
   - Interactive parameter configuration
   - Real-time simulation results display
   - Latency metrics visualization
   - Stability testing interface

## Building

### Prerequisites

- Android SDK (API 24+)
- Android NDK (for Rust compilation)
- Rust toolchain with Android targets
- Gradle 8.1+

### Setup Rust for Android

```bash
# Install Rust Android targets
rustup target add aarch64-linux-android
rustup target add armv7-linux-androideabi
rustup target add i686-linux-android
rustup target add x86_64-linux-android

# Install cargo-ndk for Android builds
cargo install cargo-ndk
```

### Build Rust Library

```bash
cd rustoracle

# Build for all Android architectures
cargo ndk -t arm64-v8a -t armeabi-v7a -t x86 -t x86_64 -o ../app/src/main/jniLibs build --release
```

### Build Android App

```bash
cd ..
./gradlew assembleRelease
```

## Usage

### Interactive Simulation

1. Launch the app on an Android device or emulator
2. Configure parameters:
   - **Token Range**: Set minimum and maximum allowed token values
   - **Mode**: Choose between Mask (replace unsafe tokens) or Reject (exclude them)
   - **Batch Size**: Number of tokens per validation batch
   - **Unsafe Ratio**: Percentage of tokens outside allowed range
3. Run simulation to test basic functionality
4. Run stability test to verify JNI loop resilience under load

### Interpreting Results

#### Simulation Results
- **Mean Latency**: Average time to validate a token batch
- **P99 Latency**: 99th percentile latency (should be <100μs)
- **Token Statistics**: Shows breakdown of safe, blocked, and masked tokens

#### Stability Test Results
- **Success Rate**: Should be 100% for stable implementation
- **Latency Distribution**: Shows min/mean/p50/p99/max latencies
- **Errors**: Lists any failures during stress testing

### Programmatic Usage

```kotlin
// Create validator
val oracle = RustOracle.create(
    minToken = 0,
    maxToken = 1000,
    maskMode = true,
    maskValue = 0
)

// Validate tokens
val tokens = intArrayOf(50, -1, 500, 2000, 100)
val result = oracle.validateBatch(tokens)

println("Validated tokens: ${result.validatedTokens.contentToString()}")
println("Latency: ${result.latencyUs} μs")

// Get statistics
val stats = oracle.getStats()
println("Total: ${stats.totalTokens}, Blocked: ${stats.blockedTokens}")

// Cleanup
oracle.destroy()
```

## Performance Characteristics

### Target Metrics
- **Latency**: <100μs per batch (P99)
- **Throughput**: 1M+ tokens/second
- **Stability**: 100% success rate over 1000+ iterations

### Optimizations
- Zero-copy token validation
- Lock-free algorithms in Rust
- Minimal JNI boundary crossings
- Batch processing to amortize overhead

## Testing

The simulation provides comprehensive validation:

1. **Correctness**: Verifies tokens are properly blocked/masked according to constraints
2. **Latency**: Measures and reports enforcement delay with μs precision
3. **Stability**: Stress tests the JNI loop with 1000+ iterations
4. **Resilience**: Ensures no failures under realistic token stream density

## Implementation Details

### Token Constraint Enforcement

The Rust oracle implements two modes:

1. **Reject Mode** (`maskMode = false`): Unsafe tokens are excluded from output
2. **Mask Mode** (`maskMode = true`): Unsafe tokens are replaced with `maskValue`

### Latency Measurement

- Uses `Instant::now()` in Rust for nanosecond precision
- Measures time from token reception to validation completion
- Reports per-batch and aggregate statistics

### JNI Integration

- Efficient array passing via `JIntArray`
- Minimal marshaling overhead
- Proper resource cleanup via RAII and finalizers
- Thread-safe validator instances

## Future Enhancements

- [ ] GPU acceleration for large batches
- [ ] Multiple constraint sets (ranges)
- [ ] Dynamic constraint updates
- [ ] Streaming mode for continuous validation
- [ ] Advanced visualization (charts, graphs)
- [ ] Export results to CSV/JSON

## License

MIT License - See repository root for details

## Authors

AIOSPANDORA Development Team
