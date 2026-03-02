// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// AIOS: Ouroboros — Versioned Save Game
//
// Schema versioning lets future builds migrate old saves gracefully instead
// of corrupting or silently discarding player progress.
//
// POLICY (see docs/production/save-compatibility.md):
//   • Increment CURRENT_SAVE_VERSION on every breaking schema change.
//   • Add a migration case in FAIOSSaveGame::MigrateFromVersion().
//   • Never remove a UPROPERTY without a deprecation cycle.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "AIOSSaveGame.generated.h"

/** Increment whenever the save schema changes in a breaking way. */
static constexpr int32 AIOS_SAVE_VERSION = 1;

/** Slot name used for both local and Steam Cloud storage. */
static const FString AIOS_SAVE_SLOT  = TEXT("AIOSProgress");
static constexpr int32 AIOS_SAVE_USER = 0;

// ---------------------------------------------------------------------------
// Player progress snapshot
// ---------------------------------------------------------------------------

USTRUCT(BlueprintType)
struct FAIOSProgressData
{
	GENERATED_BODY()

	/** Total number of successful Ritual invocations across all sessions. */
	UPROPERTY(BlueprintReadWrite, Category = "Save|Progress")
	int32 TotalRitualsInvoked = 0;

	/** Peak Giggle Growth Coefficient reached (0–100, integer for save stability). */
	UPROPERTY(BlueprintReadWrite, Category = "Save|Progress")
	int32 PeakGGC = 0;

	/** Total playtime in minutes (for ACH_ONE_HOUR achievement). */
	UPROPERTY(BlueprintReadWrite, Category = "Save|Progress")
	int32 TotalPlaytimeMinutes = 0;

	/** Whether the player has completed all constitutional gates at least once. */
	UPROPERTY(BlueprintReadWrite, Category = "Save|Progress")
	bool bConstitutionCompleted = false;
};

// ---------------------------------------------------------------------------
// Achievement tracking (offline queue — uploaded to Steam when online)
// ---------------------------------------------------------------------------

USTRUCT(BlueprintType)
struct FAIOSAchievementQueue
{
	GENERATED_BODY()

	/** Achievement IDs unlocked locally but not yet confirmed by Steamworks. */
	UPROPERTY(BlueprintReadWrite, Category = "Save|Achievements")
	TArray<FString> PendingUnlocks;

	/** Stat snapshots pending flush to Steam (StatId → value). */
	UPROPERTY(BlueprintReadWrite, Category = "Save|Achievements")
	TMap<FString, int32> PendingStatValues;
};

// ---------------------------------------------------------------------------
// Top-level save object
// ---------------------------------------------------------------------------

UCLASS()
class SYMBIONT_API UAIOSSaveGame : public USaveGame
{
	GENERATED_BODY()

public:
	UAIOSSaveGame();

	// -----------------------------------------------------------------------
	// Versioning
	// -----------------------------------------------------------------------

	/** Schema version written at save time. */
	UPROPERTY(BlueprintReadOnly, Category = "Save|Version")
	int32 SaveVersion = AIOS_SAVE_VERSION;

	/** Content build that produced this save (from FApp::GetBuildVersion). */
	UPROPERTY(BlueprintReadOnly, Category = "Save|Version")
	FString BuildVersion;

	/** Wall-clock timestamp of last write (ISO 8601). */
	UPROPERTY(BlueprintReadOnly, Category = "Save|Version")
	FString LastSavedAt;

	// -----------------------------------------------------------------------
	// Payload
	// -----------------------------------------------------------------------

	UPROPERTY(BlueprintReadWrite, Category = "Save")
	FAIOSProgressData Progress;

	UPROPERTY(BlueprintReadWrite, Category = "Save")
	FAIOSAchievementQueue AchievementQueue;

	// -----------------------------------------------------------------------
	// Migration
	// -----------------------------------------------------------------------

	/**
	 * Called after loading; upgrades the save to the current schema version.
	 * Returns true if the save was modified (caller should re-save to disk).
	 */
	bool MigrateToCurrentVersion();

private:
	bool MigrateFromVersion(int32 OldVersion);
};
