// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UniversalOptimizer.h"

/**
 * Adaptive optimization engine with oscillation prevention
 * Prevents rapid tier changes that can occur with EMA thermal smoothing (α=0.3)
 * Ensures monotonic convergence per von Neumann projection theorem
 */
class SYMBIONTCORE_API FAdaptiveOptimizationEngine
{
public:
    FAdaptiveOptimizationEngine();
    ~FAdaptiveOptimizationEngine();

    /**
     * Update the optimization tier based on current metrics
     * @param DeltaTime Time elapsed since last update
     */
    void Tick(float DeltaTime);

    /**
     * Apply a specific optimization tier
     * Records tier changes for oscillation tracking
     * @param NewTier The tier to apply
     */
    void ApplyTier(EOptimizationTier NewTier);

    /**
     * Get the current optimization profile
     * @return Current profile settings
     */
    FOptimizationProfile GetCurrentProfile() const { return CurrentProfile; }

private:
    /**
     * Check if we should scale up to a higher tier
     * Blocks upgrades if oscillating
     * @return true if conditions allow scaling up
     */
    bool ShouldScaleUp() const;

    /**
     * Check if we should scale down to a lower tier
     * @return true if conditions require scaling down
     */
    bool ShouldScaleDown() const;

    /**
     * Check if the system is oscillating between tiers
     * @return true if tier changed more than MaxTierChangesPerMinute in last 60 seconds
     */
    bool IsOscillating() const;

    /**
     * Record a tier change timestamp for oscillation detection
     */
    void RecordTierChange();

    /**
     * Remove tier change timestamps older than OscillationWindowSeconds
     */
    void PruneOldTierChanges();

private:
    // Current optimization profile
    FOptimizationProfile CurrentProfile;

    // Oscillation tracking
    TArray<double> RecentTierChangeTimestamps;
    static constexpr int32 MaxTierChangesPerMinute = 2;
    static constexpr double OscillationWindowSeconds = 60.0;

    // Timing and stability tracking
    float TimeSinceLastAdaptation;
    int32 StableFrameCount;
    int32 UnstableFrameCount;
};
