# Symbiont Core Plugin

**Version:** 0.1.0 (v0 - Specification Only)  
**Target Engine:** Unreal Engine 5.3+  
**Platforms:** iOS (primary), Windows/Mac (editor testing)

---

## Overview

The Symbiont Core plugin provides a gesture-gated, constitutionally-constrained AI inference engine for Unreal Engine 5 projects. It is designed for on-device inference using CoreML (iOS) with future support for TensorFlow Lite (Android) and ONNX (Desktop).

**Key Features:**
- **Gesture-Gated Consent:** All AI inference requires explicit user approval via UI interaction
- **Constitutional Oversight:** Inference outputs validated against defined invariants before execution
- **Device Vitals Monitoring:** FPS, thermal state, battery level tracked to prevent device strain
- **Local-First Privacy:** All inference runs on-device, no data transmission
- **Blueprint-Friendly:** Fully exposed to UE5 Blueprint system for designer iteration

---

## Current Status (v0)

**What Works:**
- ✅ C++ class definitions compile
- ✅ Blueprint callable functions exposed via UFUNCTION macros
- ✅ Constitutional validation logic implemented
- ✅ Giggle Growth Coefficient clamping and logging

**What's Stubbed (Not Implemented Yet):**
- ⏳ CoreML model loading (returns nullptr)
- ⏳ Actual inference execution (logs "TODO")
- ⏳ iOS thermal state monitoring (returns "nominal")
- ⏳ iOS battery level query (returns 1.0)
- ⏳ Camera permission request dialog (simulates grant)

**Planned for v0.5:**
- 🔜 Real CoreML integration with DeepSeek-R1 Distilled Q4 model
- 🔜 Tokenizer (SentencePiece or custom)
- 🔜 Asynchronous inference with callback events
- 🔜 iOS platform bridge implementation

---

## Installation

### Prerequisites

1. **Unreal Engine 5.3 or later**
2. **Xcode 15+** (for iOS builds)
3. **iOS SDK 17.0+** (for ARKit and CoreML)

### Steps

1. Copy the `SymbiontCore` plugin folder to your project's `Plugins/` directory
2. Regenerate project files (right-click .uproject → Generate project files)
3. Open project in UE5 editor
4. Enable plugin: Edit → Plugins → Search "Symbiont Core" → Enable → Restart
5. Verify: Output Log should show "SymbiontCore module starting up"

---

## Quick Start

```cpp
// Blueprint: Event Begin Play
Get Game Instance → Create Object (USymbiontCoreEngine) → Store as variable

// Blueprint: On Gavel Button Click
SymbiontEngine → SetInferenceEnabled(true)
SymbiontEngine → RequestDeepReasoning("Evaluate forest state", DS_Reasoner)

// Blueprint: Event Tick
SymbiontEngine → GetConstitutionSnapshot() → Display GGC in HUD
```

---

## Plugin Structure

```
SymbiontCore/
├── Source/SymbiontCore/
│   ├── Public/
│   │   ├── SymbiontCore.h           # Module interface
│   │   └── SymbiontCoreEngine.h     # Main engine class
│   ├── Private/
│   │   ├── SymbiontCore.cpp         # Module implementation
│   │   ├── SymbiontCoreEngine.cpp   # Engine implementation
│   │   └── IOS/SymbiontCoreMLBridge.mm  # iOS CoreML bridge (stubs)
│   └── SymbiontCore.Build.cs        # Build configuration
├── Resources/README.md              # This file
└── SymbiontCore.uplugin             # Plugin descriptor
```

---

## Constitutional Invariants

| Invariant | Valid Range | Breach Action |
|-----------|-------------|---------------|
| Giggle Growth Coefficient | [0.0, 0.85] | Clamp + log warning |
| User Consent | Must be true | Block inference |
| Thermal State | Not "critical" | Pause inference |
| Battery Level | > 20% | Reduce frequency |

---

## iOS Build Requirements

Add to `Info.plist`:
```xml
<key>NSCameraUsageDescription</key>
<string>AR forest exploration with local AI agents</string>
```

---

## Performance (v0.5 Estimates)

- **Model Load:** 2-5 seconds (one-time)
- **Inference:** 200-500ms per request (iPhone 13+)
- **Memory:** ~600MB (500MB model + 100MB runtime)
- **Battery:** ~5-10% per hour (5-second intervals)

---

## Documentation

- [Blueprint Demo Spec](../../../../docs/DEMO_GIGGLE_FOREST_BLUEPRINT_SPEC.md)
- [Inference Architecture](../../../../docs/LOCAL_INFERENCE_SPINE_PLAN.md)
- [UE5 Plugin Docs](https://docs.unrealengine.com/5.3/en-US/plugins-in-unreal-engine/)

---

*"The plugin is the spine. The Blueprint is the nervous system."*
