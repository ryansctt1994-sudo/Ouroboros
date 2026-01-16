// Copyright Epic Games, Inc. All Rights Reserved.
// Universal Optimization Framework - Symbiosis of Minimums Philosophy

#include "FUniversalOptimizer.h"
#include "HAL/PlatformMemory.h"
#include "RHI.h"

FUniversalOptimizer::FUniversalOptimizer()
{
}

FUniversalOptimizer::~FUniversalOptimizer()
{
}

FOptimizationProfile FUniversalOptimizer::GetAbsoluteMinimumProfile()
{
    FOptimizationProfile Profile;
    Profile.Tier = EOptimizationTier::Tier0_AbsoluteMinimum;
    
    // Performance Targets - iPhone XR baseline
    Profile.TargetFPS = 30.0f;
    Profile.MaxRSSMB = 2048;    // 2GB RSS
    Profile.MaxVRAMMB = 1024;   // 1GB VRAM
    Profile.MaxCPUThreads = 2;
    
    // GPU Features - All disabled for minimum
    Profile.bEnableGPUFeatures = false;
    Profile.bEnableShadows = false;
    Profile.bEnableReflections = false;
    Profile.bEnablePostProcessing = false;
    
    // Rendering Settings - Minimum quality
    Profile.ScreenPercentage = 50.0f;
    Profile.ShadowQuality = 0;
    Profile.LODDistanceScale = 2.0f;
    Profile.StreamingPoolSizeMB = 128;
    
    return Profile;
}

FOptimizationProfile FUniversalOptimizer::GetConservativeProfile()
{
    FOptimizationProfile Profile;
    Profile.Tier = EOptimizationTier::Tier1_Conservative;
    
    // Performance Targets
    Profile.TargetFPS = 45.0f;
    Profile.MaxRSSMB = 3072;    // 3GB RSS
    Profile.MaxVRAMMB = 1536;   // 1.5GB VRAM
    Profile.MaxCPUThreads = 4;
    
    // GPU Features - Basic features enabled
    Profile.bEnableGPUFeatures = true;
    Profile.bEnableShadows = true;
    Profile.bEnableReflections = false;
    Profile.bEnablePostProcessing = false;
    
    // Rendering Settings
    Profile.ScreenPercentage = 70.0f;
    Profile.ShadowQuality = 1;
    Profile.LODDistanceScale = 1.5f;
    Profile.StreamingPoolSizeMB = 256;
    
    return Profile;
}

FOptimizationProfile FUniversalOptimizer::GetBalancedProfile()
{
    FOptimizationProfile Profile;
    Profile.Tier = EOptimizationTier::Tier2_Balanced;
    
    // Performance Targets
    Profile.TargetFPS = 60.0f;
    Profile.MaxRSSMB = 4096;    // 4GB RSS
    Profile.MaxVRAMMB = 2048;   // 2GB VRAM
    Profile.MaxCPUThreads = 6;
    
    // GPU Features - Most features enabled
    Profile.bEnableGPUFeatures = true;
    Profile.bEnableShadows = true;
    Profile.bEnableReflections = true;
    Profile.bEnablePostProcessing = true;
    
    // Rendering Settings
    Profile.ScreenPercentage = 85.0f;
    Profile.ShadowQuality = 2;
    Profile.LODDistanceScale = 1.0f;
    Profile.StreamingPoolSizeMB = 512;
    
    return Profile;
}

FOptimizationProfile FUniversalOptimizer::GetPerformanceProfile()
{
    FOptimizationProfile Profile;
    Profile.Tier = EOptimizationTier::Tier3_Performance;
    
    // Performance Targets
    Profile.TargetFPS = 90.0f;
    Profile.MaxRSSMB = 6144;    // 6GB RSS
    Profile.MaxVRAMMB = 3072;   // 3GB+ VRAM
    Profile.MaxCPUThreads = 8;
    
    // GPU Features - All features enabled
    Profile.bEnableGPUFeatures = true;
    Profile.bEnableShadows = true;
    Profile.bEnableReflections = true;
    Profile.bEnablePostProcessing = true;
    
    // Rendering Settings
    Profile.ScreenPercentage = 100.0f;
    Profile.ShadowQuality = 3;
    Profile.LODDistanceScale = 0.8f;
    Profile.StreamingPoolSizeMB = 1024;
    
    return Profile;
}

FOptimizationProfile FUniversalOptimizer::GetProfileForTier(EOptimizationTier Tier)
{
    switch (Tier)
    {
        case EOptimizationTier::Tier0_AbsoluteMinimum:
            return GetAbsoluteMinimumProfile();
            
        case EOptimizationTier::Tier1_Conservative:
            return GetConservativeProfile();
            
        case EOptimizationTier::Tier2_Balanced:
            return GetBalancedProfile();
            
        case EOptimizationTier::Tier3_Performance:
            return GetPerformanceProfile();
            
        default:
            return GetAbsoluteMinimumProfile();
    }
}

FOptimizationProfile FUniversalOptimizer::BuildCustomProfile(
    EOptimizationTier BaseTier,
    float TargetFPSOverride,
    int64 MaxRSSOverrideMB,
    int64 MaxVRAMOverrideMB)
{
    FOptimizationProfile Profile = GetProfileForTier(BaseTier);
    
    // Apply overrides
    if (TargetFPSOverride > 0.0f)
    {
        Profile.TargetFPS = TargetFPSOverride;
    }
    
    if (MaxRSSOverrideMB > 0)
    {
        Profile.MaxRSSMB = MaxRSSOverrideMB;
    }
    
    if (MaxVRAMOverrideMB > 0)
    {
        Profile.MaxVRAMMB = MaxVRAMOverrideMB;
    }
    
    return Profile;
}

bool FUniversalOptimizer::CanDeviceSupportProfile(const FOptimizationProfile& Profile)
{
    // Check physical memory
    FPlatformMemoryStats MemStats = FPlatformMemory::GetStats();
    int64 PhysicalMemoryMB = MemStats.TotalPhysical / (1024 * 1024);
    
    if (PhysicalMemoryMB < Profile.MaxRSSMB)
    {
        return false;
    }
    
    // Check available VRAM (if RHI is initialized)
    if (GDynamicRHI)
    {
        int64 TotalVRAMMB = GDynamicRHI->RHIGetAvailableTextureMemory() / (1024 * 1024);
        if (TotalVRAMMB > 0 && TotalVRAMMB < Profile.MaxVRAMMB)
        {
            return false;
        }
    }
    
    return true;
}

void FUniversalOptimizer::ApplyProfile(const FOptimizationProfile& Profile)
{
    // Apply screen percentage
    static IConsoleVariable* CVarScreenPercentage = 
        IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage"));
    if (CVarScreenPercentage)
    {
        CVarScreenPercentage->Set(Profile.ScreenPercentage);
    }
    
    // Apply streaming pool size
    static IConsoleVariable* CVarStreamingPoolSize = 
        IConsoleManager::Get().FindConsoleVariable(TEXT("r.Streaming.PoolSize"));
    if (CVarStreamingPoolSize)
    {
        CVarStreamingPoolSize->Set(Profile.StreamingPoolSizeMB);
    }
    
    // Apply shadow quality
    static IConsoleVariable* CVarShadowQuality = 
        IConsoleManager::Get().FindConsoleVariable(TEXT("r.ShadowQuality"));
    if (CVarShadowQuality)
    {
        CVarShadowQuality->Set(Profile.ShadowQuality);
    }
    
    // Apply mobile shadows (iOS specific)
    static IConsoleVariable* CVarMobileShadows = 
        IConsoleManager::Get().FindConsoleVariable(TEXT("r.Mobile.Shadows"));
    if (CVarMobileShadows)
    {
        CVarMobileShadows->Set(Profile.bEnableShadows ? 1 : 0);
    }
    
    // Apply LOD distance scale
    static IConsoleVariable* CVarLODDistanceScale = 
        IConsoleManager::Get().FindConsoleVariable(TEXT("r.StaticMeshLODDistanceScale"));
    if (CVarLODDistanceScale)
    {
        CVarLODDistanceScale->Set(Profile.LODDistanceScale);
    }
}
