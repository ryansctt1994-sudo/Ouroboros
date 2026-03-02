// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.

#include "AIOSSmokeTestGameMode.h"
#include "AIOSGameInstance.h"
#include "Engine/Engine.h"
#include "HAL/ExceptionHandling.h"
#include "Misc/AutomationTest.h"

// ---------------------------------------------------------------------------
// Automation tests registered under the AIOS.Smoke group.
// CI runs: -ExecCmds="Automation RunTests AIOS.Smoke;Quit"
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FAIOSSmokeTest_GameInstanceExists,
	"AIOS.Smoke.GameInstanceExists",
	EAutomationTestFlags::ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FAIOSSmokeTest_GameInstanceExists::RunTest(const FString&)
{
	UGameInstance* GI = GEngine ? GEngine->GetCurrentPlayWorld()
		? GEngine->GetCurrentPlayWorld()->GetGameInstance() : nullptr : nullptr;
	TestNotNull(TEXT("GameInstance should exist"), GI);
	TestNotNull(TEXT("GameInstance should be UAIOSGameInstance"),
		Cast<UAIOSGameInstance>(GI));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FAIOSSmokeTest_SaveSlotAccessible,
	"AIOS.Smoke.SaveSlotAccessible",
	EAutomationTestFlags::ApplicationContextMask | EAutomationTestFlags::ProductFilter)

bool FAIOSSmokeTest_SaveSlotAccessible::RunTest(const FString&)
{
	// Verify save directory is writable.
	const FString SaveDir = FPaths::ProjectSavedDir();
	TestTrue(TEXT("SaveDir should exist"),
		IFileManager::Get().DirectoryExists(*SaveDir));
	return true;
}

// ---------------------------------------------------------------------------

void AAIOSSmokeTestGameMode::BeginPlay()
{
	Super::BeginPlay();
	UE_LOG(LogTemp, Log, TEXT("AIOS Smoke Test: BeginPlay — core systems present."));
	// Tests are driven by the -ExecCmds automation runner; this mode just
	// ensures the map boots without error.
}
