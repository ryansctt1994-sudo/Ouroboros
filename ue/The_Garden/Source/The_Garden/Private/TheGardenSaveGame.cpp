// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
#include "TheGardenSaveGame.h"
#include "Misc/App.h"
#include "Misc/DateTime.h"

UTheGardenSaveGame::UTheGardenSaveGame()
{
	SaveVersion  = THEGARDEN_SAVE_VERSION;
	BuildVersion = FApp::GetBuildVersion();
	LastSavedAt  = FDateTime::UtcNow().ToIso8601();
}

bool UTheGardenSaveGame::MigrateToCurrentVersion()
{
	if (SaveVersion >= THEGARDEN_SAVE_VERSION) return false;
	const bool bMigrated = MigrateFromVersion(SaveVersion);
	if (bMigrated)
	{
		SaveVersion  = THEGARDEN_SAVE_VERSION;
		BuildVersion = FApp::GetBuildVersion();
		LastSavedAt  = FDateTime::UtcNow().ToIso8601();
	}
	return bMigrated;
}

bool UTheGardenSaveGame::MigrateFromVersion(int32 OldVersion)
{
	switch (OldVersion)
	{
	case 0: return true; // 0 → 1: initial release, no structural changes.
	default:
		UE_LOG(LogTemp, Warning, TEXT("TheGardenSaveGame: unknown version %d"), OldVersion);
		return false;
	}
}
