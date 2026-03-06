use anyhow::{bail, Result};
use rand::{seq::SliceRandom, thread_rng};
use reqwest::{Client, Method, Response};
use serde::Deserialize;
use std::time::{Duration, Instant};

#[derive(Debug, Clone, Deserialize)]
pub struct Endpoint {
    pub name: String,
    pub base: String,
    #[serde(default = "default_weight")]
    pub weight: u32,
    #[serde(default)]
    pub health: Health,
}
fn default_weight() -> u32 {
    1
}

#[derive(Debug, Clone, Deserialize, Default)]
pub struct Health {
    pub latency_ms: u64,
    pub ok_ratio: f32,
    #[serde(skip)]
    pub last_checked: Option<Instant>,
}

#[derive(Debug)]
pub struct HopRequest {
    pub path: String,
    pub body: Option<serde_json::Value>,
    pub method: Method,
}

pub struct ApiVpn {
    client: Client,
    endpoints: Vec<Endpoint>,
    anchor_url: String,
    timeout: Duration,
    max_depth: usize,
}

impl ApiVpn {
    pub fn new(anchor_url: impl Into<String>) -> Self {
        Self {
            client: Client::builder()
                .timeout(Duration::from_secs(5))
                .build()
                .unwrap(),
            endpoints: Vec::new(),
            anchor_url: anchor_url.into(),
            timeout: Duration::from_secs(5),
            max_depth: 3,
        }
    }

    pub fn set_max_depth(&mut self, depth: usize) {
        self.max_depth = depth.max(1);
    }

    pub async fn refresh(&mut self) -> Result<()> {
        let eps: Vec<Endpoint> = self
            .client
            .get(&self.anchor_url)
            .send()
            .await?
            .json()
            .await?;
        self.endpoints = eps;
        Ok(())
    }

    async fn probe(&self, ep: &Endpoint) -> Result<Health> {
        let url = format!("{}/status/200", ep.base.trim_end_matches('/'));
        let started = Instant::now();
        let resp = self.client.get(&url).timeout(self.timeout).send().await?;
        let latency = started.elapsed().as_millis() as u64;
        Ok(Health {
            latency_ms: latency,
            ok_ratio: if resp.status().is_success() { 1.0 } else { 0.0 },
            last_checked: Some(Instant::now()),
        })
    }

    pub async fn hop(&mut self, req: HopRequest) -> Result<Response> {
        if self.endpoints.is_empty() {
            self.refresh().await?;
        }

        // probe without aliasing self
        let mut updated = Vec::with_capacity(self.endpoints.len());
        for ep in &self.endpoints {
            let mut e = ep.clone();
            e.health = self.probe(ep).await.unwrap_or_default();
            updated.push(e);
        }
        self.endpoints = updated;

        let mut rng = thread_rng();
        let mut eps = self.endpoints.clone();
        eps.shuffle(&mut rng);
        let depth = eps.len().min(self.max_depth);

        for ep in eps.into_iter().take(depth) {
            let url = format!("{}{}", ep.base.trim_end_matches('/'), req.path);
            let resp = match req.method {
                Method::GET => self.client.get(&url).send().await,
                _ => {
                    self.client
                        .request(req.method.clone(), &url)
                        .json(&req.body)
                        .send()
                        .await
                }
            };
            if let Ok(r) = resp {
                if r.status().is_success() {
                    return Ok(r);
                }
            }
        }
        bail!("all hops failed")
    }
}
