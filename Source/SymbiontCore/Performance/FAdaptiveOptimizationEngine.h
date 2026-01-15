// Copyright Epic Games, Inc. All Rights Reserved.
// Adaptive Optimization Engine - Runtime Performance Monitoring

#pragma once

#include "CoreMinimal.h"
#include "FUniversalOptimizer.h"

/**
 * Runtime performance metrics snapshot
 */
struct FPerformanceMetrics
{
    float CurrentFPS;
    int64 CurrentRSSMB;
    int64 CurrentVRAMMB;
    float ThermalStateC;        // Temperature in Celsius
    float BatteryLevelPercent;
    double Timestamp;
    
    FPerformanceMetrics()
        : CurrentFPS(0.0f)
        , CurrentRSSMB(0)
        , CurrentVRAMMB(0)
        , ThermalStateC(0.0f)
        , BatteryLevelPercent(100.0f)
        , Timestamp(0.0)
    {
    }
};

/**
 * Thermal smoothing using Exponential Weighted Moving Average (EMA)
 * Reduces impact of transient thermal spikes
 */
class FThermalSmoother
{
public:
    FThermalSmoother(float Alpha = 0.3f)
        : Alpha(Alpha)
        , SmoothedValue(0.0f)
        , bInitialized(false)
    {
    }
    
    float Update(float NewValue)
    {
        if (!bInitialized)
        {
            SmoothedValue = NewValue;
            bInitialized = true;
        }
        else
        {
            // EMA formula: S_t = α * X_t + (1 - α) * S_{t-1}
            SmoothedValue = Alpha * NewValue + (1.0f - Alpha) * SmoothedValue;
        }
        return SmoothedValue;
    }
    
    float GetSmoothedValue() const { return SmoothedValue; }
    void Reset() { bInitialized = false; SmoothedValue = 0.0f; }
    
private:
    float Alpha;          // Smoothing factor (0 < α < 1)
    float SmoothedValue;
    bool bInitialized;
};

/**
 * Dynamic threshold adjuster based on stability
 */
class FDynamicThreshold
{
public:
    FDynamicThreshold(float BaseThreshold, float MinThreshold, float MaxThreshold)
        : BaseThreshold(BaseThreshold)
        , CurrentThreshold(BaseThreshold)
        , MinThreshold(MinThreshold)
        , MaxThreshold(MaxThreshold)
        , StabilityCounter(0)
    {
    }
    
    void UpdateStability(bool bStable)
    {
        if (bStable)
        {
            StabilityCounter++;
            // Gradually relax threshold if stable
            if (StabilityCounter > 100)
            {
                CurrentThreshold = FMath::Min(CurrentThreshold * 1.05f, MaxThreshold);
            }
        }
        else
        {
            StabilityCounter = 0;
            // Tighten threshold on instability
            CurrentThreshold = FMath::Max(CurrentThreshold * 0.95f, MinThreshold);
        }
    }
    
    float GetThreshold() const { return CurrentThreshold; }
    void Reset() { CurrentThreshold = BaseThreshold; StabilityCounter = 0; }
    
private:
    float BaseThreshold;
    float CurrentThreshold;
    float MinThreshold;
    float MaxThreshold;
    int32 StabilityCounter;
};

/**
 * FAdaptiveOptimizationEngine - Runtime adaptation loop
 * 
 * Monitors FPS, RAM (RSS), Thermal state, and Battery level.
 * Uses EMA for thermal smoothing and dynamically adjusts thresholds.
 */
class FAdaptiveOptimizationEngine
{
public:
    FAdaptiveOptimizationEngine();
    ~FAdaptiveOptimizationEngine();
    
    /**
     * Initialize the engine with a starting profile
     */
    void Initialize(const FOptimizationProfile& InitialProfile);
    
    /**
     * Main adaptation loop - call once per frame
     * Returns true if optimization tier was changed
     */
    bool TickAdaptation(float DeltaTime);
    
    /**
     * Get current performance metrics
     */
    FPerformanceMetrics GetCurrentMetrics() const;
    
    /**
     * Get current active profile
     */
    FOptimizationProfile GetCurrentProfile() const { return CurrentProfile; }
    
    /**
     * Force a specific tier (for testing/debugging)
     */
    void SetTier(EOptimizationTier Tier);
    
    /**
     * Reset to baseline
     */
    void Reset();
    
private:
    /**
     * Measure current performance metrics
     */
    void MeasureMetrics();
    
    /**
     * Evaluate if we should scale up or down
     */
    void EvaluateAdaptation();
    
    /**
     * Apply a new optimization tier
     */
    void ApplyTier(EOptimizationTier NewTier);
    
    /**
     * Check if we should scale up to next tier
     */
    bool ShouldScaleUp() const;
    
    /**
     * Check if we should scale down to previous tier
     */
    bool ShouldScaleDown() const;
    
private:
    FOptimizationProfile CurrentProfile;
    FPerformanceMetrics CurrentMetrics;
    
    // Thermal smoothing using EMA
    FThermalSmoother ThermalSmoother;
    
    // Dynamic thresholds
    FDynamicThreshold FPSThreshold;
    FDynamicThreshold MemoryThreshold;
    
    // Adaptation timing
    float TimeSinceLastAdaptation;
    float AdaptationCooldownSeconds;
    
    // Stability tracking
    int32 StableFrameCount;
    int32 UnstableFrameCount;
    
    // Hard limits for emergency fallback
    static constexpr float EmergencyThermalThresholdC = 95.0f;
    static constexpr float CriticalBatteryPercent = 10.0f;
};
