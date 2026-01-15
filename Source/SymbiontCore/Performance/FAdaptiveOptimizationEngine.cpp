// Copyright Epic Games, Inc. All Rights Reserved.
// Adaptive Optimization Engine - Runtime Performance Monitoring

#include "FAdaptiveOptimizationEngine.h"
#include "HAL/PlatformMemory.h"
#include "HAL/PlatformTime.h"
#include "RHI.h"
#include "Engine/Engine.h"

#if PLATFORM_IOS
#include "AR/FIOSZeroCopyBridge.h"
#endif

FAdaptiveOptimizationEngine::FAdaptiveOptimizationEngine()
    : ThermalSmoother(0.3f)  // Alpha = 0.3 for thermal EMA
    , FPSThreshold(30.0f, 20.0f, 40.0f)
    , MemoryThreshold(2048.0f, 1536.0f, 3072.0f)
    , TimeSinceLastAdaptation(0.0f)
    , AdaptationCooldownSeconds(2.0f)
    , StableFrameCount(0)
    , UnstableFrameCount(0)
{
}

FAdaptiveOptimizationEngine::~FAdaptiveOptimizationEngine()
{
}

void FAdaptiveOptimizationEngine::Initialize(const FOptimizationProfile& InitialProfile)
{
    CurrentProfile = InitialProfile;
    FUniversalOptimizer::ApplyProfile(CurrentProfile);
    
    // Reset smoothers and thresholds
    ThermalSmoother.Reset();
    FPSThreshold.Reset();
    MemoryThreshold.Reset();
    
    TimeSinceLastAdaptation = 0.0f;
    StableFrameCount = 0;
    UnstableFrameCount = 0;
}

bool FAdaptiveOptimizationEngine::TickAdaptation(float DeltaTime)
{
    TimeSinceLastAdaptation += DeltaTime;
    
    // Measure current metrics
    MeasureMetrics();
    
    // Only evaluate adaptation after cooldown period
    if (TimeSinceLastAdaptation >= AdaptationCooldownSeconds)
    {
        EvaluateAdaptation();
        return true;
    }
    
    return false;
}

void FAdaptiveOptimizationEngine::MeasureMetrics()
{
    CurrentMetrics.Timestamp = FPlatformTime::Seconds();
    
    // Measure FPS
    if (GEngine)
    {
        CurrentMetrics.CurrentFPS = GEngine->GetAverageFPS();
    }
    
    // Measure memory (RSS)
    FPlatformMemoryStats MemStats = FPlatformMemory::GetStats();
    CurrentMetrics.CurrentRSSMB = MemStats.UsedPhysical / (1024 * 1024);
    
    // Measure VRAM (if available)
    if (GDynamicRHI)
    {
        // Note: RHIGetAvailableTextureMemory returns free VRAM, not used
        // For now, we track available VRAM as a proxy for usage
        // In production, would need platform-specific total VRAM query
        int64 AvailableVRAM = GDynamicRHI->RHIGetAvailableTextureMemory();
        CurrentMetrics.CurrentVRAMMB = AvailableVRAM / (1024 * 1024);
    }
    
    // Measure thermal state (platform-specific, placeholder for now)
    // On iOS, this would use ProcessInfo.thermalState
#if PLATFORM_IOS
    float RawThermalState = FIOSZeroCopyBridge::QueryThermalState();
#else
    float RawThermalState = 50.0f; // Non-iOS fallback
#endif
    CurrentMetrics.ThermalStateC = ThermalSmoother.Update(RawThermalState);
    
    // Measure battery level (platform-specific, placeholder)
    // On iOS, this would use UIDevice.batteryLevel
#if PLATFORM_IOS
    CurrentMetrics.BatteryLevelPercent = FIOSZeroCopyBridge::QueryBatteryLevel();
#else
    CurrentMetrics.BatteryLevelPercent = 80.0f; // Non-iOS fallback
#endif
}

void FAdaptiveOptimizationEngine::EvaluateAdaptation()
{
    // Check for emergency conditions first
    if (CurrentMetrics.ThermalStateC >= EmergencyThermalThresholdC ||
        CurrentMetrics.BatteryLevelPercent <= CriticalBatteryPercent ||
        CurrentMetrics.CurrentRSSMB >= CurrentProfile.MaxRSSMB * 0.95f)
    {
        // Trigger emergency fallback (handled by FEmergencyFallbackSystem)
        // For now, just force down to Tier 0
        if (CurrentProfile.Tier != EOptimizationTier::Tier0_AbsoluteMinimum)
        {
            ApplyTier(EOptimizationTier::Tier0_AbsoluteMinimum);
            UnstableFrameCount++;
            return;
        }
    }
    
    // Evaluate stability
    bool bIsStable = (CurrentMetrics.CurrentFPS >= CurrentProfile.TargetFPS * 0.9f) &&
                     (CurrentMetrics.CurrentRSSMB <= CurrentProfile.MaxRSSMB * 0.8f);
    
    if (bIsStable)
    {
        StableFrameCount++;
        UnstableFrameCount = 0;
    }
    else
    {
        UnstableFrameCount++;
        StableFrameCount = 0;
    }
    
    // Update dynamic thresholds
    FPSThreshold.UpdateStability(bIsStable);
    MemoryThreshold.UpdateStability(bIsStable);
    
    // Decide on scaling
    if (ShouldScaleUp())
    {
        // Scale up to next tier
        EOptimizationTier NextTier = static_cast<EOptimizationTier>(
            FMath::Min(static_cast<uint8>(CurrentProfile.Tier) + 1, 
                      static_cast<uint8>(EOptimizationTier::Tier3_Performance))
        );
        ApplyTier(NextTier);
    }
    else if (ShouldScaleDown())
    {
        // Scale down to previous tier
        EOptimizationTier PrevTier = static_cast<EOptimizationTier>(
            FMath::Max(static_cast<uint8>(CurrentProfile.Tier) - 1,
                      static_cast<uint8>(EOptimizationTier::Tier0_AbsoluteMinimum))
        );
        ApplyTier(PrevTier);
    }
}

bool FAdaptiveOptimizationEngine::ShouldScaleUp() const
{
    // Only scale up if we've been stable for a while
    if (StableFrameCount < 60)  // ~2 seconds at 30 FPS
    {
        return false;
    }
    
    // Don't scale up if already at max tier
    if (CurrentProfile.Tier == EOptimizationTier::Tier3_Performance)
    {
        return false;
    }
    
    // Check if we have headroom
    bool bHasFPSHeadroom = CurrentMetrics.CurrentFPS >= CurrentProfile.TargetFPS * 1.2f;
    bool bHasMemoryHeadroom = CurrentMetrics.CurrentRSSMB <= CurrentProfile.MaxRSSMB * 0.7f;
    bool bThermalOK = CurrentMetrics.ThermalStateC < 70.0f;
    bool bBatteryOK = CurrentMetrics.BatteryLevelPercent > 30.0f;
    
    return bHasFPSHeadroom && bHasMemoryHeadroom && bThermalOK && bBatteryOK;
}

bool FAdaptiveOptimizationEngine::ShouldScaleDown() const
{
    // Scale down if unstable for too long
    if (UnstableFrameCount < 30)  // ~1 second at 30 FPS
    {
        return false;
    }
    
    // Don't scale down if already at minimum tier
    if (CurrentProfile.Tier == EOptimizationTier::Tier0_AbsoluteMinimum)
    {
        return false;
    }
    
    // Check if we're struggling
    bool bFPSBelowTarget = CurrentMetrics.CurrentFPS < CurrentProfile.TargetFPS * 0.85f;
    bool bMemoryHigh = CurrentMetrics.CurrentRSSMB >= CurrentProfile.MaxRSSMB * 0.85f;
    bool bThermalHigh = CurrentMetrics.ThermalStateC > 80.0f;
    bool bBatteryLow = CurrentMetrics.BatteryLevelPercent < 20.0f;
    
    return bFPSBelowTarget || bMemoryHigh || bThermalHigh || bBatteryLow;
}

void FAdaptiveOptimizationEngine::ApplyTier(EOptimizationTier NewTier)
{
    CurrentProfile = FUniversalOptimizer::GetProfileForTier(NewTier);
    FUniversalOptimizer::ApplyProfile(CurrentProfile);
    
    TimeSinceLastAdaptation = 0.0f;
    StableFrameCount = 0;
    UnstableFrameCount = 0;
}

FPerformanceMetrics FAdaptiveOptimizationEngine::GetCurrentMetrics() const
{
    return CurrentMetrics;
}

void FAdaptiveOptimizationEngine::SetTier(EOptimizationTier Tier)
{
    ApplyTier(Tier);
}

void FAdaptiveOptimizationEngine::Reset()
{
    Initialize(FUniversalOptimizer::GetAbsoluteMinimumProfile());
}
