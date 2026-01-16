// Copyright Epic Games, Inc. All Rights Reserved.
// Emergency Fallback System - Two-Phase Reduction Strategy

#pragma once

#include "CoreMinimal.h"
#include "Async/AsyncWork.h"

/**
 * Emergency condition types
 */
enum class EEmergencyCondition : uint8
{
    None = 0,
    MemoryPressure = 1,
    ThermalCritical = 2,
    BatteryCritical = 3,
    SystemCrash = 4
};

/**
 * Emergency state tracking
 */
struct FEmergencyState
{
    EEmergencyCondition Condition;
    double TriggerTime;
    bool bPhaseAActive;
    bool bPhaseBActive;
    float MaskAlpha;  // For visual fade effect
    
    FEmergencyState()
        : Condition(EEmergencyCondition::None)
        , TriggerTime(0.0)
        , bPhaseAActive(false)
        , bPhaseBActive(false)
        , MaskAlpha(0.0f)
    {
    }
};

/**
 * Async task for Phase B reductions
 * Executes staggered async reductions to minimize Game Thread impact
 */
class FEmergencyReductionTask : public FNonAbandonableTask
{
    friend class FAsyncTask<FEmergencyReductionTask>;
    
public:
    FEmergencyReductionTask(EEmergencyCondition InCondition)
        : Condition(InCondition)
    {
    }
    
    void DoWork();
    
    FORCEINLINE TStatId GetStatId() const
    {
        RETURN_QUICK_DECLARE_CYCLE_STAT(FEmergencyReductionTask, STATGROUP_ThreadPoolAsyncTasks);
    }
    
private:
    EEmergencyCondition Condition;
    
    /**
     * Execute texture streaming pool reduction
     */
    void ReduceTextureStreamingPool();
    
    /**
     * Trigger garbage collection
     */
    void TriggerGarbageCollection();
    
    /**
     * Reduce LOD distances
     */
    void ReduceLODDistances();
};

/**
 * FEmergencyFallbackSystem - Two-Phase Emergency Reduction
 * 
 * Triggered by hard constraints:
 * - Memory Pressure (RSS > 95% of max)
 * - Thermal State > 95C
 * - Battery < 5%
 * 
 * Phase A: Visual Masking
 *   - Apply fade-to-black to hide hitches
 *   - Immediate, synchronous on Game Thread
 * 
 * Phase B: Async Reductions
 *   - Clamp texture streaming pool
 *   - Trigger garbage collection
 *   - Reduce LOD distances
 *   - Staggered using AsyncTask to minimize impact
 */
class FEmergencyFallbackSystem
{
public:
    FEmergencyFallbackSystem();
    ~FEmergencyFallbackSystem();
    
    /**
     * Initialize the system
     */
    void Initialize();
    
    /**
     * Check for emergency conditions and trigger if needed
     */
    void TickEmergencyCheck(float DeltaTime);
    
    /**
     * Manually trigger emergency fallback
     */
    void TriggerEmergency(EEmergencyCondition Condition);
    
    /**
     * Check if emergency is active
     */
    bool IsEmergencyActive() const { return CurrentState.Condition != EEmergencyCondition::None; }
    
    /**
     * Get current emergency state
     */
    FEmergencyState GetCurrentState() const { return CurrentState; }
    
    /**
     * Reset emergency state
     */
    void Reset();
    
    /**
     * Get visual mask alpha for rendering
     */
    float GetMaskAlpha() const { return CurrentState.MaskAlpha; }
    
private:
    /**
     * Execute Phase A: Visual Masking
     * Immediate fade-to-black to hide hitches
     */
    void ExecutePhaseA();
    
    /**
     * Execute Phase B: Async Reductions
     * Staggered async reductions
     */
    void ExecutePhaseB();
    
    /**
     * Update visual mask animation
     */
    void UpdateMask(float DeltaTime);
    
    /**
     * Check for emergency conditions
     */
    EEmergencyCondition CheckEmergencyConditions();
    
private:
    FEmergencyState CurrentState;
    
    // Async reduction task
    TSharedPtr<FAsyncTask<FEmergencyReductionTask>> ReductionTask;
    
    // Phase timing
    float PhaseADuration;
    float PhaseBDelay;
    float TimeSincePhaseA;
    
    // Emergency thresholds
    static constexpr float ThermalEmergencyThresholdC = 95.0f;
    static constexpr float MemoryEmergencyThreshold = 0.95f;  // 95% of max
    static constexpr float BatteryEmergencyPercent = 5.0f;
};
