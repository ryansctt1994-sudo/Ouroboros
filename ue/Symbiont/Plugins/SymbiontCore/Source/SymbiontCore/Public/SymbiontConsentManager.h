// Copyright AIOSPANDORA. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "SymbiontConsentManager.generated.h"

/**
 * USymbiontConsentManager - Game Instance Subsystem for managing user consent.
 * 
 * Handles explicit user consent for AR features and on-device AI inference.
 * This is a placeholder implementation - production apps should persist consent
 * using platform-specific storage (iOS: NSUserDefaults, Android: SharedPreferences).
 * 
 * iOS Requirement:
 * Before activating any AR or CoreML inference features, the app MUST show a native
 * consent dialog explaining data usage, processing location (on-device), and privacy
 * implications. Only after explicit user approval should GrantUserConsent() be called.
 * 
 * See Apple App Store Review Guidelines 5.1.2(i) for consent/transparency requirements.
 */
UCLASS()
class SYMBIONTCORE_API USymbiontConsentManager : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	USymbiontConsentManager();

	/** Initialize the subsystem */
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Cleanup on shutdown */
	virtual void Deinitialize() override;

	/**
	 * Check if user has granted consent for AR/inference features.
	 * @return true if consent has been explicitly granted, false otherwise
	 */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Symbiont|Consent")
	bool HasUserConsent() const;

	/**
	 * Grant user consent for AR/inference features.
	 * Call this ONLY after user has explicitly agreed via native consent dialog.
	 */
	UFUNCTION(BlueprintCallable, Category = "Symbiont|Consent")
	void GrantUserConsent();

	/**
	 * Revoke user consent for AR/inference features.
	 * User can withdraw consent at any time; all AR/inference must stop immediately.
	 */
	UFUNCTION(BlueprintCallable, Category = "Symbiont|Consent")
	void RevokeUserConsent();

private:
	/** 
	 * Consent flag - placeholder storage in memory.
	 * TODO: Persist to platform-specific storage (NSUserDefaults on iOS, SharedPreferences on Android)
	 */
	bool bUserConsentGranted;
};
