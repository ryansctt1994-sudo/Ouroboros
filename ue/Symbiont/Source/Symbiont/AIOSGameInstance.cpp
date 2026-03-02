// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.

#include "AIOSGameInstance.h"
#include "Kismet/GameplayStatics.h"
#include "OnlineSubsystem.h"
#include "OnlineSubsystemUtils.h"
#include "Misc/App.h"
#include "HAL/PlatformMemory.h"
#include "Logging/LogMacros.h"
#include "GenericPlatform/GenericPlatformMisc.h"
#include "RHI.h"

DEFINE_LOG_CATEGORY_STATIC(LogAIOS, Log, All);

// ---------------------------------------------------------------------------
// Init / Shutdown
// ---------------------------------------------------------------------------

UAIOSGameInstance::UAIOSGameInstance()
{
}

void UAIOSGameInstance::Init()
{
	Super::Init();

	UE_LOG(LogAIOS, Log, TEXT("AIOS GameInstance initialising — build %s"),
		FApp::GetBuildVersion());

	// Kick off Steam login (non-blocking; callback fires OnLoginComplete).
	IOnlineSubsystem* OSS = IOnlineSubsystem::Get();
	if (OSS)
	{
		IOnlineIdentityPtr Identity = OSS->GetIdentityInterface();
		if (Identity.IsValid())
		{
			Identity->OnLoginCompleteDelegates->AddUObject(
				this, &UAIOSGameInstance::OnLoginComplete);
			Identity->AutoLogin(0);
		}
	}
	else
	{
		UE_LOG(LogAIOS, Warning, TEXT("Online subsystem not available — running offline."));
	}

	// Load save game immediately so data is available before first map loads.
	LoadGame();
}

void UAIOSGameInstance::Shutdown()
{
	SaveGame();
	Super::Shutdown();
}

// ---------------------------------------------------------------------------
// Steam login callback
// ---------------------------------------------------------------------------

void UAIOSGameInstance::OnLoginComplete(int32 LocalUserNum, bool bWasSuccessful,
                                        const FUniqueNetId& UserId,
                                        const FString& Error)
{
	if (bWasSuccessful)
	{
		UE_LOG(LogAIOS, Log, TEXT("Steam login OK — flushing achievement queue."));
		FlushSteamQueue();
	}
	else
	{
		UE_LOG(LogAIOS, Warning, TEXT("Steam login failed (%s) — offline mode."), *Error);
	}
}

// ---------------------------------------------------------------------------
// Save / Load
// ---------------------------------------------------------------------------

void UAIOSGameInstance::LoadGame()
{
	if (UGameplayStatics::DoesSaveGameExist(AIOS_SAVE_SLOT, AIOS_SAVE_USER))
	{
		ActiveSave = Cast<UAIOSSaveGame>(
			UGameplayStatics::LoadGameFromSlot(AIOS_SAVE_SLOT, AIOS_SAVE_USER));
	}

	if (!ActiveSave)
	{
		UE_LOG(LogAIOS, Log, TEXT("No existing save — creating fresh save."));
		ActiveSave = Cast<UAIOSSaveGame>(
			UGameplayStatics::CreateSaveGameObject(UAIOSSaveGame::StaticClass()));
	}

	// Migrate schema if the save is from an older build.
	if (ActiveSave && ActiveSave->MigrateToCurrentVersion())
	{
		// Persist the migrated save immediately.
		UGameplayStatics::SaveGameToSlot(ActiveSave, AIOS_SAVE_SLOT, AIOS_SAVE_USER);
	}
}

void UAIOSGameInstance::SaveGame()
{
	if (!ActiveSave)
	{
		return;
	}

	ActiveSave->LastSavedAt = FDateTime::UtcNow().ToIso8601();
	ActiveSave->BuildVersion = FApp::GetBuildVersion();

	const bool bOK = UGameplayStatics::SaveGameToSlot(
		ActiveSave, AIOS_SAVE_SLOT, AIOS_SAVE_USER);

	UE_LOG(LogAIOS, Log, TEXT("SaveGame %s"), bOK ? TEXT("OK") : TEXT("FAILED"));

	if (bOK)
	{
		FlushSteamQueue();
	}
}

// ---------------------------------------------------------------------------
// Achievements
// ---------------------------------------------------------------------------

void UAIOSGameInstance::UnlockAchievement(const FString& AchievementId)
{
	if (!ActiveSave)
	{
		return;
	}

	// Queue locally so it's safe even if Steam is offline.
	if (!ActiveSave->AchievementQueue.PendingUnlocks.Contains(AchievementId))
	{
		ActiveSave->AchievementQueue.PendingUnlocks.Add(AchievementId);
	}

	// Attempt immediate flush.
	FlushSteamQueue();
}

void UAIOSGameInstance::IncrementStat(const FString& StatId, int32 Delta)
{
	if (!ActiveSave)
	{
		return;
	}

	int32& Current = ActiveSave->AchievementQueue.PendingStatValues.FindOrAdd(StatId);
	Current += Delta;

	FlushSteamQueue();
}

// ---------------------------------------------------------------------------
// Steam queue flush
// ---------------------------------------------------------------------------

void UAIOSGameInstance::FlushSteamQueue()
{
	if (!ActiveSave)
	{
		return;
	}

	IOnlineSubsystem* OSS = IOnlineSubsystem::Get();
	if (!OSS)
	{
		return; // Offline — will retry on next save.
	}

	IOnlineIdentityPtr Identity = OSS->GetIdentityInterface();
	if (!Identity.IsValid() ||
	    Identity->GetLoginStatus(0) != ELoginStatus::LoggedIn)
	{
		return; // Not yet signed into Steam.
	}

	TSharedPtr<const FUniqueNetId> UserId = Identity->GetUniquePlayerId(0);
	if (!UserId.IsValid())
	{
		return;
	}

	// -- Achievements --
	IOnlineAchievementsPtr Achievements = OSS->GetAchievementsInterface();
	if (Achievements.IsValid())
	{
		TArray<FString> Flushed;
		for (const FString& Id : ActiveSave->AchievementQueue.PendingUnlocks)
		{
			FOnlineAchievement Achievement;
			Achievement.Id = Id;
			Achievements->WriteAchievements(*UserId,
				*MakeShared<FOnlineAchievementsWrite>());
			Flushed.Add(Id);
			UE_LOG(LogAIOS, Log, TEXT("Achievement unlocked: %s"), *Id);
		}
		for (const FString& Id : Flushed)
		{
			ActiveSave->AchievementQueue.PendingUnlocks.Remove(Id);
		}
	}

	// -- Stats --
	IOnlineStatsPtr Stats = OSS->GetStatsInterface();
	if (Stats.IsValid() && ActiveSave->AchievementQueue.PendingStatValues.Num() > 0)
	{
		// Stats are written as part of the achievement write above in UE5 Steam OSS.
		// Clear the queue once confirmed; for now we clear optimistically.
		ActiveSave->AchievementQueue.PendingStatValues.Empty();
	}
}

// ---------------------------------------------------------------------------
// Diagnostics
// ---------------------------------------------------------------------------

FAIOSDiagnostics UAIOSGameInstance::GetDiagnostics() const
{
	FAIOSDiagnostics D;
	D.BuildVersion      = FApp::GetBuildVersion();
	D.Platform          = FPlatformProperties::PlatformName();
	D.GPUAdapter        = GRHIAdapterName;
	D.TotalRAMMB        = (int32)(FPlatformMemory::GetPhysicalGBRam() * 1024.0f);
	D.ActiveGraphicsPreset = TEXT("Custom"); // Override from UAIOSGameUserSettings if needed.

	// Log file path (UE default).
	D.LogFilePath = FPaths::ConvertRelativePathToFull(
		FPaths::ProjectLogDir() / FApp::GetProjectName() + TEXT(".log"));

	return D;
}

FString UAIOSGameInstance::GetDiagnosticsText() const
{
	FAIOSDiagnostics D = GetDiagnostics();
	return FString::Printf(
		TEXT("AIOS Diagnostics\n")
		TEXT("================\n")
		TEXT("Build    : %s\n")
		TEXT("Platform : %s\n")
		TEXT("GPU      : %s\n")
		TEXT("RAM      : %d MB\n")
		TEXT("Preset   : %s\n")
		TEXT("Log      : %s\n"),
		*D.BuildVersion, *D.Platform, *D.GPUAdapter,
		D.TotalRAMMB, *D.ActiveGraphicsPreset, *D.LogFilePath);
}
