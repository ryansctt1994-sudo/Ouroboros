//! Half-precision (`f16`) zero-copy FFI buffers for GPU diffusion pipelines
//! and Unreal Engine 5 Niagara interface integration.
//!
//! # Motivation
//!
//! The GPU diffusion compute shader and the Niagara particle system both
//! consume `f16` (IEEE 754 binary16) tensors natively.  Passing `f32` buffers
//! requires a GPU-side cast on every upload, wasting ~50 % of the PCIe / UMA
//! memory bandwidth.
//!
//! [`DiffusionBufferF16`] provides a pre-allocated `f16` buffer that the Rust
//! ECS writes directly, keeping the hot path zero-copy from the ECS tick to
//! the GPU upload.
//!
//! # Memory layout
//!
//! | Field         | Capacity          | Size @ 32 M voxels |
//! |---------------|-------------------|--------------------|
//! | `concentrations` | `MAX_VOXELS`   | 64 MB              |
//! | `gradients`      | `MAX_VOXELS×3` | 192 MB             |
//!
//! Total hot memory for the diffusion buffer: **256 MB** — well within the
//! 720 MB system budget.
//!
//! # Example
//!
//! ```
//! use eden_ecs::ffi_f16::{DiffusionBufferF16, MAX_VOXELS};
//!
//! let mut buf = DiffusionBufferF16::new();
//!
//! // Write concentrations from an f32 slice (converted on write).
//! let conc_f32: Vec<f32> = vec![0.5_f32; 16];
//! buf.write_concentrations_f32(&conc_f32);
//! assert_eq!(buf.voxel_count(), 16);
//!
//! // The raw f16 pointer can be passed to a GPU upload call via FFI.
//! let ptr = buf.concentrations_ptr();
//! assert!(!ptr.is_null());
//! ```
//!
//! # FFI surface
//!
//! The C-compatible API (`diffusion_buf_*` functions) maps cleanly to both
//! C++ Unreal Engine plugins and CUDA/Vulkan compute host code.

use half::f16;

// ── Constants ─────────────────────────────────────────────────────────────────

/// Maximum number of voxels in the diffusion grid (256 × 256 × 512 ≈ 33 M).
pub const MAX_VOXELS: usize = 33_554_432; // 2^25

// ── DiffusionBufferF16 ────────────────────────────────────────────────────────

/// Pre-allocated `f16` buffer for zero-copy GPU diffusion uploads.
///
/// The concentrations and gradient channels are laid out in separate `Vec`s
/// to avoid false sharing when the Rust ECS writes concentrations from one
/// thread and gradients from another.
pub struct DiffusionBufferF16 {
    /// Per-voxel scalar concentration — length `MAX_VOXELS`.
    concentrations: Vec<f16>,
    /// Per-voxel gradient (X, Y, Z interleaved) — length `MAX_VOXELS × 3`.
    gradients: Vec<f16>,
    /// Number of active voxels written in the last flush.
    voxel_count: usize,
}

// Safety: raw-pointer C API is single-threaded on the caller side; Vec<f16>
// is Send + Sync already.
unsafe impl Send for DiffusionBufferF16 {}
unsafe impl Sync for DiffusionBufferF16 {}

impl DiffusionBufferF16 {
    /// Allocate a new buffer.  All values are initialised to `f16::ZERO`.
    pub fn new() -> Self {
        Self {
            concentrations: vec![f16::ZERO; MAX_VOXELS],
            gradients: vec![f16::ZERO; MAX_VOXELS * 3],
            voxel_count: 0,
        }
    }

    /// Write concentration values from an `f32` slice (converted to `f16`).
    ///
    /// Values at indices beyond `values.len()` are zeroed to prevent stale
    /// data leaking to the GPU.
    ///
    /// # Panics (debug)
    /// Panics when `values.len() > MAX_VOXELS`.
    pub fn write_concentrations_f32(&mut self, values: &[f32]) {
        debug_assert!(
            values.len() <= MAX_VOXELS,
            "values.len() ({}) exceeds MAX_VOXELS ({})",
            values.len(),
            MAX_VOXELS
        );
        let n = values.len().min(MAX_VOXELS);
        for (dst, &src) in self.concentrations[..n].iter_mut().zip(values.iter()) {
            *dst = f16::from_f32(src);
        }
        // Zero the tail
        for v in &mut self.concentrations[n..self.voxel_count.max(n)] {
            *v = f16::ZERO;
        }
        self.voxel_count = n;
    }

    /// Write concentration values directly from an `f16` slice (zero-copy on
    /// platforms where the caller already holds `f16` data).
    pub fn write_concentrations_f16(&mut self, values: &[f16]) {
        let n = values.len().min(MAX_VOXELS);
        self.concentrations[..n].copy_from_slice(&values[..n]);
        for v in &mut self.concentrations[n..self.voxel_count.max(n)] {
            *v = f16::ZERO;
        }
        self.voxel_count = n;
    }

    /// Write gradient values (X/Y/Z interleaved) from an `f32` slice.
    ///
    /// `gradients_f32` must have length `3 × voxel_count` — three components
    /// per voxel.
    pub fn write_gradients_f32(&mut self, gradients_f32: &[f32]) {
        let n = gradients_f32.len().min(MAX_VOXELS * 3);
        for (dst, &src) in self.gradients[..n].iter_mut().zip(gradients_f32.iter()) {
            *dst = f16::from_f32(src);
        }
        for v in &mut self.gradients[n..] {
            *v = f16::ZERO;
        }
    }

    /// Return a raw pointer to the concentration buffer.
    ///
    /// The pointer is valid for `MAX_VOXELS × sizeof(f16)` bytes.
    #[inline]
    pub fn concentrations_ptr(&self) -> *const f16 {
        self.concentrations.as_ptr()
    }

    /// Return a raw pointer to the gradient buffer.
    #[inline]
    pub fn gradients_ptr(&self) -> *const f16 {
        self.gradients.as_ptr()
    }

    /// Number of active voxels in the last write.
    #[inline]
    pub fn voxel_count(&self) -> usize {
        self.voxel_count
    }

    /// Read a concentration back as `f32` (for unit tests / CPU readback).
    #[inline]
    pub fn concentration_f32(&self, idx: usize) -> f32 {
        self.concentrations[idx].to_f32()
    }
}

impl Default for DiffusionBufferF16 {
    fn default() -> Self {
        Self::new()
    }
}

// ── C-compatible FFI API ──────────────────────────────────────────────────────

/// Allocate a new [`DiffusionBufferF16`] and return an owning raw pointer.
///
/// The caller is responsible for freeing the buffer with
/// [`diffusion_buf_free`].
#[no_mangle]
pub extern "C" fn diffusion_buf_new() -> *mut DiffusionBufferF16 {
    Box::into_raw(Box::new(DiffusionBufferF16::new()))
}

/// Free a [`DiffusionBufferF16`] previously created by [`diffusion_buf_new`].
///
/// # Safety
/// `buf` must be a non-null pointer returned by [`diffusion_buf_new`] that
/// has not already been freed.
#[no_mangle]
pub unsafe extern "C" fn diffusion_buf_free(buf: *mut DiffusionBufferF16) {
    if !buf.is_null() {
        drop(Box::from_raw(buf));
    }
}

/// Write `n` `f32` concentration values into the buffer, converting to `f16`.
///
/// Returns 0 on success, -1 on null-pointer error.
///
/// # Safety
/// `buf` and `values` must be valid non-null pointers.  `values` must point to
/// at least `n` valid `f32` values.
#[no_mangle]
pub unsafe extern "C" fn diffusion_buf_write_concentrations_f32(
    buf: *mut DiffusionBufferF16,
    values: *const f32,
    n: usize,
) -> i32 {
    if buf.is_null() || values.is_null() {
        return -1;
    }
    let slice = std::slice::from_raw_parts(values, n.min(MAX_VOXELS));
    (*buf).write_concentrations_f32(slice);
    0
}

/// Write `n` `f16` concentration values into the buffer (zero-copy path).
///
/// Returns 0 on success, -1 on null-pointer error.
///
/// # Safety
/// `buf` and `values` must be valid non-null pointers.  `values` must point to
/// at least `n` valid `f16` (u16) values.
#[no_mangle]
pub unsafe extern "C" fn diffusion_buf_write_concentrations_f16(
    buf: *mut DiffusionBufferF16,
    values: *const u16, // f16 as u16 for C compatibility
    n: usize,
) -> i32 {
    if buf.is_null() || values.is_null() {
        return -1;
    }
    let n = n.min(MAX_VOXELS);
    // Transmute u16 pointer to f16 pointer (same layout).
    let f16_ptr = values as *const f16;
    let slice = std::slice::from_raw_parts(f16_ptr, n);
    (*buf).write_concentrations_f16(slice);
    0
}

/// Return a const pointer to the `f16` concentration buffer.
///
/// # Safety
/// `buf` must be a valid, non-null [`DiffusionBufferF16`] pointer.
#[no_mangle]
pub unsafe extern "C" fn diffusion_buf_concentrations_ptr(
    buf: *const DiffusionBufferF16,
) -> *const u16 {
    if buf.is_null() {
        return std::ptr::null();
    }
    (*buf).concentrations_ptr() as *const u16
}

/// Return a const pointer to the `f16` gradient buffer.
///
/// # Safety
/// `buf` must be a valid, non-null [`DiffusionBufferF16`] pointer.
#[no_mangle]
pub unsafe extern "C" fn diffusion_buf_gradients_ptr(buf: *const DiffusionBufferF16) -> *const u16 {
    if buf.is_null() {
        return std::ptr::null();
    }
    (*buf).gradients_ptr() as *const u16
}

/// Return the number of active voxels in the last write.
///
/// # Safety
/// `buf` must be a valid, non-null [`DiffusionBufferF16`] pointer.
#[no_mangle]
pub unsafe extern "C" fn diffusion_buf_voxel_count(buf: *const DiffusionBufferF16) -> usize {
    if buf.is_null() {
        return 0;
    }
    (*buf).voxel_count()
}

// ── Tests ─────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use half::f16;

    #[test]
    fn test_new_buffer_zeroed() {
        let buf = DiffusionBufferF16::new();
        assert_eq!(buf.voxel_count(), 0);
        assert_eq!(buf.concentrations[0], f16::ZERO);
    }

    #[test]
    fn test_write_concentrations_f32_roundtrip() {
        let mut buf = DiffusionBufferF16::new();
        let values = vec![0.0_f32, 0.25, 0.5, 0.75, 1.0];
        buf.write_concentrations_f32(&values);
        assert_eq!(buf.voxel_count(), 5);
        // f16 has ~3 decimal digits of precision; 0.5 and 1.0 are exact.
        assert!((buf.concentration_f32(2) - 0.5).abs() < 0.001);
        assert!((buf.concentration_f32(4) - 1.0).abs() < 0.001);
    }

    #[test]
    fn test_write_concentrations_zeroes_tail() {
        let mut buf = DiffusionBufferF16::new();
        buf.write_concentrations_f32(&[1.0_f32; 5]);
        assert_eq!(buf.voxel_count(), 5);
        // Write fewer values — tail should be zeroed.
        buf.write_concentrations_f32(&[0.5_f32; 3]);
        assert_eq!(buf.voxel_count(), 3);
        assert_eq!(buf.concentrations[3], f16::ZERO);
        assert_eq!(buf.concentrations[4], f16::ZERO);
    }

    #[test]
    fn test_write_concentrations_f16() {
        let mut buf = DiffusionBufferF16::new();
        let vals: Vec<f16> = vec![f16::from_f32(0.1), f16::from_f32(0.9)];
        buf.write_concentrations_f16(&vals);
        assert_eq!(buf.voxel_count(), 2);
        assert!((buf.concentration_f32(0) - 0.1).abs() < 0.01);
        assert!((buf.concentration_f32(1) - 0.9).abs() < 0.01);
    }

    #[test]
    fn test_concentrations_ptr_non_null() {
        let buf = DiffusionBufferF16::new();
        assert!(!buf.concentrations_ptr().is_null());
        assert!(!buf.gradients_ptr().is_null());
    }

    #[test]
    fn test_write_gradients_f32() {
        let mut buf = DiffusionBufferF16::new();
        let grads = vec![1.0_f32, 0.0, -1.0]; // one voxel: (gx, gy, gz)
        buf.write_gradients_f32(&grads);
        assert!((buf.gradients[0].to_f32() - 1.0).abs() < 0.01);
        assert!((buf.gradients[2].to_f32() - (-1.0)).abs() < 0.01);
    }

    // ── FFI ───────────────────────────────────────────────────────────────────

    #[test]
    fn test_ffi_lifecycle() {
        unsafe {
            let buf = diffusion_buf_new();
            assert!(!buf.is_null());
            assert_eq!(diffusion_buf_voxel_count(buf), 0);
            assert!(!diffusion_buf_concentrations_ptr(buf).is_null());
            assert!(!diffusion_buf_gradients_ptr(buf).is_null());
            diffusion_buf_free(buf);
        }
    }

    #[test]
    fn test_ffi_write_concentrations_f32() {
        unsafe {
            let buf = diffusion_buf_new();
            let values = vec![0.5_f32, 0.25, 0.75];
            let rc = diffusion_buf_write_concentrations_f32(buf, values.as_ptr(), values.len());
            assert_eq!(rc, 0);
            assert_eq!(diffusion_buf_voxel_count(buf), 3);
            diffusion_buf_free(buf);
        }
    }

    #[test]
    fn test_ffi_null_safety() {
        unsafe {
            diffusion_buf_free(std::ptr::null_mut()); // no-op
            assert!(diffusion_buf_concentrations_ptr(std::ptr::null()).is_null());
            assert!(diffusion_buf_gradients_ptr(std::ptr::null()).is_null());
            assert_eq!(diffusion_buf_voxel_count(std::ptr::null()), 0);

            let rc =
                diffusion_buf_write_concentrations_f32(std::ptr::null_mut(), std::ptr::null(), 0);
            assert_eq!(rc, -1);
        }
    }
}
