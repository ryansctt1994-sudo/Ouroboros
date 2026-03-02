// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// AIOS: Ouroboros — GameMode
//
// AIOSGameMode is the root gameplay class for the AIOS experience.
// It wires the Symbiont Core engine (constitutional AI oversight) into
// the standard UE5 game-loop and exposes Ritual invocation to Blueprints.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "SymbiontCoreEngine.h"
#include "AIOSGameMode.generated.h"

/**
 * AIOS Game Mode
 *
 * Responsibilities:
 *  - Instantiate and own the USymbiontCoreEngine at game start.
 *  - Expose InvokeRitual() to Blueprints for UI / input binding.
 *  - Report constitutional state (GGC, vitals) for the HUD.
 */
UCLASS()
class SYMBIONT_API AAIOSGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AAIOSGameMode();

	// -----------------------------------------------------------------------
	// Blueprint-callable API
	// -----------------------------------------------------------------------

	/** Invoke the Symbiont constitutional AI ritual. Returns true if gating passed. */
	UFUNCTION(BlueprintCallable, Category = "AIOS|Ritual")
	bool InvokeRitual();

	/** Get a snapshot of the current Symbiont constitution for HUD display. */
	UFUNCTION(BlueprintCallable, Category = "AIOS|Ritual")
	FSymbiontConstitution GetConstitutionSnapshot() const;

	/** Grant user consent (call after showing the in-game consent dialog). */
	UFUNCTION(BlueprintCallable, Category = "AIOS|Consent")
	void GrantUserConsent();

protected:
	virtual void BeginPlay() override;

private:
	/** The constitutional Symbiont Core engine instance. */
	UPROPERTY()
	USymbiontCoreEngine* SymbiontEngine;
};
