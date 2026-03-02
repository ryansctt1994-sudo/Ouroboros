// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// The Garden — Game Instance
// Steam OSS init · Cloud saves · Leaderboard flush · Session management

#pragma once
#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "Interfaces/OnlineSessionInterface.h"
#include "TheGardenSaveGame.h"
#include "TheGardenGameInstance.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnSessionReady, bool, bSuccess);

UCLASS()
class THE_GARDEN_API UTheGardenGameInstance : public UGameInstance
{
	GENERATED_BODY()
public:
	virtual void Init() override;
	virtual void Shutdown() override;

	// ---- Save / Cloud ------------------------------------------------
	UFUNCTION(BlueprintCallable, Category="Garden|Save") void LoadGame();
	UFUNCTION(BlueprintCallable, Category="Garden|Save") void SaveGame();
	UFUNCTION(BlueprintPure,     Category="Garden|Save")
	UTheGardenSaveGame* GetSave() const { return ActiveSave; }

	// ---- Sessions (lobbies) ------------------------------------------
	/** Create a new Garden session (host). */
	UFUNCTION(BlueprintCallable, Category="Garden|Session") void CreateSession(int32 MaxPlayers = 8);
	/** Find open Garden sessions. */
	UFUNCTION(BlueprintCallable, Category="Garden|Session") void FindSessions();
	/** Join a found session by index. */
	UFUNCTION(BlueprintCallable, Category="Garden|Session") void JoinSession(int32 Index);
	/** Destroy current session cleanly. */
	UFUNCTION(BlueprintCallable, Category="Garden|Session") void DestroySession();

	UPROPERTY(BlueprintAssignable, Category="Garden|Session") FOnSessionReady OnSessionReady;

	// ---- Diagnostics -------------------------------------------------
	UFUNCTION(BlueprintCallable, Category="Garden|Diagnostics") FString GetDiagnosticsText() const;

private:
	UPROPERTY() UTheGardenSaveGame* ActiveSave = nullptr;

	TSharedPtr<class FOnlineSessionSearch> SessionSearch;

	// Steam login callback
	void OnLoginComplete(int32 LocalUser, bool bOK,
	                     const FUniqueNetId& Id, const FString& Err);
	// Session callbacks
	void OnCreateSessionComplete(FName SessionName, bool bOK);
	void OnFindSessionsComplete(bool bOK);
	void OnJoinSessionComplete(FName SessionName, EOnJoinSessionCompleteResult::Type Result);
	void OnDestroySessionComplete(FName SessionName, bool bOK);
};
