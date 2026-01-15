// Copyright Epic Games, Inc. All Rights Reserved.
// Emergency Fallback System - Two-Phase Reduction Strategy

#include "FEmergencyFallbackSystem.h"
#include "FAdaptiveOptimizationEngine.h"
#include "HAL/PlatformMemory.h"
#include "HAL/PlatformTime.h"
#include "Engine/Engine.h"
#include "Async/AsyncWork.h"

// ============================================================================
// FEmergencyReductionTask Implementation
// ============================================================================

void FEmergencyReductionTask::DoWork()
{
    // Execute staggered reductions based on condition
    switch (Condition)
    {
        case EEmergencyCondition::MemoryPressure:
            ReduceTextureStreamingPool();
            TriggerGarbageCollection();
            break;
            
        case EEmergencyCondition::ThermalCritical:
            ReduceLODDistances();
            ReduceTextureStreamingPool();
            break;
            
        case EEmergencyCondition::BatteryCritical:
            ReduceLODDistances();
            break;
            
        default:
            break;
    }
}

void FEmergencyReductionTask::ReduceTextureStreamingPool()
{
    // Clamp texture streaming pool to minimum
    // NOTE: We avoid FlushResourceStreaming() on Game Thread as per requirements
    static IConsoleVariable* CVarStreamingPoolSize = 
        IConsoleManager::Get().FindConsoleVariable(TEXT("r.Streaming.PoolSize"));
    if (CVarStreamingPoolSize)
    {
        // Reduce to absolute minimum (64MB)
        CVarStreamingPoolSize->Set(64);
    }
    
    // Optional: Set texture streaming quality to lowest
    static IConsoleVariable* CVarStreamingQuality = 
        IConsoleManager::Get().FindConsoleVariable(TEXT("r.Streaming.LimitPoolSizeToVRAM"));
    if (CVarStreamingQuality)
    {
        CVarStreamingQuality->Set(1);
    }
}

void FEmergencyReductionTask::TriggerGarbageCollection()
{
    // Request async garbage collection
    // This will be picked up by the engine's GC system
    if (GEngine)
    {
        GEngine->ForceGarbageCollection(false);  // Non-blocking
    }
}

void FEmergencyReductionTask::ReduceLODDistances()
{
    // Increase LOD distance scale to show lower LODs sooner
    static IConsoleVariable* CVarLODDistanceScale = 
        IConsoleManager::Get().FindConsoleVariable(TEXT("r.StaticMeshLODDistanceScale"));
    if (CVarLODDistanceScale)
    {
        CVarLODDistanceScale->Set(3.0f);  // Aggressive LOD scaling
    }
    
    // Also reduce view distance scale
    static IConsoleVariable* CVarViewDistanceScale = 
        IConsoleManager::Get().FindConsoleVariable(TEXT("r.ViewDistanceScale"));
    if (CVarViewDistanceScale)
    {
        CVarViewDistanceScale->Set(0.5f);
    }
}

// ============================================================================
// FEmergencyFallbackSystem Implementation
// ============================================================================

FEmergencyFallbackSystem::FEmergencyFallbackSystem()
    : PhaseADuration(0.5f)     // 500ms fade duration
    , PhaseBDelay(0.2f)        // 200ms delay before Phase B
    , TimeSincePhaseA(0.0f)
{
}

FEmergencyFallbackSystem::~FEmergencyFallbackSystem()
{
    // Ensure async task is cleaned up
    if (ReductionTask.IsValid())
    {
        ReductionTask->EnsureCompletion();
        ReductionTask.Reset();
    }
}

void FEmergencyFallbackSystem::Initialize()
{
    Reset();
}

void FEmergencyFallbackSystem::TickEmergencyCheck(float DeltaTime)
{
    // Check for emergency conditions
    if (CurrentState.Condition == EEmergencyCondition::None)
    {
        EEmergencyCondition DetectedCondition = CheckEmergencyConditions();
        if (DetectedCondition != EEmergencyCondition::None)
        {
            TriggerEmergency(DetectedCondition);
        }
    }
    
    // Update active emergency
    if (IsEmergencyActive())
    {
        TimeSincePhaseA += DeltaTime;
        
        // Update visual mask
        UpdateMask(DeltaTime);
        
        // Trigger Phase B after delay
        if (!CurrentState.bPhaseBActive && TimeSincePhaseA >= PhaseBDelay)
        {
            ExecutePhaseB();
        }
    }
}

void FEmergencyFallbackSystem::TriggerEmergency(EEmergencyCondition Condition)
{
    CurrentState.Condition = Condition;
    CurrentState.TriggerTime = FPlatformTime::Seconds();
    
    // Execute Phase A immediately
    ExecutePhaseA();
}

void FEmergencyFallbackSystem::ExecutePhaseA()
{
    // Phase A: Visual Masking
    // Apply fade-to-black to hide hitches
    
    CurrentState.bPhaseAActive = true;
    CurrentState.MaskAlpha = 0.0f;  // Will fade to 1.0 over PhaseADuration
    TimeSincePhaseA = 0.0f;
    
    // Immediately apply most critical settings synchronously
    // Reduce screen percentage to absolute minimum
    static IConsoleVariable* CVarScreenPercentage = 
        IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage"));
    if (CVarScreenPercentage)
    {
        CVarScreenPercentage->Set(30.0f);  // Emergency minimum
    }
    
    // Disable expensive features immediately
    static IConsoleVariable* CVarShadowQuality = 
        IConsoleManager::Get().FindConsoleVariable(TEXT("r.ShadowQuality"));
    if (CVarShadowQuality)
    {
        CVarShadowQuality->Set(0);
    }
    
    static IConsoleVariable* CVarMobileShadows = 
        IConsoleManager::Get().FindConsoleVariable(TEXT("r.Mobile.Shadows"));
    if (CVarMobileShadows)
    {
        CVarMobileShadows->Set(0);
    }
}

void FEmergencyFallbackSystem::ExecutePhaseB()
{
    // Phase B: Async Reductions
    // Execute staggered async reductions to minimize Game Thread impact
    
    CurrentState.bPhaseBActive = true;
    
    // Launch async reduction task
    ReductionTask = MakeShareable(new FAsyncTask<FEmergencyReductionTask>(CurrentState.Condition));
    ReductionTask->StartBackgroundTask();
}

void FEmergencyFallbackSystem::UpdateMask(float DeltaTime)
{
    if (CurrentState.bPhaseAActive)
    {
        // Fade in the mask over PhaseADuration
        float Progress = FMath::Clamp(TimeSincePhaseA / PhaseADuration, 0.0f, 1.0f);
        CurrentState.MaskAlpha = FMath::InterpEaseInOut(0.0f, 1.0f, Progress, 2.0f);
    }
}

EEmergencyCondition FEmergencyFallbackSystem::CheckEmergencyConditions()
{
    // Check memory pressure
    FPlatformMemoryStats MemStats = FPlatformMemory::GetStats();
    float MemoryUsageRatio = static_cast<float>(MemStats.UsedPhysical) / 
                             static_cast<float>(MemStats.TotalPhysical);
    if (MemoryUsageRatio >= MemoryEmergencyThreshold)
    {
        return EEmergencyCondition::MemoryPressure;
    }
    
    // Check thermal state (platform-specific, placeholder for now)
    // On iOS, this would use ProcessInfo.thermalState
    float ThermalState = 50.0f;  // Placeholder
    if (ThermalState >= ThermalEmergencyThresholdC)
    {
        return EEmergencyCondition::ThermalCritical;
    }
    
    // Check battery level (platform-specific, placeholder)
    float BatteryLevel = 80.0f;  // Placeholder
    if (BatteryLevel <= BatteryEmergencyPercent)
    {
        return EEmergencyCondition::BatteryCritical;
    }
    
    return EEmergencyCondition::None;
}

void FEmergencyFallbackSystem::Reset()
{
    CurrentState = FEmergencyState();
    TimeSincePhaseA = 0.0f;
    
    if (ReductionTask.IsValid())
    {
        ReductionTask->EnsureCompletion();
        ReductionTask.Reset();
    }
}
