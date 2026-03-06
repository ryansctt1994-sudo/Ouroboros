//! # Bunny‑approved checklist 🐇
//! - Never hardcode real keys/tokens.
//! - Keep hop depth short—rabbits hate long tunnels (latency).
//! - Burrow exits (endpoints) get sealed after cave‑ins: cooldown on failure.
//! - Carry a map: refresh anchor list periodically and cache it.

mod health;
mod retry;
mod crypto;
mod observability;

pub use health::EndpointHealth;
pub use retry::{RetryPolicy, attempt_with_retry};
pub use crypto::{encrypt_payload, decrypt_payload};
pub use observability::{record_hop, record_failure};

#[cfg(test)]
mod tests;
