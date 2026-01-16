# SymbiontCore Plugin

**Version**: 1.0.0  
**Engine**: Unreal Engine 5  
**Platforms**: Win64, Mac, iOS

## Overview

The **SymbiontCore** plugin provides a Constitutional AI framework for safe, on-device inference with built-in safety gates and user consent management. It implements the "Giggle Forest Ritual" invocation flow with thermal, battery, and performance monitoring.

## Key Features

### 1. Consent Management
- `USymbiontConsentManager` - Game Instance Subsystem for explicit user consent
- Blueprint-callable consent grant/revoke methods
- Persistent storage placeholders (iOS/Android integration required)
- Full compliance with App Store guidelines 5.1.2(i)

### 2. Gavel-Tap Ritual Detection
- `UGavelTapDetectorComponent` - Actor Component for gesture detection
- Configurable tap count (default: 2) and hold duration (default: 1.0s)
- Blueprint-friendly event system (`OnGavelTapDetected` delegate)
- UMG touch input integration

### 3. Constitutional Core Engine
- `USymbiontCoreEngine` - Core inference orchestrator with safety gates
- Four constitutional checks:
  1. User Consent (required)
  2. Thermal Sanctuary (device not overheating)
  3. Frame Soul (FPS ≥ 30)
  4. Battery Communion (battery ≥ 15%)
- Giggle Growth Coefficient (playfulness tuning: 0.0 to 0.85)
- Blueprint-callable ritual invocation with automatic gating

### 4. iOS CoreML Bridge
- `FIOSCoreMLBridge` - Objective-C++ bridge for on-device inference
- A17/A18 Neural Engine optimization
- Asynchronous model loading
- Memory management and thermal monitoring integration
- Stub implementation (requires actual `.mlmodelc` model files)

### 5. Data Structures
- `FSymbiontVitals` - Device state (FPS, thermal, battery, network)
- `FSymbiontConstitution` - Safety invariants and consent flags
- `EDeepSeekModel` - Model variants (Reasoner, Chat, Coder, Distilled)

## Installation

1. Copy the `SymbiontCore` plugin to your project's `Plugins/` folder
2. Enable the plugin in your `.uproject` file or via the Plugins browser
3. Regenerate Visual Studio/Xcode project files
4. Build the project

## Quick Start

### Blueprint

1. **Get Consent Manager**:
   ```
   Get Game Instance → Get Subsystem (USymbiontConsentManager)
   ```

2. **Grant Consent** (after showing native dialog):
   ```
   Consent Manager → Grant User Consent
   ```

3. **Add Gavel Detector to Actor**:
   - Add `UGavelTapDetectorComponent` to your Player Controller or Pawn
   - Bind to `OnGavelTapDetected` event

4. **Invoke Ritual**:
   ```
   On Gavel Tap Detected:
     → Create USymbiontCoreEngine
     → Set Giggle Growth Coefficient (0.5)
     → Invoke Symbiont Ritual
     → Bind to OnRitualBegin
   ```

### C++

```cpp
// Get consent manager
USymbiontConsentManager* ConsentManager = 
    GetGameInstance()->GetSubsystem<USymbiontConsentManager>();

// Grant consent (after showing native dialog)
ConsentManager->GrantUserConsent();

// Add gavel detector
UGavelTapDetectorComponent* GavelDetector = 
    CreateDefaultSubobject<UGavelTapDetectorComponent>(TEXT("GavelDetector"));
GavelDetector->OnGavelTapDetected.AddDynamic(this, &AMyActor::OnGavelTap);

// Invoke ritual
void AMyActor::OnGavelTap()
{
    USymbiontCoreEngine* CoreEngine = NewObject<USymbiontCoreEngine>(this);
    CoreEngine->SetGiggleGrowthCoefficient(0.5f);
    CoreEngine->OnRitualBegin.AddDynamic(this, &AMyActor::OnRitualBegin);
    
    if (!CoreEngine->InvokeSymbiontRitual())
    {
        // Constitutional gates failed - check logs for details
    }
}
```

## File Structure

```
SymbiontCore/
├── SymbiontCore.uplugin              # Plugin descriptor
├── Source/SymbiontCore/
│   ├── SymbiontCore.Build.cs         # Build configuration
│   ├── Public/
│   │   ├── SymbiontCore.h            # Module header
│   │   ├── SymbiontTypes.h           # Enums and structs
│   │   ├── SymbiontConsentManager.h  # Consent subsystem
│   │   ├── GavelTapDetectorComponent.h  # Gesture detector
│   │   └── SymbiontCoreEngine.h      # Core inference engine
│   └── Private/
│       ├── SymbiontCore.cpp          # Module implementation
│       ├── SymbiontConsentManager.cpp
│       ├── GavelTapDetectorComponent.cpp
│       ├── SymbiontCoreEngine.cpp
│       └── IOS/
│           └── FIOSCoreMLBridge.mm   # iOS CoreML bridge
```

## Platform-Specific Notes

### iOS

- **CoreML Models**: Add `.mlmodelc` files to your Xcode project's Resources
- **Thermal Monitoring**: Implement `NSProcessInfo.thermalState` integration
- **Battery Level**: Implement `UIDevice.batteryLevel` integration
- **Consent Dialog**: Show native `UIAlertController` before calling `GrantUserConsent()`
- **Neural Engine**: Automatically optimized for A17 Pro and A18/A18 Pro chips

### Windows/Mac

- CoreML bridge is iOS-only (guarded by `#if PLATFORM_IOS`)
- For desktop inference, integrate ONNX Runtime or similar
- Thermal/battery monitoring requires platform-specific APIs

## Configuration

### Gavel Tap Settings

Edit in Blueprint Details panel or C++:
```cpp
GavelDetector->RequiredTaps = 3;      // Number of taps
GavelDetector->HoldDuration = 2.0f;   // Hold duration in seconds
```

### Constitutional Thresholds

Currently hardcoded in `SymbiontCoreEngine.cpp`:
- Thermal: Critical threshold = 3 (iOS thermal state)
- FPS: Minimum = 30 FPS
- Battery: Minimum = 15%

To customize, modify `InvokeSymbiontRitual()` and `UpdateConstitution()`.

## Documentation

- **Developer Guide**: `docs/GIGGLE_FOREST_RITUAL.md` - Invocation flow and lore-to-code mapping
- **App Store Compliance**: `docs/APP_STORE_COMPLIANCE.md` - Guidelines 2.5.2 and 5.1.2(i) mapping
- **Demo README**: `ue/Symbiont/Content/Demos/GiggleForest/README.md` - Demo level guide

## TODO / Future Work

- [ ] Implement iOS thermal state monitoring (NSProcessInfo)
- [ ] Implement iOS battery monitoring (UIDevice)
- [ ] Implement Android equivalents (ThermalManager, BatteryManager)
- [ ] Add actual CoreML model loading (requires `.mlmodelc` files)
- [ ] Persist consent to platform storage (NSUserDefaults / SharedPreferences)
- [ ] Add user notification system (HUD, toasts)
- [ ] Implement inference result handling
- [ ] Add analytics/telemetry for ritual success/failure
- [ ] Create UMG example widgets
- [ ] Add automated tests

## License

Copyright AIOSPANDORA. All Rights Reserved.

## Support

For issues, questions, or contributions, see the main repository:
https://github.com/AIOSPANDORA/Ouroboros
