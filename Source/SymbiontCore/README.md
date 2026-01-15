# SymbiontCore - Universal Optimization Framework

This directory contains the implementation of the **Universal Optimization Framework** based on the "Symbiosis of Minimums" philosophy for Unreal Engine 5.

## Directory Structure

```
Source/SymbiontCore/
├── Performance/           # Core optimization and memory management
│   ├── FUniversalOptimizer.h/cpp           # Tier definitions and profile builder
│   ├── FAdaptiveOptimizationEngine.h/cpp   # Runtime adaptation with EMA smoothing
│   ├── FEmergencyFallbackSystem.h/cpp      # Two-phase emergency reduction
│   ├── USymbiontMemoryGovernor.h/cpp       # Central coordinator
│   └── FUniversalAssetLoader.h/cpp         # Capability-based asset loading
└── AR/                    # iOS hardware integration
    ├── FIOSZeroCopyBridge.h                # Zero-copy bridge interface
    └── FIOSZeroCopyBridge.mm               # CVPixelBuffer implementation
```

## Components

### Performance Management

#### FUniversalOptimizer
Defines optimization profiles for 4 tiers (Tier 0-3):
- **Tier 0 (Absolute Minimum)**: 30 FPS, 2GB RSS, 1GB VRAM - iPhone XR baseline
- **Tier 1 (Conservative)**: 45 FPS, 3GB RSS, 1.5GB VRAM
- **Tier 2 (Balanced)**: 60 FPS, 4GB RSS, 2GB VRAM
- **Tier 3 (Performance)**: 90+ FPS, 6GB RSS, 3GB+ VRAM

#### FAdaptiveOptimizationEngine
Implements the runtime adaptation loop:
- Measures FPS, RAM (RSS), VRAM, Thermal state, Battery level
- Uses **EMA (Exponential Weighted Moving Average)** for thermal smoothing (α=0.3)
- Dynamically adjusts thresholds based on stability
- Scales up/down between tiers based on headroom

#### FEmergencyFallbackSystem
Two-phase emergency reduction strategy:
- **Phase A (Immediate)**: Visual fade-to-black masking + critical settings
- **Phase B (Async)**: Staggered reductions via AsyncTask (texture pool, GC, LOD)
- **NO** `FlushResourceStreaming()` on Game Thread (per requirements)

#### USymbiontMemoryGovernor
Central coordinator exposing Blueprint API:
- `Initialize(Tier)` - Start with specific tier
- `Tick(DeltaTime)` - Update once per frame
- `GetRuntimeState()` - Returns `FRuntimeStateSnapshot`
- `TriggerEmergency()` - Manual emergency override

#### FUniversalAssetLoader
Capability-based asset loading:
- Discovers device capabilities at runtime (not hardcoded models)
- Determines appropriate asset tier (Low/Medium/High/Ultra)
- Loads asset variants asynchronously via `FStreamableManager`
- Manages asset cache by tier

### AR/Hardware Integration

#### FIOSZeroCopyBridge
Zero-copy texture bridge for iOS:
- Uses `CVPixelBuffer` with IOSurface backing
- Direct Metal texture mapping (no CPU memcpy)
- Suitable for ARKit camera frames and Neural Engine inference
- Platform-guarded with `#if PLATFORM_IOS`

## Usage Example

```cpp
// Initialize governor at game start
USymbiontMemoryGovernor* Governor = NewObject<USymbiontMemoryGovernor>();
Governor->Initialize(0);  // Start at Tier 0

// Tick once per frame in game mode
void AMyGameMode::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    Governor->Tick(DeltaTime);
    
    // Render emergency mask if active
    float MaskAlpha = Governor->GetEmergencyMaskAlpha();
    if (MaskAlpha > 0.0f)
    {
        RenderEmergencyMask(MaskAlpha);
    }
}

// Get runtime state for monitoring
FRuntimeStateSnapshot State = Governor->GetRuntimeState();
UE_LOG(LogTemp, Log, TEXT("FPS: %.1f, Tier: %d"), State.CurrentFPS, State.CurrentTier);
```

## Configuration

See `Config/UniversalMinimum.ini` for Tier 0 rendering settings.

## Documentation

See `docs/OPTIMIZATION_STRATEGY.md` for complete philosophy and implementation details.

## Key Design Decisions

1. **EMA Smoothing**: Prevents reactivity to transient thermal spikes
2. **AsyncTask for Phase B**: Minimizes Game Thread impact during emergency
3. **Dynamic Thresholds**: Self-adjusting system learns device stability
4. **Blueprint Exposure**: `USymbiontMemoryGovernor` can be used in Blueprint
5. **Platform Guards**: iOS-specific code properly guarded for cross-platform builds

## Technical Constraints Met

✅ Target: Unreal Engine 5 project  
✅ Minimum Device: iPhone XR (iOS 16+)  
✅ Use `AsyncTask` for non-critical reductions  
✅ No `FlushResourceStreaming()` on Game Thread during active gameplay  
✅ CVPixelBuffer zero-copy bridge for ARKit/Metal/Neural Engine  
✅ EMA thermal smoothing (α=0.3)  
✅ Two-phase emergency reduction with visual masking  
✅ Clean data contract (`FRuntimeStateSnapshot`)  

## License

Copyright Epic Games, Inc. All Rights Reserved.
