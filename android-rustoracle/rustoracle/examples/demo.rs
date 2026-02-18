//! Example: Standalone Rust token validation demo
//!
//! This example demonstrates the token validation functionality
//! without requiring Android/JNI.

use rustoracle::{TokenConstraint, TokenValidator};

fn main() {
    println!("=== RustOracle Token Validation Demo ===\n");
    
    // Example 1: Reject Mode
    println!("Example 1: REJECT MODE");
    println!("Configuration: min=0, max=100, reject unsafe tokens");
    
    let constraint = TokenConstraint::new(0, 100, false, 0);
    let mut validator = TokenValidator::new(constraint);
    
    let test_tokens = vec![50, -10, 75, 150, 25, 100, -5, 0];
    println!("Input tokens: {:?}", test_tokens);
    
    let (validated, latency_ns) = validator.validate_batch(&test_tokens);
    println!("Validated tokens: {:?}", validated);
    println!("Latency: {} ns ({:.2} μs)", latency_ns, latency_ns as f64 / 1000.0);
    
    let stats = validator.get_stats();
    println!("Statistics:");
    println!("  Total: {}", stats.total_tokens);
    println!("  Safe: {} ({:.1}%)", stats.total_tokens - stats.blocked_tokens, 
             (stats.total_tokens - stats.blocked_tokens) as f64 / stats.total_tokens as f64 * 100.0);
    println!("  Blocked: {} ({:.1}%)", stats.blocked_tokens, 
             stats.blocked_tokens as f64 / stats.total_tokens as f64 * 100.0);
    
    println!("\n{}", "=".repeat(60));
    
    // Example 2: Mask Mode
    println!("\nExample 2: MASK MODE");
    println!("Configuration: min=0, max=100, mask unsafe tokens with 999");
    
    let constraint = TokenConstraint::new(0, 100, true, 999);
    let mut validator = TokenValidator::new(constraint);
    
    let test_tokens = vec![50, -10, 75, 150, 25, 100, -5, 0];
    println!("Input tokens: {:?}", test_tokens);
    
    let (validated, latency_ns) = validator.validate_batch(&test_tokens);
    println!("Validated tokens: {:?}", validated);
    println!("Latency: {} ns ({:.2} μs)", latency_ns, latency_ns as f64 / 1000.0);
    
    let stats = validator.get_stats();
    println!("Statistics:");
    println!("  Total: {}", stats.total_tokens);
    println!("  Safe: {} ({:.1}%)", stats.total_tokens - stats.masked_tokens, 
             (stats.total_tokens - stats.masked_tokens) as f64 / stats.total_tokens as f64 * 100.0);
    println!("  Masked: {} ({:.1}%)", stats.masked_tokens, 
             stats.masked_tokens as f64 / stats.total_tokens as f64 * 100.0);
    
    println!("\n{}", "=".repeat(60));
    
    // Example 3: Performance Test
    println!("\nExample 3: PERFORMANCE TEST");
    println!("Testing with large batch (1000 tokens)");
    
    let constraint = TokenConstraint::new(0, 1000, true, 0);
    let mut validator = TokenValidator::new(constraint);
    
    // Generate 1000 random-ish tokens
    let large_batch: Vec<i32> = (0..1000).map(|i| {
        if i % 5 == 0 { i * 2 } else { i }  // Some will be > 1000
    }).collect();
    
    let (validated, latency_ns) = validator.validate_batch(&large_batch);
    println!("Batch size: {}", large_batch.len());
    println!("Output size: {}", validated.len());
    println!("Latency: {} ns ({:.2} μs)", latency_ns, latency_ns as f64 / 1000.0);
    println!("Per-token latency: {:.2} ns ({:.4} μs)", 
             latency_ns as f64 / large_batch.len() as f64,
             latency_ns as f64 / large_batch.len() as f64 / 1000.0);
    
    let stats = validator.get_stats();
    println!("Statistics:");
    println!("  Total: {}", stats.total_tokens);
    println!("  Safe: {}", stats.total_tokens - stats.masked_tokens);
    println!("  Masked: {}", stats.masked_tokens);
    println!("  Mean latency: {} ns ({:.2} μs)", stats.mean_latency_ns, 
             stats.mean_latency_ns as f64 / 1000.0);
    
    // Latency target check
    let latency_us = latency_ns as f64 / 1000.0;
    println!("\nLatency Target (<100μs): {}", 
             if latency_us < 100.0 { "✓ MET" } else { "✗ MISSED" });
    
    println!("\n{}", "=".repeat(60));
    println!("\nDemo complete!");
}
