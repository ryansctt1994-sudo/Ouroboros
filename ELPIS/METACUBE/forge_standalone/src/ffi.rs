//! FFI (Foreign Function Interface) module
//!
//! Provides C-compatible API for integration with Python and other languages

use std::ptr;
use crate::{ForgeEngine, ConsciousnessState};

/// Create a new Forge engine
#[no_mangle]
pub extern "C" fn forge_engine_new(num_agents: usize) -> *mut ForgeEngine {
    let engine = Box::new(ForgeEngine::new(num_agents));
    Box::into_raw(engine)
}

/// Free a Forge engine
#[no_mangle]
pub extern "C" fn forge_engine_free(engine: *mut ForgeEngine) {
    if !engine.is_null() {
        unsafe {
            drop(Box::from_raw(engine));
        }
    }
}

/// Perform one consensus round
#[no_mangle]
pub extern "C" fn forge_engine_consensus_round(engine: *mut ForgeEngine) -> u8 {
    if engine.is_null() {
        return 0;
    }
    
    unsafe {
        let result = (*engine).consensus_round();
        if result.consensus_achieved { 1 } else { 0 }
    }
}

/// Get network gamma metric
#[no_mangle]
pub extern "C" fn forge_engine_get_network_gamma(engine: *const ForgeEngine) -> f64 {
    if engine.is_null() {
        return 0.0;
    }
    
    unsafe {
        let metrics = (*engine).network_metrics();
        metrics.mean_gamma
    }
}

/// Update agent state from C array
#[no_mangle]
pub extern "C" fn forge_engine_update_agent_array(
    engine: *mut ForgeEngine,
    agent_id: usize,
    values: *const f64,
    values_len: usize,
) -> i32 {
    if engine.is_null() || values.is_null() {
        return -1;
    }
    
    // Bounds check
    if values_len < 7 {
        return -3;
    }
    
    unsafe {
        let slice = std::slice::from_raw_parts(values, 7);
        let vals: [f64; 7] = slice.try_into().unwrap();
        
        let state = ConsciousnessState::new(vals);
        match (*engine).update_agent(agent_id, state) {
            Ok(_) => 0,
            Err(_) => -2,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ffi_engine_lifecycle() {
        // Create engine via FFI (need at least 4 agents for BFT)
        let engine = forge_engine_new(5);
        assert!(!engine.is_null());
        
        // Get gamma
        let gamma = forge_engine_get_network_gamma(engine);
        assert!(gamma >= 0.0);
        
        // Free engine
        forge_engine_free(engine);
    }
}
