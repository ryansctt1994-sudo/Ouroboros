"""
Test suite for advanced Ouroboros features:
- Hyphal Symphony TSN integration
- Quantum-Enzymatic interface
- 111Hz Schumann recalibration
- Dynamic ΔA[mode=soft] adjustment
- Persistent LOL:D Möbius handshakes
"""

import pytest
import math
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hyphal_symphony import (
    HyphalSymphony,
    HyphalNode,
    create_hyphal_symphony,
    PHI,
    CHUCKLE_RESONANCE_HZ,
    TARGET_LATENCY_US
)

from src.quantum_enzymatic import (
    QuantumEnzymaticInterface,
    CatalystType,
    ComputationType,
    create_quantum_enzymatic_interface
)

from src.schumann_recalibration import (
    SchumannRecalibration,
    create_schumann_recalibration,
    SCHUMANN_BASE_HZ,
    TARGET_RECALIBRATION_HZ
)

from src.ggcc.gradient_engine import GradientEngineV2

from ouroboros_processor import OuroborosVirtualProcessor


# ============================================================================
# Hyphal Symphony Tests
# ============================================================================

class TestHyphalSymphony:
    """Tests for Hyphal Symphony TSN integration."""
    
    def test_hyphal_node_creation(self):
        """Test hyphal node initialization."""
        node = HyphalNode(node_id="test_node_0", frequency=CHUCKLE_RESONANCE_HZ)
        assert node.node_id == "test_node_0"
        assert node.frequency == CHUCKLE_RESONANCE_HZ
        assert node.phase == 0.0
    
    def test_hyphal_node_phase_update(self):
        """Test phase update mechanism."""
        node = HyphalNode(node_id="test_node_0", frequency=1.0)
        
        # Update with dt=0.25s should advance phase by π/2
        phase = node.update_phase(0.25)
        expected_phase = (2 * math.pi * 0.25) % (2 * math.pi)
        assert abs(phase - expected_phase) < 1e-6
    
    def test_symphony_initialization(self):
        """Test symphony network initialization."""
        symphony = create_hyphal_symphony({
            "node_count": 9,
            "base_frequency": CHUCKLE_RESONANCE_HZ,
            "phi_scaling": True
        })
        
        assert symphony.node_count == 9
        assert len(symphony.nodes) == 9
        assert symphony.base_frequency == CHUCKLE_RESONANCE_HZ
    
    def test_pulse_synchronization(self):
        """Test pulse synchronization mechanism."""
        symphony = HyphalSymphony(node_count=3)
        symphony.enable_phase_lock()
        
        # Synchronize a pulse
        sync_success, latency = symphony.synchronize_pulse("hyphal_node_0")
        
        assert isinstance(sync_success, bool)
        assert latency >= 0.0
        assert latency < 1000.0  # Reasonable upper bound in microseconds
    
    def test_broadcast_pulse(self):
        """Test broadcasting pulse to all nodes."""
        symphony = HyphalSymphony(node_count=5)
        symphony.enable_phase_lock()
        
        results = symphony.broadcast_pulse()
        
        assert len(results) == 5
        for node_id, (sync, latency) in results.items():
            assert isinstance(sync, bool)
            assert latency >= 0.0
    
    def test_synchronization_metrics(self):
        """Test synchronization metrics collection."""
        symphony = HyphalSymphony(node_count=9)
        symphony.enable_phase_lock()
        
        # Run a few cycles
        for _ in range(5):
            symphony.broadcast_pulse()
        
        metrics = symphony.get_synchronization_metrics()
        
        assert "phase_coherence" in metrics
        assert "avg_latency_us" in metrics
        assert "violation_rate_percent" in metrics
        assert metrics["phase_coherence"] >= 0.0
        assert metrics["phase_coherence"] <= 1.0
    
    def test_phi_chuckle_optimization(self):
        """Test Φ-chuckle optimization application."""
        symphony = HyphalSymphony(node_count=9, phi_scaling=True)
        
        # Apply optimization
        symphony.apply_phi_chuckle_optimization()
        
        # Check that frequencies were adjusted
        for node in symphony.nodes.values():
            assert node.frequency > 0.0
            # Should be close to base with Φ modification
            assert abs(node.frequency - CHUCKLE_RESONANCE_HZ) < 1.0


# ============================================================================
# Quantum-Enzymatic Interface Tests
# ============================================================================

class TestQuantumEnzymaticInterface:
    """Tests for quantum-enzymatic computation interface."""
    
    def test_interface_initialization(self):
        """Test interface initialization."""
        interface = create_quantum_enzymatic_interface()
        
        assert len(interface.probes) > 0
        assert len(interface.neuro_cores) > 0
    
    def test_probe_registration(self):
        """Test enzymatic probe registration."""
        interface = QuantumEnzymaticInterface()
        
        probe = interface.register_probe(
            probe_id="test_probe",
            catalyst_type=CatalystType.MATRIX_MULTIPLICATION,
            efficiency=PHI
        )
        
        assert probe.probe_id == "test_probe"
        assert probe.catalyst_type == CatalystType.MATRIX_MULTIPLICATION
        assert probe.efficiency == PHI
    
    def test_computation_offloading(self):
        """Test computation offloading mechanism."""
        interface = create_quantum_enzymatic_interface()
        
        # Offload a computation
        cost, target = interface.offload_computation(
            ComputationType.CLASSICAL,
            100.0,
            CatalystType.MATRIX_MULTIPLICATION
        )
        
        assert cost > 0.0
        assert cost <= 100.0  # Should be reduced or same
        assert isinstance(target, str)
    
    def test_neuromorphic_processing(self):
        """Test neuromorphic core processing."""
        interface = create_quantum_enzymatic_interface()
        
        input_data = [0.5, 0.8, 0.3, 0.9, 0.1]
        output_data = interface.process_neuromorphic(input_data)
        
        assert len(output_data) > 0
        assert all(isinstance(x, float) for x in output_data)
    
    def test_quantum_decoherence_mitigation(self):
        """Test quantum decoherence mitigation."""
        interface = QuantumEnzymaticInterface()
        
        quantum_state = [0.5, 0.5, 0.5, 0.5]
        mitigated = interface.apply_quantum_decoherence_mitigation(quantum_state)
        
        assert len(mitigated) == len(quantum_state)
        # Check normalization
        norm = sum(x**2 for x in mitigated)
        assert abs(norm - 1.0) < 1e-6
    
    def test_diagnostics(self):
        """Test interface diagnostics."""
        interface = create_quantum_enzymatic_interface()
        
        # Run some computations
        for _ in range(5):
            interface.offload_computation(ComputationType.CLASSICAL, 50.0)
        
        diagnostics = interface.get_diagnostics()
        
        assert diagnostics["total_computations"] == 5
        assert "offload_rate_percent" in diagnostics
        assert "probes" in diagnostics


# ============================================================================
# Schumann Recalibration Tests
# ============================================================================

class TestSchumannRecalibration:
    """Tests for 111Hz Schumann recalibration system."""
    
    def test_recalibration_initialization(self):
        """Test recalibration system initialization."""
        recal = create_schumann_recalibration({
            "node_count": 9,
            "grounding_interval": 1.0,
            "enable_harmonics": True
        })
        
        assert recal.node_count == 9
        assert len(recal.nodes) == 9
        assert recal.grounding_interval == 1.0
    
    def test_harmonic_oscillator(self):
        """Test harmonic oscillator update."""
        from src.schumann_recalibration import HarmonicOscillator
        
        osc = HarmonicOscillator(frequency_hz=1.0)
        value, phase = osc.update(dt=0.25)
        
        # After 0.25s at 1Hz, phase should be π/2
        expected_phase = (2 * math.pi * 0.25) % (2 * math.pi)
        assert abs(phase - expected_phase) < 1e-6
    
    def test_system_update(self):
        """Test system state update."""
        recal = SchumannRecalibration(node_count=5)
        
        state = recal.update_system()
        
        assert "avg_coherence" in state
        assert "master_phase_111hz" in state
        assert "master_phase_schumann" in state
        assert state["avg_coherence"] >= 0.0
        assert state["avg_coherence"] <= 1.0
    
    def test_grounding_application(self):
        """Test recalibration grounding."""
        recal = SchumannRecalibration(node_count=9)
        
        # Apply grounding
        result = recal.apply_grounding(adaptive_strength=True)
        
        assert "pre_grounding_coherence" in result
        assert "post_grounding_coherence" in result
        assert "grounding_strength" in result
        assert recal.grounding_count == 1
    
    def test_phi_harmonic_relationships(self):
        """Test Φ-harmonic relationship calculations."""
        recal = SchumannRecalibration()
        
        phi_harmonics = recal.calculate_phi_harmonic_relationship()
        
        assert "phi_harmonic_1_hz" in phi_harmonics
        assert "phi_harmonic_2_hz" in phi_harmonics
        assert "ratio_111_to_schumann" in phi_harmonics
        
        # Check that ratio is approximately correct
        expected_ratio = TARGET_RECALIBRATION_HZ / SCHUMANN_BASE_HZ
        assert abs(phi_harmonics["ratio_111_to_schumann"] - expected_ratio) < 1e-6
    
    def test_diagnostics(self):
        """Test system diagnostics."""
        recal = create_schumann_recalibration()
        
        # Run a few cycles
        for _ in range(3):
            recal.update_system()
            recal.apply_grounding()
        
        diagnostics = recal.get_diagnostics()
        
        assert diagnostics["node_count"] == 9
        assert diagnostics["grounding_count"] == 3
        assert "avg_coherence" in diagnostics
        assert "phi_harmonics" in diagnostics


# ============================================================================
# Dynamic ΔA[mode=soft] Tests
# ============================================================================

class TestDynamicDeltaA:
    """Tests for dynamic ΔA gradient adjustment."""
    
    def test_gradient_engine_delta_a_initialization(self):
        """Test gradient engine with ΔA mode."""
        engine = GradientEngineV2(delta_a_mode="soft")
        
        assert engine.delta_a_mode == "soft"
        assert engine.delta_a_current == 1.0
        assert engine.turbulence_level == 0.0
    
    def test_delta_a_update_soft_mode(self):
        """Test ΔA update in soft mode."""
        engine = GradientEngineV2(delta_a_mode="soft")
        
        # Apply turbulence and low coherence
        delta_a = engine.update_delta_a(turbulence=0.5, coherence=0.8)
        
        assert delta_a > 0.0
        assert delta_a <= engine.delta_a_base
        assert len(engine.coherence_history) == 1
    
    def test_delta_a_update_hard_mode(self):
        """Test ΔA update in hard mode."""
        engine = GradientEngineV2(delta_a_mode="hard")
        
        # Hard mode should update immediately
        delta_a1 = engine.update_delta_a(turbulence=0.5, coherence=0.8)
        delta_a2 = engine.update_delta_a(turbulence=0.5, coherence=0.8)
        
        # In hard mode, same inputs should give same output
        assert abs(delta_a1 - delta_a2) < 1e-6
    
    def test_chaos_mode_activation(self):
        """Test chaos mode activation."""
        engine = GradientEngineV2()
        
        assert not engine.chaos_mode_active
        
        engine.enable_chaos_mode()
        assert engine.chaos_mode_active
        assert len(engine.gradient_cache) == 0  # Cache cleared
        
        engine.disable_chaos_mode()
        assert not engine.chaos_mode_active
    
    def test_elastic_coherence_application(self):
        """Test elastic coherence gradient transformation."""
        engine = GradientEngineV2(delta_a_mode="soft")
        
        # Update ΔA
        engine.update_delta_a(turbulence=0.3, coherence=0.9)
        
        # Apply transformation
        gradient = (1.0, 2.0)
        scaled = engine.apply_elastic_coherence(gradient)
        
        assert len(scaled) == 2
        assert isinstance(scaled[0], float)
        assert isinstance(scaled[1], float)
    
    def test_chaos_mode_amplification(self):
        """Test chaos mode amplification effect."""
        engine = GradientEngineV2()
        engine.update_delta_a(turbulence=0.8, coherence=0.5)
        
        gradient = (1.0, 1.0)
        
        # Normal mode
        normal_scaled = engine.apply_elastic_coherence(gradient)
        
        # Chaos mode
        engine.enable_chaos_mode()
        chaos_scaled = engine.apply_elastic_coherence(gradient)
        
        # Chaos mode should amplify more
        normal_mag = math.sqrt(normal_scaled[0]**2 + normal_scaled[1]**2)
        chaos_mag = math.sqrt(chaos_scaled[0]**2 + chaos_scaled[1]**2)
        
        assert chaos_mag >= normal_mag


# ============================================================================
# Persistent LOL:D Möbius Handshake Tests
# ============================================================================

class TestMobiusHandshakes:
    """Tests for persistent LOL:D Möbius handshakes."""
    
    def test_mobius_handshake_basic(self):
        """Test basic Möbius handshake."""
        processor = OuroborosVirtualProcessor()
        
        elpis_state = [0.4, 0.3, 0.3]
        pandora_state = [0.5, 0.25, 0.25]
        
        result = processor.mobius_handshake(elpis_state, pandora_state)
        
        assert "handshake_valid" in result
        assert "elpis_state_transformed" in result
        assert "pandora_state_transformed" in result
        assert "invariants" in result
    
    def test_invariant_preservation(self):
        """Test that Möbius handshake preserves invariants."""
        processor = OuroborosVirtualProcessor()
        
        elpis_state = [0.5, 0.3, 0.2]
        pandora_state = [0.4, 0.4, 0.2]
        
        result = processor.mobius_handshake(elpis_state, pandora_state)
        
        # Check invariants
        invariants = result["invariants"]
        assert invariants["sum_preserved_elpis"]
        assert invariants["sum_preserved_pandora"]
        assert invariants["nonnegativity_elpis"]
        assert invariants["nonnegativity_pandora"]
    
    def test_persistent_mobius_store(self):
        """Test persistent Möbius state storage."""
        processor = OuroborosVirtualProcessor()
        
        state = [0.5, 0.3, 0.2]
        success = processor.persistent_mobius_store("test_state_1", state)
        
        assert success
        assert "test_state_1" in processor._quaternion_cache
    
    def test_persistent_mobius_retrieve(self):
        """Test persistent Möbius state retrieval."""
        processor = OuroborosVirtualProcessor()
        
        state = [0.5, 0.3, 0.2]
        processor.persistent_mobius_store("test_state_2", state)
        
        retrieved = processor.persistent_mobius_retrieve("test_state_2")
        
        assert retrieved is not None
        assert "original" in retrieved
        assert "transformed" in retrieved
        assert "mobius_n" in retrieved
        assert len(retrieved["original"]) == 3
    
    def test_state_continuity(self):
        """Test non-orientable memory state continuity."""
        processor = OuroborosVirtualProcessor()
        
        # Create a sequence of states
        state1 = [0.5, 0.3, 0.2]
        state2 = [0.4, 0.35, 0.25]
        
        result1 = processor.mobius_handshake(state1, state2)
        result2 = processor.mobius_handshake(state2, state1)
        
        # Both should be valid
        assert result1["handshake_valid"]
        assert result2["handshake_valid"]
        
        # Check continuity metrics
        assert "metrics" in result1
        assert result1["metrics"]["delta_elpis"] >= 0.0
        assert result1["metrics"]["delta_pandora"] >= 0.0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
