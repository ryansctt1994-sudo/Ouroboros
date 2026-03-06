use std::time::Duration;
use tracing::{error, info};

pub fn record_hop(endpoint: &str, hop_depth: usize, latency: Duration, status: u16) {
    info!(
        endpoint = endpoint,
        hop_depth = hop_depth,
        latency_ms = latency.as_millis() as u64,
        status = status,
        "hop completed"
    );
}

pub fn record_failure(endpoint: &str, hop_depth: usize, error: &str) {
    error!(
        endpoint = endpoint,
        hop_depth = hop_depth,
        error = error,
        "hop failed"
    );
}
