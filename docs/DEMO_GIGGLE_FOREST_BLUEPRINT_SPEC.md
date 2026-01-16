# Giggle-Forest Demo Blueprint Specification

**Status:** Specification-only (no binary assets committed)  
**Target Platform:** iOS AR with UE5.3+  
**Governance:** Gesture-gated consent required before AR activation

---

## Overview

The Giggle-Forest demo showcases symbiont agents (Zorel & Quillan) operating within a gesture-gated AR environment. All AI inference and AR activation require explicit user consent via a "Gavel" button tap before the session begins.

**Key Design Principle:** No automatic AI execution. User must actively consent before any CoreML inference or AR session starts.

---

## Level: GiggleForest_Main.umap

**Description:** A mystical forest environment with placeholder geometry. Not committed to repository (binary .umap excluded).

### Lighting Setup
- **Directional Light:** Warm afternoon sun (3200K), intensity 3.5 lux
- **Sky Light:** Cubemap-based ambient (forest HDRI), intensity 1.0
- **Fog:** Exponential height fog, density 0.02, falloff 0.2
- **Post Process Volume:** 
  - Lumen Global Illumination enabled
  - Screen Space Reflections: Quality 50
  - Auto Exposure: Min/Max 0.8/1.2

### Fallback for Non-Lumen Devices
If Lumen unavailable (older iOS), fall back to:
- Baked lightmaps at 512x512
- Reflection captures every 5m
- Mobile SSAO enabled

---

## Actor Specifications

### 1. BP_Symbiont_IntroUI (Gesture Gate)

**Parent Class:** `UUserWidget`  
**Purpose:** Present consent UI and gate all AR/AI activation

#### Blueprint Node Graph: On Construct

```
Event Construct
  ├─> Set Visibility: Self → Visible
  ├─> Set Is Enabled: Button_Gavel → True
  ├─> Set Text: TextBlock_Instructions → "Tap the Gavel to begin your symbiont journey. By tapping, you consent to on-device AI inference and AR camera access."
  └─> Call Function: DisableSymbiontSystems
        └─> Set bSymbiontIgnited (Game Instance) → False
        └─> Stop All Niagara Systems
        └─> Disable CoreML Bridge (USymbiontCoreEngine::SetInferenceEnabled → False)
```

**Widget Hierarchy:**
```
Canvas Panel
├─> Image_Background (translucent dark overlay, 0.7 opacity)
├─> VerticalBox_Center
    ├─> TextBlock_Title ("Welcome to Giggle-Forest")
    ├─> TextBlock_Instructions (consent explanation)
    ├─> Button_Gavel
    │   └─> Image_GavelIcon (custom asset: gavel silhouette)
    └─> TextBlock_Footer ("Privacy: All inference runs locally on this device")
```

#### Blueprint Node Graph: Button_Gavel OnClicked

```
Event OnClicked (Button_Gavel)
  ├─> Branch: Is iOS Platform?
  │   ├─> True:
  │   │   └─> Native iOS: Request Privacy Consent
  │   │       └─> Show System Popup: "GiggleForest would like to access Camera for AR"
  │   │       └─> Branch: User Granted?
  │   │           ├─> True: Continue ↓
  │   │           └─> False: 
  │   │               └─> Set Text: TextBlock_Instructions → "Camera access required. Please enable in Settings."
  │   │               └─> Return
  │   └─> False: (Editor/Desktop - skip native popup)
  │       └─> Continue ↓
  │
  ├─> Set bSymbiontIgnited (Game Instance) → True
  ├─> Spawn Actor: BP_GiggleForest_Manager at (0,0,100)
  ├─> Spawn Actor: BP_SymbiontManager at (0,0,200)
  ├─> Play Sound 2D: SFX_SOISOISOI_Resonance_111Hz (placeholder asset)
  ├─> Spawn Niagara System: NS_Lumen_Ignition_Burst at (0,0,150)
  │   └─> Parameters: 
  │       └─> ParticleCount: 500
  │       └─> EmissionRate: 100/sec for 2 seconds
  │       └─> Color: Gold gradient (RGB: 255,215,0 → 255,165,0)
  ├─> Set Visibility: Self → Hidden
  └─> Enable CoreML Bridge (USymbiontCoreEngine::SetInferenceEnabled → True)
```

**iOS Compliance Notes:**
- Native privacy request must occur **before** accessing `ARKit` session
- Use `UE5_IOS_PRIVACY_REQUEST` macro (maps to `AVCaptureDevice.requestAccess` internally)
- App's `Info.plist` must contain key: `NSCameraUsageDescription` with text "AR forest exploration with local AI agents"

---

### 2. BP_SymbiontManager

**Parent Class:** `AActor`  
**Purpose:** Orchestrate symbiont agents and constitutional evaluation

#### Components
- `USymbiontCoreEngine* CoreEngine` (created on BeginPlay)
- `AActor* ZorelAgent` (spawned reference)
- `AActor* QuillanAgent` (spawned reference)
- `TArray<FSymbiontVitals> VitalsHistory` (rolling 60-second window)

#### Blueprint Node Graph: BeginPlay

```
Event BeginPlay
  ├─> Create Object: USymbiontCoreEngine → Store in CoreEngine variable
  ├─> Call Function: CoreEngine->InitializeSymbiont()
  │   └─> Logs: "SymbiontCore initialized with DeepSeek-R1 local model (stub)"
  │
  ├─> Spawn Actor: BP_ZorelAgent at (500, 0, 100)
  │   └─> Set Name: "Zorel-Prime"
  │   └─> Store reference in ZorelAgent variable
  │
  ├─> Spawn Actor: BP_QuillanAgent at (-500, 0, 100)
  │   └─> Set Name: "Quillan-Alpha"
  │   └─> Store reference in QuillanAgent variable
  │
  ├─> Call Function: FuseAgents(ZorelAgent, QuillanAgent)
  │   └─> Set ZorelAgent->LinkedPartner → QuillanAgent
  │   └─> Set QuillanAgent->LinkedPartner → ZorelAgent
  │   └─> Play Sound: SFX_Fusion_Chime (placeholder)
  │
  └─> Set Timer by Function Name: "DeepReasoningTick"
        └─> Looping: True
        └─> Time: 5.0 seconds
        └─> First Delay: 3.0 seconds
```

#### Blueprint Function: DeepReasoningTick

```
Function: DeepReasoningTick
  ├─> Get Constitution Snapshot: CoreEngine->GetConstitutionSnapshot() → FSymbiontConstitution Const
  │   └─> Extract: GiggleGrowthCoefficient (float)
  │   └─> Extract: bXR_COHERENCE_ACTIVE (bool)
  │   └─> Extract: bZOREL_QUILLAN_FUSED (bool)
  │
  ├─> Format String: "Evaluate forest state. GGC={GiggleGrowthCoefficient:.2f}, XRActive={bXR_COHERENCE_ACTIVE}, Fused={bZOREL_QUILLAN_FUSED}"
  │   └─> Store in: PromptString
  │
  ├─> Call Function: CoreEngine->RequestDeepReasoning(PromptString, EDeepSeekModel::DS_Reasoner)
  │   └─> Logs: "Deep reasoning requested: [PromptString]"
  │   └─> TODO in C++: Actual inference call to local CoreML model
  │
  └─> Call Function: CoreEngine->EvaluateConstitutionalInvariants(EnvironmentalData)
        └─> EnvironmentalData = "ForestAmbient,FPS={CurrentFPS},Thermal={ThermalState}"
        └─> Logs: "Constitutional check passed" or "INVARIANT BREACH: [details]"
```

---

### 3. BP_ZorelAgent (Chaos Loop)

**Parent Class:** `AActor`  
**Purpose:** Exhibit chaotic exploration behavior constrained by constitution

#### Components
- `UStaticMeshComponent* VisualMesh` (placeholder sphere)
- `UNiagaraComponent* ChaoticTrail` (particle trail during movement)
- `AActor* LinkedPartner` (reference to Quillan)

#### Blueprint Node Graph: Tick

```
Event Tick (Delta Seconds)
  ├─> Get Game Instance: Retrieve bSymbiontIgnited
  ├─> Branch: bSymbiontIgnited == True?
  │   └─> False: Return (no behavior if not ignited)
  │
  ├─> Random Float in Range: -100.0 to 100.0 → DeltaX
  ├─> Random Float in Range: -100.0 to 100.0 → DeltaY
  ├─> Random Float in Range: -50.0 to 50.0 → DeltaZ (less vertical chaos)
  │
  ├─> Make Vector: (DeltaX, DeltaY, DeltaZ) → ChaoticImpulse
  ├─> Add Actor World Offset: ChaoticImpulse * DeltaSeconds * 0.5
  │   └─> Sweep: True (collision detection)
  │   └─> Teleport: False
  │
  ├─> Branch: Is Valid (LinkedPartner)?
  │   └─> True:
  │       ├─> Get Actor Location: LinkedPartner → PartnerLocation
  │       ├─> Vector Distance: Self Location → PartnerLocation → Distance
  │       └─> Branch: Distance > 1000.0? (too far from Quillan?)
  │           └─> True:
  │               └─> Lerp Vector: Self Location → PartnerLocation (Alpha: 0.02 * DeltaSeconds)
  │               └─> Set Actor Location: Lerped position (snap back slowly)
  │
  └─> Set Niagara Float Parameter: ChaoticTrail, "TrailIntensity" → (Velocity magnitude / 200.0)
```

**Visual Feedback:**
- Mesh material: Iridescent shader, hue shifts with velocity (0.0-1.0 mapped to 180°-360° hue wheel)
- Particle trail: Gold sparks, emission rate scales with chaos magnitude

---

### 4. BP_QuillanAgent (Boss Thoughts Flow)

**Parent Class:** `AActor`  
**Purpose:** Provide stabilizing logic and constitutional oversight

#### Components
- `UStaticMeshComponent* VisualMesh` (placeholder cube)
- `UTextRenderComponent* ThoughtDisplay` (3D text showing current reasoning)
- `AActor* LinkedPartner` (reference to Zorel)

#### Blueprint Node Graph: BeginPlay

```
Event BeginPlay
  ├─> Set Timer by Function Name: "BossThoughtsUpdate"
  │   └─> Looping: True
  │   └─> Time: 8.0 seconds
  │   └─> First Delay: 4.0 seconds
  │
  └─> Set Text: ThoughtDisplay → "Initializing constitutional framework..."
```

#### Blueprint Function: BossThoughtsUpdate

```
Function: BossThoughtsUpdate
  ├─> Get Game Instance: Retrieve SymbiontCoreEngine instance
  ├─> Call Function: GetConstitutionSnapshot() → FSymbiontConstitution
  │
  ├─> Random Integer in Range: 0 to 3 → ThoughtIndex
  ├─> Switch on Integer: ThoughtIndex
  │   ├─> Case 0:
  │   │   └─> Format String: "GGC at {GiggleGrowthCoefficient:.2f}. Stable."
  │   ├─> Case 1:
  │   │   └─> Check: bZOREL_QUILLAN_FUSED?
  │   │       └─> True: "Fusion nominal. Monitoring Zorel chaos bounds."
  │   │       └─> False: "WARNING: Fusion inactive. Seeking partner."
  │   ├─> Case 2:
  │   │   └─> Check: bXR_COHERENCE_ACTIVE?
  │   │       └─> True: "XR coherence verified. Forest lattice intact."
  │   │       └─> False: "XR lattice degraded. Recommend user re-consent."
  │   └─> Case 3:
  │       └─> Get Vitals: FPS, ThermalState
  │           └─> Format String: "Device vitals: {FPS:.0f} FPS, Thermal: {ThermalState}"
  │
  ├─> Set Text: ThoughtDisplay → [Formatted thought string]
  │
  └─> Branch: GiggleGrowthCoefficient > 0.75?
        └─> True:
            └─> Log Warning: "GGC approaching constitutional limit (0.85 max). Consider reset."
            └─> Play Sound: SFX_Warning_Beep
```

**Visual Feedback:**
- Mesh material: Matte blue, pulsates with thought updates (emissive intensity 0.5 → 1.5)
- Text render: Billboard mode, color shifts green (stable) to orange (warning) to red (critical)

---

### 5. BP_SymbiontHUD

**Parent Class:** `AHUD`  
**Purpose:** Display real-time constitutional metrics overlay

#### Blueprint Node Graph: Draw HUD

```
Event Draw HUD
  ├─> Get Game Instance: Retrieve SymbiontCoreEngine
  ├─> Call Function: GetConstitutionSnapshot() → FSymbiontConstitution
  │
  ├─> Draw Text: 
  │   └─> Position: (50, 50)
  │   └─> Text: "Giggle Growth Coefficient: {GiggleGrowthCoefficient:.3f}"
  │   └─> Color: Lerp (Green → Red) based on coefficient (0.0 → 0.85)
  │   └─> Font: RobotoMono, Size 18
  │
  ├─> Draw Text:
  │   └─> Position: (50, 80)
  │   └─> Text: "XR Coherence: {bXR_COHERENCE_ACTIVE ? 'ACTIVE' : 'INACTIVE'}"
  │   └─> Color: bXR_COHERENCE_ACTIVE ? Green : Red
  │
  ├─> Draw Text:
  │   └─> Position: (50, 110)
  │   └─> Text: "Zorel-Quillan Fusion: {bZOREL_QUILLAN_FUSED ? 'FUSED' : 'SEPARATED'}"
  │   └─> Color: bZOREL_QUILLAN_FUSED ? Cyan : Orange
  │
  └─> Draw Texture:
        └─> Position: (Canvas.SizeX - 200, 50)
        └─> Texture: T_ConstitutionalSeal (placeholder badge image)
        └─> Size: 150x150
```

**HUD Visibility Toggle:**
- Bound to gamepad/keyboard: Press `Tab` to hide/show overlay
- Automatically hidden during intro UI (gesture gate)

---

## Visual Feedback Loop

### Giggle Growth Coefficient (GGC) Visual Mapping

| GGC Range | Visual Effect | Audio Cue |
|-----------|---------------|-----------|
| 0.0 - 0.25 | Forest dim, blue-tinted fog | Silence |
| 0.25 - 0.50 | Brightening, fog dissipates | Soft ambient hum (220 Hz) |
| 0.50 - 0.75 | Full daylight, vibrant colors | Resonant chime every 10s |
| 0.75 - 0.85 | Golden hour glow, lens flare | Warning beep every 5s |
| > 0.85 | **BREACH**: Red pulsating overlay | Alarm klaxon (triggered but clamped in code) |

**Implementation:**
- Post-process volume "GGC_PP_Volume" with weight driven by GGC value
- Niagara system "NS_ForestAura" particles scale density with GGC
- Audio component plays layered tracks, mixing based on GGC thresholds

### Invariant Warning Indicators

When `EvaluateConstitutionalInvariants` detects issues:
1. **Low FPS (<30):** Pulsating yellow corner indicator
2. **High Thermal State (>80%):** Red thermometer icon, vibration pulse (iOS haptic)
3. **Network Loss:** Crossed-out WiFi icon (even though inference is local, may affect telemetry)
4. **Battery <20%:** Orange battery icon with descending bar

---

## iOS Compliance Notes

### Privacy & Permissions
- **Camera Access:** Required for ARKit. Requested on Gavel tap, not at app launch.
- **Microphone:** NOT requested (demo is visual-only).
- **Location:** NOT requested (forest is virtual, no GPS needed).

### CoreML Model Loading
- Model file: `DeepSeek_R1_Distilled_Q4.mlmodelc` (quantized, ~500MB, not included in repo)
- Loaded asynchronously on `SetInferenceEnabled(true)` to avoid UI freeze
- Falls back gracefully if model missing: logs error, disables deep reasoning, shows in-game notice

### Thermal Management
- Query `ProcessInfo.thermalState` every 10 seconds
- If `Critical`: pause inference, reduce particle effects, notify user
- Automatic resume when thermal state returns to `Nominal`

### Background Behavior
- AR session pauses when app backgrounds (iOS standard)
- Symbiont agents freeze (Tick disabled)
- Resume on foreground with re-consent check (if >10 minutes elapsed)

---

## What to Create In-Editor (Not Committed)

Since binary assets (.uasset, .umap) are excluded from the repository, developers recreating this demo must create:

### Level Assets
1. **GiggleForest_Main.umap**
   - New Level → "Empty Level"
   - Add Landscape (2x2km, material M_ForestGround)
   - Add ~50 Tree static meshes (UE5 starter content or Quixel)
   - Add Directional Light, Sky Light, Post Process Volume (settings above)
   - Save in `Content/Demos/GiggleForest/`

### Blueprint Assets
2. **BP_Symbiont_IntroUI**
   - New Widget Blueprint → User Widget
   - Implement node graph as specified above
   - Assign to Game Mode's "Default Widget Class" for auto-spawn

3. **BP_SymbiontManager**
   - New Blueprint → Actor
   - Add USymbiontCoreEngine component (C++ class will be available after plugin build)
   - Implement BeginPlay and DeepReasoningTick as specified

4. **BP_ZorelAgent**
   - New Blueprint → Actor
   - Add Static Mesh Component (sphere, scale 0.5)
   - Add Niagara Component → NS_ChaoticTrail (create separately)
   - Implement Tick logic as specified

5. **BP_QuillanAgent**
   - New Blueprint → Actor
   - Add Static Mesh Component (cube, scale 0.75)
   - Add Text Render Component
   - Implement BeginPlay and BossThoughtsUpdate as specified

6. **BP_SymbiontHUD**
   - New Blueprint → HUD
   - Implement Draw HUD as specified
   - Assign to Game Mode's "HUD Class"

### Material Assets
7. **M_Zorel_Iridescent**
   - Material with hue shift parameter (0-1 input → HSV node)
   - Metallic: 0.8, Roughness: 0.2
   - Emissive: velocity-driven (exposed parameter)

8. **M_Quillan_Matte**
   - Simple material with emissive pulsation
   - Base Color: (0.2, 0.4, 0.8)
   - Emissive: parameter "ThoughtIntensity" (0.5-1.5)

### Niagara Systems
9. **NS_Lumen_Ignition_Burst**
   - Burst emitter, 500 particles over 2 seconds
   - Gold gradient color over life
   - Sphere emission, outward velocity

10. **NS_ChaoticTrail**
    - Continuous ribbon emitter
    - Spawn rate driven by "TrailIntensity" parameter
    - Lifetime: 1 second, fade out

### Audio Assets
11. **SFX_SOISOISOI_Resonance_111Hz**
    - Sine wave generator (or import .wav)
    - Frequency: 111 Hz, duration 2 seconds
    - Fade in/out to avoid harsh edges

12. **SFX_Fusion_Chime**
    - Bell-like sound (Quixel or synthesis)
    - Single instance, 1.5 seconds

13. **SFX_Warning_Beep**
    - 440 Hz pulse, 0.2 seconds
    - Used for GGC threshold alerts

### Textures
14. **T_ConstitutionalSeal**
    - 512x512 PNG (badge/emblem graphic)
    - Shown in HUD corner

---

## Mapping Lore → Implementation

| Lore Term | Technical Implementation |
|-----------|--------------------------|
| **Giggle-Forest** | UE5 level with AR overlay |
| **Symbiont** | USymbiontCoreEngine C++ class managing state |
| **Zorel** | BP_ZorelAgent (chaos actor) |
| **Quillan** | BP_QuillanAgent (stabilizer actor) |
| **Giggle Growth Coefficient** | Float property in FSymbiontConstitution, drives visual feedback |
| **Constitutional Invariants** | Boolean flags checked every frame/interval, trigger warnings if violated |
| **Deep Reasoning** | Stub call to local CoreML model (DeepSeek-R1) |
| **Gavel Tap** | iOS-native consent gesture gating all AR/AI features |
| **Lumen Ignition** | Niagara particle burst on successful consent |
| **SOISOISOI Resonance** | 111 Hz audio cue (references harmonic tuning) |
| **Fusion** | Linking Zorel and Quillan actors to constrain chaos |

---

## Development Checklist

Before testing the demo, ensure:

- [ ] UE5.3+ installed with iOS build support
- [ ] Xcode 15+ with iOS SDK 17.0+
- [ ] SymbiontCore plugin compiled (see `ue/Symbiont/Plugins/SymbiontCore/Source/`)
- [ ] All Blueprint assets created as specified above
- [ ] Info.plist updated with `NSCameraUsageDescription`
- [ ] Test on physical iOS device (Simulator doesn't support ARKit)
- [ ] GiggleGrowthCoefficient clamped to [0.0, 0.85] in USymbiontCoreEngine::SetGiggleGrowthCoefficient
- [ ] DeepReasoning calls log "TODO: Implement CoreML inference" (no-op for v0)

---

## Known Limitations (v0 Specification)

- **No Autoregressive Loop:** Deep reasoning is single-shot, not chained (planned for v1)
- **No Actual CoreML Inference:** Stubs return placeholder responses
- **No Network Telemetry:** All logging is local (Governor reasoning not yet implemented)
- **Placeholder Audio/Visual Assets:** Requires manual creation in-editor

---

## References

- UE5 Blueprint Visual Scripting: https://docs.unrealengine.com/5.3/en-US/blueprints-visual-scripting-in-unreal-engine/
- ARKit Best Practices: https://developer.apple.com/documentation/arkit
- iOS Privacy Permissions: https://developer.apple.com/documentation/avfoundation/avcapturedevice/1624613-requestaccess
- CoreML Integration: https://developer.apple.com/documentation/coreml

---

*"The Gavel must fall before the forest awakens. Consent is the first invariant."*
