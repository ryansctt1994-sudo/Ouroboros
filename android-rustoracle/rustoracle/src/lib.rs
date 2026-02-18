//! Rust Oracle - Token Constraint Enforcement for Android
//!
//! This module implements high-performance token stream validation with
//! unsafe token exclusion and constraint mask enforcement.
//!
//! Performance target: <100μs latency for constraint checking

use jni::JNIEnv;
use jni::objects::{JClass, JIntArray, JLongArray};
use jni::sys::{jint, jlong, jboolean};
use std::time::Instant;

/// Token constraint configuration
#[repr(C)]
pub struct TokenConstraint {
    /// Minimum allowed token value (inclusive)
    pub min_token: i32,
    /// Maximum allowed token value (inclusive)
    pub max_token: i32,
    /// Whether to mask (true) or reject (false) unsafe tokens
    pub mask_mode: bool,
    /// Mask replacement value (used when mask_mode is true)
    pub mask_value: i32,
}

impl TokenConstraint {
    pub fn new(min_token: i32, max_token: i32, mask_mode: bool, mask_value: i32) -> Self {
        Self {
            min_token,
            max_token,
            mask_mode,
            mask_value,
        }
    }
    
    /// Check if a token is within allowed constraints
    #[inline]
    pub fn is_safe(&self, token: i32) -> bool {
        token >= self.min_token && token <= self.max_token
    }
    
    /// Enforce constraint on a token
    #[inline]
    pub fn enforce(&self, token: i32) -> Option<i32> {
        if self.is_safe(token) {
            Some(token)
        } else if self.mask_mode {
            Some(self.mask_value)
        } else {
            None
        }
    }
}

/// Token stream validator with latency tracking
pub struct TokenValidator {
    constraint: TokenConstraint,
    total_tokens: u64,
    blocked_tokens: u64,
    masked_tokens: u64,
    total_latency_ns: u64,
}

impl TokenValidator {
    pub fn new(constraint: TokenConstraint) -> Self {
        Self {
            constraint,
            total_tokens: 0,
            blocked_tokens: 0,
            masked_tokens: 0,
            total_latency_ns: 0,
        }
    }
    
    /// Validate a batch of tokens and return filtered results
    pub fn validate_batch(&mut self, tokens: &[i32]) -> (Vec<i32>, u64) {
        let start = Instant::now();
        let mut validated = Vec::with_capacity(tokens.len());
        
        for &token in tokens {
            self.total_tokens += 1;
            
            match self.constraint.enforce(token) {
                Some(safe_token) => {
                    if safe_token != token {
                        self.masked_tokens += 1;
                    }
                    validated.push(safe_token);
                }
                None => {
                    self.blocked_tokens += 1;
                    // Token is rejected, not added to output
                }
            }
        }
        
        let latency_ns = start.elapsed().as_nanos() as u64;
        self.total_latency_ns += latency_ns;
        
        (validated, latency_ns)
    }
    
    pub fn get_stats(&self) -> ValidationStats {
        ValidationStats {
            total_tokens: self.total_tokens,
            blocked_tokens: self.blocked_tokens,
            masked_tokens: self.masked_tokens,
            mean_latency_ns: if self.total_tokens > 0 {
                self.total_latency_ns / self.total_tokens
            } else {
                0
            },
        }
    }
    
    pub fn reset_stats(&mut self) {
        self.total_tokens = 0;
        self.blocked_tokens = 0;
        self.masked_tokens = 0;
        self.total_latency_ns = 0;
    }
}

#[repr(C)]
pub struct ValidationStats {
    pub total_tokens: u64,
    pub blocked_tokens: u64,
    pub masked_tokens: u64,
    pub mean_latency_ns: u64,
}

// JNI bindings for Android

/// Create a new TokenValidator
/// Returns a pointer to the validator (as jlong)
#[no_mangle]
pub extern "C" fn Java_com_aiospandora_rustoracle_RustOracle_nativeCreateValidator(
    _env: JNIEnv,
    _class: JClass,
    min_token: jint,
    max_token: jint,
    mask_mode: jboolean,
    mask_value: jint,
) -> jlong {
    let constraint = TokenConstraint::new(
        min_token as i32,
        max_token as i32,
        mask_mode != 0,
        mask_value as i32,
    );
    let validator = Box::new(TokenValidator::new(constraint));
    Box::into_raw(validator) as jlong
}

/// Destroy a TokenValidator
#[no_mangle]
pub extern "C" fn Java_com_aiospandora_rustoracle_RustOracle_nativeDestroyValidator(
    _env: JNIEnv,
    _class: JClass,
    validator_ptr: jlong,
) {
    if validator_ptr != 0 {
        unsafe {
            drop(Box::from_raw(validator_ptr as *mut TokenValidator));
        }
    }
}

/// Validate a batch of tokens
/// Returns the latency in nanoseconds
#[no_mangle]
pub extern "C" fn Java_com_aiospandora_rustoracle_RustOracle_nativeValidateBatch(
    env: JNIEnv,
    _class: JClass,
    validator_ptr: jlong,
    input_tokens: JIntArray,
    output_tokens: JIntArray,
) -> jlong {
    if validator_ptr == 0 {
        return -1;
    }
    
    unsafe {
        let validator = &mut *(validator_ptr as *mut TokenValidator);
        
        // Get input tokens from Java array
        let input_len = env.get_array_length(&input_tokens).unwrap_or(0) as usize;
        let mut tokens = vec![0i32; input_len];
        if env.get_int_array_region(&input_tokens, 0, &mut tokens).is_err() {
            return -2;
        }
        
        // Validate batch
        let (validated, latency_ns) = validator.validate_batch(&tokens);
        
        // Copy validated tokens to output array
        let output_len = env.get_array_length(&output_tokens).unwrap_or(0) as usize;
        let copy_len = validated.len().min(output_len);
        if copy_len > 0 {
            if env.set_int_array_region(&output_tokens, 0, &validated[..copy_len]).is_err() {
                return -3;
            }
        }
        
        latency_ns as jlong
    }
}

/// Get validation statistics
/// Returns stats as a long array: [total_tokens, blocked_tokens, masked_tokens, mean_latency_ns]
#[no_mangle]
pub extern "C" fn Java_com_aiospandora_rustoracle_RustOracle_nativeGetStats(
    env: JNIEnv,
    _class: JClass,
    validator_ptr: jlong,
    stats_array: JLongArray,
) {
    if validator_ptr == 0 {
        return;
    }
    
    unsafe {
        let validator = &*(validator_ptr as *const TokenValidator);
        let stats = validator.get_stats();
        
        let stats_data = [
            stats.total_tokens as i64,
            stats.blocked_tokens as i64,
            stats.masked_tokens as i64,
            stats.mean_latency_ns as i64,
        ];
        
        let _ = env.set_long_array_region(&stats_array, 0, &stats_data);
    }
}

/// Reset validation statistics
#[no_mangle]
pub extern "C" fn Java_com_aiospandora_rustoracle_RustOracle_nativeResetStats(
    _env: JNIEnv,
    _class: JClass,
    validator_ptr: jlong,
) {
    if validator_ptr == 0 {
        return;
    }
    
    unsafe {
        let validator = &mut *(validator_ptr as *mut TokenValidator);
        validator.reset_stats();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_token_constraint_safe() {
        let constraint = TokenConstraint::new(0, 100, false, 0);
        assert!(constraint.is_safe(50));
        assert!(constraint.is_safe(0));
        assert!(constraint.is_safe(100));
        assert!(!constraint.is_safe(-1));
        assert!(!constraint.is_safe(101));
    }
    
    #[test]
    fn test_token_constraint_reject_mode() {
        let constraint = TokenConstraint::new(0, 100, false, 0);
        assert_eq!(constraint.enforce(50), Some(50));
        assert_eq!(constraint.enforce(-1), None);
        assert_eq!(constraint.enforce(101), None);
    }
    
    #[test]
    fn test_token_constraint_mask_mode() {
        let constraint = TokenConstraint::new(0, 100, true, 0);
        assert_eq!(constraint.enforce(50), Some(50));
        assert_eq!(constraint.enforce(-1), Some(0));
        assert_eq!(constraint.enforce(101), Some(0));
    }
    
    #[test]
    fn test_validator_batch() {
        let constraint = TokenConstraint::new(0, 100, false, 0);
        let mut validator = TokenValidator::new(constraint);
        
        let tokens = vec![50, -1, 75, 101, 25];
        let (validated, latency_ns) = validator.validate_batch(&tokens);
        
        assert_eq!(validated, vec![50, 75, 25]);
        assert!(latency_ns > 0);
        
        let stats = validator.get_stats();
        assert_eq!(stats.total_tokens, 5);
        assert_eq!(stats.blocked_tokens, 2);
        assert_eq!(stats.masked_tokens, 0);
    }
    
    #[test]
    fn test_validator_mask_mode() {
        let constraint = TokenConstraint::new(0, 100, true, 999);
        let mut validator = TokenValidator::new(constraint);
        
        let tokens = vec![50, -1, 75, 101, 25];
        let (validated, _) = validator.validate_batch(&tokens);
        
        assert_eq!(validated, vec![50, 999, 75, 999, 25]);
        
        let stats = validator.get_stats();
        assert_eq!(stats.total_tokens, 5);
        assert_eq!(stats.blocked_tokens, 0);
        assert_eq!(stats.masked_tokens, 2);
    }
}
