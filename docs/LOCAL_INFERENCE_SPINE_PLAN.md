# Local Inference Spine Plan

**Version:** v0 Specification  
**Target:** On-device AI reasoning with constitutional oversight  
**Platform:** iOS (CoreML), Android (TFLite future), Desktop (ONNX future)

---

## First Principles

### 1. Privacy-First Architecture

**Core Tenet:** All inference happens on-device. No user data leaves the device without explicit, renewed consent.

**Implementation:**
- Model files embedded in app bundle or downloaded once with user approval
- Network calls limited to:
  - Model updates (opt-in, WiFi-only)
  - Anonymous telemetry (aggregated, no PII, opt-in)
- Inference engine runs in isolated sandbox (iOS App Sandbox, CoreML framework)

### 2. Constitutional Constraint Enforcement

**Core Tenet:** AI outputs are not blindly trusted. Every inference result is validated against constitutional invariants before execution.

**Invariant Categories:**
1. **Safety:** No hallucinated data presented as fact
2. **Thermal:** Inference paused if device overheating
3. **Battery:** Reduced inference frequency if battery < 20%
4. **Coherence:** Outputs must align with known environmental state (AR lattice, user context)
5. **Consent:** No inference if user revoked permissions

**Validation Flow:**
```
Inference Request → Model Execution → Output → Constitutional Check → (Pass/Fail)
  ├─> Pass: Execute action, update UI, log success
  └─> Fail: Discard output, log violation, notify user (optional)
```

### 3. Predictable Degradation

**Core Tenet:** System remains functional even when inference is unavailable or disabled.

**Fallback Behaviors:**
- **No Model Loaded:** Static guidance text, pre-scripted agent dialogs
- **Inference Timeout:** Retry once, then fallback to last known good state
- **High Thermal State:** Pause inference, reduce visual effects, resume when cool
- **Battery Critical:** Disable inference, maintain minimal UI, prompt user to charge

### 4. Observable State Machine

**Core Tenet:** Every state transition is logged and inspectable for debugging and governance.

**State Transitions:**
```
UNINITIALIZED → MODEL_LOADING → IDLE → INFERENCING → RESULT_READY → VALIDATED → IDLE
                                   ↓
                              THERMAL_PAUSE ←→ IDLE
                                   ↓
                              BATTERY_REDUCED ←→ IDLE
                                   ↓
                              CONSENT_REVOKED (terminal, requires app restart)
```

Each transition emits:
- Timestamp (milliseconds since epoch)
- Previous state
- New state
- Trigger (user action, timer, system event)
- Payload (optional JSON context)

---

## Telemetry Contract

### What Governor Reasons Over

The "Governor" (planned component for v1+) will analyze telemetry to adjust inference behavior. For v0, telemetry is logged but not yet consumed.

**Telemetry Schema (JSON):**

```json
{
  "session_id": "uuid-v4",
  "timestamp": "ISO8601",
  "event_type": "inference_request | constitutional_check | thermal_event | user_action",
  "payload": {
    "model": "deepseek-r1-distilled-q4",
    "prompt_hash": "sha256-first-8-chars",
    "inference_duration_ms": 450,
    "output_token_count": 128,
    "constitutional_result": "pass | fail",
    "invariant_flags": {
      "xr_coherence_active": true,
      "zorel_quillan_fused": true,
      "thermal_nominal": true,
      "battery_sufficient": true
    },
    "device_vitals": {
      "fps": 58.3,
      "thermal_state": "nominal",
      "battery_level": 0.72,
      "network_available": false
    }
  }
}
```

**Governor Analysis (Future):**
- Detect patterns: "Inference requests spike when FPS drops → reduce inference frequency"
- Optimize: "Thermal events occur after 3 consecutive inferences → insert cooldown delay"
- Alert: "Constitutional failures increasing → notify developer, suggest model retraining"

**Privacy Guarantee:**
- Prompt content NEVER logged (only hash)
- Output content NEVER logged (only token count)
- User actions aggregated (no per-user tracking)

---

## Minimal Spine v0 Scope

### What IS Included

1. **Model Loading Stub**
   - `USymbiontCoreEngine::LoadModel(FString ModelPath)` (iOS: CoreML path)
   - Returns success/failure, logs model metadata (size, version)
   - **No actual loading yet** → TODO comment placeholder

2. **Inference Request Interface**
   - `USymbiontCoreEngine::RequestDeepReasoning(FString Prompt, EDeepSeekModel ModelType)`
   - Accepts prompt, model type enum (Reasoner, Chat, Coder, Distilled)
   - Returns immediately (asynchronous design, callback planned for v1)
   - **No actual inference yet** → Logs "TODO: Call CoreML predict" and returns placeholder

3. **Constitutional Validation**
   - `USymbiontCoreEngine::EvaluateConstitutionalInvariants(FString EnvironmentalData)`
   - Checks current `FSymbiontConstitution` struct against thresholds
   - Returns boolean: pass/fail
   - **Fully implemented** (no external dependencies)

4. **Vitals Monitoring**
   - `USymbiontCoreEngine::UpdateDeviceVitals()` called every frame (Tick)
   - Populates `FSymbiontVitals` struct with FPS, thermal, battery
   - **Partial implementation:** FPS from UE5 stats, others are stubs (iOS bridge required)

5. **Giggle Growth Coefficient Control**
   - `USymbiontCoreEngine::SetGiggleGrowthCoefficient(float Coeff)`
   - Clamps to [0.0, 0.85], logs if out of range
   - Drives visual feedback in Blueprint (HUD, particles, fog)
   - **Fully implemented**

### What IS NOT Included (v0)

1. **Autoregressive Inference Loop**
   - No chaining of model outputs (e.g., "reason → reflect → refine")
   - Single-shot inference only
   - **Planned for v1:** Iterative reasoning with halting condition

2. **Actual CoreML/TFLite Calls**
   - Stubs return `"[Placeholder response: Constitutional check passed]"`
   - **Planned for v0.5:** Real model loading and inference
   - Requires:
     - DeepSeek-R1 model export to CoreML (.mlmodelc)
     - Tokenizer integration (SentencePiece or custom)
     - GPU acceleration via Metal (iOS) or CoreML accelerators

3. **Network Telemetry Upload**
   - Telemetry logged to local JSON file only
   - **Planned for v1:** Opt-in upload to secure analytics endpoint
   - Requires:
     - User consent flow (separate from AR consent)
     - Encrypted HTTPS POST to backend
     - Compliance with GDPR/CCPA (anonymous only, no PII)

4. **Governor Reasoning Engine**
   - No analysis of telemetry patterns yet
   - **Planned for v1:** Rust-based analyzer (separate process/binary)
   - Consumes telemetry JSON, outputs recommendations JSON
   - Example: `{"action": "reduce_inference_freq", "reason": "thermal_events_detected", "suggested_delay_seconds": 10}`

5. **Multi-Model Swapping**
   - Only one model loaded at a time (EDeepSeekModel enum specifies intent, but actual model is the same)
   - **Planned for v2:** Dynamic model switching based on task (e.g., Reasoner for logic, Chat for dialog)

---

## Implementation Roadmap

### v0 (Current Specification - This PR)
- ✅ Struct definitions: `FSymbiontConstitution`, `FSymbiontVitals`, `EDeepSeekModel`
- ✅ Interface stubs: `RequestDeepReasoning`, `EvaluateConstitutionalInvariants`
- ✅ Constitutional validation logic
- ✅ Giggle Growth Coefficient control
- ✅ Blueprint-callable UE5 functions (UFUNCTION macros)
- ✅ Placeholder iOS bridge (.mm file with TODO comments)

### v0.5 (Model Loading - Next Sprint)
- ⬜ CoreML model integration (`DeepSeek_R1_Distilled_Q4.mlmodelc`)
- ⬜ Tokenizer (SentencePiece C++ library or Swift wrapper)
- ⬜ Asynchronous inference with callback (`OnDeepReasoningComplete` event)
- ⬜ iOS thermal monitoring (`ProcessInfo.thermalState` Objective-C++ bridge)
- ⬜ Battery level monitoring (`UIDevice.batteryLevel`)

### v1 (Autoregressive Loop + Telemetry)
- ⬜ Iterative reasoning: "Chain of Thought" prompts with halting condition
- ⬜ Telemetry upload (opt-in, HTTPS POST)
- ⬜ Governor reasoning engine (Rust binary, reads JSON telemetry)
- ⬜ Dynamic inference frequency adjustment based on Governor recommendations

### v2 (Multi-Model + Advanced Features)
- ⬜ Model hot-swapping (load Reasoner vs. Chat based on context)
- ⬜ Quantization level selection (Q4 vs. Q8 based on device capabilities)
- ⬜ On-device fine-tuning (LoRA adapters for user-specific behavior)
- ⬜ Cross-platform support (Android TFLite, Desktop ONNX)

---

## Technical Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    UE5 Blueprint Layer                       │
│  (BP_SymbiontManager, BP_ZorelAgent, BP_QuillanAgent, HUD)  │
└────────────────────┬────────────────────────────────────────┘
                     │ UFUNCTION calls
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              USymbiontCoreEngine (C++ UObject)               │
│  - RequestDeepReasoning(Prompt, ModelType)                  │
│  - EvaluateConstitutionalInvariants(EnvironmentalData)      │
│  - GetConstitutionSnapshot() → FSymbiontConstitution        │
│  - SetGiggleGrowthCoefficient(float)                        │
│  - UpdateDeviceVitals() → FSymbiontVitals                   │
└────────────────────┬────────────────────────────────────────┘
                     │ iOS calls (Objective-C++)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          SymbiontCoreMLBridge.mm (Platform Layer)           │
│  - LoadCoreMLModel(ModelPath) → MLModel*                    │
│  - PredictWithModel(Tokens) → OutputTokens                  │
│  - GetThermalState() → ProcessInfo.thermalState             │
│  - GetBatteryLevel() → UIDevice.batteryLevel                │
└────────────────────┬────────────────────────────────────────┘
                     │ CoreML framework
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  iOS CoreML Runtime                          │
│  - Neural Engine acceleration (A14+ chips)                   │
│  - GPU fallback (Metal shaders)                              │
│  - CPU fallback (BNNS library)                               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow: Inference Request

```
User taps "Gavel" button (gesture gate)
  └─> BP_Symbiont_IntroUI::OnClicked
        └─> Spawn BP_SymbiontManager
              └─> BeginPlay: CoreEngine->InitializeSymbiont()
                    └─> Load model (stub, logs TODO)
                          └─> Set Timer: DeepReasoningTick (every 5s)
                                └─> CoreEngine->RequestDeepReasoning("Evaluate forest state", DS_Reasoner)
                                      └─> [v0 stub] Logs prompt, returns immediately
                                      └─> [v0.5] CoreMLBridge->PredictWithModel(tokens)
                                            └─> CoreML inference (200-500ms on A15+)
                                                  └─> Return output tokens
                                                        └─> Detokenize to string
                                                              └─> EvaluateConstitutionalInvariants(output)
                                                                    └─> Check: within GGC bounds? XR active? Fused?
                                                                          ├─> Pass: Execute Blueprint logic (move agents, update HUD)
                                                                          └─> Fail: Discard output, log warning, show in-game notice
```

---

## Constitutional Enforcement Logic

### Invariant Definitions

Defined in `FSymbiontConstitution` struct (C++):

```cpp
USTRUCT(BlueprintType)
struct FSymbiontConstitution
{
    GENERATED_BODY()

    // Giggle Growth Coefficient: Controls chaos-order balance
    // Valid range: [0.0, 0.85]. >0.85 triggers constitutional breach.
    UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
    float GiggleGrowthCoefficient = 0.5f;

    // XR Coherence: Is AR session active and tracking?
    UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
    bool bXR_COHERENCE_ACTIVE = false;

    // Zorel-Quillan Fusion: Are agents linked?
    UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
    bool bZOREL_QUILLAN_FUSED = false;

    // Thermal Safety: Is device temperature nominal?
    UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
    bool bTHERMAL_NOMINAL = true;

    // Battery Sufficiency: Is battery above critical threshold (20%)?
    UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
    bool bBATTERY_SUFFICIENT = true;

    // User Consent: Has user approved AR/AI features?
    UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
    bool bUSER_CONSENTED = false;
};
```

### Evaluation Algorithm

```cpp
bool USymbiontCoreEngine::EvaluateConstitutionalInvariants(const FString& EnvironmentalData)
{
    bool bPassed = true;

    // Check GGC bounds
    if (Constitution.GiggleGrowthCoefficient < 0.0f || Constitution.GiggleGrowthCoefficient > 0.85f)
    {
        UE_LOG(LogSymbiont, Warning, TEXT("CONSTITUTIONAL BREACH: GGC out of bounds (%.3f)"), Constitution.GiggleGrowthCoefficient);
        bPassed = false;
    }

    // Check consent
    if (!Constitution.bUSER_CONSENTED)
    {
        UE_LOG(LogSymbiont, Error, TEXT("CONSTITUTIONAL BREACH: User consent revoked or never granted"));
        bPassed = false;
    }

    // Check thermal state
    if (!Constitution.bTHERMAL_NOMINAL)
    {
        UE_LOG(LogSymbiont, Warning, TEXT("CONSTITUTIONAL WARNING: Thermal state critical, pausing inference"));
        bPassed = false; // Non-fatal, but inference should pause
    }

    // Check battery
    if (!Constitution.bBATTERY_SUFFICIENT)
    {
        UE_LOG(LogSymbiont, Warning, TEXT("CONSTITUTIONAL WARNING: Battery low, reducing inference frequency"));
        // Could return true but with throttling flag
    }

    // Log environmental context
    UE_LOG(LogSymbiont, Verbose, TEXT("Constitutional check: %s | Environment: %s"), 
        bPassed ? TEXT("PASSED") : TEXT("FAILED"), 
        *EnvironmentalData);

    return bPassed;
}
```

---

## Device Vitals Monitoring

### FSymbiontVitals Struct

```cpp
USTRUCT(BlueprintType)
struct FSymbiontVitals
{
    GENERATED_BODY()

    // Frames per second (from UE5 stats)
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
    float FPS = 60.0f;

    // Thermal state: "nominal", "fair", "serious", "critical"
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
    FString ThermalState = TEXT("nominal");

    // Battery level: 0.0 (empty) to 1.0 (full)
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
    float BatteryLevel = 1.0f;

    // Is device connected to network? (WiFi or cellular)
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
    bool bNetworkAvailable = false;

    // Is user actively interacting? (touch input in last 5 seconds)
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
    bool bUserInteracting = false;

    // Timestamp of last vitals update (Unix epoch milliseconds)
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
    int64 LastUpdateTimestamp = 0;
};
```

### Update Logic (Called Every Frame)

```cpp
void USymbiontCoreEngine::UpdateDeviceVitals()
{
    // FPS from UE5 engine stats
    Vitals.FPS = 1.0f / GetWorld()->GetDeltaSeconds();

    // Thermal state (iOS bridge required)
    #if PLATFORM_IOS
    Vitals.ThermalState = SymbiontCoreMLBridge::GetThermalStateString();
    Constitution.bTHERMAL_NOMINAL = (Vitals.ThermalState == TEXT("nominal") || Vitals.ThermalState == TEXT("fair"));
    #else
    Vitals.ThermalState = TEXT("unknown");
    Constitution.bTHERMAL_NOMINAL = true; // Assume nominal on non-iOS
    #endif

    // Battery level (iOS bridge required)
    #if PLATFORM_IOS
    Vitals.BatteryLevel = SymbiontCoreMLBridge::GetBatteryLevel();
    Constitution.bBATTERY_SUFFICIENT = (Vitals.BatteryLevel > 0.2f);
    #else
    Vitals.BatteryLevel = 1.0f; // Assume full on desktop
    Constitution.bBATTERY_SUFFICIENT = true;
    #endif

    // Network availability (UE5 platform abstraction)
    Vitals.bNetworkAvailable = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->HasNetworkDevice();

    // User interaction (check input system)
    APlayerController* PC = GetWorld()->GetFirstPlayerController();
    if (PC)
    {
        float TimeSinceInput = GetWorld()->GetTimeSeconds() - PC->GetInputKeyTimeDown(EKeys::AnyKey);
        Vitals.bUserInteracting = (TimeSinceInput < 5.0f);
    }

    // Timestamp
    Vitals.LastUpdateTimestamp = FDateTime::UtcNow().ToUnixTimestamp() * 1000;
}
```

---

## Model Selection Strategy

### EDeepSeekModel Enum

```cpp
UENUM(BlueprintType)
enum class EDeepSeekModel : uint8
{
    DS_Reasoner   UMETA(DisplayName = "DeepSeek-R1 Reasoner"),     // Long-form reasoning, 128k context
    DS_Chat       UMETA(DisplayName = "DeepSeek-R1 Chat"),         // Conversational, 64k context
    DS_Coder      UMETA(DisplayName = "DeepSeek-Coder-V2"),        // Code generation/analysis
    DS_Distilled  UMETA(DisplayName = "DeepSeek-R1 Distilled Q4")  // Quantized, fastest, 16k context
};
```

### Selection Heuristics (v1 Implementation)

| Task Type | Model | Rationale |
|-----------|-------|-----------|
| Logical conflict resolution | DS_Reasoner | Needs chain-of-thought reasoning |
| Agent dialog generation | DS_Chat | Conversational style |
| Blueprint script suggestion | DS_Coder | Code-aware tokenizer |
| Real-time constitutional check | DS_Distilled | Fastest inference (200ms vs. 800ms) |

**v0 Behavior:** All requests use DS_Distilled (only model planned for inclusion). Enum is future-proofing.

---

## Fallback and Error Handling

### Model Load Failures

```cpp
bool USymbiontCoreEngine::LoadModel(const FString& ModelPath)
{
    #if PLATFORM_IOS
    MLModel* LoadedModel = SymbiontCoreMLBridge::LoadCoreMLModel(ModelPath);
    if (!LoadedModel)
    {
        UE_LOG(LogSymbiont, Error, TEXT("Failed to load CoreML model at path: %s"), *ModelPath);
        UE_LOG(LogSymbiont, Error, TEXT("Inference will be disabled. Please ensure DeepSeek_R1_Distilled_Q4.mlmodelc is in Resources/"));
        bModelLoaded = false;
        return false;
    }
    bModelLoaded = true;
    return true;
    #else
    UE_LOG(LogSymbiont, Warning, TEXT("CoreML not available on this platform. Inference disabled."));
    bModelLoaded = false;
    return false;
    #endif
}
```

**User-Facing Behavior:**
- HUD shows: "Inference unavailable. Check model installation."
- Agents still spawn and move (no AI dialog, pre-scripted only)
- Giggle Growth Coefficient defaults to 0.5 (static, no dynamic adjustment)

### Inference Timeout

```cpp
// v0.5 implementation (asynchronous callback)
void USymbiontCoreEngine::OnInferenceTimeout()
{
    UE_LOG(LogSymbiont, Warning, TEXT("Inference timed out after 2 seconds. Retrying once..."));
    if (RetryCount < 1)
    {
        RetryCount++;
        RequestDeepReasoning(LastPrompt, LastModelType);
    }
    else
    {
        UE_LOG(LogSymbiont, Error, TEXT("Inference failed after retry. Using fallback response."));
        OnDeepReasoningComplete(TEXT("[Fallback: Constitutional check passed, proceeding with default behavior]"));
        RetryCount = 0;
    }
}
```

---

## Privacy and Compliance

### Data Retention

- **Telemetry JSON:** Stored locally for 7 days, then auto-deleted
- **Model Files:** Persist in app bundle, never transmitted
- **User Inputs:** NEVER logged (only prompt hash for debugging)
- **Inference Outputs:** NEVER logged (only token count)

### GDPR/CCPA Compliance

- **Right to Deletion:** Clear telemetry JSON on user request (Settings → Privacy → Delete Telemetry)
- **Right to Access:** Export telemetry JSON to user's Files app (anonymized, no PII)
- **Right to Opt-Out:** Disable telemetry in Settings (default: enabled, can be toggled)

### iOS App Store Review

- **Privacy Manifest:** Include `NSPrivacyAccessedAPITypes` with CoreML, Camera (ARKit)
- **Tracking Transparency:** NOT required (no third-party SDKs, no cross-app tracking)
- **Data Use Description:** "On-device AI inference for AR agents. No data leaves your device."

---

## Testing Strategy

### Unit Tests (C++)

```cpp
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSymbiontConstitutionClampTest, "Symbiont.Constitution.ClampGGC", EAutomationTestFlags::ApplicationContextMask | EAutomationTestFlags::ProductFilter)
bool FSymbiontConstitutionClampTest::RunTest(const FString& Parameters)
{
    USymbiontCoreEngine* Engine = NewObject<USymbiontCoreEngine>();
    
    // Test upper bound clamp
    Engine->SetGiggleGrowthCoefficient(1.5f);
    TestEqual("GGC clamped to 0.85", Engine->GetConstitutionSnapshot().GiggleGrowthCoefficient, 0.85f);
    
    // Test lower bound clamp
    Engine->SetGiggleGrowthCoefficient(-0.3f);
    TestEqual("GGC clamped to 0.0", Engine->GetConstitutionSnapshot().GiggleGrowthCoefficient, 0.0f);
    
    // Test valid value
    Engine->SetGiggleGrowthCoefficient(0.6f);
    TestEqual("GGC set to 0.6", Engine->GetConstitutionSnapshot().GiggleGrowthCoefficient, 0.6f);
    
    return true;
}
```

### Integration Tests (Blueprint)

- **Test_GavelConsent:** Simulate button tap, verify AR session starts, agents spawn
- **Test_ConstitutionalBreach:** Set GGC to 0.9, verify HUD shows red warning, inference pauses
- **Test_ThermalPause:** Mock thermal state to "critical", verify agents freeze, inference stops
- **Test_ModelLoadFailure:** Remove model file, verify graceful fallback to static behavior

### Device Tests (Physical iOS)

- **iPhone 12 (A14):** Test baseline performance (30 FPS minimum)
- **iPhone 15 Pro (A17):** Test Neural Engine acceleration (60 FPS target)
- **iPad Air (M1):** Test thermal headroom (sustained inference without throttle)
- **Low Battery (<15%):** Verify reduced inference frequency, no crashes

---

## Future Enhancements

### v3: Cross-Agent Collaboration

- Multiple symbiont instances (Zorel-1, Zorel-2, Quillan-A, Quillan-B)
- Shared constitutional state (distributed lattice)
- Consensus-based decision making (3-of-5 agents must agree before action)

### v4: User Fine-Tuning

- LoRA adapters trained on user interactions (e.g., preferred agent dialog style)
- Stored locally, never uploaded
- Opt-in feature: "Teach your symbiont your preferences"

### v5: Multi-Platform Sync

- Optional iCloud sync of constitutional state (encrypted)
- Consistent agent behavior across user's devices
- Strict privacy controls (user can disable sync anytime)

---

## References

- **CoreML Documentation:** https://developer.apple.com/documentation/coreml
- **ARKit Privacy Best Practices:** https://developer.apple.com/documentation/arkit/verifying_user_is_in_a_safe_environment
- **DeepSeek Model Cards:** https://github.com/deepseek-ai/DeepSeek-R1 (hypothetical)
- **UE5 Plugins Guide:** https://docs.unrealengine.com/5.3/en-US/plugins-in-unreal-engine/
- **iOS Thermal State Monitoring:** https://developer.apple.com/documentation/foundation/processinfo/thermalstate

---

*"Inference without constraint is hallucination. Constraints without flexibility are dogma. The spine balances both."*
