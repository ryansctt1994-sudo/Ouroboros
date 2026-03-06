use std::time::Duration;
use tokio::time::sleep;

pub struct RetryPolicy {
    max_attempts: usize,
    base_delay: Duration,
    factor: f64,
}

impl RetryPolicy {
    pub fn new(max_attempts: usize, base_delay_ms: u64, factor: f64) -> Self {
        Self {
            max_attempts,
            base_delay: Duration::from_millis(base_delay_ms),
            factor,
        }
    }

    pub async fn retry<F, Fut, T, E>(&self, mut operation: F) -> Result<T, E>
    where
        F: FnMut() -> Fut,
        Fut: std::future::Future<Output = Result<T, E>>,
    {
        let mut attempt = 0;
        loop {
            match operation().await {
                Ok(val) => return Ok(val),
                Err(e) => {
                    attempt += 1;
                    if attempt >= self.max_attempts {
                        return Err(e);
                    }
                    let delay = self.base_delay.mul_f64(self.factor.powi(attempt as i32));
                    sleep(delay).await;
                }
            }
        }
    }
}

pub async fn attempt_with_retry<F, Fut, T, E>(
    operation: F,
    max_attempts: usize,
    base_delay_ms: u64,
    factor: f64,
) -> Result<T, E>
where
    F: FnMut() -> Fut,
    Fut: std::future::Future<Output = Result<T, E>>,
{
    let policy = RetryPolicy::new(max_attempts, base_delay_ms, factor);
    policy.retry(operation).await
}
