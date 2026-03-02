// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// The Garden — Leaderboard Subsystem
//
// Wraps IOnlineLeaderboards to provide Blueprint-accessible score submission
// and reading for the coherence leaderboard.
// Cloud saves drive the local score; this subsystem syncs it to Steam.

#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Interfaces/OnlineLeaderboardInterface.h"
#include "TheGardenLeaderboard.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnLeaderboardRead,
	bool, bSuccess, const TArray<FString>&, DisplayStrings);

UCLASS()
class THE_GARDEN_API UTheGardenLeaderboard : public UGameInstanceSubsystem
{
	GENERATED_BODY()
public:
	// USubsystem
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	// ------------------------------------------------------------------
	// Submit
	// ------------------------------------------------------------------

	/**
	 * Submit the player's coherence score to the Steam leaderboard.
	 * Uses UPLOADSCOREMETHOD_KeepBest — will not overwrite a higher score.
	 */
	UFUNCTION(BlueprintCallable, Category="Garden|Leaderboard")
	void SubmitCoherenceScore(float Score);

	// ------------------------------------------------------------------
	// Read
	// ------------------------------------------------------------------

	/** Read the top N global entries. Fires OnLeaderboardRead when complete. */
	UFUNCTION(BlueprintCallable, Category="Garden|Leaderboard")
	void ReadTopScores(int32 Count = 10);

	/** Read the player's friends' entries. */
	UFUNCTION(BlueprintCallable, Category="Garden|Leaderboard")
	void ReadFriendScores(int32 Count = 10);

	/** Fired when a read completes. DisplayStrings = ["PlayerName  Score", ...] */
	UPROPERTY(BlueprintAssignable, Category="Garden|Leaderboard")
	FOnLeaderboardRead OnLeaderboardRead;

private:
	static const FName LeaderboardName;

	void OnReadComplete(bool bSuccess,
	                    FOnlineLeaderboardReadRef ReadObject);
};
