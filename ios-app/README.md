# iOS App Manifold: Mobile Symbiosis Core

The iOS application layer for the Ouroboros framework, implementing the "Symbiosis of Minimums" philosophy on Apple devices.

## Contents

### Bindings (`Source/SymbiontCore/AR/`)
- `FIOSZeroCopyBridge.mm` - CVPixelBuffer → IOSurface → MTLTexture zero-copy pipeline
- iOS thermal/battery bindings via `NSProcessInfo` and `UIDevice`

### ARKit Integration
- Camera frame capture (YCbCr → BGRA conversion)
- LiDAR depth buffer integration
- World tracking and anchors

### CoreML Integration
- On-device inference via Neural Engine
- Model loading and async prediction
- A17/A18 Pro optimizations

### Thermal Governors
- EMA-smoothed thermal state (α=0.3)
- 4-tier adaptive optimization (Tier 0-3)
- Emergency fallback with fade-to-black mask

## Target Devices
- Minimum: iPhone XR (iOS 16+)
- Optimized: iPhone 14-16 Pro (A17/A18 Neural Engine)

## Related PRs
- PR #29: Universal Optimization Framework
- PR #30: iOS Thermal/Battery Bindings
