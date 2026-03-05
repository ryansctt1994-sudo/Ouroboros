//! Zero-copy telemetry FFI bridge between the Rust ECS and the Python observer.
//!
//! # Design
//!
//! [`ECSStateBuffer`] owns three pre-allocated `f64` arrays:
//!
//! | Field | Capacity | Semantics |
//! |---|---|---|
//! | `prediction_errors` | `MAX_ENTITIES` | Per-entity prediction error (Kalman / Hebbian residual) |
//! | `activations`       | `MAX_ENTITIES` | Per-entity activation magnitude |
//! | `connectivity_weights` | `MAX_EDGES` | Edge weights in the connectivity graph |
//!
//! All buffers use `f64` throughout so that Python's `ctypes.c_double` /
//! NumPy `float64` can wrap them without a copy.
//!
//! [`flush_to_python`] is called from the ECS deferred-deletion phase.
//! It writes live state into the pre-allocated buffers **without** acquiring
//! any lock that could stall the hot ECS path.  The Python side reads
//! concurrently via raw pointer access (epoch-gated to avoid torn reads).
//!
//! # Buffer limits
//!
//! ```
//! # use eden_ecs::telemetry_ffi::{MAX_ENTITIES, MAX_EDGES};
//! assert_eq!(MAX_ENTITIES, 100_000);
//! assert_eq!(MAX_EDGES,    800_000);
//! ```

use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};

/// Maximum number of entities supported by the telemetry buffers.
pub const MAX_ENTITIES: usize = 100_000;

/// Maximum number of directed edges (connectivity weights) in the graph.
pub const MAX_EDGES: usize = 800_000;

/// Atomic write-epoch used for simple double-buffering synchronisation.
///
/// The Rust side increments the epoch *before* writing and again *after*.
/// Python considers a snapshot consistent only when the epoch is even and
/// unchanged throughout the read.
static WRITE_EPOCH: AtomicU64 = AtomicU64::new(0);

/// Pre-allocated, zero-copy telemetry state exported to the Python observer.
///
/// All buffers are heap-allocated at construction time and live for the full
/// process lifetime.  The C-compatible accessors below hand raw pointers to
/// Python without transferring ownership.
///
/// # Implementation note — `Vec` vs `Box<[T; N]>`
///
/// The large array sizes (`MAX_ENTITIES` = 100 000 × 8 B = 800 KB each,
/// `MAX_EDGES` = 800 000 × 8 B = 6.4 MB) make it impossible to use
/// `Box::new([0.0_f64; N])`: Rust constructs the array **on the stack** before
/// boxing it, overflowing the default 8 MB thread stack.  `Vec` allocates
/// directly on the heap and is used here instead.  All slice operations
/// (`[..n]`, `.iter()`, `.as_ptr()`) are identical for `Vec<f64>`.
pub struct ECSStateBuffer {
    /// Per-entity prediction errors — length `MAX_ENTITIES`, active slice
    /// is `[0 .. entity_count]`.
    prediction_errors: Vec<f64>,

    /// Per-entity activation magnitudes — length `MAX_ENTITIES`.
    activations: Vec<f64>,

    /// Edge connectivity weights — length `MAX_EDGES`, active slice is
    /// `[0 .. edge_count]`.
    connectivity_weights: Vec<f64>,

    /// Number of active entities written during the last flush.
    entity_count: AtomicU32,

    /// Number of active edges written during the last flush.
    edge_count: AtomicU32,
}

// Safety: the raw-pointer C API must only be called from a single Python
// thread at a time, but the struct itself contains no thread-local state.
unsafe impl Send for ECSStateBuffer {}
unsafe impl Sync for ECSStateBuffer {}

impl ECSStateBuffer {
    /// Allocate a new buffer.  All values are initialised to `0.0`.
    pub fn new() -> Self {
        Self {
            prediction_errors: vec![0.0_f64; MAX_ENTITIES],
            activations: vec![0.0_f64; MAX_ENTITIES],
            connectivity_weights: vec![0.0_f64; MAX_EDGES],
            entity_count: AtomicU32::new(0),
            edge_count: AtomicU32::new(0),
        }
    }

    /// Write live ECS state into the shared buffers.
    ///
    /// Called from the **deferred-deletion phase** of the ECS tick so that
    /// no critical simulation locks are held during the copy.
    ///
    /// # Parameters
    ///
    /// * `errors`  — slice of per-entity prediction errors (length ≤ `MAX_ENTITIES`)
    /// * `acts`    — slice of per-entity activations       (length ≤ `MAX_ENTITIES`)
    /// * `weights` — slice of edge connectivity weights    (length ≤ `MAX_EDGES`)
    ///
    /// Values beyond the provided slice lengths are zeroed so that stale data
    /// from a previous (larger) frame never leaks.
    ///
    /// # Panics
    ///
    /// Panics in debug builds when any slice exceeds its pre-allocated limit.
    pub fn flush_to_python(
        &mut self,
        errors: &[f64],
        acts: &[f64],
        weights: &[f64],
    ) {
        debug_assert!(
            errors.len() <= MAX_ENTITIES,
            "prediction_errors slice ({}) exceeds MAX_ENTITIES ({})",
            errors.len(),
            MAX_ENTITIES
        );
        debug_assert!(
            acts.len() <= MAX_ENTITIES,
            "activations slice ({}) exceeds MAX_ENTITIES ({})",
            acts.len(),
            MAX_ENTITIES
        );
        debug_assert!(
            weights.len() <= MAX_EDGES,
            "connectivity_weights slice ({}) exceeds MAX_EDGES ({})",
            weights.len(),
            MAX_EDGES
        );

        // Clamp to allocated bounds in release builds.
        let n_e = errors.len().min(MAX_ENTITIES);
        let n_a = acts.len().min(MAX_ENTITIES);
        let n_w = weights.len().min(MAX_EDGES);

        // Signal the start of a write by incrementing to an odd epoch.
        WRITE_EPOCH.fetch_add(1, Ordering::Release);

        // --- write prediction errors ---
        self.prediction_errors[..n_e].copy_from_slice(&errors[..n_e]);
        // zero any tail from a previous larger frame
        for v in &mut self.prediction_errors[n_e..] {
            *v = 0.0;
        }

        // --- write activations ---
        self.activations[..n_a].copy_from_slice(&acts[..n_a]);
        for v in &mut self.activations[n_a..] {
            *v = 0.0;
        }

        // --- write connectivity weights ---
        self.connectivity_weights[..n_w].copy_from_slice(&weights[..n_w]);
        for v in &mut self.connectivity_weights[n_w..] {
            *v = 0.0;
        }

        // Commit counts and signal end of write (even epoch = consistent).
        self.entity_count.store(n_e as u32, Ordering::Relaxed);
        self.edge_count.store(n_w as u32, Ordering::Relaxed);
        WRITE_EPOCH.fetch_add(1, Ordering::Release);
    }

    /// Return the number of active entities in the last flush.
    #[inline]
    pub fn entity_count(&self) -> u32 {
        self.entity_count.load(Ordering::Acquire)
    }

    /// Return the number of active edges in the last flush.
    #[inline]
    pub fn edge_count(&self) -> u32 {
        self.edge_count.load(Ordering::Acquire)
    }
}

impl Default for ECSStateBuffer {
    fn default() -> Self {
        Self::new()
    }
}

// ── C-compatible API ──────────────────────────────────────────────────────────

/// Allocate a new [`ECSStateBuffer`] on the heap and return an owning raw
/// pointer.  Ownership is transferred to the caller; the buffer **must** be
/// freed with [`ecs_state_buffer_free`].
#[no_mangle]
pub extern "C" fn ecs_state_buffer_new() -> *mut ECSStateBuffer {
    Box::into_raw(Box::new(ECSStateBuffer::new()))
}

/// Free an [`ECSStateBuffer`] previously created by [`ecs_state_buffer_new`].
///
/// # Safety
///
/// `buf` must be a non-null pointer returned by [`ecs_state_buffer_new`] that
/// has not already been freed.
#[no_mangle]
pub unsafe extern "C" fn ecs_state_buffer_free(buf: *mut ECSStateBuffer) {
    if !buf.is_null() {
        drop(Box::from_raw(buf));
    }
}

/// Populate shared buffers from raw C arrays.
///
/// This is the C entry-point for [`ECSStateBuffer::flush_to_python`].
///
/// # Parameters
///
/// * `buf`            — pointer to the [`ECSStateBuffer`]
/// * `errors`         — pointer to `n_entities` `f64` prediction-error values
/// * `n_entities`     — number of active entities (≤ `MAX_ENTITIES`)
/// * `acts`           — pointer to `n_entities` `f64` activation values
/// * `weights`        — pointer to `n_edges` `f64` connectivity-weight values
/// * `n_edges`        — number of active edges (≤ `MAX_EDGES`)
///
/// Returns `0` on success, `-1` on null-pointer error.
///
/// # Safety
///
/// All pointer arguments must be valid for the duration of the call.
#[no_mangle]
pub unsafe extern "C" fn ecs_state_buffer_flush(
    buf: *mut ECSStateBuffer,
    errors: *const f64,
    n_entities: usize,
    acts: *const f64,
    weights: *const f64,
    n_edges: usize,
) -> i32 {
    if buf.is_null() || errors.is_null() || acts.is_null() || weights.is_null() {
        return -1;
    }

    let n_e = n_entities.min(MAX_ENTITIES);
    let n_w = n_edges.min(MAX_EDGES);

    let err_slice = std::slice::from_raw_parts(errors, n_e);
    let act_slice = std::slice::from_raw_parts(acts, n_e);
    let wgt_slice = std::slice::from_raw_parts(weights, n_w);

    (*buf).flush_to_python(err_slice, act_slice, wgt_slice);
    0
}

/// Return a const pointer to the `prediction_errors` buffer.
///
/// The returned pointer remains valid for the lifetime of `buf`.
///
/// # Safety
///
/// `buf` must be a valid, non-null [`ECSStateBuffer`] pointer.
#[no_mangle]
pub unsafe extern "C" fn ecs_state_buffer_prediction_errors_ptr(
    buf: *const ECSStateBuffer,
) -> *const f64 {
    if buf.is_null() {
        return std::ptr::null();
    }
    (*buf).prediction_errors.as_ptr()
}

/// Return a const pointer to the `activations` buffer.
///
/// # Safety
///
/// `buf` must be a valid, non-null [`ECSStateBuffer`] pointer.
#[no_mangle]
pub unsafe extern "C" fn ecs_state_buffer_activations_ptr(
    buf: *const ECSStateBuffer,
) -> *const f64 {
    if buf.is_null() {
        return std::ptr::null();
    }
    (*buf).activations.as_ptr()
}

/// Return a const pointer to the `connectivity_weights` buffer.
///
/// # Safety
///
/// `buf` must be a valid, non-null [`ECSStateBuffer`] pointer.
#[no_mangle]
pub unsafe extern "C" fn ecs_state_buffer_connectivity_weights_ptr(
    buf: *const ECSStateBuffer,
) -> *const f64 {
    if buf.is_null() {
        return std::ptr::null();
    }
    (*buf).connectivity_weights.as_ptr()
}

/// Return the number of active entities written in the last flush.
///
/// # Safety
///
/// `buf` must be a valid, non-null [`ECSStateBuffer`] pointer.
#[no_mangle]
pub unsafe extern "C" fn ecs_state_buffer_entity_count(buf: *const ECSStateBuffer) -> u32 {
    if buf.is_null() {
        return 0;
    }
    (*buf).entity_count()
}

/// Return the number of active edges written in the last flush.
///
/// # Safety
///
/// `buf` must be a valid, non-null [`ECSStateBuffer`] pointer.
#[no_mangle]
pub unsafe extern "C" fn ecs_state_buffer_edge_count(buf: *const ECSStateBuffer) -> u32 {
    if buf.is_null() {
        return 0;
    }
    (*buf).edge_count()
}

// ── Tests ─────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_constants() {
        assert_eq!(MAX_ENTITIES, 100_000);
        assert_eq!(MAX_EDGES, 800_000);
    }

    #[test]
    fn test_new_buffer_zeroed() {
        let buf = ECSStateBuffer::new();
        assert_eq!(buf.entity_count(), 0);
        assert_eq!(buf.edge_count(), 0);
        assert!(buf.prediction_errors.iter().all(|&v| v == 0.0));
        assert!(buf.activations.iter().all(|&v| v == 0.0));
        assert!(buf.connectivity_weights.iter().all(|&v| v == 0.0));
    }

    #[test]
    fn test_flush_basic() {
        let mut buf = ECSStateBuffer::new();

        let errors = vec![0.1_f64, 0.2, 0.3];
        let acts = vec![1.0_f64, 2.0, 3.0];
        let weights = vec![0.5_f64; 6];

        buf.flush_to_python(&errors, &acts, &weights);

        assert_eq!(buf.entity_count(), 3);
        assert_eq!(buf.edge_count(), 6);
        assert_eq!(buf.prediction_errors[0], 0.1);
        assert_eq!(buf.activations[2], 3.0);
        assert_eq!(buf.connectivity_weights[5], 0.5);
        // Tail should be zeroed
        assert_eq!(buf.prediction_errors[3], 0.0);
    }

    #[test]
    fn test_flush_zeroes_tail() {
        let mut buf = ECSStateBuffer::new();

        // First flush: 5 entities
        let errors5 = vec![1.0_f64; 5];
        let acts5 = vec![1.0_f64; 5];
        let weights10 = vec![1.0_f64; 10];
        buf.flush_to_python(&errors5, &acts5, &weights10);
        assert_eq!(buf.entity_count(), 5);

        // Second flush: 3 entities (smaller) — indices 3 and 4 must be zeroed
        let errors3 = vec![2.0_f64; 3];
        let acts3 = vec![2.0_f64; 3];
        let weights4 = vec![2.0_f64; 4];
        buf.flush_to_python(&errors3, &acts3, &weights4);

        assert_eq!(buf.entity_count(), 3);
        assert_eq!(buf.prediction_errors[2], 2.0);
        assert_eq!(buf.prediction_errors[3], 0.0);
        assert_eq!(buf.prediction_errors[4], 0.0);
    }

    #[test]
    fn test_flush_max_entities() {
        let mut buf = ECSStateBuffer::new();
        let errors = vec![0.5_f64; MAX_ENTITIES];
        let acts = vec![0.5_f64; MAX_ENTITIES];
        let weights = vec![0.5_f64; MAX_EDGES];
        buf.flush_to_python(&errors, &acts, &weights);
        assert_eq!(buf.entity_count(), MAX_ENTITIES as u32);
        assert_eq!(buf.edge_count(), MAX_EDGES as u32);
    }

    // ── FFI API tests ──────────────────────────────────────────────────────

    #[test]
    fn test_ffi_lifecycle() {
        unsafe {
            let buf = ecs_state_buffer_new();
            assert!(!buf.is_null());

            assert_eq!(ecs_state_buffer_entity_count(buf), 0);
            assert_eq!(ecs_state_buffer_edge_count(buf), 0);
            assert!(!ecs_state_buffer_prediction_errors_ptr(buf).is_null());
            assert!(!ecs_state_buffer_activations_ptr(buf).is_null());
            assert!(!ecs_state_buffer_connectivity_weights_ptr(buf).is_null());

            ecs_state_buffer_free(buf);
        }
    }

    #[test]
    fn test_ffi_flush() {
        unsafe {
            let buf = ecs_state_buffer_new();

            let errors = vec![0.1_f64, 0.2_f64];
            let acts = vec![1.0_f64, 2.0_f64];
            let weights = vec![0.9_f64, 0.8_f64, 0.7_f64];

            let rc = ecs_state_buffer_flush(
                buf,
                errors.as_ptr(),
                errors.len(),
                acts.as_ptr(),
                weights.as_ptr(),
                weights.len(),
            );
            assert_eq!(rc, 0);

            assert_eq!(ecs_state_buffer_entity_count(buf), 2);
            assert_eq!(ecs_state_buffer_edge_count(buf), 3);

            let err_ptr = ecs_state_buffer_prediction_errors_ptr(buf);
            assert_eq!(*err_ptr, 0.1);
            assert_eq!(*err_ptr.add(1), 0.2);

            ecs_state_buffer_free(buf);
        }
    }

    #[test]
    fn test_ffi_null_safety() {
        unsafe {
            // Calling free on null is a no-op
            ecs_state_buffer_free(std::ptr::null_mut());

            // Accessors on null return null / 0
            assert!(ecs_state_buffer_prediction_errors_ptr(std::ptr::null()).is_null());
            assert!(ecs_state_buffer_activations_ptr(std::ptr::null()).is_null());
            assert!(ecs_state_buffer_connectivity_weights_ptr(std::ptr::null()).is_null());
            assert_eq!(ecs_state_buffer_entity_count(std::ptr::null()), 0);
            assert_eq!(ecs_state_buffer_edge_count(std::ptr::null()), 0);

            // flush returns -1 on null
            let rc = ecs_state_buffer_flush(
                std::ptr::null_mut(),
                std::ptr::null(),
                0,
                std::ptr::null(),
                std::ptr::null(),
                0,
            );
            assert_eq!(rc, -1);
        }
    }
}
