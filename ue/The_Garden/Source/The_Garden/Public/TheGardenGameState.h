// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// The Garden — GameState
// Tracks per-session coherence scores for all connected players.
// Replicated so session-based leaderboard battles are visible to all clients.
#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameStateBase.h"
#include "TheGardenGameState.generated.h"

USTRUCT(BlueprintType)
struct FGardenPlayerScore
{
	GENERATED_BODY()
	UPROPERTY(BlueprintReadOnly) FString PlayerName;
	UPROPERTY(BlueprintReadOnly) float   CoherenceScore = 0.f;
	UPROPERTY(BlueprintReadOnly) int32   EntitiesSpawned = 0;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnScoresUpdated);

UCLASS()
class THE_GARDEN_API ATheGardenGameState : public AGameStateBase
{
	GENERATED_BODY()
public:
	/** Current session scores — replicated to all clients. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category="Garden|Score")
	TArray<FGardenPlayerScore> PlayerScores;

	UPROPERTY(BlueprintAssignable) FOnScoresUpdated OnScoresUpdated;

	/** Update this player's score (call on server/authority). */
	UFUNCTION(BlueprintCallable, Category="Garden|Score")
	void UpdatePlayerScore(const FString& PlayerName,
	                       float CoherenceScore, int32 EntitiesSpawned);

	/** Returns the top scorer this session. */
	UFUNCTION(BlueprintPure, Category="Garden|Score")
	FGardenPlayerScore GetTopScore() const;

	virtual void GetLifetimeReplicatedProps(
		TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
