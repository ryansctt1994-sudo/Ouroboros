# Post-Quantum Cryptography (PQC) Alignment

**Version 1.0.0**  
**Last Updated:** February 17, 2026

---

## Executive Summary

This document outlines the AIOSPANDORA/Ouroboros project's alignment with post-quantum cryptography standards to ensure long-term security against quantum computing threats.

---

## 1. Overview

### 1.1 Quantum Threat Landscape

Quantum computers pose a significant threat to current cryptographic systems:
- **Shor's Algorithm**: Breaks RSA, ECC, and Diffie-Hellman
- **Grover's Algorithm**: Weakens symmetric key algorithms by half
- **Timeline**: Cryptographically relevant quantum computers projected within 10-20 years
- **Harvest Now, Decrypt Later**: Adversaries collecting encrypted data for future decryption

### 1.2 NIST PQC Standardization

NIST selected post-quantum cryptographic algorithms:
- **CRYSTALS-Kyber**: Key encapsulation mechanism (KEM)
- **CRYSTALS-Dilithium**: Digital signature algorithm
- **SPHINCS+**: Stateless hash-based signature
- **FALCON**: Lattice-based signature (compact signatures)

---

## 2. Current Cryptographic Inventory

### 2.1 Cryptographic Usage in Ouroboros

| Component | Current Algorithm | Quantum Vulnerable | Priority |
|-----------|------------------|-------------------|----------|
| Git commits | SHA-1, SHA-256 | Partial (collision resistance) | Medium |
| Code signing | RSA/ECDSA | Yes | High |
| Teleport adapter | XOR (placeholder) | N/A (not cryptographic) | High |
| Data hashing | SHA-256 | No (Grover reduces to 128-bit) | Low |
| IPC authentication | System-level auth | Depends on system | Medium |

### 2.2 Dependency Analysis

External cryptographic dependencies:
- Python `hashlib`: SHA family (quantum-resistant for hashing)
- System TLS libraries: May use quantum-vulnerable key exchange
- Git: Uses SHA-1/SHA-256 (git moving to SHA-256)

---

## 3. PQC Migration Strategy

### 3.1 Phase 1: Preparation (Q1-Q2 2026)

**Actions**:
1. Inventory all cryptographic operations
2. Identify quantum-vulnerable components
3. Research PQC libraries for Python
4. Develop migration roadmap
5. Update threat models

**Status**: ✅ Inventory complete (this document)

---

### 3.2 Phase 2: Hybrid Approach (Q3-Q4 2026)

**Actions**:
1. Implement hybrid cryptography (classical + PQC)
2. Deploy PQC alongside existing algorithms
3. Test interoperability and performance
4. Update teleport adapter with proper encryption

**Recommended Libraries**:
- **liboqs-python**: Open Quantum Safe Python bindings
- **PQClean**: Clean PQC implementations
- **Kyber**: For key encapsulation
- **Dilithium**: For digital signatures

**Implementation Example**:
```python
# Hybrid key exchange
classical_key = ecdh_generate()
pqc_key = kyber_generate()
shared_secret = kdf(classical_key + pqc_key)
```

---

### 3.3 Phase 3: PQC-First (2027)

**Actions**:
1. Default to PQC algorithms
2. Maintain classical for backward compatibility
3. Deprecate quantum-vulnerable algorithms
4. Full PQC adoption where possible

---

### 3.4 Phase 4: PQC-Only (2028+)

**Actions**:
1. Remove quantum-vulnerable algorithms
2. Full PQC compliance
3. Regular updates as standards evolve
4. Continuous threat monitoring

---

## 4. Specific Component Recommendations

### 4.1 Teleport Adapter Enhancement

**Current**: XOR-based encryption (placeholder)

**Recommended**:
```python
from oqs import KeyEncapsulation

class PQCTeleportAdapter:
    def __init__(self):
        self.kem = KeyEncapsulation('Kyber512')
        
    def encrypt_state(self, state_data):
        public_key = self.kem.generate_keypair()
        ciphertext, shared_secret = self.kem.encap_secret(public_key)
        # Use shared_secret with AES-256 for encryption
        encrypted = aes256_gcm_encrypt(shared_secret, state_data)
        return ciphertext, encrypted
    
    def decrypt_state(self, ciphertext, encrypted):
        shared_secret = self.kem.decap_secret(ciphertext)
        return aes256_gcm_decrypt(shared_secret, encrypted)
```

---

### 4.2 Code Signing

**Current**: RSA/ECDSA via git

**Recommended**:
- Transition to SPHINCS+ or Dilithium for commit signing
- Use git's future PQC support
- Hybrid signatures during transition

---

### 4.3 Hash Functions

**Current**: SHA-256

**Status**: Quantum-resistant for hashing (Grover reduces security to 128-bit, still acceptable)

**Action**: Monitor for SHA-3 adoption, maintain current usage

---

### 4.4 IPC Security

**Current**: Unix socket with system permissions

**Recommended**:
- Add optional PQC key exchange for remote IPC
- Implement mutual authentication with PQC certificates
- Use Kyber for session key establishment

---

## 5. Algorithm Selection Criteria

### 5.1 Key Encapsulation (KEM)

**CRYSTALS-Kyber** (NIST selected)
- **Kyber512**: ~128-bit security, smaller keys
- **Kyber768**: ~192-bit security (recommended)
- **Kyber1024**: ~256-bit security, larger keys

**Selection**: Kyber768 for balance of security and performance

---

### 5.2 Digital Signatures

**CRYSTALS-Dilithium** (NIST selected)
- **Dilithium2**: ~128-bit security
- **Dilithium3**: ~192-bit security (recommended)
- **Dilithium5**: ~256-bit security

**Selection**: Dilithium3 for standard use, SPHINCS+ for long-term signatures

---

### 5.3 Hash-Based Signatures

**SPHINCS+** (NIST selected)
- Stateless (no state management complexity)
- Longer signatures and slower
- Best for infrequent, high-security signing

**Use Case**: Software release signing, critical infrastructure

---

## 6. Performance Considerations

### 6.1 Benchmark Targets

| Operation | Classical | PQC (Kyber/Dilithium) | Acceptable Overhead |
|-----------|-----------|----------------------|---------------------|
| Key generation | 1ms | 0.5-2ms | 2x |
| Encryption | 0.1ms | 0.2-0.5ms | 5x |
| Decryption | 0.1ms | 0.3-0.7ms | 7x |
| Sign | 1ms | 2-5ms | 5x |
| Verify | 0.5ms | 1-3ms | 6x |

---

### 6.2 Optimization Strategies

1. **Hardware Acceleration**: Use CPU extensions (AVX2, AVX-512)
2. **Caching**: Cache public keys and parameters
3. **Batching**: Batch signature verifications
4. **Lazy Loading**: Load PQC libraries only when needed

---

## 7. Testing and Validation

### 7.1 Test Requirements

1. **Interoperability**: Test with multiple PQC libraries
2. **Performance**: Benchmark against classical algorithms
3. **Security**: Penetration testing, fuzzing
4. **Compatibility**: Ensure backward compatibility during transition

### 7.2 Test Vectors

Use official NIST test vectors:
- Kyber: https://csrc.nist.gov/Projects/pqc-forum/round-3-submissions
- Dilithium: NIST PQC standardization test vectors
- SPHINCS+: NIST test vectors

---

## 8. Dependencies and Libraries

### 8.1 Recommended Python Libraries

1. **liboqs-python**
   - Bindings to Open Quantum Safe library
   - Supports all NIST PQC algorithms
   - Actively maintained

2. **PQCrypto**
   - Pure Python implementations (slower)
   - Good for research and prototyping

3. **cryptography (future)**
   - Will add PQC support as standards finalize
   - Widely used, well-audited

### 8.2 Installation

```bash
pip install liboqs-python
# Or build from source for latest algorithms
```

---

## 9. Compliance and Standards

### 9.1 Alignment

- **NIST SP 800-208**: Recommendation for Stateful HBS
- **NIST SP 800-209**: SHA-3 Derived Functions
- **NIST PQC Standardization**: Follow final standards (expected 2024)
- **CNSA 2.0** (NSA): Post-quantum requirements for national security systems

### 9.2 Audit Trail

Maintain audit trail of:
- Algorithm selections and rationale
- Migration milestones
- Security incidents related to cryptography
- Compliance assessments

---

## 10. Risk Management

### 10.1 Identified Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Early quantum computer | Low | Critical | Hybrid approach, monitoring |
| PQC algorithm break | Medium | High | Algorithm agility, diversity |
| Performance degradation | High | Medium | Optimization, selective use |
| Implementation bugs | Medium | High | Code review, testing, audits |

### 10.2 Contingency Planning

1. **Algorithm Agility**: Design for easy algorithm swapping
2. **Crypto-Agility Framework**: Abstract cryptographic operations
3. **Regular Updates**: Monitor NIST and IACR for developments
4. **Incident Response**: Plan for cryptographic breaks

---

## 11. Future Considerations

### 11.1 Emerging Standards

- **NIST Round 4**: Additional algorithm candidates
- **ISO/IEC 23644**: Quantum-resistant cryptography standard
- **Hybrid TLS**: TLS 1.3 with hybrid key exchange

### 11.2 Research Areas

- Code-based cryptography
- Multivariate cryptography
- Isogeny-based cryptography (backup if lattice-based fails)

---

## 12. Implementation Checklist

- [ ] Install liboqs-python library
- [ ] Update teleport adapter with Kyber encryption
- [ ] Implement hybrid key exchange for IPC
- [ ] Add Dilithium signature support
- [ ] Benchmark PQC performance
- [ ] Create migration guide for users
- [ ] Update security documentation
- [ ] Conduct security audit of PQC implementation
- [ ] Train maintainers on PQC concepts
- [ ] Establish algorithm update process

---

## 13. Resources

### 13.1 NIST Resources
- [NIST PQC Project](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [PQC Standardization](https://csrc.nist.gov/projects/post-quantum-cryptography/post-quantum-cryptography-standardization)

### 13.2 Open Source Libraries
- [Open Quantum Safe](https://openquantumsafe.org/)
- [PQClean](https://github.com/PQClean/PQClean)
- [liboqs](https://github.com/open-quantum-safe/liboqs)

### 13.3 Research Papers
- Kyber specification: https://pq-crystals.org/kyber/
- Dilithium specification: https://pq-crystals.org/dilithium/
- SPHINCS+ specification: https://sphincs.org/

---

## Version History

- v1.0.0 (2026-02-17): Initial PQC alignment document

---

*Preparing for the quantum future ensures long-term security of AIOSPANDORA/Ouroboros.*
