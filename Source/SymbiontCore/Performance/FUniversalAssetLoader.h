// Copyright Epic Games, Inc. All Rights Reserved.
// Universal Asset Loader - Runtime Capability-Based Asset Selection

#pragma once

#include "CoreMinimal.h"

/**
 * Device capability snapshot for asset selection
 */
struct FDeviceCapabilities
{
    int64 TotalRAMMB;
    int64 TotalVRAMMB;
    bool bSupportsMetalTier3;
    bool bSupportsNeuralEngine;
    int32 CPUCoreCount;
    FString DeviceModel;
    
    FDeviceCapabilities()
        : TotalRAMMB(0)
        , TotalVRAMMB(0)
        , bSupportsMetalTier3(false)
        , bSupportsNeuralEngine(false)
        , CPUCoreCount(0)
    {
    }
    
    /**
     * Discover device capabilities at runtime
     */
    static FDeviceCapabilities Discover();
};

/**
 * Asset quality tier
 */
enum class EAssetQualityTier : uint8
{
    Low = 0,      // Tier 0 devices (iPhone XR)
    Medium = 1,   // Tier 1-2 devices (iPhone 11-13)
    High = 2,     // Tier 3 devices (iPhone 14 Pro+)
    Ultra = 3     // Future-proof tier
};

/**
 * Asset variant descriptor
 */
struct FAssetVariant
{
    FString AssetPath;
    EAssetQualityTier QualityTier;
    int32 LODLevel;
    int32 TextureResolution;
    bool bPreload;
    
    FAssetVariant()
        : QualityTier(EAssetQualityTier::Low)
        , LODLevel(0)
        , TextureResolution(512)
        , bPreload(false)
    {
    }
};

/**
 * FUniversalAssetLoader - Capability-based asset loading
 * 
 * Philosophy: Load asset variants based on real-time device capability
 * discovery rather than hardcoded device models.
 * 
 * Benefits:
 * - Future-proof: New devices automatically categorized
 * - Accurate: Based on actual hardware capabilities
 * - Adaptive: Can adjust at runtime based on memory pressure
 * 
 * Usage:
 *   FDeviceCapabilities Caps = FDeviceCapabilities::Discover();
 *   EAssetQualityTier Tier = FUniversalAssetLoader::DetermineAssetTier(Caps);
 *   FAssetVariant Variant = FUniversalAssetLoader::SelectAssetVariant("MyAsset", Tier);
 */
class FUniversalAssetLoader
{
public:
    /**
     * Determine appropriate asset tier based on device capabilities
     */
    static EAssetQualityTier DetermineAssetTier(const FDeviceCapabilities& Capabilities);
    
    /**
     * Select asset variant for a given asset name and tier
     * 
     * @param AssetBaseName - Base asset name (e.g., "Character_Hero")
     * @param Tier - Quality tier to load
     * @return Asset variant descriptor
     */
    static FAssetVariant SelectAssetVariant(const FString& AssetBaseName, EAssetQualityTier Tier);
    
    /**
     * Load asset asynchronously based on capabilities
     * 
     * @param AssetBaseName - Base asset name
     * @param Capabilities - Device capabilities
     * @param OnLoadComplete - Callback when load completes
     */
    static void LoadAssetForDevice(
        const FString& AssetBaseName,
        const FDeviceCapabilities& Capabilities,
        TFunction<void(UObject*)> OnLoadComplete
    );
    
    /**
     * Preload critical assets for current device tier
     */
    static void PreloadCriticalAssets();
    
    /**
     * Unload assets for lower tiers to free memory
     * (Used when scaling up to higher tier)
     */
    static void UnloadLowerTierAssets(EAssetQualityTier CurrentTier);
    
    /**
     * Get recommended texture resolution for tier
     */
    static int32 GetTextureResolutionForTier(EAssetQualityTier Tier);
    
    /**
     * Get recommended LOD count for tier
     */
    static int32 GetLODCountForTier(EAssetQualityTier Tier);
    
private:
    /**
     * Build asset path for specific tier
     */
    static FString BuildAssetPath(const FString& BaseName, EAssetQualityTier Tier);
    
    /**
     * Cache of loaded assets by tier
     */
    static TMap<EAssetQualityTier, TArray<UObject*>> LoadedAssetCache;
};
