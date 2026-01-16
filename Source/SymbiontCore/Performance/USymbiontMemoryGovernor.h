// Copyright Epic Games, Inc. All Rights Reserved.
// Memory Governor and Runtime State Management

#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "FAdaptiveOptimizationEngine.h"
#include "FEmergencyFallbackSystem.h"
#include "USymbiontMemoryGovernor.generated.h"

/**
 * Runtime State Snapshot - Clean data contract for the governor
 * 
 * Provides a clean interface for runtime state reasoning
 */
USTRUCT(BlueprintType)
struct FRuntimeStateSnapshot
{
    GENERATED_BODY()
    
    // Performance Metrics
    UPROPERTY(BlueprintReadOnly, Category = "Performance")
    float CurrentFPS;
    
    UPROPERTY(BlueprintReadOnly, Category = "Performance")
    int64 CurrentRSSMB;
    
    UPROPERTY(BlueprintReadOnly, Category = "Performance")
    int64 CurrentVRAMMB;
    
    UPROPERTY(BlueprintReadOnly, Category = "Performance")
    float ThermalStateC;
    
    UPROPERTY(BlueprintReadOnly, Category = "Performance")
    float BatteryLevelPercent;
    
    // Current Tier
    UPROPERTY(BlueprintReadOnly, Category = "Optimization")
    uint8 CurrentTier;
    
    UPROPERTY(BlueprintReadOnly, Category = "Optimization")
    float TargetFPS;
    
    UPROPERTY(BlueprintReadOnly, Category = "Optimization")
    int64 MaxRSSMB;
    
    // Emergency State
    UPROPERTY(BlueprintReadOnly, Category = "Emergency")
    bool bEmergencyActive;
    
    UPROPERTY(BlueprintReadOnly, Category = "Emergency")
    uint8 EmergencyCondition;
    
    UPROPERTY(BlueprintReadOnly, Category = "Emergency")
    float EmergencyMaskAlpha;
    
    // Timestamp
    UPROPERTY(BlueprintReadOnly, Category = "State")
    double Timestamp;
    
    FRuntimeStateSnapshot()
        : CurrentFPS(0.0f)
        , CurrentRSSMB(0)
        , CurrentVRAMMB(0)
        , ThermalStateC(0.0f)
        , BatteryLevelPercent(100.0f)
        , CurrentTier(0)
        , TargetFPS(30.0f)
        , MaxRSSMB(2048)
        , bEmergencyActive(false)
        , EmergencyCondition(0)
        , EmergencyMaskAlpha(0.0f)
        , Timestamp(0.0)
    {
    }
};

/**
 * USymbiontMemoryGovernor - Central runtime state and memory management
 * 
 * Coordinates the adaptive optimization engine and emergency fallback system.
 * Provides a clean data contract (FRuntimeStateSnapshot) for reasoning.
 */
UCLASS(BlueprintType)
class USymbiontMemoryGovernor : public UObject
{
    GENERATED_BODY()
    
public:
    USymbiontMemoryGovernor();
    virtual ~USymbiontMemoryGovernor() override;
    
    /**
     * Initialize the governor with starting tier
     */
    UFUNCTION(BlueprintCallable, Category = "Memory Governor")
    void Initialize(uint8 StartingTier = 0);
    
    /**
     * Tick the governor - call once per frame
     */
    UFUNCTION(BlueprintCallable, Category = "Memory Governor")
    void Tick(float DeltaTime);
    
    /**
     * Get current runtime state snapshot
     */
    UFUNCTION(BlueprintCallable, Category = "Memory Governor")
    FRuntimeStateSnapshot GetRuntimeState() const;
    
    /**
     * Manually set optimization tier
     */
    UFUNCTION(BlueprintCallable, Category = "Memory Governor")
    void SetOptimizationTier(uint8 Tier);
    
    /**
     * Manually trigger emergency fallback
     */
    UFUNCTION(BlueprintCallable, Category = "Memory Governor")
    void TriggerEmergency();
    
    /**
     * Reset to baseline state
     */
    UFUNCTION(BlueprintCallable, Category = "Memory Governor")
    void ResetToBaseline();
    
    /**
     * Check if emergency is active
     */
    UFUNCTION(BlueprintCallable, Category = "Memory Governor")
    bool IsEmergencyActive() const;
    
    /**
     * Get emergency mask alpha for rendering
     */
    UFUNCTION(BlueprintCallable, Category = "Memory Governor")
    float GetEmergencyMaskAlpha() const;
    
protected:
    /**
     * Build runtime state snapshot from current state
     */
    FRuntimeStateSnapshot BuildStateSnapshot() const;
    
private:
    // Core systems
    TUniquePtr<FAdaptiveOptimizationEngine> AdaptiveEngine;
    TUniquePtr<FEmergencyFallbackSystem> EmergencySystem;
    
    // State tracking
    bool bInitialized;
    double LastTickTime;
};
