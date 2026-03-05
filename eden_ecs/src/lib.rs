//! EDEN ECS — Rust telemetry FFI bridge
//!
//! Exposes the zero-copy [`ECSStateBuffer`] and its C-compatible API so that
//! the Python [`OuroborosTelemetryDaemon`] can map shared memory without
//! locking critical ECS paths.

pub mod telemetry_ffi;

pub use telemetry_ffi::{
    ecs_state_buffer_new,
    ecs_state_buffer_free,
    ecs_state_buffer_flush,
    ecs_state_buffer_prediction_errors_ptr,
    ecs_state_buffer_activations_ptr,
    ecs_state_buffer_connectivity_weights_ptr,
    ecs_state_buffer_entity_count,
    ecs_state_buffer_edge_count,
    MAX_ENTITIES,
    MAX_EDGES,
};
