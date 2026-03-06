//! EDEN ECS — biologically-inspired, RAM-bound mycelial ECS.
//!
//! # Modules
//!
//! | Module            | Purpose                                               |
//! |-------------------|-------------------------------------------------------|
//! | [`telemetry_ffi`] | Zero-copy `f64` telemetry bridge to the Python daemon |
//! | [`spatial_grid`]  | Ultra-dense linearised spatial grid (PackedEntityRef) |
//! | [`weaver`]        | Fungal routing policy sandbox                         |
//! | [`ffi_f16`]       | Half-precision `f16` buffers for GPU diffusion / UE5  |
//! | [`tracy`]         | Tracy profiling macros and Sakib Index metric         |
//!
//! # Feature flags
//!
//! | Feature           | Effect                                             |
//! |-------------------|----------------------------------------------------|
//! | `tracy`           | Enable live Tracy profiling (zero overhead if off) |

pub mod ffi_f16;
pub mod spatial_grid;
pub mod telemetry_ffi;
pub mod tracy;
pub mod weaver;

pub use telemetry_ffi::{
    ecs_state_buffer_activations_ptr, ecs_state_buffer_connectivity_weights_ptr,
    ecs_state_buffer_edge_count, ecs_state_buffer_entity_count, ecs_state_buffer_flush,
    ecs_state_buffer_free, ecs_state_buffer_new, ecs_state_buffer_prediction_errors_ptr, MAX_EDGES,
    MAX_ENTITIES,
};
pub mod vpn;
