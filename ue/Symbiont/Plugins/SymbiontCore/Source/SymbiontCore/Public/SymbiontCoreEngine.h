// Copyright 2024 AIOSPANDORA. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "SymbiontCoreEngine.generated.h"

/**
 * DeepSeek model variants for inference selection
 * v0: Only DS_Distilled is planned for implementation
 */
UENUM(BlueprintType)
enum class EDeepSeekModel : uint8
{
    DS_Reasoner   UMETA(DisplayName = "DeepSeek-R1 Reasoner"),     // Long-form reasoning, 128k context
    DS_Chat       UMETA(DisplayName = "DeepSeek-R1 Chat"),         // Conversational, 64k context
    DS_Coder      UMETA(DisplayName = "DeepSeek-Coder-V2"),        // Code generation/analysis
    DS_Distilled  UMETA(DisplayName = "DeepSeek-R1 Distilled Q4")  // Quantized, fastest, 16k context (default)
};

/**
 * Constitutional invariants that govern symbiont behavior
 * All flags must be true (or within bounds) for inference to proceed
 */
USTRUCT(BlueprintType)
struct SYMBIONTCORE_API FSymbiontConstitution
{
    GENERATED_BODY()

    /** Giggle Growth Coefficient: Controls chaos-order balance. Valid range: [0.0, 0.85] */
    UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
    float GiggleGrowthCoefficient = 0.5f;

    /** XR Coherence: Is AR session active and tracking? */
    UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
    bool bXR_COHERENCE_ACTIVE = false;

    /** Zorel-Quillan Fusion: Are agents linked for stable operation? */
    UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
    bool bZOREL_QUILLAN_FUSED = false;

    /** Thermal Safety: Is device temperature nominal? */
    UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
    bool bTHERMAL_NOMINAL = true;

    /** Battery Sufficiency: Is battery above critical threshold (20%)? */
    UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
    bool bBATTERY_SUFFICIENT = true;

    /** User Consent: Has user approved AR/AI features via gesture gate? */
    UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
    bool bUSER_CONSENTED = false;
};

/**
 * Device vitals monitored every frame for constitutional enforcement
 */
USTRUCT(BlueprintType)
struct SYMBIONTCORE_API FSymbiontVitals
{
    GENERATED_BODY()

    /** Frames per second (from UE5 engine stats) */
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
    float FPS = 60.0f;

    /** Thermal state: "nominal", "fair", "serious", "critical" */
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
    FString ThermalState = TEXT("nominal");

    /** Battery level: 0.0 (empty) to 1.0 (full) */
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
    float BatteryLevel = 1.0f;

    /** Is device connected to network? (WiFi or cellular) */
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
    bool bNetworkAvailable = false;

    /** Is user actively interacting? (touch input in last 5 seconds) */
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
    bool bUserInteracting = false;

    /** Timestamp of last vitals update (Unix epoch milliseconds) */
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
    int64 LastUpdateTimestamp = 0;
};

/**
 * Core engine for symbiont AI inference and constitutional oversight
 * 
 * v0: Stubs only, no actual CoreML inference
 * v0.5: Real CoreML integration planned
 */
UCLASS(BlueprintType, Blueprintable)
class SYMBIONTCORE_API USymbiontCoreEngine : public UObject
{
    GENERATED_BODY()

public:
    USymbiontCoreEngine();

    /**
     * Initialize the symbiont core engine
     * v0: Logs initialization, no actual model loading
     */
    UFUNCTION(BlueprintCallable, Category = "Symbiont|Core")
    void InitializeSymbiont();

    /**
     * Request deep reasoning inference from local AI model
     * @param LogicalConflict - The prompt/question for the model
     * @param Model - Which DeepSeek model variant to use (v0: ignored, all use Distilled)
     * v0: Logs request and returns immediately (stub)
     * v0.5: Will call CoreML and return result via callback
     */
    UFUNCTION(BlueprintCallable, Category = "Symbiont|Inference")
    void RequestDeepReasoning(const FString& LogicalConflict, EDeepSeekModel Model = EDeepSeekModel::DS_Distilled);

    /**
     * Evaluate constitutional invariants against current state
     * @param EnvironmentalData - Context string (e.g., "FPS=60,Thermal=nominal")
     * @return True if all invariants pass, False if any breach detected
     */
    UFUNCTION(BlueprintCallable, Category = "Symbiont|Constitution")
    bool EvaluateConstitutionalInvariants(const FString& EnvironmentalData);

    /**
     * Get current constitutional state snapshot
     * @return Struct containing all constitutional flags and GGC
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Symbiont|Constitution")
    FSymbiontConstitution GetConstitutionSnapshot() const;

    /**
     * Set Giggle Growth Coefficient with constitutional clamping
     * @param Coeff - Desired coefficient (will be clamped to [0.0, 0.85])
     */
    UFUNCTION(BlueprintCallable, Category = "Symbiont|Constitution")
    void SetGiggleGrowthCoefficient(float Coeff);

    /**
     * Get current device vitals snapshot
     * @return Struct containing FPS, thermal, battery, etc.
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Symbiont|Vitals")
    FSymbiontVitals GetDeviceVitals() const;

    /**
     * Enable or disable inference capability (controlled by gesture gate)
     * @param bEnabled - True to allow inference, False to disable
     */
    UFUNCTION(BlueprintCallable, Category = "Symbiont|Core")
    void SetInferenceEnabled(bool bEnabled);

    /**
     * Update device vitals (called every frame or on timer)
     * Populates FSymbiontVitals struct with current system state
     */
    UFUNCTION(BlueprintCallable, Category = "Symbiont|Vitals")
    void UpdateDeviceVitals();

protected:
    /** Current constitutional state */
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|State")
    FSymbiontConstitution Constitution;

    /** Current device vitals */
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|State")
    FSymbiontVitals Vitals;

    /** Is inference currently enabled? (Set by gesture gate) */
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|State")
    bool bInferenceEnabled = false;

    /** Has the CoreML model been loaded successfully? */
    UPROPERTY(BlueprintReadOnly, Category = "Symbiont|State")
    bool bModelLoaded = false;

private:
    /** Load CoreML model (v0: stub, v0.5: actual implementation) */
    bool LoadModel(const FString& ModelPath);

    /** Internal: Clamp GGC to constitutional bounds [0.0, 0.85] */
    float ClampGGC(float Value) const;
};
