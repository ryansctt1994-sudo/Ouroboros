# Giggle Forest Ritual - Developer Guide

## Overview

The **Giggle Forest Ritual** is the invocation flow for activating the Constitutional Symbiont's on-device AI inference capabilities. This document maps the conceptual "lore" terminology to the actual implementation in Unreal Engine.

## Terminology Mapping

| Lore Term | Code Component | Description |
|-----------|----------------|-------------|
| **Constitutional Symbiont** | `USymbiontCoreEngine` | The core AI inference engine with built-in safety constraints |
| **Gavel-Tap Ritual** | `UGavelTapDetectorComponent` | User gesture (2 taps + hold) that initiates the invocation flow |
| **User Consent** | `USymbiontConsentManager` | Explicit permission for AR/inference features (required before any activation) |
| **Thermal Sanctuary** | `FSymbiontConstitution.bThermalSanctuaryIntact` | Device temperature within safe operating range (< critical threshold) |
| **Frame Soul** | `FSymbiontConstitution.bFrameSoulSynchronized` | Frame rate above minimum threshold (≥30 FPS) |
| **Battery Communion** | `FSymbiontConstitution.bBatteryCommunionMaintained` | Sufficient battery level (≥15%) for sustained inference |
| **Giggle Growth Coefficient** | `FSymbiontConstitution.GiggleGrowthCoefficient` | Playfulness/creativity tuning parameter (0.0 to 0.85) |

## Invocation Flow

### 1. User Consent (Prerequisite)

Before any ritual can be performed, the user must explicitly grant consent:

```cpp
USymbiontConsentManager* ConsentManager = GetGameInstance()->GetSubsystem<USymbiontConsentManager>();

// Show native consent dialog first (iOS requirement)
// Then grant consent:
ConsentManager->GrantUserConsent();
```

**iOS Requirement**: Before calling `GrantUserConsent()`, you MUST show a native dialog explaining:
- What data is being processed (sensor inputs, user interactions)
- Where processing occurs (on-device, no cloud upload)
- How to revoke consent later

### 2. Gavel-Tap Detection

Add the detector component to your actor (e.g., Player Controller or UI widget):

```cpp
UGavelTapDetectorComponent* GavelDetector = CreateDefaultSubobject<UGavelTapDetectorComponent>(TEXT("GavelDetector"));
GavelDetector->RequiredTaps = 2;        // Default: 2 taps
GavelDetector->HoldDuration = 1.0f;     // Default: 1 second hold

// Bind to the ritual completion event
GavelDetector->OnGavelTapDetected.AddDynamic(this, &AMyController::OnGavelTapRitualComplete);
```

In UMG Blueprint, wire touch/click events to the detector:

```cpp
void UMyWidget::NativeOnTouchStarted(const FGeometry& InGeometry, const FPointerEvent& InGestureEvent)
{
    Super::NativeOnTouchStarted(InGeometry, InGestureEvent);
    GavelDetector->NotifyTouchBegan(InGestureEvent.GetScreenSpacePosition());
}

void UMyWidget::NativeOnTouchEnded(const FGeometry& InGeometry, const FPointerEvent& InGestureEvent)
{
    Super::NativeOnTouchEnded(InGeometry, InGestureEvent);
    GavelDetector->NotifyTouchEnded(InGestureEvent.GetScreenSpacePosition());
}

// Or for simple button clicks:
void UMyWidget::OnButtonClicked()
{
    GavelDetector->NotifyTap();
}
```

### 3. Constitutional Gating

When the gavel-tap ritual completes, invoke the Symbiont:

```cpp
void AMyController::OnGavelTapRitualComplete()
{
    USymbiontCoreEngine* CoreEngine = NewObject<USymbiontCoreEngine>(this);
    
    // Set playfulness coefficient (optional)
    CoreEngine->SetGiggleGrowthCoefficient(0.5f);  // Medium playfulness
    
    // Bind to ritual begin event (fires when all gates pass)
    CoreEngine->OnRitualBegin.AddDynamic(this, &AMyController::OnSymbiontRitualBegin);
    
    // Invoke the ritual (performs all constitutional checks)
    bool bSuccess = CoreEngine->InvokeSymbiontRitual();
    
    if (!bSuccess)
    {
        // Constitutional gates failed - notify user
        // (CoreEngine logs detailed failure reasons)
    }
}
```

### 4. Constitutional Checks (Automatic)

`InvokeSymbiontRitual()` performs these checks in order:

1. **User Consent**: Has user explicitly granted permission?
2. **Thermal Sanctuary**: Is device temperature < critical threshold?
3. **Frame Soul**: Is frame rate ≥ 30 FPS?
4. **Battery Communion**: Is battery level ≥ 15%?

If ANY check fails, the ritual is blocked and the user is notified.

### 5. Model Loading (Success Path)

If all constitutional gates pass:

1. `OnRitualBegin` delegate fires
2. CoreML model begins loading asynchronously (iOS) or equivalent on other platforms
3. Model configuration optimizes for A17/A18 Neural Engine (iOS)
4. When loading completes, inference is ready

## Updating Constitution Dynamically

To keep the constitutional state fresh, update it periodically:

```cpp
void AMyGameMode::UpdateSymbiontVitals()
{
    FSymbiontVitals CurrentVitals;
    CurrentVitals.FPS = GetCurrentFrameRate();                  // From engine stats
    CurrentVitals.ThermalState = GetPlatformThermalState();     // Platform-specific
    CurrentVitals.BatteryLevel = GetPlatformBatteryLevel();     // Platform-specific
    CurrentVitals.bNetworkAvailable = IsNetworkConnected();     // Platform-specific
    
    CoreEngine->UpdateConstitution(CurrentVitals);
}
```

Call `UpdateSymbiontVitals()` once per second via a timer.

## Blueprint Usage

All components are Blueprint-friendly:

- `USymbiontConsentManager`: Get via `GetGameInstance()->GetSubsystem(USymbiontConsentManager::StaticClass())`
- `UGavelTapDetectorComponent`: Add to any actor, configure in details panel
- `USymbiontCoreEngine`: Spawn as Blueprint variable, call `InvokeSymbiontRitual()`

## Safety Notes

- **Never bypass consent checks** - this violates App Store guidelines and user trust
- **Always respect thermal/battery limits** - sustained high-temperature operation damages devices
- **Giggle Growth Coefficient is clamped to 0.85** - this prevents excessive creative outputs that might violate content policies
- **Frame rate gating prevents jank** - inference pauses if frame rate drops below 30 FPS

## Debugging

Enable verbose logging:

```cpp
LogTemp.SetVerbosity(ELogVerbosity::Verbose);
```

Watch for these log markers:
- `GAVEL TAP RITUAL COMPLETED` - User completed the tap sequence
- `ALL CONSTITUTIONAL GATES PASSED` - Ritual invocation succeeded
- `Ritual BLOCKED` - A constitutional gate failed (reason logged)

## Next Steps

- Implement platform-specific thermal/battery monitoring
- Add actual CoreML model files (`.mlmodelc`) to bundle
- Create UMG widgets for ritual visualization
- Add analytics for ritual success/failure rates
- Implement user notification system (HUD messages, toasts)
