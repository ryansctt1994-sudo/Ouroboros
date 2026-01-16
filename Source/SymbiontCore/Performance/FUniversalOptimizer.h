// Copyright Epic Games, Inc. All Rights Reserved.
// Universal Optimization Framework - Symbiosis of Minimums Philosophy

#pragma once

#include "CoreMinimal.h"

/**
 * Optimization Tier Levels
 * Based on "Symbiosis of Minimums" - start from Tier 0 and scale up
 */
enum class EOptimizationTier : uint8
{
    Tier0_AbsoluteMinimum = 0,  // iPhone XR baseline: 30 FPS, 2GB RSS, 1GB VRAM
    Tier1_Conservative = 1,      // 45 FPS, 3GB RSS, 1.5GB VRAM
    Tier2_Balanced = 2,          // 60 FPS, 4GB RSS, 2GB VRAM
    Tier3_Performance = 3        // 90+ FPS, 6GB RSS, 3GB+ VRAM
};

/**
 * Optimization Profile - defines performance targets and rendering settings
 */
struct FOptimizationProfile
{
    EOptimizationTier Tier;
    
    // Performance Targets
    float TargetFPS;
    int64 MaxRSSMB;          // Maximum Resident Set Size (MB)
    int64 MaxVRAMMB;         // Maximum Video RAM (MB)
    int32 MaxCPUThreads;
    
    // GPU Features
    bool bEnableGPUFeatures;
    bool bEnableShadows;
    bool bEnableReflections;
    bool bEnablePostProcessing;
    
    // Rendering Settings
    float ScreenPercentage;
    int32 ShadowQuality;
    float LODDistanceScale;
    int32 StreamingPoolSizeMB;
    
    FOptimizationProfile()
        : Tier(EOptimizationTier::Tier0_AbsoluteMinimum)
        , TargetFPS(30.0f)
        , MaxRSSMB(2048)
        , MaxVRAMMB(1024)
        , MaxCPUThreads(2)
        , bEnableGPUFeatures(false)
        , bEnableShadows(false)
        , bEnableReflections(false)
        , bEnablePostProcessing(false)
        , ScreenPercentage(50.0f)
        , ShadowQuality(0)
        , LODDistanceScale(2.0f)
        , StreamingPoolSizeMB(128)
    {
    }
};

/**
 * FUniversalOptimizer - Defines and builds optimization profiles
 * 
 * Philosophy: Start from Absolute Minimum (Tier 0) and scale up only when
 * performance is proven. Never degrade from maximum; always build from baseline.
 */
class FUniversalOptimizer
{
public:
    FUniversalOptimizer();
    ~FUniversalOptimizer();
    
    /**
     * Get the Absolute Minimum Profile (Tier 0)
     * Target: iPhone XR, iOS 16+
     * - 30 FPS
     * - 2GB RSS
     * - 1GB VRAM
     * - 2 CPU threads
     * - No GPU features
     */
    static FOptimizationProfile GetAbsoluteMinimumProfile();
    
    /**
     * Get profile for a specific tier
     */
    static FOptimizationProfile GetProfileForTier(EOptimizationTier Tier);
    
    /**
     * Build a custom profile with specific overrides
     */
    static FOptimizationProfile BuildCustomProfile(
        EOptimizationTier BaseTier,
        float TargetFPSOverride = -1.0f,
        int64 MaxRSSOverrideMB = -1,
        int64 MaxVRAMOverrideMB = -1
    );
    
    /**
     * Validate if current device can support a given profile
     */
    static bool CanDeviceSupportProfile(const FOptimizationProfile& Profile);
    
    /**
     * Apply profile to engine console variables
     */
    static void ApplyProfile(const FOptimizationProfile& Profile);
    
private:
    /**
     * Get Tier 1 - Conservative Profile
     */
    static FOptimizationProfile GetConservativeProfile();
    
    /**
     * Get Tier 2 - Balanced Profile
     */
    static FOptimizationProfile GetBalancedProfile();
    
    /**
     * Get Tier 3 - Performance Profile
     */
    static FOptimizationProfile GetPerformanceProfile();
};
