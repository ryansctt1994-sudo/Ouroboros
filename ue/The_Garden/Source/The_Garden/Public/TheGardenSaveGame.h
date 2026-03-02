// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// The Garden — Save Game (versioned, migration-capable)

#pragma once
#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "TheGardenSaveGame.generated.h"

static constexpr int32 THEGARDEN_SAVE_VERSION = 1;
static const FString   THEGARDEN_SAVE_SLOT     = TEXT("TheGardenProgress");
static constexpr int32 THEGARDEN_SAVE_USER     = 0;

USTRUCT(BlueprintType)
struct FTheGardenProgress
{
	GENERATED_BODY()

	/** Cumulative coherence score across all sessions (submitted to leaderboard). */
	UPROPERTY(BlueprintReadWrite, Category="Save") float CoherenceScore = 0.f;

	/** Total entities spawned across all sessions. */
	UPROPERTY(BlueprintReadWrite, Category="Save") int32 TotalEntitiesSpawned = 0;

	/** Total playtime in minutes. */
	UPROPERTY(BlueprintReadWrite, Category="Save") int32 TotalPlaytimeMinutes = 0;

	/** Number of sessions completed. */
	UPROPERTY(BlueprintReadWrite, Category="Save") int32 SessionsCompleted = 0;
};

UCLASS()
class THE_GARDEN_API UTheGardenSaveGame : public USaveGame
{
	GENERATED_BODY()
public:
	UTheGardenSaveGame();

	UPROPERTY(BlueprintReadOnly, Category="Save") int32   SaveVersion  = THEGARDEN_SAVE_VERSION;
	UPROPERTY(BlueprintReadOnly, Category="Save") FString BuildVersion;
	UPROPERTY(BlueprintReadOnly, Category="Save") FString LastSavedAt;
	UPROPERTY(BlueprintReadWrite, Category="Save") FTheGardenProgress Progress;

	/** Migrate to current schema. Returns true if save was modified. */
	bool MigrateToCurrentVersion();
private:
	bool MigrateFromVersion(int32 OldVersion);
};
