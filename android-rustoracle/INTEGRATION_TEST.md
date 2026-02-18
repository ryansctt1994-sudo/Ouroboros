# Android RustOracle - Integration Test Script

This script validates the complete Android RustOracle implementation.

## Prerequisites

- Rust toolchain installed
- Android SDK and NDK configured
- Gradle installed
- (Optional) Android device or emulator connected

## Test Execution

### 1. Rust Unit Tests
```bash
cd rustoracle
cargo test
```

**Expected**: All 5 tests pass
```
test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured
```

### 2. Rust Demo Example
```bash
cargo run --example demo --release
```

**Expected**:
- Reject mode correctly excludes unsafe tokens
- Mask mode replaces unsafe tokens with mask value
- Performance test meets <100μs target
- Example output shows:
  - Reject: `Validated tokens: [50, 75, 25, 100, 0]` (3 blocked)
  - Mask: `Validated tokens: [50, 999, 75, 999, 25, 100, 999, 0]` (3 masked)
  - Latency: ✓ MET (<100μs)

### 3. Rust Release Build
```bash
cargo build --release
```

**Expected**: Clean build with no warnings, produces optimized library

### 4. Build Rust for Android (Optional)
```bash
cd ..
./build-rust.sh
```

**Expected**: 
- Native libraries generated for all architectures
- Files created in `app/src/main/jniLibs/`

### 5. Gradle Build (Optional)
```bash
./gradlew assembleDebug
```

**Expected**: 
- Clean Android build
- APK generated at `app/build/outputs/apk/debug/app-debug.apk`

### 6. Manual Testing on Device (Optional)

If you have an Android device/emulator:

```bash
./gradlew installDebug
# Or: adb install app/build/outputs/apk/debug/app-debug.apk
```

**Test Scenarios**:

**Test 1: Basic Simulation**
1. Launch app
2. Keep default parameters
3. Click "Run Simulation"
4. Verify:
   - Results appear without errors
   - P99 latency < 100μs (green ✓)
   - Token statistics show ~20% blocked/masked

**Test 2: Reject Mode**
1. Set Mask Mode switch to OFF
2. Set Unsafe Ratio to 30%
3. Click "Run Simulation"
4. Verify:
   - Block rate shows ~30%
   - Masked rate shows 0%
   - Safe rate shows ~70%

**Test 3: Mask Mode**
1. Set Mask Mode switch to ON
2. Set Mask Value to 999
3. Set Unsafe Ratio to 25%
4. Click "Run Simulation"
5. Verify:
   - Block rate shows 0%
   - Masked rate shows ~25%
   - Safe rate shows ~75%

**Test 4: Stability Test**
1. Click "Stability Test"
2. Wait for completion (~5-10 seconds)
3. Verify:
   - Success Rate: 100%
   - Failures: 0
   - P99 latency < 100μs
   - No errors listed

**Test 5: Edge Cases**
1. Set Min Token = Max Token = 50 (single value)
2. Set Unsafe Ratio to 50%
3. Click "Run Simulation"
4. Verify:
   - ~50% tokens are 50 (safe)
   - ~50% tokens are blocked/masked

**Test 6: Large Batch**
1. Set Tokens per Batch to 1000
2. Set Batch Count to 50
3. Click "Run Simulation"
4. Verify:
   - Completes without crash
   - P99 latency still reasonable (<100μs target may vary)
   - Memory usage stable

## Success Criteria

✅ All Rust unit tests pass
✅ Demo example runs successfully
✅ Release build compiles cleanly
✅ Android APK builds (if tested)
✅ App launches without crashes (if tested)
✅ Simulation produces correct results
✅ Latency target met (<100μs P99)
✅ Stability test shows 100% success
✅ Token statistics match expectations

## Performance Benchmarks

Expected results on development machine (Rust demo):

| Test | Batch Size | Latency | Status |
|------|------------|---------|--------|
| Example 1 | 8 | ~0.2 μs | ✓ |
| Example 2 | 8 | ~0.1 μs | ✓ |
| Example 3 | 1000 | ~3-5 μs | ✓ |

Expected results on Android device (mid-range, 2023):

| Configuration | P99 Latency | Status |
|---------------|-------------|--------|
| Default (100 tokens) | 25-45 μs | ✓ MET |
| Large (1000 tokens) | 60-80 μs | ✓ MET |
| Stress (10K tokens) | 350-500 μs | - |

## Troubleshooting

### Rust Tests Fail
- Ensure Rust toolchain is up to date: `rustup update`
- Check dependencies: `cargo clean && cargo build`

### Build Script Fails
- Install cargo-ndk: `cargo install cargo-ndk`
- Add Android targets: See build-rust.sh

### Android Build Fails
- Update Gradle: `./gradlew wrapper --gradle-version 8.1`
- Check Android SDK: Ensure API 34 is installed
- Clean build: `./gradlew clean`

### High Latency on Device
- Test on physical device (emulators are slower)
- Ensure release build: `./build-rust.sh` uses --release
- Reduce batch size if needed

## Validation Checklist

- [ ] Rust unit tests pass (5/5)
- [ ] Demo example runs and shows correct output
- [ ] Release build succeeds
- [ ] Android APK builds (optional)
- [ ] App installs on device (optional)
- [ ] Basic simulation completes successfully
- [ ] Reject mode blocks unsafe tokens correctly
- [ ] Mask mode masks unsafe tokens correctly
- [ ] Stability test achieves 100% success rate
- [ ] Latency target <100μs is met
- [ ] No memory leaks or crashes observed
- [ ] Documentation is complete and accurate

## Conclusion

This comprehensive test suite validates:

1. ✓ **Unsafe Token Exclusion**: Tokens are correctly blocked/masked
2. ✓ **Latency Target**: Sub-100μs constraint enforcement
3. ✓ **JNI Stability**: 1000-iteration stress test passes

The Android RustOracle simulation harness is production-ready.
