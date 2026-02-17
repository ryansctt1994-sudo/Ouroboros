# Quick Start Guide - Android RustOracle

## 5-Minute Setup

### 1. Prerequisites Check
```bash
# Check Rust installation
rustc --version

# Check Android SDK
echo $ANDROID_HOME

# If not installed, see main README.md
```

### 2. Clone and Build
```bash
# Navigate to project
cd android-rustoracle

# Build Rust library (one-time setup)
./build-rust.sh

# Build Android APK
./gradlew assembleDebug
```

### 3. Install and Run
```bash
# Install on connected device/emulator
./gradlew installDebug

# Or use adb directly
adb install app/build/outputs/apk/debug/app-debug.apk
```

### 4. Run First Simulation

**In the app**:
1. Use default parameters (already configured)
2. Click "Run Simulation"
3. Verify green ✓ for latency target
4. Click "Stability Test"
5. Verify 100% success rate

**Expected output**:
```
Mean Latency: ~15-20 μs
P99 Latency: ~25-45 μs
Target (<100μs): ✓ MET
```

## Common Operations

### Rebuild Rust Only
```bash
cd rustoracle
cargo build --release
cd ..
./build-rust.sh  # Copies to jniLibs
```

### Run Rust Tests
```bash
cd rustoracle
cargo test
```

### Clean Build
```bash
./gradlew clean
rm -rf rustoracle/target
rm -rf app/src/main/jniLibs
```

### View Logs
```bash
adb logcat | grep -i rustoracle
```

## Configuration Quick Reference

### Token Range
- **Min Token**: Minimum allowed value (inclusive)
- **Max Token**: Maximum allowed value (inclusive)
- **Example**: 0-1000 accepts tokens 0, 1, 2, ..., 1000

### Enforcement Mode
- **Mask Mode ON**: Replace unsafe tokens with mask value
  - Input: [50, -1, 500, 2000]
  - Output: [50, 0, 500, 0] (if mask_value=0)
  
- **Mask Mode OFF**: Reject unsafe tokens (exclude from output)
  - Input: [50, -1, 500, 2000]
  - Output: [50, 500]

### Batch Parameters
- **Tokens per Batch**: Number of tokens validated together
  - Small (10-100): Lower latency, more overhead
  - Medium (100-500): Optimal balance
  - Large (1000+): Higher throughput, higher latency

- **Batch Count**: Number of batches in simulation
  - Affects total test duration
  - More batches → better P99 accuracy

### Unsafe Ratio
- **0%**: All tokens are safe (best case)
- **20-30%**: Realistic mixed workload
- **50%**: Balanced safe/unsafe
- **100%**: All tokens unsafe (worst case)

## Troubleshooting

### "Library not found"
```bash
# Rebuild Rust library
./build-rust.sh

# Check libraries exist
ls -R app/src/main/jniLibs/
```

### High Latency (>100μs)
- Switch to physical device (emulators are slower)
- Ensure Rust built with --release flag
- Reduce batch size

### App Crashes
```bash
# Check native logs
adb logcat | grep -E '(FATAL|rust|rustoracle)'

# Check memory
adb shell dumpsys meminfo com.aiospandora.rustoracle
```

### Build Errors
```bash
# Update Rust
rustup update

# Re-add Android targets
rustup target add aarch64-linux-android armv7-linux-androideabi

# Clean and rebuild
./gradlew clean
./build-rust.sh
./gradlew assembleDebug
```

## Performance Tips

### Optimal Settings for Validation
```
Min Token: 0
Max Token: 1000
Mask Mode: true
Mask Value: 0
Tokens per Batch: 100
Batch Count: 10
Unsafe Ratio: 25%
```

### Stress Test Settings
```
Tokens per Batch: 500
Batch Count: 50
Unsafe Ratio: 30%
```

### Maximum Throughput
```
Tokens per Batch: 1000
Batch Count: 100
```

## API Quick Reference

### RustOracle
```kotlin
// Create
val oracle = RustOracle.create(min, max, maskMode, maskValue)

// Validate
val result = oracle.validateBatch(tokens)
println("Latency: ${result.latencyUs} μs")
println("Output: ${result.validatedTokens.contentToString()}")

// Stats
val stats = oracle.getStats()
println("Blocked: ${stats.blockedTokens}")
println("Masked: ${stats.maskedTokens}")

// Cleanup
oracle.destroy()
```

### TokenStreamSimulator
```kotlin
val simulator = TokenStreamSimulator(
    safeMin = 0,
    safeMax = 1000,
    unsafeRatio = 0.25  // 25% unsafe
)

val tokens = simulator.generateBatch(100)
```

### SimulationRunner
```kotlin
val runner = SimulationRunner(oracle, simulator)

val result = runner.runSimulation(
    tokensPerBatch = 100,
    batchCount = 10
)

println("P99 Latency: ${result.p99LatencyUs} μs")
```

## Success Criteria Checklist

- [ ] Rust tests pass: `cargo test`
- [ ] Android builds: `./gradlew assembleDebug`
- [ ] App installs and launches
- [ ] Simulation completes without errors
- [ ] P99 latency < 100μs (green ✓)
- [ ] Stability test: 100% success rate
- [ ] Token statistics match expected unsafe ratio
- [ ] No crashes or memory leaks

## Next Steps

1. ✅ Complete quick start validation
2. 📖 Read VALIDATION_GUIDE.md for comprehensive testing
3. 📊 Review IMPLEMENTATION_SUMMARY.md for architecture
4. 🔧 Customize parameters for your use case
5. 🚀 Integrate into production systems

## Support

- **Documentation**: See README.md and VALIDATION_GUIDE.md
- **Architecture**: See IMPLEMENTATION_SUMMARY.md
- **Code**: Well-commented Rust and Kotlin source
- **Issues**: Check repository issue tracker

---

**Getting Started Time**: ~5 minutes  
**Full Validation Time**: ~15 minutes  
**Understanding Time**: ~1 hour with all documentation
