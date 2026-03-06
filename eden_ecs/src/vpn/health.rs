use std::collections::HashMap;
use std::time::{Duration, Instant};
use rand::distributions::{Distribution, WeightedIndex};
use rand::thread_rng;

#[derive(Debug, Clone)]
pub struct EndpointStats {
    pub success_count: u32,
    pub failure_count: u32,
    pub last_seen: Instant,
    pub p95_latency: Duration,
}

#[derive(Debug, Clone)]
pub struct EndpointHealth {
    stats: HashMap<String, EndpointStats>,
    cooldown_until: HashMap<String, Instant>,
    cooldown_duration: Duration,
}

impl EndpointHealth {
    pub fn new(cooldown_duration: Duration) -> Self {
        Self {
            stats: HashMap::new(),
            cooldown_until: HashMap::new(),
            cooldown_duration,
        }
    }

    pub fn record_success(&mut self, endpoint: &str, latency: Duration) {
        let stat = self.stats.entry(endpoint.to_string()).or_insert(EndpointStats {
            success_count: 0,
            failure_count: 0,
            last_seen: Instant::now(),
            p95_latency: latency,
        });
        stat.success_count += 1;
        stat.last_seen = Instant::now();
        stat.p95_latency = stat.p95_latency.mul_f64(0.95) + latency.mul_f64(0.05);
        self.cooldown_until.remove(endpoint);
    }

    pub fn record_failure(&mut self, endpoint: &str) {
        let stat = self.stats.entry(endpoint.to_string()).or_insert(EndpointStats {
            success_count: 0,
            failure_count: 0,
            last_seen: Instant::now(),
            p95_latency: Duration::from_secs(1),
        });
        stat.failure_count += 1;
        stat.last_seen = Instant::now();
        self.cooldown_until.insert(endpoint.to_string(), Instant::now() + self.cooldown_duration);
    }

    pub fn is_on_cooldown(&self, endpoint: &str) -> bool {
        matches!(self.cooldown_until.get(endpoint), Some(until) if *until > Instant::now())
    }

    /// Weighted random pick by success ratio; endpoints on cooldown are skipped.
    pub fn select_healthy_endpoint(&self) -> Option<String> {
        let mut endpoints = Vec::new();
        let mut weights = Vec::new();
        for (ep, stat) in &self.stats {
            if self.is_on_cooldown(ep) {
                continue;
            }
            let total = stat.success_count + stat.failure_count;
            let w = if total == 0 {
                1.0
            } else {
                stat.success_count as f64 / total as f64
            };
            endpoints.push(ep.clone());
            weights.push(w.max(0.0001)); // avoid zero weight
        }
        if endpoints.is_empty() {
            return None;
        }
        let dist = WeightedIndex::new(weights).ok()?;
        let idx = dist.sample(&mut thread_rng());
        Some(endpoints[idx].clone())
    }
}
