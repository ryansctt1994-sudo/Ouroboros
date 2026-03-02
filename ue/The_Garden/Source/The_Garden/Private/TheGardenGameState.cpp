// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
#include "TheGardenGameState.h"
#include "Net/UnrealNetwork.h"

void ATheGardenGameState::GetLifetimeReplicatedProps(
	TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ATheGardenGameState, PlayerScores);
}

void ATheGardenGameState::UpdatePlayerScore(const FString& PlayerName,
                                             float CoherenceScore,
                                             int32 EntitiesSpawned)
{
	for (FGardenPlayerScore& Entry : PlayerScores)
	{
		if (Entry.PlayerName == PlayerName)
		{
			Entry.CoherenceScore  = CoherenceScore;
			Entry.EntitiesSpawned = EntitiesSpawned;
			OnScoresUpdated.Broadcast();
			return;
		}
	}
	FGardenPlayerScore New;
	New.PlayerName      = PlayerName;
	New.CoherenceScore  = CoherenceScore;
	New.EntitiesSpawned = EntitiesSpawned;
	PlayerScores.Add(New);
	OnScoresUpdated.Broadcast();
}

FGardenPlayerScore ATheGardenGameState::GetTopScore() const
{
	FGardenPlayerScore Top;
	for (const FGardenPlayerScore& S : PlayerScores)
		if (S.CoherenceScore > Top.CoherenceScore) Top = S;
	return Top;
}
