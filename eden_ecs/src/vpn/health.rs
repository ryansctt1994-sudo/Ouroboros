use rand::distributions::{Distribution, WeightedIndex};
use rand::thread_rng;
use std::collections::HashMap;
use std::time::{Duration, Instant};

pub const DEFAULT_COOLDOWN_SECS: u64 = 60;
pub const DEFAULT_MAX_HOP_DEPTH: usize = 3;

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

    pub fn with_default_cooldown() -> Self {
        Self::new(Duration::from_secs(DEFAULT_COOLDOWN_SECS))
    }

    pub fn record_success(&mut self, endpoint: &str, latency: Duration) {
        let stat = self
            .stats
            .entry(endpoint.to_string())
            .or_insert(EndpointStats {
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
        let stat = self
            .stats
            .entry(endpoint.to_string())
            .or_insert(EndpointStats {
                success_count: 0,
                failure_count: 0,
                last_seen: Instant::now(),
                p95_latency: Duration::from_secs(1),
            });
        stat.failure_count += 1;
        stat.last_seen = Instant::now();
        self.cooldown_until.insert(
            endpoint.to_string(),
            Instant::now() + self.cooldown_duration,
        );
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
            weights.push(w.max(0.0001));
        }
        if endpoints.is_empty() {
            return None;
        }
        let dist = WeightedIndex::new(weights).ok()?;
        let idx = dist.sample(&mut thread_rng());
        Some(endpoints[idx].clone())
    }

    /// Softmax selection with temperature to keep exploration alive.
    pub fn select_healthy_endpoint_with_temperature(&self, temperature: f32) -> Option<String> {
        let mut endpoints = Vec::new();
        let mut scores = Vec::new();
        for (ep, stat) in &self.stats {
            if self.is_on_cooldown(ep) {
                continue;
            }
            let total = stat.success_count + stat.failure_count;
            let score = if total == 0 {
                0.5
            } else {
                stat.success_count as f32 / total as f32
            };
            endpoints.push(ep.clone());
            scores.push(score);
        }
        if endpoints.is_empty() {
            return None;
        }
        let max_score = scores.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
        let exp_scores: Vec<f32> = scores
            .into_iter()
            .map(|s| ((s - max_score) / temperature).exp())
            .collect();
        let sum: f32 = exp_scores.iter().sum();
        let probs: Vec<f32> = exp_scores.iter().map(|p| p / sum).collect();
        let dist = WeightedIndex::new(probs).ok()?;
        let idx = dist.sample(&mut thread_rng());
        Some(endpoints[idx].clone())
    }

    /// Snapshot of endpoint scores (success ratio; new endpoints = 0.0).
    pub fn health_snapshot(&self) -> Vec<(String, f32)> {
        self.stats
            .iter()
            .map(|(ep, stat)| {
                let total = stat.success_count + stat.failure_count;
                let score = if total > 0 {
                    stat.success_count as f32 / total as f32
                } else {
                    0.0
                };
                (ep.clone(), score)
            })
            .collect()
    }
}
