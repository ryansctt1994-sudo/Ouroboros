// Copyright AIOSPANDORA. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GavelTapDetectorComponent.generated.h"

/**
 * Delegate fired when the gavel-tap ritual is successfully detected.
 * Blueprints can bind to this to trigger the Symbiont invocation flow.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnGavelTapDetected);

/**
 * UGavelTapDetectorComponent - Actor Component for detecting gavel-tap gesture ritual.
 * 
 * This is a placeholder component that provides a Blueprint-friendly API for
 * detecting a "gavel tap" gesture (e.g., 2 taps + hold for 1 second).
 * 
 * In a production app, this would integrate with:
 * - UMG touch input events
 * - Platform gesture recognizers (iOS UITapGestureRecognizer + UILongPressGestureRecognizer)
 * - Custom AR hand tracking for physical gavel gesture detection
 * 
 * For now, it exposes simple notification methods that UI/Blueprint can call
 * when the user performs tap or touch actions.
 */
UCLASS(ClassGroup=(Symbiont), meta=(BlueprintSpawnableComponent))
class SYMBIONTCORE_API UGavelTapDetectorComponent : public UActorComponent
{
	GENERATED_BODY()

public:	
	UGavelTapDetectorComponent();

	/** Number of taps required to start the ritual (default: 2) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Symbiont|Gavel Tap")
	int32 RequiredTaps = 2;

	/** Duration in seconds the final tap must be held (default: 1.0s) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Symbiont|Gavel Tap")
	float HoldDuration = 1.0f;

	/** Event fired when the gavel-tap ritual is successfully completed */
	UPROPERTY(BlueprintAssignable, Category = "Symbiont|Gavel Tap")
	FOnGavelTapDetected OnGavelTapDetected;

	/**
	 * Notify the detector that a touch/tap began.
	 * Call from UMG OnTouchStarted or similar events.
	 */
	UFUNCTION(BlueprintCallable, Category = "Symbiont|Gavel Tap")
	void NotifyTouchBegan(const FVector2D& TouchLocation);

	/**
	 * Notify the detector that a touch/tap ended.
	 * Call from UMG OnTouchEnded or similar events.
	 */
	UFUNCTION(BlueprintCallable, Category = "Symbiont|Gavel Tap")
	void NotifyTouchEnded(const FVector2D& TouchLocation);

	/**
	 * Notify the detector of a simple tap (began + ended quickly).
	 * Convenience method for UMG OnClicked events.
	 */
	UFUNCTION(BlueprintCallable, Category = "Symbiont|Gavel Tap")
	void NotifyTap();

	/** Reset the detector state (clears tap count and timers) */
	UFUNCTION(BlueprintCallable, Category = "Symbiont|Gavel Tap")
	void ResetDetector();

protected:
	virtual void BeginPlay() override;

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	/** Current number of taps detected in the sequence */
	int32 CurrentTapCount;

	/** Whether we're currently in a hold state (waiting for hold duration to complete) */
	bool bIsHolding;

	/** Time accumulated during the current hold */
	float HoldTimeAccumulated;

	/** Last time a tap was registered (for sequence timeout) */
	float LastTapTime;

	/** Maximum time between taps before sequence resets (seconds) */
	static constexpr float TapSequenceTimeout = 2.0f;

	/** Check if the ritual is complete and fire the event if so */
	void CheckRitualCompletion();
};
