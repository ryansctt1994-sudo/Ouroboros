//! # Bunny‑approved checklist 🐇
//! - Never hardcode real keys/tokens.
//! - Keep hop depth short—rabbits hate long tunnels (latency).
//! - Burrow exits (endpoints) get sealed after cave‑ins: cooldown on failure.
//! - Carry a map: refresh anchor list periodically and cache it.

mod crypto;
mod health;
mod observability;
mod retry;

pub use crypto::{decrypt_payload, encrypt_payload};
pub use health::{EndpointHealth, DEFAULT_COOLDOWN_SECS, DEFAULT_MAX_HOP_DEPTH};
pub use observability::{record_failure, record_hop};
pub use retry::{
    attempt_with_retry, RetryPolicy, DEFAULT_BASE_RETRY_MS, DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_FACTOR,
};

#[cfg(test)]
mod tests;
