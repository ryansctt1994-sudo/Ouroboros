// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
#include "TheGardenLeaderboard.h"
#include "OnlineSubsystem.h"
#include "OnlineSubsystemUtils.h"
#include "Interfaces/OnlineIdentityInterface.h"

const FName UTheGardenLeaderboard::LeaderboardName = TEXT("CoherenceScore");

void UTheGardenLeaderboard::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	UE_LOG(LogTemp, Log, TEXT("TheGardenLeaderboard: subsystem ready."));
}

// ---------------------------------------------------------------------------
// Submit
// ---------------------------------------------------------------------------

void UTheGardenLeaderboard::SubmitCoherenceScore(float Score)
{
	IOnlineSubsystem* OSS = IOnlineSubsystem::Get();
	if (!OSS) { UE_LOG(LogTemp, Warning, TEXT("Leaderboard: no OSS.")); return; }

	IOnlineLeaderboardsPtr LB = OSS->GetLeaderboardsInterface();
	IOnlineIdentityPtr     ID = OSS->GetIdentityInterface();
	if (!LB.IsValid() || !ID.IsValid()) return;

	TSharedPtr<const FUniqueNetId> UserId = ID->GetUniquePlayerId(0);
	if (!UserId.IsValid()) return;

	FOnlineLeaderboardWrite WriteObj;
	WriteObj.LeaderboardNames.Add(LeaderboardName);
	WriteObj.RatedStat        = LeaderboardName;
	WriteObj.SortMethod       = ELeaderboardSort::Descending;
	WriteObj.DisplayFormat    = ELeaderboardFormat::Number;
	WriteObj.UpdateMethod     = ELeaderboardUpdateMethod::KeepBest;
	WriteObj.SetIntStat(LeaderboardName, FMath::RoundToInt(Score));

	LB->WriteLeaderboards(NAME_GameSession, *UserId, WriteObj);
	LB->FlushLeaderboards(NAME_GameSession);

	UE_LOG(LogTemp, Log, TEXT("Leaderboard: submitted score %.1f"), Score);
}

// ---------------------------------------------------------------------------
// Read
// ---------------------------------------------------------------------------

void UTheGardenLeaderboard::ReadTopScores(int32 Count)
{
	IOnlineSubsystem* OSS = IOnlineSubsystem::Get();
	if (!OSS) return;
	IOnlineLeaderboardsPtr LB = OSS->GetLeaderboardsInterface();
	if (!LB.IsValid()) return;

	FOnlineLeaderboardReadRef ReadObj =
		MakeShareable(new FOnlineLeaderboardRead());
	ReadObj->LeaderboardName = LeaderboardName;
	ReadObj->SortedColumn    = LeaderboardName;
	ReadObj->ColumnMetadata.Add(
		FColumnMetaData(LeaderboardName, EOnlineKeyValuePairDataType::Int32));

	FOnLeaderboardReadCompleteDelegate Delegate =
		FOnLeaderboardReadCompleteDelegate::CreateUObject(
			this, &UTheGardenLeaderboard::OnReadComplete, ReadObj);

	LB->AddOnLeaderboardReadCompleteDelegate_Handle(Delegate);
	LB->ReadLeaderboardsAroundRank(0, Count, ReadObj);
}

void UTheGardenLeaderboard::ReadFriendScores(int32 Count)
{
	IOnlineSubsystem* OSS = IOnlineSubsystem::Get();
	if (!OSS) return;
	IOnlineLeaderboardsPtr LB = OSS->GetLeaderboardsInterface();
	IOnlineIdentityPtr     ID = OSS->GetIdentityInterface();
	if (!LB.IsValid() || !ID.IsValid()) return;

	TSharedPtr<const FUniqueNetId> UserId = ID->GetUniquePlayerId(0);
	if (!UserId.IsValid()) return;

	TArray<TSharedRef<const FUniqueNetId>> Friends;
	Friends.Add(UserId.ToSharedRef()); // Always include self.

	FOnlineLeaderboardReadRef ReadObj =
		MakeShareable(new FOnlineLeaderboardRead());
	ReadObj->LeaderboardName = LeaderboardName;
	ReadObj->SortedColumn    = LeaderboardName;
	ReadObj->ColumnMetadata.Add(
		FColumnMetaData(LeaderboardName, EOnlineKeyValuePairDataType::Int32));

	FOnLeaderboardReadCompleteDelegate Delegate =
		FOnLeaderboardReadCompleteDelegate::CreateUObject(
			this, &UTheGardenLeaderboard::OnReadComplete, ReadObj);

	LB->AddOnLeaderboardReadCompleteDelegate_Handle(Delegate);
	LB->ReadLeaderboards(Friends, ReadObj);
}

void UTheGardenLeaderboard::OnReadComplete(bool bSuccess,
                                            FOnlineLeaderboardReadRef ReadObj)
{
	TArray<FString> Display;
	if (bSuccess)
	{
		for (const FOnlineStatsRow& Row : ReadObj->Rows)
		{
			int32 Score = 0;
			const FVariantData* Val = Row.Columns.Find(LeaderboardName);
			if (Val) Val->GetValue(Score);
			Display.Add(FString::Printf(TEXT("%-20s %d"),
				*Row.NickName, Score));
		}
	}
	OnLeaderboardRead.Broadcast(bSuccess, Display);
}
