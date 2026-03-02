// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
#include "TheGardenGameInstance.h"
#include "TheGardenLeaderboard.h"
#include "OnlineSubsystem.h"
#include "OnlineSessionSettings.h"
#include "Interfaces/OnlineIdentityInterface.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"
#include "RHI.h"

DEFINE_LOG_CATEGORY_STATIC(LogGarden, Log, All);

static const FName SESSION_NAME = TEXT("TheGardenSession");

// ---------------------------------------------------------------------------
void UTheGardenGameInstance::Init()
{
	Super::Init();
	UE_LOG(LogGarden, Log, TEXT("The Garden | build %s"), FApp::GetBuildVersion());

	IOnlineSubsystem* OSS = IOnlineSubsystem::Get();
	if (OSS)
	{
		if (auto ID = OSS->GetIdentityInterface())
			ID->OnLoginCompleteDelegates->AddUObject(this, &UTheGardenGameInstance::OnLoginComplete);
		if (auto Sess = OSS->GetSessionInterface())
		{
			Sess->OnCreateSessionCompleteDelegates.AddUObject(this, &UTheGardenGameInstance::OnCreateSessionComplete);
			Sess->OnFindSessionsCompleteDelegates .AddUObject(this, &UTheGardenGameInstance::OnFindSessionsComplete);
			Sess->OnJoinSessionCompleteDelegates  .AddUObject(this, &UTheGardenGameInstance::OnJoinSessionComplete);
			Sess->OnDestroySessionCompleteDelegates.AddUObject(this, &UTheGardenGameInstance::OnDestroySessionComplete);
		}
		OSS->GetIdentityInterface()->AutoLogin(0);
	}
	else { UE_LOG(LogGarden, Warning, TEXT("OSS unavailable — offline mode.")); }

	LoadGame();
}

void UTheGardenGameInstance::Shutdown()
{
	SaveGame();
	// Delete crash sentinel on clean shutdown (written by TheGardenGameUserSettings)
	const FString Sentinel = FPaths::ProjectSavedDir() / TEXT("TheGarden_CrashSentinel.tmp");
	IFileManager::Get().Delete(*Sentinel);
	Super::Shutdown();
}

// ---------------------------------------------------------------------------
// Steam login
// ---------------------------------------------------------------------------
void UTheGardenGameInstance::OnLoginComplete(int32, bool bOK,
	const FUniqueNetId&, const FString& Err)
{
	if (bOK)
	{
		UE_LOG(LogGarden, Log, TEXT("Steam login OK."));
		// Flush any pending leaderboard score from last session.
		if (ActiveSave && ActiveSave->Progress.CoherenceScore > 0.f)
			if (auto* LB = GetSubsystem<UTheGardenLeaderboard>())
				LB->SubmitCoherenceScore(ActiveSave->Progress.CoherenceScore);
	}
	else { UE_LOG(LogGarden, Warning, TEXT("Steam login failed: %s"), *Err); }
}

// ---------------------------------------------------------------------------
// Save / Load
// ---------------------------------------------------------------------------
void UTheGardenGameInstance::LoadGame()
{
	if (UGameplayStatics::DoesSaveGameExist(THEGARDEN_SAVE_SLOT, THEGARDEN_SAVE_USER))
		ActiveSave = Cast<UTheGardenSaveGame>(
			UGameplayStatics::LoadGameFromSlot(THEGARDEN_SAVE_SLOT, THEGARDEN_SAVE_USER));

	if (!ActiveSave)
		ActiveSave = Cast<UTheGardenSaveGame>(
			UGameplayStatics::CreateSaveGameObject(UTheGardenSaveGame::StaticClass()));

	if (ActiveSave && ActiveSave->MigrateToCurrentVersion())
		UGameplayStatics::SaveGameToSlot(ActiveSave, THEGARDEN_SAVE_SLOT, THEGARDEN_SAVE_USER);
}

void UTheGardenGameInstance::SaveGame()
{
	if (!ActiveSave) return;
	ActiveSave->LastSavedAt = FDateTime::UtcNow().ToIso8601();
	ActiveSave->BuildVersion = FApp::GetBuildVersion();
	const bool bOK = UGameplayStatics::SaveGameToSlot(
		ActiveSave, THEGARDEN_SAVE_SLOT, THEGARDEN_SAVE_USER);
	UE_LOG(LogGarden, Log, TEXT("SaveGame: %s"), bOK ? TEXT("OK") : TEXT("FAILED"));
}

// ---------------------------------------------------------------------------
// Sessions
// ---------------------------------------------------------------------------
void UTheGardenGameInstance::CreateSession(int32 MaxPlayers)
{
	IOnlineSubsystem* OSS = IOnlineSubsystem::Get();
	if (!OSS) { OnSessionReady.Broadcast(false); return; }
	auto Sess = OSS->GetSessionInterface();
	if (!Sess.IsValid()) { OnSessionReady.Broadcast(false); return; }

	FOnlineSessionSettings Settings;
	Settings.NumPublicConnections  = MaxPlayers;
	Settings.bIsLANMatch           = false;
	Settings.bUsesPresence         = true;
	Settings.bAllowJoinInProgress  = true;
	Settings.bShouldAdvertise      = true;
	Settings.bUseLobbiesIfAvailable = true;
	Settings.Set(FName("GAME_MODE"), FString("TheGarden"),
	             EOnlineDataAdvertisementType::ViaOnlineService);

	auto UserId = OSS->GetIdentityInterface()->GetUniquePlayerId(0);
	Sess->CreateSession(*UserId, SESSION_NAME, Settings);
}

void UTheGardenGameInstance::FindSessions()
{
	IOnlineSubsystem* OSS = IOnlineSubsystem::Get();
	if (!OSS) return;
	auto Sess = OSS->GetSessionInterface();
	if (!Sess.IsValid()) return;

	SessionSearch = MakeShareable(new FOnlineSessionSearch());
	SessionSearch->MaxSearchResults = 20;
	SessionSearch->bIsLanQuery      = false;
	SessionSearch->QuerySettings.Set(SEARCH_LOBBIES, true,
	                                 EOnlineComparisonOp::Equals);

	auto UserId = OSS->GetIdentityInterface()->GetUniquePlayerId(0);
	Sess->FindSessions(*UserId, SessionSearch.ToSharedRef());
}

void UTheGardenGameInstance::JoinSession(int32 Index)
{
	IOnlineSubsystem* OSS = IOnlineSubsystem::Get();
	if (!OSS || !SessionSearch.IsValid()) return;
	if (!SessionSearch->SearchResults.IsValidIndex(Index)) return;
	auto Sess   = OSS->GetSessionInterface();
	auto UserId = OSS->GetIdentityInterface()->GetUniquePlayerId(0);
	Sess->JoinSession(*UserId, SESSION_NAME, SessionSearch->SearchResults[Index]);
}

void UTheGardenGameInstance::DestroySession()
{
	IOnlineSubsystem* OSS = IOnlineSubsystem::Get();
	if (!OSS) return;
	if (auto Sess = OSS->GetSessionInterface())
		Sess->DestroySession(SESSION_NAME);
}

void UTheGardenGameInstance::OnCreateSessionComplete(FName, bool bOK)
{
	OnSessionReady.Broadcast(bOK);
}

void UTheGardenGameInstance::OnFindSessionsComplete(bool bOK)
{
	const int32 Found = SessionSearch.IsValid()
		? SessionSearch->SearchResults.Num() : 0;
	UE_LOG(LogGarden, Log, TEXT("FindSessions: %s (%d results)"),
		bOK ? TEXT("OK") : TEXT("FAILED"), Found);
}

void UTheGardenGameInstance::OnJoinSessionComplete(FName,
	EOnJoinSessionCompleteResult::Type Result)
{
	OnSessionReady.Broadcast(Result == EOnJoinSessionCompleteResult::Success);
}

void UTheGardenGameInstance::OnDestroySessionComplete(FName, bool bOK)
{
	UE_LOG(LogGarden, Log, TEXT("DestroySession: %s"), bOK ? TEXT("OK") : TEXT("FAILED"));
}

// ---------------------------------------------------------------------------
// Diagnostics
// ---------------------------------------------------------------------------
FString UTheGardenGameInstance::GetDiagnosticsText() const
{
	return FString::Printf(
		TEXT("The Garden Diagnostics\n======================\nBuild  : %s\nPlatform: %s\nGPU    : %s\nLog    : %s\n"),
		FApp::GetBuildVersion(),
		FPlatformProperties::PlatformName(),
		*GRHIAdapterName,
		*FPaths::ConvertRelativePathToFull(FPaths::ProjectLogDir() / TEXT("TheGarden.log")));
}
