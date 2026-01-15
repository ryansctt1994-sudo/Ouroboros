# Universal Optimization Framework
## Symbiosis of Minimums - Optimization Strategy

---

## Philosophy

The **Symbiosis of Minimums** is a performance optimization philosophy that inverts traditional optimization approaches:

> **"Optimize from the Absolute Minimum and allow better devices to scale up only when performance is proven. Never degrade from a maximum; always build up from a proven baseline."**

### Core Principles

1. **Start from Tier 0 (Absolute Minimum)**: Always begin with the lowest viable performance profile
2. **Prove Performance**: Only scale up when metrics demonstrate stable headroom
3. **Never Degrade**: Avoid starting from high quality and downgrading (causes jarring transitions)
4. **Build from Baseline**: Each tier builds incrementally upon the previous tier's proven stability

### Why This Approach?

Traditional optimization strategies often start at maximum quality and reactively degrade when performance issues occur. This creates:
- **Jarring visual transitions**: Users notice quality drops more than gradual improvements
- **Reactive hitching**: Degradation happens during stress, compounding performance issues
- **Unstable baselines**: No guaranteed minimum experience

The Symbiosis of Minimums guarantees a **stable baseline** that works on the weakest target device, then **proactively scales up** on better hardware.

---

## Tier Definitions

### Tier 0: Absolute Minimum
**Target Device**: iPhone XR (iOS 16+)

**Performance Targets**:
- **FPS**: 30 FPS
- **RAM (RSS)**: 2GB maximum
- **VRAM**: 1GB maximum
- **CPU Threads**: 2 threads
- **GPU Features**: Disabled

**Rendering Settings**:
```ini
r.ScreenPercentage=50
r.Streaming.PoolSize=128
r.ShadowQuality=0
r.Mobile.Shadows=0
r.StaticMeshLODDistanceScale=2.0
r.PostProcessAAQuality=0
r.ReflectionMethod=0
```

**Use Cases**:
- Emergency fallback state
- Thermal throttling recovery
- Low battery mode
- Memory pressure situations
- Oldest supported devices

---

### Tier 1: Conservative
**Target Device**: iPhone 11 / iPhone XR with headroom

**Performance Targets**:
- **FPS**: 45 FPS
- **RAM (RSS)**: 3GB maximum
- **VRAM**: 1.5GB maximum
- **CPU Threads**: 4 threads
- **GPU Features**: Basic shadows enabled

**Rendering Settings**:
```ini
r.ScreenPercentage=70
r.Streaming.PoolSize=256
r.ShadowQuality=1
r.Mobile.Shadows=1
r.StaticMeshLODDistanceScale=1.5
```

**Scale-Up Conditions**:
- 60+ stable frames at Tier 0
- Memory usage < 70% of Tier 0 max
- Thermal < 70°C
- Battery > 30%

---

### Tier 2: Balanced
**Target Device**: iPhone 12 / iPhone 13

**Performance Targets**:
- **FPS**: 60 FPS
- **RAM (RSS)**: 4GB maximum
- **VRAM**: 2GB maximum
- **CPU Threads**: 6 threads
- **GPU Features**: Shadows, reflections, post-processing

**Rendering Settings**:
```ini
r.ScreenPercentage=85
r.Streaming.PoolSize=512
r.ShadowQuality=2
r.Mobile.Shadows=1
r.StaticMeshLODDistanceScale=1.0
r.PostProcessAAQuality=2
r.ReflectionMethod=1
```

**Scale-Up Conditions**:
- 72+ stable frames at Tier 1
- Memory usage < 70% of Tier 1 max
- Thermal < 70°C
- Battery > 30%

---

### Tier 3: Performance
**Target Device**: iPhone 14 Pro / iPhone 15 Pro

**Performance Targets**:
- **FPS**: 90+ FPS (120 FPS for ProMotion displays)
- **RAM (RSS)**: 6GB maximum
- **VRAM**: 3GB+ maximum
- **CPU Threads**: 8 threads
- **GPU Features**: All features enabled

**Rendering Settings**:
```ini
r.ScreenPercentage=100
r.Streaming.PoolSize=1024
r.ShadowQuality=3
r.Mobile.Shadows=1
r.StaticMeshLODDistanceScale=0.8
r.PostProcessAAQuality=4
r.ReflectionMethod=2
```

**Scale-Up Conditions**:
- 108+ stable frames at Tier 2
- Memory usage < 70% of Tier 2 max
- Thermal < 70°C
- Battery > 30%

---

## Adaptive Optimization Engine

### Architecture

```
┌─────────────────────────────────────────┐
│    USymbiontMemoryGovernor              │
│  (Central Coordinator)                  │
└────────┬───────────────────┬────────────┘
         │                   │
         │                   │
    ┌────▼────────┐    ┌─────▼──────────┐
    │  Adaptive   │    │   Emergency    │
    │  Engine     │    │   Fallback     │
    └─────────────┘    └────────────────┘
```

### Measurement Loop

The Adaptive Optimization Engine runs once per frame and measures:

1. **FPS**: Current frame rate vs. target
2. **Memory (RSS)**: Resident Set Size via platform APIs
3. **VRAM**: Video memory usage via RHI
4. **Thermal State**: Device temperature (platform-specific)
5. **Battery Level**: Battery percentage (platform-specific)

### Thermal Smoothing (EMA)

To prevent reactivity to transient thermal spikes, we use **Exponential Weighted Moving Average**:

```
S_t = α * X_t + (1 - α) * S_{t-1}
```

Where:
- `S_t` = Smoothed thermal value at time t
- `X_t` = Raw thermal reading at time t
- `α` = 0.3 (smoothing factor)

This prevents sudden tier changes from brief CPU bursts.

### Dynamic Thresholds

Thresholds adapt based on stability:

- **Stable Performance** (100+ frames): Gradually relax thresholds by 5%
- **Unstable Performance**: Tighten thresholds by 5%

This creates a self-adjusting system that becomes more aggressive on unstable devices and more permissive on stable devices.

---

## Emergency Fallback System

### Triggers

Emergency fallback is triggered by **hard constraints**:

- **Memory Pressure**: RSS > 95% of maximum
- **Thermal Critical**: Temperature > 95°C
- **Battery Critical**: Battery < 5%

### Two-Phase Reduction

#### Phase A: Visual Masking (Immediate)
*Executed synchronously on Game Thread*

1. **Apply fade-to-black** (500ms transition)
   - Hides visual hitches during reduction
   - Uses alpha interpolation for smooth fade
2. **Emergency settings** (immediate):
   ```cpp
   r.ScreenPercentage = 30   // Absolute emergency minimum
   r.ShadowQuality = 0        // All shadows off
   r.Mobile.Shadows = 0       // Mobile shadows off
   ```

#### Phase B: Async Reductions (Staggered)
*Executed on background thread via AsyncTask*

Triggered 200ms after Phase A:

1. **Texture Streaming Pool Clamp**:
   ```cpp
   r.Streaming.PoolSize = 64  // Emergency minimum (64MB)
   ```
2. **Garbage Collection** (non-blocking):
   ```cpp
   GEngine->ForceGarbageCollection(false)
   ```
3. **LOD Distance Reduction**:
   ```cpp
   r.StaticMeshLODDistanceScale = 3.0  // Aggressive LOD scaling
   r.ViewDistanceScale = 0.5
   ```

**Key Constraint**: No `FlushResourceStreaming()` on Game Thread during active gameplay.

---

## iOS Hardware Integration

### Zero-Copy Texture Bridge

For ARKit and Neural Engine integration, we implement a **zero-copy bridge** using `CVPixelBuffer`:

```cpp
// Create zero-copy handle from ARKit camera frame
FZeroCopyTextureHandle Handle = 
    FIOSZeroCopyBridge::CreateFromPixelBuffer(arFrame.capturedImage);

// Direct Metal texture mapping (no CPU copy)
void* MetalTexture = FIOSZeroCopyBridge::MapToMetalTexture(Handle);
```

**Benefits**:
- **Zero CPU copies**: Direct IOSurface-backed memory sharing
- **Lower memory footprint**: Single buffer shared across ARKit/Metal/Neural Engine
- **Reduced latency**: No memcpy overhead

**Use Cases**:
- ARKit camera frame processing
- Neural Engine inference input/output
- Real-time video effects

---

## Asset Loading Strategy

### Universal Asset Loader Concept

Instead of hardcoded device models, the Universal Asset Loader uses **real-time capability discovery**:

```cpp
// Pseudocode
FDeviceCapabilities Caps = FDeviceCapabilities::Discover();

if (Caps.VRAM >= 2048 && Caps.SupportsMetalTier3)
{
    LoadAssetVariant("HighRes");
}
else if (Caps.VRAM >= 1024)
{
    LoadAssetVariant("MediumRes");
}
else
{
    LoadAssetVariant("LowRes");
}
```

**Advantages**:
- **Future-proof**: New devices automatically categorized
- **Accurate**: Based on actual hardware, not device model strings
- **Adaptive**: Can adjust at runtime based on memory pressure

---

## Implementation Checklist

### Core Systems
- [x] `FUniversalOptimizer` - Profile builder with Tier 0-3 definitions
- [x] `FAdaptiveOptimizationEngine` - Runtime measurement and adaptation
- [x] `FEmergencyFallbackSystem` - Two-phase emergency reduction
- [x] `USymbiontMemoryGovernor` - Central coordinator with clean data contract

### Configuration
- [x] `Config/UniversalMinimum.ini` - Tier 0 rendering settings

### iOS Integration
- [x] `FIOSZeroCopyBridge` - CVPixelBuffer zero-copy bridge

### Documentation
- [x] `docs/OPTIMIZATION_STRATEGY.md` - This document

---

## Usage Examples

### Basic Initialization

```cpp
// Create and initialize governor
USymbiontMemoryGovernor* Governor = NewObject<USymbiontMemoryGovernor>();
Governor->Initialize(0);  // Start at Tier 0

// Tick once per frame
void AMyGameMode::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    Governor->Tick(DeltaTime);
}
```

### Manual Tier Override

```cpp
// Force a specific tier (for testing/debugging)
Governor->SetOptimizationTier(2);  // Force Tier 2
```

### Emergency Override

```cpp
// Manually trigger emergency fallback
Governor->TriggerEmergency();
```

### Runtime State Monitoring

```cpp
// Get current runtime state
FRuntimeStateSnapshot State = Governor->GetRuntimeState();

UE_LOG(LogTemp, Log, TEXT("FPS: %.1f, Tier: %d, Emergency: %s"),
    State.CurrentFPS,
    State.CurrentTier,
    State.bEmergencyActive ? TEXT("Active") : TEXT("None"));
```

### Visual Masking in UI

```cpp
// In HUD/Widget rendering
float MaskAlpha = Governor->GetEmergencyMaskAlpha();
if (MaskAlpha > 0.0f)
{
    // Render black overlay with alpha
    DrawRect(FLinearColor(0, 0, 0, MaskAlpha));
}
```

---

## Performance Metrics

### Expected Performance on Target Devices

| Device | Tier | FPS | RSS (MB) | Notes |
|--------|------|-----|----------|-------|
| iPhone XR | 0 | 30 | 1800 | Baseline |
| iPhone 11 | 1 | 45 | 2500 | Conservative scale-up |
| iPhone 12 | 2 | 60 | 3200 | Balanced quality |
| iPhone 13 | 2 | 60 | 3000 | Thermal headroom |
| iPhone 14 Pro | 3 | 90+ | 4500 | ProMotion support |
| iPhone 15 Pro | 3 | 120 | 4200 | Maximum quality |

---

## Future Enhancements

### Planned Features
1. **Machine Learning Predictor**: Predict optimal tier based on scene complexity
2. **User Preference Override**: Allow users to cap at specific tier (battery saving)
3. **Thermal History**: Learn device-specific thermal characteristics over time
4. **Network-Aware Scaling**: Adjust based on network quality for multiplayer

### Research Areas
1. **Perceptual Quality Metrics**: Use SSIM/PSNR to measure perceived quality
2. **Eye Tracking Integration**: Prioritize quality in foveal region (Vision Pro)
3. **Dynamic Resolution Scaling**: Frame-by-frame resolution adjustment

---

## References

- **Unreal Engine Documentation**: [Performance Guidelines for Mobile](https://docs.unrealengine.com/en-US/performance-guidelines-for-mobile-devices/)
- **Apple Developer**: [Optimizing Your App for Today's Devices](https://developer.apple.com/videos/play/wwdc2021/10057/)
- **GDC 2023**: "Adaptive Performance in Mobile Gaming" talk
- **CVPixelBuffer**: [Apple Core Video Documentation](https://developer.apple.com/documentation/corevideo/cvpixelbuffer)

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-15  
**Maintained By**: AIOSPANDORA/Ouroboros Team
