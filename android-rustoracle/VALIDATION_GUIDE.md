# Android RustOracle - Simulation Validation Guide

## Validation Objectives

This document outlines the validation process for the three primary simulation goals:

### 1. Unsafe Token Exclusion
**Objective**: Verify that tokens outside allowed ranges are blocked or masked correctly.

**Test Procedure**:
1. Configure token range (e.g., 0-1000)
2. Set unsafe ratio to 20-30%
3. Run simulation with multiple batches
4. Verify token statistics show correct blocking/masking

**Success Criteria**:
- All tokens outside range are either blocked (reject mode) or masked (mask mode)
- No unsafe tokens appear in validated output
- Block/mask rates match input unsafe ratio

**Example Configuration**:
```
Min Token: 0
Max Token: 1000
Mask Mode: true
Mask Value: 0
Unsafe Ratio: 25%
```

**Expected Results**:
- Safe tokens: ~75% (within 0-1000)
- Masked tokens: ~25% (replaced with 0)
- Blocked tokens: 0 (in mask mode)

### 2. Constraint Mask Latency
**Objective**: Measure the delay between token injection and enforcement with sub-100μs target.

**Test Procedure**:
1. Configure moderate batch sizes (100-500 tokens)
2. Run simulation with sufficient iterations (10+ batches)
3. Check P99 latency metric
4. Verify latency target indicator shows "✓ MET"

**Success Criteria**:
- P99 latency < 100μs
- Mean latency < 50μs (typical)
- Consistent performance across batches

**Performance Factors**:
- Batch size affects total time but not per-token latency
- Rust implementation provides nanosecond precision
- JNI overhead is minimal due to batch processing

**Example Results** (100 tokens/batch):
```
Mean Latency: 15.2 μs
Max Latency: 42.8 μs
P99 Latency: 38.5 μs
Target (<100μs): ✓ MET
```

### 3. JNI + Rust Loop Stability
**Objective**: Ensure the integration sustains repeated calls under realistic token stream density.

**Test Procedure**:
1. Click "Stability Test" button
2. Test runs 1000 iterations automatically
3. Monitor success rate and error count
4. Review latency distribution

**Success Criteria**:
- Success rate: 100%
- Failure count: 0
- Stable latency (low variance)
- No memory leaks or crashes

**Stability Metrics**:
- **Success Rate**: Should be 100% for reliable implementation
- **Latency Variance**: P99/Mean ratio should be < 3.0
- **Error List**: Should be empty

**Example Results**:
```
Iterations: 1000
Success: 1000
Failures: 0
Success Rate: 100.00%

Latency Distribution:
Mean: 16.3 μs
Min: 12.1 μs
P50: 15.8 μs
P99: 24.7 μs
Max: 31.2 μs
```

## Validation Scenarios

### Scenario 1: Reject Mode - Strict Filtering
**Configuration**:
- Min: 0, Max: 100
- Mask Mode: false (reject)
- Tokens/Batch: 100
- Unsafe Ratio: 30%

**Expected Behavior**:
- ~30 tokens blocked per batch
- ~70 tokens in validated output
- Zero masked tokens
- Output size < input size

### Scenario 2: Mask Mode - Data Preservation
**Configuration**:
- Min: 0, Max: 100
- Mask Mode: true
- Mask Value: 50
- Tokens/Batch: 100
- Unsafe Ratio: 30%

**Expected Behavior**:
- ~30 tokens masked with value 50
- ~70 original safe tokens
- Zero blocked tokens
- Output size = input size

### Scenario 3: High Load Stress Test
**Configuration**:
- Tokens/Batch: 1000
- Batch Count: 100
- Total tokens: 100,000

**Expected Behavior**:
- All batches complete successfully
- Latency remains stable (<100μs P99)
- Memory usage stays constant
- No JNI errors

### Scenario 4: Edge Cases
**Test narrow ranges and extreme values**:
- Single value range (min = max)
- Negative token ranges
- Large token values (±10000)
- 100% safe or 100% unsafe ratios

## Troubleshooting

### Issue: High Latency (>100μs)
**Possible Causes**:
- Large batch sizes (>10000 tokens)
- Emulator instead of real device
- Debug build instead of release

**Solutions**:
- Reduce batch size
- Test on physical device
- Build Rust library in release mode

### Issue: Validation Failures
**Possible Causes**:
- JNI library not loaded
- Missing native library for device architecture
- Incorrect min/max configuration (min > max)

**Solutions**:
- Check logcat for library load errors
- Rebuild Rust for device architecture
- Validate configuration parameters

### Issue: App Crashes
**Possible Causes**:
- Memory exhaustion (too large batches)
- Native code panic
- Invalid pointer in JNI

**Solutions**:
- Reduce batch size and count
- Check Rust logs for panic messages
- Verify RustOracle.destroy() is called

## Performance Benchmarks

Expected performance on mid-range Android device (2023):

| Batch Size | Mean Latency | P99 Latency | Throughput |
|------------|--------------|-------------|------------|
| 10         | 8 μs         | 15 μs       | 1.25M/s    |
| 100        | 15 μs        | 25 μs       | 6.6M/s     |
| 1000       | 45 μs        | 80 μs       | 22M/s      |
| 10000      | 350 μs       | 500 μs      | 28M/s      |

*Measurements on Snapdragon 865, Android 13*

## Validation Checklist

Before considering the simulation validated:

- [ ] Run basic simulation with default parameters
- [ ] Verify unsafe tokens are excluded/masked correctly
- [ ] Check P99 latency is below 100μs target
- [ ] Run stability test with 1000 iterations
- [ ] Verify 100% success rate in stability test
- [ ] Test both reject and mask modes
- [ ] Test with various unsafe ratios (0%, 25%, 50%, 100%)
- [ ] Test edge cases (narrow ranges, negative values)
- [ ] Verify no memory leaks over extended runs
- [ ] Check latency remains stable under load

## Reporting Results

When reporting validation results, include:

1. **Device Information**: Model, Android version, chipset
2. **Configuration**: All parameters used in tests
3. **Simulation Results**: Screenshots of results screen
4. **Stability Results**: Success rate and latency distribution
5. **Observations**: Any anomalies or interesting findings

## Next Steps

After successful validation:

1. **Production Integration**: Integrate validated token constraint enforcement into production systems
2. **Monitoring**: Deploy latency and correctness metrics tracking
3. **Optimization**: Profile for further latency improvements if needed
4. **Scaling**: Test with production-scale token volumes
5. **Documentation**: Update system documentation with validation evidence

## References

- Rust Oracle implementation: `rustoracle/src/lib.rs`
- JNI bridge: `RustOracle.kt`
- Token simulator: `TokenStreamSimulator.kt`
- UI components: `MainActivity.kt`
