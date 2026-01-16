"""Example usage of the Magnetar Elastic Coherence Engine.

This script demonstrates how to use the Magnetar Coherence Engine
to analyze signals and generate coherence metrics.
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.magnetar_coherence_engine import (
    MagnetarElasticCoherenceEngine,
    CoherenceAnalyzer,
    PHI, MAGNETAR_FREQ, SCHUMANN_FREQ
)


def example_basic_usage():
    """Basic usage example."""
    print("=" * 70)
    print("Example 1: Basic Usage")
    print("=" * 70)
    
    # Create the engine
    engine = MagnetarElasticCoherenceEngine()
    
    # Create a test signal (magnetar frequency)
    t = np.linspace(0, 1, 1000)
    signal = np.sin(2 * np.pi * MAGNETAR_FREQ * t)
    
    # Process the signal
    result = engine(signal)
    
    print(f"Input signal shape: {signal.shape}")
    print(f"Output signal shape: {result['output'].shape}")
    print(f"Coherence score: {result['coherence_score']:.4f}")
    print()


def example_with_analyzer():
    """Example using the CoherenceAnalyzer."""
    print("=" * 70)
    print("Example 2: Using CoherenceAnalyzer")
    print("=" * 70)
    
    # Create analyzer
    analyzer = CoherenceAnalyzer()
    
    # Generate different test signals
    signals = {
        'magnetar': analyzer.generate_test_signal(1000, 'magnetar'),
        'schumann': analyzer.generate_test_signal(1000, 'schumann'),
        'mixed': analyzer.generate_test_signal(1000, 'mixed'),
    }
    
    # Analyze each signal
    for name, sig in signals.items():
        analysis = analyzer.analyze(sig, label=name)
        metrics = analyzer.compute_metrics(analysis)
        
        print(f"\n{name.upper()} Signal:")
        print(f"  Coherence Score:  {metrics['coherence_score']:.4f}")
        print(f"  SNR Improvement:  {metrics['snr_improvement']:.4f}x")
        print(f"  Phase Stability:  {metrics['phase_stability']:.4f}")
        print(f"  Spectral Purity:  {metrics['spectral_purity']:.4f}")
        print(f"  Amplification:    {metrics['amplification_factor']:.4f}x")
    
    print()


def example_custom_modules():
    """Example with custom module parameters."""
    print("=" * 70)
    print("Example 3: Custom Module Parameters")
    print("=" * 70)
    
    from src.magnetar_coherence_engine import PhaseObfuscationDetector
    
    # Create custom detector with higher sensitivity
    detector = PhaseObfuscationDetector(
        n_harmonics=12,
        sensitivity=0.05,
        correction_strength=0.9
    )
    
    # Create signal with phase jump
    t = np.linspace(0, 10, 1000)
    signal = np.sin(2 * np.pi * t)
    signal[500:] += 0.5  # Add phase discontinuity
    
    # Process
    corrected = detector(signal)
    
    print(f"Original signal std: {np.std(signal):.4f}")
    print(f"Corrected signal std: {np.std(corrected):.4f}")
    print(f"Phase jump detected and corrected!")
    print()


def example_diagnostics():
    """Example showing detailed diagnostics."""
    print("=" * 70)
    print("Example 4: Detailed Diagnostics")
    print("=" * 70)
    
    engine = MagnetarElasticCoherenceEngine()
    
    # Create a complex signal
    t = np.linspace(0, 1, 1000)
    signal = (
        np.sin(2 * np.pi * MAGNETAR_FREQ * t) +
        0.3 * np.sin(2 * np.pi * SCHUMANN_FREQ * t) +
        0.1 * np.random.randn(1000)
    )
    
    # Process with diagnostics
    result = engine(signal, return_diagnostics=True)
    
    print(f"Overall Coherence: {result['coherence_score']:.4f}")
    print("\nModule-by-Module Coherence:")
    
    breakdown = result['diagnostics']['coherence_breakdown']
    for module_name, score in breakdown.items():
        bar = '█' * int(score * 20)
        print(f"  {module_name:30s} [{bar:20s}] {score:.4f}")
    
    print()


def example_integration_with_ouroboros():
    """Example showing integration with Ouroboros components."""
    print("=" * 70)
    print("Example 5: Integration with Ouroboros")
    print("=" * 70)
    
    try:
        from ouroboros_processor import OuroborosVirtualProcessor
        
        # Create processor
        processor = OuroborosVirtualProcessor(radius=1.0, lambda_=0.3)
        
        # Run ternary cycle
        state = processor.ternary_cycle([0.4, 0.2, 0.4])
        
        # Validate coherence
        engine = MagnetarElasticCoherenceEngine()
        
        # Convert state to signal (repeat to get adequate length)
        signal = np.tile(state, 334)  # ~1000 samples
        
        result = engine(signal)
        
        print(f"Ouroboros state: {state}")
        print(f"State coherence: {result['coherence_score']:.4f}")
        
        if result['coherence_score'] > 0.7:
            print("✓ State has excellent coherence!")
        elif result['coherence_score'] > 0.5:
            print("✓ State has good coherence")
        else:
            print("⚠ State coherence could be improved")
        
    except ImportError:
        print("OuroborosVirtualProcessor not available")
        print("This example shows how to integrate when the processor is available")
    
    print()


def example_phi_alignment():
    """Example demonstrating φ (golden ratio) alignment."""
    print("=" * 70)
    print("Example 6: Golden Ratio (Φ) Alignment")
    print("=" * 70)
    
    from src.magnetar_coherence_engine import CoherenceRegenerator
    
    # Create signal
    t = np.linspace(0, 10, 1000)
    signal = np.sin(2 * np.pi * t)
    
    # Add noise to degrade coherence
    degraded = signal + 0.2 * np.random.randn(1000)
    
    # Regenerate with φ alignment
    regenerator_phi = CoherenceRegenerator(phi_alignment=True, regeneration_strength=0.8)
    regenerator_no_phi = CoherenceRegenerator(phi_alignment=False, regeneration_strength=0.8)
    
    regenerated_phi = regenerator_phi(degraded)
    regenerated_no_phi = regenerator_no_phi(degraded)
    
    # Compare
    mse_phi = np.mean((signal - regenerated_phi)**2)
    mse_no_phi = np.mean((signal - regenerated_no_phi)**2)
    
    print(f"Golden Ratio (Φ): {PHI:.6f}")
    print(f"\nMSE with Φ alignment:    {mse_phi:.6f}")
    print(f"MSE without Φ alignment: {mse_no_phi:.6f}")
    print(f"\nImprovement: {((mse_no_phi - mse_phi) / mse_no_phi * 100):.2f}%")
    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "    MAGNETAR ELASTIC COHERENCE ENGINE - EXAMPLES    ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")
    
    example_basic_usage()
    example_with_analyzer()
    example_custom_modules()
    example_diagnostics()
    example_integration_with_ouroboros()
    example_phi_alignment()
    
    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print()
    print("For more information, see MAGNETAR_COHERENCE_ENGINE_README.md")
    print()


if __name__ == "__main__":
    main()
