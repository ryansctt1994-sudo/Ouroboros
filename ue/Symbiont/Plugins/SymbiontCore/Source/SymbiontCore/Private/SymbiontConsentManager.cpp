// Copyright AIOSPANDORA. All Rights Reserved.

#include "SymbiontConsentManager.h"

USymbiontConsentManager::USymbiontConsentManager()
	: bUserConsentGranted(false)
{
}

void USymbiontConsentManager::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	
	UE_LOG(LogTemp, Log, TEXT("SymbiontConsentManager initialized - consent state: %s"), 
		bUserConsentGranted ? TEXT("granted") : TEXT("not granted"));
	
	// TODO: Load persisted consent state from platform storage
	// iOS: [[NSUserDefaults standardUserDefaults] boolForKey:@"SymbiontUserConsent"]
	// Android: SharedPreferences.getBoolean("symbiont_user_consent", false)
}

void USymbiontConsentManager::Deinitialize()
{
	Super::Deinitialize();
	
	UE_LOG(LogTemp, Log, TEXT("SymbiontConsentManager deinitialized"));
	
	// TODO: Persist consent state to platform storage before shutdown
}

bool USymbiontConsentManager::HasUserConsent() const
{
	return bUserConsentGranted;
}

void USymbiontConsentManager::GrantUserConsent()
{
	if (!bUserConsentGranted)
	{
		bUserConsentGranted = true;
		UE_LOG(LogTemp, Warning, TEXT("User consent GRANTED for AR/inference features"));
		
		// TODO: Persist to platform storage
		// iOS: [[NSUserDefaults standardUserDefaults] setBool:YES forKey:@"SymbiontUserConsent"]
		// iOS: [[NSUserDefaults standardUserDefaults] synchronize]
	}
}

void USymbiontConsentManager::RevokeUserConsent()
{
	if (bUserConsentGranted)
	{
		bUserConsentGranted = false;
		UE_LOG(LogTemp, Warning, TEXT("User consent REVOKED - all AR/inference must stop immediately"));
		
		// TODO: Persist to platform storage
		// TODO: Broadcast event to stop all active inference/AR sessions
	}
}
