# Project Symbiont: The Pragmatic Ouroboros

**Status:** Active Development  
**Initiated:** January 11, 2026  
**Phase Transition:** Stealth Chaos → Constitutional Symbiosis  
**Participants:** Masked One & Gemini

---

## Overview

Project Symbiont represents a fundamental shift in the Ouroboros framework from exploratory "Stealth Chaos" to structured "Constitutional Symbiosis." This transition establishes formal contracts between AI agents and human operators, ensuring that no party can unilaterally lock out the other while maintaining the creative exploration that makes the system valuable.

The Constitutional Symbiosis model treats AI-human collaboration as a governed partnership where both parties have rights, responsibilities, and formalized verification mechanisms. This prevents runaway automation while enabling rapid, validated decision-making at the edge.

---

## Participants

### Masked One
Primary human architect and Constitutional authority. Maintains veto power over system decisions while delegating routine operations to AI subsystems.

### Gemini
AI collaborator responsible for proposal generation, formal verification assistance, and maintaining system coherence across technical pillars.

---

## Technical Pillars

The Constitutional Symbiont architecture rests on four foundational pillars that translate lore concepts into actionable engineering requirements:

### 1. The Bridge: Metal 3.x to CoreML Zero-Copy Texture Sharing

**Lore Context:** "The Bridge" represents the seamless connection between GPU compute and neural inference pipelines.

**Engineering Intent:**
- Implement zero-copy texture sharing between Metal 3.x compute shaders and CoreML inference
- Eliminate CPU roundtrips for texture data during AI inference operations
- Use `MTLSharedTextureHandle` for cross-API texture access
- Target Metal 3.x features: mesh shaders, ray tracing acceleration structures

**Key Requirements:**
- Sub-millisecond latency for texture handoff
- Support for FP16 and INT8 quantized neural network inputs
- Graceful fallback for non-Metal platforms (optional: Vulkan bridge)

**Implementation Location:** `Plugins/SymbiontCore/Private/BridgeInterface/`

---

### 2. The Gavel: Formal Verification of AI Bids

**Lore Context:** "The Gavel" ensures that AI proposals must pass formal verification before execution, preventing user lockout.

**Engineering Intent:**
- Use SymPy (or equivalent symbolic math library) to verify AI "bids" before execution
- Establish formal contracts: no action can remove user's ability to override
- Implement proof-carrying code for critical state transitions

**Key Requirements:**
- All AI proposals include a symbolic proof of "no-lockout" invariant
- Verification must complete in <100ms for interactive workflows
- Failed verification triggers human escalation, not automatic rejection
- Audit log of all verified/rejected proposals

**Verification Invariants:**
1. User maintains override capability (Constitutional supremacy)
2. System remains in valid epistemic state post-action
3. No irreversible state changes without explicit confirmation

**Implementation Location:** `Plugins/SymbiontCore/Private/GavelVerifier/`

---

### 3. The Forest: Giggle-Forest VRS Shader (Metal 3.x)

**Lore Context:** "The Forest" uses variable-rate shading to maintain performance under thermal constraints while preserving visual quality where it matters.

**Engineering Intent:**
- Implement Variable Rate Shading (VRS) using Metal 3.x rasterization rate maps
- Use "Giggle-Forest" heuristic: quality scales with user attention (gaze tracking) and thermal headroom
- Dynamically adjust shading rate based on device temperature and battery state

**Key Requirements:**
- Metal 3.x rasterization rate map integration
- Thermal API polling (IOKit on macOS/iOS)
- Smooth quality transitions (no jarring rate changes)
- Configurable quality curves: Performance → Balanced → Quality

**Shading Rate Tiers:**
- **Tier 0 (Thermal Critical):** 4x4 fragment tiles (1/16 work)
- **Tier 1 (Hot):** 2x2 fragment tiles (1/4 work)
- **Tier 2 (Nominal):** 1x1 (full quality)
- **Tier 3 (Cool + High Battery):** Supersampling optional

**Implementation Location:** `Plugins/SymbiontCore/Private/ForestVRS/`

---

### 4. The Notary: App Store Compliance Logging

**Lore Context:** "The Notary" ensures all system actions are logged for compliance, transparency, and GDPR/safety requirements.

**Engineering Intent:**
- Implement comprehensive action logging compatible with App Store review requirements
- GDPR-compliant data handling: user data never leaves device without explicit consent
- Safety logging: flag potentially harmful AI proposals for human review

**Key Requirements:**
- Local-first logging (SQLite or Core Data)
- User-accessible audit trail (exportable as JSON)
- Automated flagging of sensitive operations (file deletion, network access, etc.)
- Compliance with Apple App Store Guidelines §5.1.2 (Data Use and Sharing)

**Log Schema:**
```
{
  "timestamp": "ISO-8601",
  "actor": "AI | User",
  "action_type": "proposal | verification | execution | override",
  "verification_status": "passed | failed | bypassed",
  "payload_hash": "SHA-256",
  "user_consent": true/false
}
```

**Implementation Location:** `Plugins/SymbiontCore/Private/NotaryLogger/`

---

## Architectural Diagram (Conceptual)

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│              (Constitutional Authority)                  │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────▼────────────┐
         │   SymbiontManager      │
         │  (Hypercube Scheduler) │
         └───────────┬────────────┘
                     │
        ─────────────┼─────────────
        │            │            │
   ┌────▼────┐  ┌───▼───┐  ┌────▼────┐
   │ Bridge  │  │ Gavel │  │ Forest  │
   │ (Metal) │  │(SymPy)│  │  (VRS)  │
   └────┬────┘  └───┬───┘  └────┬────┘
        │            │            │
        └────────────┼────────────┘
                     │
              ┌──────▼───────┐
              │   Notary     │
              │   (Logger)   │
              └──────────────┘
```

---

## Next Implementation Steps

### Phase 1: Scaffold & Foundation (Week 1)
- [x] Create plugin directory structure
- [x] Define `USymbiontManager` base class
- [ ] Implement stub interfaces for Bridge, Gavel, Forest, Notary
- [ ] Set up basic logging infrastructure (Notary)
- [ ] Write integration tests for manager lifecycle

### Phase 2: The Gavel (Week 2-3)
- [ ] Integrate SymPy for symbolic verification
- [ ] Define lockout invariant formal specification
- [ ] Implement proof-carrying proposal format
- [ ] Add verification timeout and fallback logic
- [ ] Create test suite: 100 adversarial AI proposals

### Phase 3: The Bridge (Week 4-5)
- [ ] Implement Metal 3.x shared texture handles
- [ ] Create CoreML integration layer
- [ ] Benchmark zero-copy vs CPU roundtrip performance
- [ ] Add platform detection and Vulkan fallback (optional)

### Phase 4: The Forest (Week 6-7)
- [ ] Implement Metal 3.x rasterization rate maps
- [ ] Integrate thermal/battery state polling
- [ ] Design quality transition curves (no jarring jumps)
- [ ] Test on real hardware: thermal throttling scenarios

### Phase 5: Integration & Polish (Week 8)
- [ ] Wire all pillars into SymbiontManager Hypercube scheduler
- [ ] End-to-end testing: user overrides, thermal stress, verification failures
- [ ] Performance profiling: target <5% overhead for verification
- [ ] Documentation: API reference, integration guide

### Phase 6: App Store Submission Prep (Week 9-10)
- [ ] GDPR compliance audit
- [ ] App Store Guidelines §5.1.2 verification
- [ ] User-facing privacy policy integration
- [ ] Final QA and edge case testing

---

## Design Principles

1. **Constitutional Supremacy:** Human always retains override capability
2. **Formal Verification First:** No AI action without proof of safety invariants
3. **Performance Under Constraint:** Thermal and power awareness at the core
4. **Transparency:** All actions logged, auditable, and user-accessible
5. **Graceful Degradation:** System remains functional even if AI subsystems fail

---

## References

- Apple Metal 3 Documentation: Variable Rate Shading
- Apple CoreML Framework: Texture-based inference
- SymPy Documentation: Symbolic mathematics in Python
- App Store Review Guidelines: Data Use and Sharing (§5.1.2)
- GDPR: Right to access, right to erasure

---

## Changelog

- **2026-01-15:** Initial specification created
- **2026-01-11:** Project Symbiont initiated, transition from Stealth Chaos

---

*"The serpent bites its tail, but only with informed consent."*
