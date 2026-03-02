"""Test Quantum-Ready Stubs v2.0.0"""
import sys
import os

# Add parent directory to path
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

import importlib
eden_ecs = importlib.import_module('eden_ecs')
QuantumCircuit = eden_ecs.QuantumCircuit
QuantumResonance = eden_ecs.QuantumResonance
NoiseChannel = eden_ecs.NoiseChannel


def test_quantum_circuit_basics():
    """Test basic quantum circuit operations"""
    print("=" * 60)
    print("Test 1: Quantum Circuit Basics")
    print("=" * 60)
    
    circuit = QuantumCircuit(num_qubits=3)
    
    # Add various gates
    circuit.h(0)
    circuit.x(1)
    circuit.y(2)
    circuit.cx(0, 1)
    circuit.rz(2, 1.57)
    
    print(f"Num qubits: {circuit.num_qubits}")
    print(f"Num gates: {len(circuit.gates)}")
    print(f"Circuit depth: {circuit.depth()}")
    print(f"Noise channels: {len(circuit.noise_model)}")
    
    if len(circuit.gates) == 5 and circuit.num_qubits == 3:
        print("✅ Quantum circuit basics working!\n")
        return True
    else:
        print("⚠️  Quantum circuit issues\n")
        return False


def test_deep_circuit():
    """Test circuit with 1000+ gates"""
    print("=" * 60)
    print("Test 2: Deep Circuit (1000+ gates)")
    print("=" * 60)
    
    circuit = QuantumCircuit(num_qubits=10)
    
    # Build deep circuit with 1000+ gates
    for i in range(250):
        # Layer of single-qubit gates
        for q in range(10):
            circuit.h(q)
        
        # Layer of entangling gates
        for q in range(0, 9, 2):
            circuit.cx(q, q + 1)
    
    gate_count = len(circuit.gates)
    depth = circuit.depth()
    
    print(f"Total gates: {gate_count:,}")
    print(f"Circuit depth: {depth:,}")
    print(f"Gates per qubit: {gate_count / circuit.num_qubits:.1f}")
    
    if gate_count >= 1000:
        print("✅ Deep circuit (1000+ gates) working!\n")
        return True
    else:
        print(f"⚠️  Only {gate_count} gates, expected 1000+\n")
        return False


def test_noise_channels():
    """Test 5 noise channels"""
    print("=" * 60)
    print("Test 3: Five Noise Channels")
    print("=" * 60)
    
    circuit = QuantumCircuit(num_qubits=5)
    
    # Check default noise model
    print("Default noise channels:")
    for channel, prob in circuit.noise_model.items():
        print(f"  {channel}: {prob:.4f}")
    
    # Update noise channels
    circuit.apply_noise(NoiseChannel.DEPOLARIZING, 0.01)
    circuit.apply_noise(NoiseChannel.AMPLITUDE_DAMPING, 0.005)
    circuit.apply_noise(NoiseChannel.PHASE_DAMPING, 0.003)
    circuit.apply_noise(NoiseChannel.BIT_FLIP, 0.002)
    circuit.apply_noise(NoiseChannel.PHASE_FLIP, 0.002)
    
    print("\nUpdated noise channels:")
    for channel, prob in circuit.noise_model.items():
        print(f"  {channel}: {prob:.4f}")
    
    # Verify all 5 channels exist
    expected_channels = {
        NoiseChannel.DEPOLARIZING.value,
        NoiseChannel.AMPLITUDE_DAMPING.value,
        NoiseChannel.PHASE_DAMPING.value,
        NoiseChannel.BIT_FLIP.value,
        NoiseChannel.PHASE_FLIP.value
    }
    
    actual_channels = set(circuit.noise_model.keys())
    
    if expected_channels == actual_channels:
        print("✅ All 5 noise channels present!\n")
        return True
    else:
        missing = expected_channels - actual_channels
        print(f"⚠️  Missing channels: {missing}\n")
        return False


def test_noise_simulation():
    """Test statevector simulation with noise injection"""
    print("=" * 60)
    print("Test 4: Noise Injection and Fidelity")
    print("=" * 60)
    
    # Create clean circuit
    clean_circuit = QuantumCircuit(num_qubits=3)
    for _ in range(10):
        clean_circuit.h(0)
        clean_circuit.cx(0, 1)
        clean_circuit.cx(1, 2)
    
    # Set very low noise
    for channel in NoiseChannel:
        clean_circuit.apply_noise(channel, 0.0001)
    
    clean_result = clean_circuit.simulate_with_noise()
    
    print(f"Low noise fidelity: {clean_result['fidelity']:.6f}")
    print(f"Total gates: {clean_result['total_gates']}")
    
    # Create noisy circuit
    noisy_circuit = QuantumCircuit(num_qubits=3)
    for _ in range(10):
        noisy_circuit.h(0)
        noisy_circuit.cx(0, 1)
        noisy_circuit.cx(1, 2)
    
    # Set high noise
    for channel in NoiseChannel:
        noisy_circuit.apply_noise(channel, 0.01)
    
    noisy_result = noisy_circuit.simulate_with_noise()
    
    print(f"High noise fidelity: {noisy_result['fidelity']:.6f}")
    print(f"Total gates: {noisy_result['total_gates']}")
    
    # Clean circuit should have higher fidelity
    if clean_result['fidelity'] > noisy_result['fidelity']:
        print("✅ Noise injection affects fidelity correctly!\n")
        return True
    else:
        print("⚠️  Noise simulation issues\n")
        return False


def test_qasm_export():
    """Test QASM 2.0 export"""
    print("=" * 60)
    print("Test 5: QASM 2.0 Export")
    print("=" * 60)
    
    circuit = QuantumCircuit(num_qubits=2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.rz(1, 3.14159)
    
    qasm = circuit.to_qasm()
    
    print("Generated QASM:")
    print(qasm)
    print()
    
    # Verify QASM structure
    lines = qasm.split('\n')
    has_header = 'OPENQASM 2.0' in qasm
    has_qreg = 'qreg q[2]' in qasm
    has_creg = 'creg c[2]' in qasm
    has_gates = any('h q[0]' in line for line in lines)
    has_measurements = any('measure' in line for line in lines)
    
    all_valid = has_header and has_qreg and has_creg and has_gates and has_measurements
    
    if all_valid:
        print("✅ QASM 2.0 export working!\n")
        return True
    else:
        missing = []
        if not has_header: missing.append("header")
        if not has_qreg: missing.append("qreg")
        if not has_creg: missing.append("creg")
        if not has_gates: missing.append("gates")
        if not has_measurements: missing.append("measurements")
        print(f"⚠️  QASM missing: {missing}\n")
        return False


def test_quantum_resonance_integration():
    """Test QuantumResonance component with circuit"""
    print("=" * 60)
    print("Test 6: QuantumResonance Integration")
    print("=" * 60)
    
    resonance = QuantumResonance(frequency=528.0)
    
    # Create circuit
    circuit = resonance.create_circuit(num_qubits=4)
    
    # Build a test circuit
    for i in range(4):
        circuit.h(i)
    for i in range(3):
        circuit.cx(i, i + 1)
    
    print(f"Circuit qubits: {circuit.num_qubits}")
    print(f"Circuit gates: {len(circuit.gates)}")
    
    # Get fidelity
    fidelity = resonance.get_fidelity()
    print(f"Circuit fidelity: {fidelity:.6f}")
    
    # Resonate
    resonance.resonate(delta_time=0.1)
    print(f"Phase after resonance: {resonance.phase:.4f}")
    
    if circuit.num_qubits == 4 and 0 <= fidelity <= 1.0:
        print("✅ QuantumResonance integration working!\n")
        return True
    else:
        print("⚠️  Integration issues\n")
        return False


def main():
    print("\n🔥 Testing EDEN-ECS v2.0.0 Quantum-Ready Stubs\n")
    
    results = []
    results.append(test_quantum_circuit_basics())
    results.append(test_deep_circuit())
    results.append(test_noise_channels())
    results.append(test_noise_simulation())
    results.append(test_qasm_export())
    results.append(test_quantum_resonance_integration())
    
    print("=" * 60)
    print(f"Tests passed: {sum(results)}/{len(results)}")
    print("=" * 60)
    
    if all(results):
        print("\n🎉 All quantum system tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
