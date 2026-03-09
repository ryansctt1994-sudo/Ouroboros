use reqwest::{Client, Method, Response};
use serde_json::Value;
use std::time::Duration;
use tracing::{error, info};

const HF_HUB_API: &str = "https://huggingface.co/api/models"\;

#[derive(Debug)]
pub struct SovereignInferenceClient {
    client: Client,
    hf_token: Option<String>,           // optional HF token (free tier)
    fallback_providers: Vec<String>,    // e.g. ["fireworks-ai", "fal-ai", "together-ai"]
    timeout: Duration,
}

impl SovereignInferenceClient {
    pub fn new(hf_token: Option<String>) -> Self {
        Self {
            client: Client::builder()
                .timeout(Duration::from_secs(15))
                .build()
                .unwrap(),
            hf_token,
            fallback_providers: vec![
                "fireworks-ai".into(),
                "fal-ai".into(),
                "together-ai".into(),   // free tier available
                "novita".into(),
            ],
            timeout: Duration::from_secs(15),
        }
    }

    /// Discover models for a provider (free call)
    pub async fn discover_models(&self, provider: &str, pipeline_tag: Option<&str>) -> Result<Vec<String>, String> {
        let mut url = format!("{}?inference_provider={}", HF_HUB_API, provider);
        if let Some(tag) = pipeline_tag {
            url.push_str(&format!("&pipeline_tag={}", tag));
        }

        let mut req = self.client.get(&url);
        if let Some(token) = &self.hf_token {
            req = req.bearer_auth(token);
        }

        let resp = req.send().await.map_err(|e| e.to_string())?;
        let models: Vec<Value> = resp.json().await.map_err(|e| e.to_string())?;
        let ids: Vec<String> = models.iter().filter_map(|m| m["id"].as_str().map(|s| s.to_string())).collect();
        Ok(ids)
    }

    /// Main sovereign call — tries providers in order with key rotation
    pub async fn call(
        &self,
        model: &str,
        payload: Value,
        task: &str,           // e.g. "conversational"
    ) -> Result<String, Box<dyn std::error::Error>> {
        for provider in &self.fallback_providers {
            let url = format!("https://api-inference.huggingface.co/models/{}", model);
            let mut req = self.client.post(&url)
                .json(&payload)
                .header("X-Inference-Provider", provider);

            if let Some(token) = &self.hf_token {
                req = req.bearer_auth(token);
            }

            match req.send().await {
                Ok(resp) if resp.status().is_success() => {
                    let text = resp.text().await?;
                    info!("✅ Sovereign call succeeded via {}", provider);
                    return Ok(text);
                }
                Ok(resp) => {
                    error!("Provider {} failed: {}", provider, resp.status());
                    continue;
                }
                Err(e) => {
                    error!("Provider {} network error: {}", provider, e);
                    continue;
                }
            }
        }

        Err("All providers failed. No free inference available.".into())
    }
}
