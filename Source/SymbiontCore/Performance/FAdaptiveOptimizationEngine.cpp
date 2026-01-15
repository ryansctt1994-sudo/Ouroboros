// Copyright Epic Games, Inc. All Rights Reserved.

#include "FAdaptiveOptimizationEngine.h"
#include "HAL/PlatformTime.h"

FAdaptiveOptimizationEngine::FAdaptiveOptimizationEngine()
    : TimeSinceLastAdaptation(0.0f)
    , StableFrameCount(0)
    , UnstableFrameCount(0)
{
    // Initialize with default tier
    CurrentProfile = FUniversalOptimizer::GetProfileForTier(EOptimizationTier::Tier1);
}

FAdaptiveOptimizationEngine::~FAdaptiveOptimizationEngine()
{
}

void FAdaptiveOptimizationEngine::Tick(float DeltaTime)
{
    TimeSinceLastAdaptation += DeltaTime;

    // Evaluate current performance metrics
    bool bPerformanceGood = true; // Placeholder - would check actual metrics
    bool bPerformanceBad = false;  // Placeholder - would check actual metrics

    if (bPerformanceGood)
    {
        StableFrameCount++;
        UnstableFrameCount = 0;
    }
    else if (bPerformanceBad)
    {
        UnstableFrameCount++;
        StableFrameCount = 0;
    }

    // Check if we should change tiers
    if (ShouldScaleUp())
    {
        // Scale up to higher tier (better quality)
        EOptimizationTier NewTier = static_cast<EOptimizationTier>(
            FMath::Min(static_cast<int32>(CurrentProfile.Tier) + 1, 
                      static_cast<int32>(EOptimizationTier::Tier3)));
        ApplyTier(NewTier);
    }
    else if (ShouldScaleDown())
    {
        // Scale down to lower tier (better performance)
        EOptimizationTier NewTier = static_cast<EOptimizationTier>(
            FMath::Max(static_cast<int32>(CurrentProfile.Tier) - 1, 
                      static_cast<int32>(EOptimizationTier::Tier0)));
        ApplyTier(NewTier);
    }
}

void FAdaptiveOptimizationEngine::ApplyTier(EOptimizationTier NewTier)
{
    if (NewTier != CurrentProfile.Tier)
    {
        RecordTierChange();  // Track for oscillation detection
    }
    
    CurrentProfile = FUniversalOptimizer::GetProfileForTier(NewTier);
    FUniversalOptimizer::ApplyProfile(CurrentProfile);
    
    TimeSinceLastAdaptation = 0.0f;
    StableFrameCount = 0;
    UnstableFrameCount = 0;
}

bool FAdaptiveOptimizationEngine::ShouldScaleUp() const
{
    // Block upgrades if oscillating
    if (IsOscillating())
    {
        return false;
    }
    
    // Existing logic - require stable performance for scaling up
    const float MinTimeBeforeUpgrade = 5.0f;
    const int32 MinStableFrames = 150;
    
    return (TimeSinceLastAdaptation >= MinTimeBeforeUpgrade) && 
           (StableFrameCount >= MinStableFrames) &&
           (CurrentProfile.Tier != EOptimizationTier::Tier3);
}

bool FAdaptiveOptimizationEngine::ShouldScaleDown() const
{
    // Allow immediate downgrade if performance is bad
    const int32 MaxUnstableFrames = 30;
    
    return (UnstableFrameCount >= MaxUnstableFrames) &&
           (CurrentProfile.Tier != EOptimizationTier::Tier0);
}

bool FAdaptiveOptimizationEngine::IsOscillating() const
{
    // If tier changed more than MaxTierChangesPerMinute times in last 60 seconds,
    // we're oscillating - lock current tier to prevent Tier 3→2→3 loops
    return RecentTierChangeTimestamps.Num() > MaxTierChangesPerMinute;
}

void FAdaptiveOptimizationEngine::RecordTierChange()
{
    RecentTierChangeTimestamps.Add(FPlatformTime::Seconds());
    PruneOldTierChanges();
}

void FAdaptiveOptimizationEngine::PruneOldTierChanges()
{
    double CurrentTime = FPlatformTime::Seconds();
    RecentTierChangeTimestamps.RemoveAll([CurrentTime](double Timestamp) {
        return (CurrentTime - Timestamp) > OscillationWindowSeconds;
    });
}
