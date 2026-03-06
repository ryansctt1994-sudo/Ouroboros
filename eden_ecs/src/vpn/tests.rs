use super::*;
use base64::Engine;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::Duration;

#[test]
fn test_health_scoring_and_snapshot() {
    let mut health = EndpointHealth::with_default_cooldown();
    health.record_success("ep1", Duration::from_millis(100));
    health.record_success("ep1", Duration::from_millis(150));
    health.record_failure("ep2");
    health.record_success("ep2", Duration::from_millis(200));

    let snap = health.health_snapshot();
    assert!(snap.iter().any(|(e, _)| e == "ep1"));

    assert!(health.select_healthy_endpoint().is_some());
    assert!(health
        .select_healthy_endpoint_with_temperature(0.5)
        .is_some());
}

#[tokio::test]
async fn test_retry_success() {
    let attempts = Arc::new(AtomicUsize::new(0));
    let attempts_cloned = attempts.clone();
    let result = attempt_with_retry(
        move || {
            let attempts = attempts_cloned.clone();
            async move {
                let n = attempts.fetch_add(1, Ordering::SeqCst) + 1;
                if n < 3 {
                    Err("fail")
                } else {
                    Ok("ok")
                }
            }
        },
        DEFAULT_MAX_RETRIES,
        DEFAULT_BASE_RETRY_MS,
        DEFAULT_RETRY_FACTOR,
    )
    .await;
    assert_eq!(result.unwrap(), "ok");
    assert_eq!(attempts.load(Ordering::SeqCst), 3);
}

#[tokio::test]
async fn test_retry_exhausted() {
    let result: Result<(), &str> = attempt_with_retry(
        || async { Err("always fail") },
        2,
        DEFAULT_BASE_RETRY_MS,
        DEFAULT_RETRY_FACTOR,
    )
    .await;
    assert!(result.is_err());
}

#[test]
fn test_encryption_roundtrip() {
    let key = base64::engine::general_purpose::STANDARD.encode(&[0u8; 32]);
    std::env::set_var("VPN_KEY", key);
    let data = b"hello world";
    let enc = encrypt_payload(data).unwrap();
    let dec = decrypt_payload(&enc).unwrap();
    assert_eq!(dec, data);
}

#[test]
fn test_encryption_tamper() {
    let key = base64::engine::general_purpose::STANDARD.encode(&[0u8; 32]);
    std::env::set_var("VPN_KEY", key);
    let data = b"test";
    let enc = encrypt_payload(data).unwrap();
    let mut bytes = base64::engine::general_purpose::STANDARD
        .decode(&enc)
        .unwrap();
    if bytes.len() > 10 {
        bytes[10] ^= 0x01;
    }
    let tampered = base64::engine::general_purpose::STANDARD.encode(&bytes);
    assert!(decrypt_payload(&tampered).is_err());
}
