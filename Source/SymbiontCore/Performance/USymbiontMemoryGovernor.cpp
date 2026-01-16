// Copyright Epic Games, Inc. All Rights Reserved.
// Memory Governor and Runtime State Management

#include "USymbiontMemoryGovernor.h"
#include "FUniversalOptimizer.h"
#include "HAL/PlatformTime.h"

USymbiontMemoryGovernor::USymbiontMemoryGovernor()
    : bInitialized(false)
    , LastTickTime(0.0)
{
}

USymbiontMemoryGovernor::~USymbiontMemoryGovernor()
{
}

void USymbiontMemoryGovernor::Initialize(uint8 StartingTier)
{
    if (bInitialized)
    {
        return;
    }
    
    // Create core systems
    AdaptiveEngine = MakeUnique<FAdaptiveOptimizationEngine>();
    EmergencySystem = MakeUnique<FEmergencyFallbackSystem>();
    
    // Initialize with starting tier
    EOptimizationTier Tier = static_cast<EOptimizationTier>(
        FMath::Clamp(StartingTier, 
                     static_cast<uint8>(EOptimizationTier::Tier0_AbsoluteMinimum),
                     static_cast<uint8>(EOptimizationTier::Tier3_Performance))
    );
    
    FOptimizationProfile InitialProfile = FUniversalOptimizer::GetProfileForTier(Tier);
    AdaptiveEngine->Initialize(InitialProfile);
    EmergencySystem->Initialize();
    
    bInitialized = true;
    LastTickTime = FPlatformTime::Seconds();
}

void USymbiontMemoryGovernor::Tick(float DeltaTime)
{
    if (!bInitialized)
    {
        // Auto-initialize with Tier 0 if not initialized
        Initialize(0);
    }
    
    LastTickTime = FPlatformTime::Seconds();
    
    // Tick emergency system first (highest priority)
    EmergencySystem->TickEmergencyCheck(DeltaTime);
    
    // Only tick adaptive engine if not in emergency mode
    if (!EmergencySystem->IsEmergencyActive())
    {
        AdaptiveEngine->TickAdaptation(DeltaTime);
    }
}

FRuntimeStateSnapshot USymbiontMemoryGovernor::GetRuntimeState() const
{
    if (!bInitialized)
    {
        return FRuntimeStateSnapshot();
    }
    
    return BuildStateSnapshot();
}

FRuntimeStateSnapshot USymbiontMemoryGovernor::BuildStateSnapshot() const
{
    FRuntimeStateSnapshot Snapshot;
    
    // Get performance metrics from adaptive engine
    FPerformanceMetrics Metrics = AdaptiveEngine->GetCurrentMetrics();
    Snapshot.CurrentFPS = Metrics.CurrentFPS;
    Snapshot.CurrentRSSMB = Metrics.CurrentRSSMB;
    Snapshot.CurrentVRAMMB = Metrics.CurrentVRAMMB;
    Snapshot.ThermalStateC = Metrics.ThermalStateC;
    Snapshot.BatteryLevelPercent = Metrics.BatteryLevelPercent;
    
    // Get current optimization profile
    FOptimizationProfile Profile = AdaptiveEngine->GetCurrentProfile();
    Snapshot.CurrentTier = static_cast<uint8>(Profile.Tier);
    Snapshot.TargetFPS = Profile.TargetFPS;
    Snapshot.MaxRSSMB = Profile.MaxRSSMB;
    
    // Get emergency state
    FEmergencyState EmergencyState = EmergencySystem->GetCurrentState();
    Snapshot.bEmergencyActive = EmergencyState.Condition != EEmergencyCondition::None;
    Snapshot.EmergencyCondition = static_cast<uint8>(EmergencyState.Condition);
    Snapshot.EmergencyMaskAlpha = EmergencyState.MaskAlpha;
    
    // Timestamp
    Snapshot.Timestamp = FPlatformTime::Seconds();
    
    return Snapshot;
}

void USymbiontMemoryGovernor::SetOptimizationTier(uint8 Tier)
{
    if (!bInitialized)
    {
        Initialize(Tier);
        return;
    }
    
    EOptimizationTier OptTier = static_cast<EOptimizationTier>(
        FMath::Clamp(Tier,
                     static_cast<uint8>(EOptimizationTier::Tier0_AbsoluteMinimum),
                     static_cast<uint8>(EOptimizationTier::Tier3_Performance))
    );
    
    AdaptiveEngine->SetTier(OptTier);
}

void USymbiontMemoryGovernor::TriggerEmergency()
{
    if (!bInitialized)
    {
        Initialize(0);
    }
    
    EmergencySystem->TriggerEmergency(EEmergencyCondition::MemoryPressure);
}

void USymbiontMemoryGovernor::ResetToBaseline()
{
    if (!bInitialized)
    {
        Initialize(0);
        return;
    }
    
    AdaptiveEngine->Reset();
    EmergencySystem->Reset();
}

bool USymbiontMemoryGovernor::IsEmergencyActive() const
{
    if (!bInitialized)
    {
        return false;
    }
    
    return EmergencySystem->IsEmergencyActive();
}

float USymbiontMemoryGovernor::GetEmergencyMaskAlpha() const
{
    if (!bInitialized)
    {
        return 0.0f;
    }
    
    return EmergencySystem->GetMaskAlpha();
}
