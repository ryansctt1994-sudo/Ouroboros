// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// AIOS: Ouroboros — GameMode implementation

#include "AIOSGameMode.h"
#include "SymbiontConsentManager.h"
#include "Engine/Engine.h"

AAIOSGameMode::AAIOSGameMode()
	: SymbiontEngine(nullptr)
{
}

void AAIOSGameMode::BeginPlay()
{
	Super::BeginPlay();

	// Instantiate the Symbiont Core engine.
	SymbiontEngine = NewObject<USymbiontCoreEngine>(this);
	if (!SymbiontEngine)
	{
		UE_LOG(LogTemp, Error, TEXT("AIOS: Failed to create SymbiontCoreEngine."));
		return;
	}

	// Default: gentle GGC coefficient suitable for first launch.
	SymbiontEngine->SetGiggleGrowthCoefficient(0.5f);

	UE_LOG(LogTemp, Log, TEXT("AIOS GameMode started — Symbiont Core engine initialised."));
}

bool AAIOSGameMode::InvokeRitual()
{
	if (!SymbiontEngine)
	{
		UE_LOG(LogTemp, Warning, TEXT("AIOS: InvokeRitual called before BeginPlay."));
		return false;
	}
	return SymbiontEngine->InvokeSymbiontRitual();
}

FSymbiontConstitution AAIOSGameMode::GetConstitutionSnapshot() const
{
	if (!SymbiontEngine)
	{
		return FSymbiontConstitution{};
	}
	return SymbiontEngine->GetCurrentConstitution();
}

void AAIOSGameMode::GrantUserConsent()
{
	if (!SymbiontEngine)
	{
		return;
	}
	// Route through the consent manager subsystem if available.
	if (UGameInstance* GI = GetGameInstance())
	{
		if (USymbiontConsentManager* CM = GI->GetSubsystem<USymbiontConsentManager>())
		{
			CM->GrantUserConsent();
			return;
		}
	}
	// Fallback: set directly on the engine constitution.
	FSymbiontConstitution Constitution = SymbiontEngine->GetCurrentConstitution();
	Constitution.bUSER_CONSENTED = true;
	UE_LOG(LogTemp, Log, TEXT("AIOS: User consent granted."));
}
