// Copyright AIOSPANDORA. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "SymbiontTypes.h"
#include "SymbiontCoreEngine.generated.h"

/**
 * Delegate fired when the Symbiont ritual begins (after gating checks pass).
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnRitualBegin);

/**
 * USymbiontCoreEngine - Core engine for Constitutional Symbiont AI inference.
 * 
 * This class orchestrates the "ritual" of invoking on-device AI inference with
 * Constitutional safeguards:
 * 1. User consent check
 * 2. Thermal sanctuary verification (device not overheating)
 * 3. Frame soul synchronization (FPS adequate)
 * 4. Battery communion maintenance (sufficient power)
 * 
 * Only when all constitutional invariants are satisfied does the engine
 * proceed to load and invoke the CoreML model asynchronously.
 * 
 * The "Giggle Growth Coefficient" is a playfulness metric (0.0 to 0.85) that
 * can tune the model's creative/humorous output characteristics.
 */
UCLASS(BlueprintType, Blueprintable)
class SYMBIONTCORE_API USymbiontCoreEngine : public UObject
{
	GENERATED_BODY()

public:
	USymbiontCoreEngine();

	/** The current constitutional state of the Symbiont */
	UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Core")
	FSymbiontConstitution CurrentConstitution;

	/** Event fired when the ritual begins (all checks passed, model loading started) */
	UPROPERTY(BlueprintAssignable, Category = "Symbiont|Core")
	FOnRitualBegin OnRitualBegin;

	/**
	 * Invoke the Symbiont ritual - main entry point for AI inference.
	 * 
	 * Performs constitutional gating:
	 * - Checks if user consent has been granted
	 * - Validates thermal state (< critical threshold)
	 * - Verifies frame rate and battery level
	 * - If all checks pass, initiates async CoreML model loading
	 * 
	 * @return true if ritual invocation started, false if gating checks failed
	 */
	UFUNCTION(BlueprintCallable, Category = "Symbiont|Core")
	bool InvokeSymbiontRitual();

	/**
	 * Set the Giggle Growth Coefficient (playfulness/creativity tuning).
	 * 
	 * @param Coeff - Value between 0.0 (serious/analytical) and 0.85 (maximum playfulness)
	 */
	UFUNCTION(BlueprintCallable, Category = "Symbiont|Core")
	void SetGiggleGrowthCoefficient(float Coeff);

	/**
	 * Get a snapshot of the current constitutional state.
	 * 
	 * @return Copy of the current FSymbiontConstitution
	 */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Symbiont|Core")
	FSymbiontConstitution GetConstitutionSnapshot() const;

	/**
	 * Update the constitution based on current device vitals.
	 * Call this periodically (e.g., once per second) to refresh the constitutional state.
	 * 
	 * @param Vitals - Current device vitals (FPS, thermal, battery, network)
	 */
	UFUNCTION(BlueprintCallable, Category = "Symbiont|Core")
	void UpdateConstitution(const FSymbiontVitals& Vitals);

private:
	/**
	 * Get current thermal state from platform.
	 * TODO: Implement platform-specific thermal monitoring.
	 * iOS: [[NSProcessInfo processInfo] thermalState]
	 * Android: ThermalManager.getCurrentThermalStatus()
	 * 
	 * @return Thermal state: 0 = nominal, 1 = fair, 2 = serious, 3 = critical
	 */
	int32 GetThermalState() const;

	/**
	 * Notify user of ritual status (success, failure, warnings).
	 * TODO: Implement proper notification system (HUD, toasts, etc.)
	 * 
	 * @param Message - Message to display to the user
	 * @param bIsError - Whether this is an error notification
	 */
	void NotifyUser(const FString& Message, bool bIsError = false) const;

	/** Load CoreML model asynchronously - implementation in iOS bridge */
	void LoadModelAsync(EDeepSeekModel Model);
};
