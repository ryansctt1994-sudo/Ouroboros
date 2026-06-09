# Design Notes

## WeaverPolicy edge weight buffer boundary

Status: `L2_IMPLEMENTED / TEST_ADDED / EXECUTION_PENDING`

Registry anchor: `cathedral-kernel-v1.0-rc1`

### Current implementation

`eden_ecs::weaver::PolicyContext` currently exposes edge weights as:

```rust
pub edge_weights: &'a mut Vec<f32>
```

This means Weaver policies mutate an existing caller-owned vector in place. The current implementation is still a mutable, zero-copy policy path in the ordinary ownership sense: the policy does not clone the edge-weight buffer and does not allocate a replacement buffer during policy application.

However, it is not the same as the previously documented pure slice boundary:

```rust
pub edge_weights: &'a mut [f32]
```

The pure slice form remains a design target rather than the current repository state.

### Evidence correction

The registry must not claim that the current mainline implementation uses `&mut [f32]`. The correct current claim is:

- Implemented: in-place mutation through `&mut Vec<f32>`.
- Specified target: narrower `&mut [f32]` policy boundary.
- Not yet validated: any performance benefit from changing `&mut Vec<f32>` to `&mut [f32]`.

### Decision for 1.0 RC

For `cathedral-kernel-v1.0-rc1`, keep the existing `&mut Vec<f32>` API and document the discrepancy.

Rationale:

1. The current API is already implemented and testable.
2. A slice refactor would widen the change surface before a basic correctness receipt exists.
3. The practical runtime cost is likely dominated by iteration over the edge-weight buffer, not the `Vec` container reference itself.
4. No benchmark receipt currently proves that the slice boundary materially improves the policy tick.

### Future optimization path

A later `1.1` pass may refactor `PolicyContext` to:

```rust
pub edge_weights: &'a mut [f32]
```

The promotion condition for that change is:

1. All existing Weaver tests still pass.
2. Call sites convert existing vectors with `as_mut_slice()` rather than cloning.
3. A benchmark compares `&mut Vec<f32>` and `&mut [f32]` under representative policy loads.
4. The benchmark receipt is stored under `receipts/` before any performance claim is promoted.

### Registry status

Current status:

```text
WeaverPolicy: L2_IMPLEMENTED / TEST_ADDED / EXECUTION_PENDING
Pure slice boundary: L1_SPECIFIED / FUTURE_OPTIMIZATION
Performance claims: CLAIMED_TARGETS / BENCHMARK_RECEIPT_REQUIRED
```

No L3 promotion is allowed until a successful test execution receipt exists.
