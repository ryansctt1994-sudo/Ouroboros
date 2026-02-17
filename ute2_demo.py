#!/usr/bin/env python3
"""
Example demonstration of the UTe2 Hybrid AI-Powered Simulation System

This script demonstrates the complete workflow:
1. Loading configuration
2. Initializing the hybrid execution engine
3. Running simulations in different modes
4. Using AI advisor suggestions
5. Generating phase diagrams
6. Checking cache performance
"""

import yaml
from pathlib import Path
import numpy as np

from ute2_hybrid_engine import HybridExecutionEngine
from ute2_simulation import UTe2SimulationEngine
from ute2_ai_advisor import AIAdvisor

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def main():
    print_section("UTe₂ Hybrid System Demonstration")
    
    # 1. Load configuration
    print("📁 Loading configuration...")
    config_path = Path('hybrid_config.yaml')
    if not config_path.exists():
        print("❌ Configuration file not found!")
        return
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    print(f"✅ Configuration loaded from {config_path}")
    
    # 2. Initialize hybrid execution engine
    print_section("Initializing Hybrid Execution Engine")
    engine = HybridExecutionEngine(config, 'knowledge_base.json')
    print(f"✅ Engine initialized in {engine.current_mode.value} mode")
    print(f"   Internet available: {engine.internet_available}")
    
    # 3. Get AI advisor suggestions
    print_section("AI Advisor Suggestions")
    
    # Get device-specific recommendations
    device_type = 'laptop'
    device_recs = engine.advisor.get_device_recommendations(device_type)
    print(f"💡 Recommendations for {device_type}:")
    if device_recs:
        print(f"   K-grid: {device_recs.get('recommended_k_grid', 'N/A')}")
        print(f"   Precision: {device_recs.get('precision', 'N/A')}")
        if 'tips' in device_recs:
            print(f"   Tips:")
            for tip in device_recs['tips'][:3]:  # Show first 3 tips
                print(f"     • {tip}")
    
    # Get parameter suggestions for reentrant region
    suggestions = engine.advisor.suggest_parameters(
        temperature=0.5,
        magnetic_field=50.0,  # In reentrant region
        device_type=device_type
    )
    print(f"\n🎯 Suggested parameters for H=50T (reentrant region):")
    for key, value in suggestions.items():
        print(f"   {key}: {value}")
    
    # 4. Run simulations in different modes
    print_section("Running Simulations")
    
    # Test parameters
    test_cases = [
        {'temperature_K': 0.5, 'magnetic_field_T': 0.0, 'k_grid_size': 8, 'label': 'Low-field SC'},
        {'temperature_K': 0.5, 'magnetic_field_T': 50.0, 'k_grid_size': 8, 'label': 'Reentrant SC'},
        {'temperature_K': 2.0, 'magnetic_field_T': 10.0, 'k_grid_size': 8, 'label': 'Normal state'},
    ]
    
    # Test offline mode
    print("🔧 Testing OFFLINE mode:")
    engine.set_mode('offline')
    
    for i, params in enumerate(test_cases):
        task_id = engine.submit_task({k: v for k, v in params.items() if k != 'label'})
        result = engine.execute_next_task()
        
        if result and result.success:
            gap_mean = result.result.gap_function.mean()
            print(f"  ✅ {params['label']}: Gap={gap_mean:.6f} eV (time={result.execution_time:.3f}s)")
        else:
            print(f"  ❌ {params['label']}: Failed")
    
    # Test local mode with caching
    print("\n🔧 Testing LOCAL mode with caching:")
    engine.set_mode('local')
    
    # Run same simulation twice to test cache
    params = test_cases[0].copy()
    params.pop('label')
    
    # First run (cache miss)
    task_id = engine.submit_task(params)
    result1 = engine.execute_next_task()
    print(f"  First run: time={result1.execution_time:.3f}s, cache_hit={result1.metadata.get('cache_hit', False)}")
    
    # Second run (cache hit)
    task_id = engine.submit_task(params)
    result2 = engine.execute_next_task()
    print(f"  Second run: time={result2.execution_time:.3f}s, cache_hit={result2.metadata.get('cache_hit', False)}")
    print(f"  ⚡ Speedup: {result1.execution_time / max(result2.execution_time, 0.001):.1f}x")
    
    # 5. Generate phase diagram
    print_section("Phase Diagram Generation")
    
    print("📊 Generating T-H phase diagram...")
    sim_engine = UTe2SimulationEngine(config)
    phase_data = sim_engine.generate_phase_diagram(
        temperature_range=(0.1, 2.0),
        field_range=(0, 70),
        resolution=20  # Reduced for quick demo
    )
    
    print(f"✅ Phase diagram generated")
    print(f"   Temperature range: {phase_data['temperature'][0]:.1f} - {phase_data['temperature'][-1]:.1f} K")
    print(f"   Field range: {phase_data['magnetic_field'][0]:.1f} - {phase_data['magnetic_field'][-1]:.1f} T")
    print(f"   Resolution: {phase_data['phase'].shape}")
    
    # Count phases
    phases = phase_data['phase'].flatten()
    labels = phase_data['labels']
    for phase_id, label in labels.items():
        count = np.sum(phases == phase_id)
        percentage = count / len(phases) * 100
        print(f"   {label}: {percentage:.1f}% of phase space")
    
    # 6. System status and statistics
    print_section("System Status")
    
    status = engine.get_status()
    print("📊 Execution Engine:")
    print(f"   Current mode: {status['current_mode']}")
    print(f"   Queued tasks: {status['queued_tasks']}")
    print(f"   Completed tasks: {status['completed_tasks']}")
    
    print("\n💾 Cache:")
    cache_stats = status['cache_stats']
    print(f"   Enabled: {cache_stats['enabled']}")
    print(f"   Entries: {cache_stats['total_entries']}")
    print(f"   Size: {cache_stats['total_size_mb']:.3f} MB / {cache_stats['max_size_mb']} MB")
    print(f"   Accesses: {cache_stats['total_accesses']}")
    
    print("\n🤖 AI Advisor:")
    advisor_stats = status['advisor_stats']
    print(f"   Enabled: {advisor_stats['enabled']}")
    print(f"   Offline mode: {advisor_stats['offline_mode']}")
    print(f"   Simulations recorded: {advisor_stats['total_simulations_recorded']}")
    
    # 7. Troubleshooting example
    print_section("AI Advisor - Troubleshooting")
    
    error_types = ['convergence_failure', 'memory_overflow']
    for error_type in error_types:
        solutions = engine.advisor.get_troubleshooting_advice(error_type)
        print(f"💡 {error_type}:")
        for i, solution in enumerate(solutions[:2], 1):  # Show first 2 solutions
            print(f"   {i}. {solution}")
        print()
    
    # Final summary
    print_section("Summary")
    print("✅ All demonstrations completed successfully!")
    print(f"   Total simulations run: {status['completed_tasks']}")
    print(f"   Cache entries created: {cache_stats['total_entries']}")
    print(f"   AI learning records: {advisor_stats['total_simulations_recorded']}")
    print("\n📚 See UTE2_HYBRID_SYSTEM_README.md for full documentation")
    print("🎨 Try ute2_dashboard.ipynb for interactive visualizations")
    

if __name__ == '__main__':
    main()
