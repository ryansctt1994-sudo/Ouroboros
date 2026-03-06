//! Encryption helpers using AES-GCM. Key must be provided via env var `VPN_KEY` (32 bytes base64).
use aes_gcm::{
    aead::{Aead, KeyInit},
    Aes256Gcm, Nonce,
};
use base64::{engine::general_purpose::STANDARD as BASE64, Engine};
use rand::RngCore;
use std::env;

const NONCE_LEN: usize = 12;
const VERSION: u8 = 1;

fn get_key() -> Result<[u8; 32], String> {
    let key_b64 = env::var("VPN_KEY").map_err(|_| "VPN_KEY env var not set".to_string())?;
    let key_bytes = BASE64.decode(key_b64).map_err(|e| format!("Invalid base64 key: {}", e))?;
    if key_bytes.len() != 32 {
        return Err(format!("Key must be 32 bytes, got {}", key_bytes.len()));
    }
    let mut key = [0u8; 32];
    key.copy_from_slice(&key_bytes);
    Ok(key)
}

pub fn encrypt_payload(plaintext: &[u8]) -> Result<String, String> {
    let key = get_key()?;
    let cipher = Aes256Gcm::new_from_slice(&key).map_err(|e| format!("Cipher init error: {}", e))?;

    let mut nonce_buf = [0u8; NONCE_LEN];
    rand::thread_rng().fill_bytes(&mut nonce_buf);
    let nonce = Nonce::from_slice(&nonce_buf);

    let ciphertext = cipher.encrypt(nonce, plaintext).map_err(|e| format!("Encryption failed: {}", e))?;

    // Envelope: version(1) || nonce(12) || ciphertext+tag
    let mut envelope = Vec::with_capacity(1 + NONCE_LEN + ciphertext.len());
    envelope.push(VERSION);
    envelope.extend_from_slice(nonce.as_slice());
    envelope.extend_from_slice(&ciphertext);

    Ok(BASE64.encode(envelope))
}

pub fn decrypt_payload(encrypted_b64: &str) -> Result<Vec<u8>, String> {
    let key = get_key()?;
    let cipher = Aes256Gcm::new_from_slice(&key).map_err(|e| format!("Cipher init error: {}", e))?;

    let envelope = BASE64.decode(encrypted_b64).map_err(|e| format!("Invalid base64: {}", e))?;
    if envelope.len() < 1 + NONCE_LEN + 16 {
        return Err("Envelope too short".to_string());
    }

    let version = envelope[0];
    if version != VERSION {
        return Err(format!("Unsupported version {}", version));
    }

    let nonce = Nonce::from_slice(&envelope[1..1 + NONCE_LEN]);
    let ciphertext = &envelope[1 + NONCE_LEN..];

    let plaintext = cipher.decrypt(nonce, ciphertext).map_err(|e| format!("Decryption failed: {}", e))?;
    Ok(plaintext)
}
