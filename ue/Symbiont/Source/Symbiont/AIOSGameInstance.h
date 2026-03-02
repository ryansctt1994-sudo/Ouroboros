// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// AIOS: Ouroboros — Game Instance
//
// Responsibilities:
//   • Initialize Steam Online Subsystem at game start.
//   • Manage the canonical save game slot (local + Steam Cloud).
//   • Queue achievement / stat flushes; retry when Steam comes online.
//   • Provide a global "copy diagnostics" payload for the support flow.

#pragma once

#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "AIOSSaveGame.h"
#include "Interfaces/OnlineIdentityInterface.h"
#include "Interfaces/OnlineAchievementsInterface.h"
#include "Interfaces/OnlineStatsInterface.h"
#include "AIOSGameInstance.generated.h"

// ---------------------------------------------------------------------------
// Diagnostic payload (shown in-game "Copy Diagnostics" button)
// ---------------------------------------------------------------------------

USTRUCT(BlueprintType)
struct FAIOSDiagnostics
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Diagnostics")
	FString BuildVersion;

	UPROPERTY(BlueprintReadOnly, Category = "Diagnostics")
	FString Platform;

	UPROPERTY(BlueprintReadOnly, Category = "Diagnostics")
	FString GPUAdapter;

	UPROPERTY(BlueprintReadOnly, Category = "Diagnostics")
	int32 TotalRAMMB = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Diagnostics")
	FString ActiveGraphicsPreset;

	UPROPERTY(BlueprintReadOnly, Category = "Diagnostics")
	FString LogFilePath;
};

// ---------------------------------------------------------------------------
// Game Instance
// ---------------------------------------------------------------------------

UCLASS()
class SYMBIONT_API UAIOSGameInstance : public UGameInstance
{
	GENERATED_BODY()

public:
	UAIOSGameInstance();

	// UGameInstance interface
	virtual void Init() override;
	virtual void Shutdown() override;

	// -----------------------------------------------------------------------
	// Save / Load
	// -----------------------------------------------------------------------

	/** Load from disk (or Steam Cloud on first run). Migrates schema if needed. */
	UFUNCTION(BlueprintCallable, Category = "AIOS|Save")
	void LoadGame();

	/** Write to disk and flush pending Steam stats/achievements. */
	UFUNCTION(BlueprintCallable, Category = "AIOS|Save")
	void SaveGame();

	/** Access the active save data. */
	UFUNCTION(BlueprintPure, Category = "AIOS|Save")
	UAIOSSaveGame* GetSaveGame() const { return ActiveSave; }

	// -----------------------------------------------------------------------
	// Achievements
	// -----------------------------------------------------------------------

	/**
	 * Unlock an achievement by its Steamworks ID string.
	 * Safe to call offline — queued in the save file and retried on flush.
	 */
	UFUNCTION(BlueprintCallable, Category = "AIOS|Achievements")
	void UnlockAchievement(const FString& AchievementId);

	/** Increment an integer Steam stat. */
	UFUNCTION(BlueprintCallable, Category = "AIOS|Achievements")
	void IncrementStat(const FString& StatId, int32 Delta = 1);

	// -----------------------------------------------------------------------
	// Diagnostics
	// -----------------------------------------------------------------------

	/** Build a diagnostic payload for the in-game support panel. */
	UFUNCTION(BlueprintCallable, Category = "AIOS|Diagnostics")
	FAIOSDiagnostics GetDiagnostics() const;

	/** Returns human-readable diagnostics as a plain text string for clipboard copy. */
	UFUNCTION(BlueprintCallable, Category = "AIOS|Diagnostics")
	FString GetDiagnosticsText() const;

private:
	// Cached save reference
	UPROPERTY()
	UAIOSSaveGame* ActiveSave = nullptr;

	// Flush pending achievements / stats to Steam; call after save and on resume.
	void FlushSteamQueue();

	// Called when the Online Identity login completes (Steam sign-in confirmed).
	void OnLoginComplete(int32 LocalUserNum, bool bWasSuccessful,
	                     const FUniqueNetId& UserId, const FString& Error);
};
