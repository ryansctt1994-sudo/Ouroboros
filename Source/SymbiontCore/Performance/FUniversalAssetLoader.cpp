// Copyright Epic Games, Inc. All Rights Reserved.
// Universal Asset Loader - Runtime Capability-Based Asset Selection

#include "FUniversalAssetLoader.h"
#include "HAL/PlatformMemory.h"
#include "RHI.h"
#include "Engine/StreamableManager.h"
#include "Engine/AssetManager.h"

// Static cache initialization
TMap<EAssetQualityTier, TArray<UObject*>> FUniversalAssetLoader::LoadedAssetCache;

FDeviceCapabilities FDeviceCapabilities::Discover()
{
    FDeviceCapabilities Caps;
    
    // Discover RAM
    FPlatformMemoryStats MemStats = FPlatformMemory::GetStats();
    Caps.TotalRAMMB = MemStats.TotalPhysical / (1024 * 1024);
    
    // Discover VRAM
    if (GDynamicRHI)
    {
        int64 TotalVRAM = GDynamicRHI->RHIGetAvailableTextureMemory();
        Caps.TotalVRAMMB = TotalVRAM / (1024 * 1024);
    }
    
    // Platform-specific capabilities
    #if PLATFORM_IOS
        // On iOS, check Metal feature set
        // This is a simplified check - actual implementation would query Metal device
        Caps.bSupportsMetalTier3 = (Caps.TotalRAMMB >= 4096);
        Caps.bSupportsNeuralEngine = (Caps.TotalRAMMB >= 3072);
    #else
        Caps.bSupportsMetalTier3 = true;
        Caps.bSupportsNeuralEngine = false;
    #endif
    
    // Discover CPU core count
    Caps.CPUCoreCount = FPlatformMisc::NumberOfCores();
    
    // Get device model (platform-specific)
    Caps.DeviceModel = FPlatformMisc::GetDefaultDeviceProfileName();
    
    return Caps;
}

EAssetQualityTier FUniversalAssetLoader::DetermineAssetTier(const FDeviceCapabilities& Capabilities)
{
    // Tier determination based on capabilities
    // Philosophy: Conservative allocation - err on side of lower tier
    
    // Ultra tier - Future devices with 8GB+ RAM and 4GB+ VRAM
    if (Capabilities.TotalRAMMB >= 8192 && Capabilities.TotalVRAMMB >= 4096)
    {
        return EAssetQualityTier::Ultra;
    }
    
    // High tier - iPhone 14 Pro+ (6GB+ RAM, 3GB+ VRAM, Metal Tier 3)
    if (Capabilities.TotalRAMMB >= 6144 && 
        Capabilities.TotalVRAMMB >= 3072 && 
        Capabilities.bSupportsMetalTier3)
    {
        return EAssetQualityTier::High;
    }
    
    // Medium tier - iPhone 11-13 (4GB+ RAM, 1.5GB+ VRAM)
    if (Capabilities.TotalRAMMB >= 4096 && Capabilities.TotalVRAMMB >= 1536)
    {
        return EAssetQualityTier::Medium;
    }
    
    // Low tier - iPhone XR baseline (default)
    return EAssetQualityTier::Low;
}

FAssetVariant FUniversalAssetLoader::SelectAssetVariant(const FString& AssetBaseName, EAssetQualityTier Tier)
{
    FAssetVariant Variant;
    Variant.AssetPath = BuildAssetPath(AssetBaseName, Tier);
    Variant.QualityTier = Tier;
    Variant.TextureResolution = GetTextureResolutionForTier(Tier);
    Variant.LODLevel = GetLODCountForTier(Tier);
    
    // Preload critical assets for Low tier
    Variant.bPreload = (Tier == EAssetQualityTier::Low);
    
    return Variant;
}

void FUniversalAssetLoader::LoadAssetForDevice(
    const FString& AssetBaseName,
    const FDeviceCapabilities& Capabilities,
    TFunction<void(UObject*)> OnLoadComplete)
{
    // Determine appropriate tier
    EAssetQualityTier Tier = DetermineAssetTier(Capabilities);
    
    // Select variant
    FAssetVariant Variant = SelectAssetVariant(AssetBaseName, Tier);
    
    // Load asynchronously using Streamable Manager
    if (UAssetManager* AssetManager = UAssetManager::GetIfValid())
    {
        FStreamableManager& StreamableManager = AssetManager->GetStreamableManager();
        
        FSoftObjectPath AssetPath(Variant.AssetPath);
        StreamableManager.RequestAsyncLoad(
            AssetPath,
            [OnLoadComplete, AssetPath]()
            {
                UObject* LoadedAsset = AssetPath.ResolveObject();
                if (OnLoadComplete)
                {
                    OnLoadComplete(LoadedAsset);
                }
            }
        );
    }
}

void FUniversalAssetLoader::PreloadCriticalAssets()
{
    // Discover current device capabilities
    FDeviceCapabilities Caps = FDeviceCapabilities::Discover();
    EAssetQualityTier Tier = DetermineAssetTier(Caps);
    
    // Preload critical assets for current tier
    // This is a placeholder - actual implementation would load from asset registry
    TArray<FString> CriticalAssets = {
        TEXT("UI/MainMenu"),
        TEXT("Characters/Player"),
        TEXT("Environment/Ground")
    };
    
    for (const FString& AssetName : CriticalAssets)
    {
        LoadAssetForDevice(AssetName, Caps, [](UObject* Asset) {
            // Asset loaded - cache it
        });
    }
}

void FUniversalAssetLoader::UnloadLowerTierAssets(EAssetQualityTier CurrentTier)
{
    // Unload assets from lower tiers to free memory
    for (auto& Pair : LoadedAssetCache)
    {
        EAssetQualityTier CachedTier = Pair.Key;
        
        // Only unload if cached tier is lower than current
        if (CachedTier < CurrentTier)
        {
            TArray<UObject*>& Assets = Pair.Value;
            
            // Mark assets for garbage collection
            for (UObject* Asset : Assets)
            {
                if (Asset && Asset->IsValidLowLevel())
                {
                    Asset->MarkAsGarbage();
                }
            }
            
            Assets.Empty();
        }
    }
}

int32 FUniversalAssetLoader::GetTextureResolutionForTier(EAssetQualityTier Tier)
{
    switch (Tier)
    {
        case EAssetQualityTier::Ultra:
            return 4096;  // 4K textures
        case EAssetQualityTier::High:
            return 2048;  // 2K textures
        case EAssetQualityTier::Medium:
            return 1024;  // 1K textures
        case EAssetQualityTier::Low:
        default:
            return 512;   // 512x512 textures
    }
}

int32 FUniversalAssetLoader::GetLODCountForTier(EAssetQualityTier Tier)
{
    switch (Tier)
    {
        case EAssetQualityTier::Ultra:
            return 6;  // Maximum LOD detail
        case EAssetQualityTier::High:
            return 5;
        case EAssetQualityTier::Medium:
            return 4;
        case EAssetQualityTier::Low:
        default:
            return 3;  // Minimum LOD count
    }
}

FString FUniversalAssetLoader::BuildAssetPath(const FString& BaseName, EAssetQualityTier Tier)
{
    // Build asset path with tier suffix
    FString TierSuffix;
    switch (Tier)
    {
        case EAssetQualityTier::Ultra:
            TierSuffix = TEXT("_Ultra");
            break;
        case EAssetQualityTier::High:
            TierSuffix = TEXT("_High");
            break;
        case EAssetQualityTier::Medium:
            TierSuffix = TEXT("_Medium");
            break;
        case EAssetQualityTier::Low:
        default:
            TierSuffix = TEXT("_Low");
            break;
    }
    
    return FString::Printf(TEXT("/Game/Assets/%s%s"), *BaseName, *TierSuffix);
}
