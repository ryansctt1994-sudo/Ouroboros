// Copyright AIOSPANDORA. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SymbiontTypes.generated.h"

/**
 * DeepSeek model variants for on-device inference.
 * Maps to specific CoreML model files in the app bundle.
 */
UENUM(BlueprintType)
enum class EDeepSeekModel : uint8
{
	DS_Reasoner     UMETA(DisplayName = "DeepSeek Reasoner"),
	DS_Chat         UMETA(DisplayName = "DeepSeek Chat"),
	DS_Coder        UMETA(DisplayName = "DeepSeek Coder"),
	DS_Distilled    UMETA(DisplayName = "DeepSeek Distilled")
};

/**
 * Real-time device vitals for thermal and performance monitoring.
 * Updated each frame by platform-specific sensors.
 */
USTRUCT(BlueprintType)
struct FSymbiontVitals
{
	GENERATED_BODY()

	/** Current frames per second */
	UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
	float FPS = 60.0f;

	/** Thermal state: 0 = nominal, 1 = fair, 2 = serious, 3 = critical, 4 = emergency shutdown imminent */
	UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
	int32 ThermalState = 0;

	/** Battery level from 0.0 (empty) to 1.0 (full) */
	UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
	float BatteryLevel = 1.0f;

	/** Whether network connectivity is available */
	UPROPERTY(BlueprintReadOnly, Category = "Symbiont|Vitals")
	bool bNetworkAvailable = false;
};

/**
 * The Constitutional Symbiont state - consent flags and safety invariants.
 * Represents the current "health" of the symbiotic relationship.
 */
USTRUCT(BlueprintType)
struct FSymbiontConstitution
{
	GENERATED_BODY()

	/** User has explicitly granted consent for AR/inference features */
	UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
	bool bUserConsentGranted = false;

	/** Thermal sanctuary intact: device temperature within safe operating range */
	UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
	bool bThermalSanctuaryIntact = true;

	/** Frame soul synchronized: FPS above minimum threshold (e.g., 30 FPS) */
	UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
	bool bFrameSoulSynchronized = true;

	/** Battery communion maintained: sufficient power for sustained inference */
	UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
	bool bBatteryCommunionMaintained = true;

	/** Giggle Growth Coefficient: humor/playfulness metric (0.0 to 0.85 max) */
	UPROPERTY(BlueprintReadWrite, Category = "Symbiont|Constitution")
	float GiggleGrowthCoefficient = 0.0f;
};
