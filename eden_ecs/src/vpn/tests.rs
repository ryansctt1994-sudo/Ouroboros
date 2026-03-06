use super::*;
use std::time::Duration;

#[test]
fn test_health_scoring() {
    let mut health = EndpointHealth::new(Duration::from_secs(60));
    health.record_success("ep1", Duration::from_millis(100));
    health.record_success("ep1", Duration::from_millis(150));
    health.record_failure("ep2");
    health.record_success("ep2", Duration::from_millis(200)); // ep2 now has both success and failure
    health.cooldown_until.remove("ep2");

    let selected = health.select_healthy_endpoint();
    assert!(selected.is_some());
}

#[tokio::test]
async fn test_retry_success() {
    let mut attempts = 0;
    let result = attempt_with_retry(
        || async {
            attempts += 1;
            if attempts < 3 { Err("fail") } else { Ok("ok") }
        },
        5,
        10,
        2.0,
    ).await;
    assert_eq!(result.unwrap(), "ok");
    assert_eq!(attempts, 3);
}

#[tokio::test]
async fn test_retry_exhausted() {
    let result: Result<(), &str> = attempt_with_retry(
        || async { Err("always fail") },
        2,
        10,
        2.0,
    ).await;
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
    let mut bytes = base64::engine::general_purpose::STANDARD.decode(&enc).unwrap();
    if bytes.len() > 10 { bytes[10] ^= 0x01; }
    let tampered = base64::engine::general_purpose::STANDARD.encode(&bytes);
    assert!(decrypt_payload(&tampered).is_err());
}
