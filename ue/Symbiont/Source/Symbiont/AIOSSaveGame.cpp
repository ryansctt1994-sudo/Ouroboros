// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.

#include "AIOSSaveGame.h"
#include "Misc/App.h"
#include "Misc/DateTime.h"

UAIOSSaveGame::UAIOSSaveGame()
{
	SaveVersion  = AIOS_SAVE_VERSION;
	BuildVersion = FApp::GetBuildVersion();
	LastSavedAt  = FDateTime::UtcNow().ToIso8601();
}

bool UAIOSSaveGame::MigrateToCurrentVersion()
{
	if (SaveVersion >= AIOS_SAVE_VERSION)
	{
		return false; // Already current.
	}

	const bool bMigrated = MigrateFromVersion(SaveVersion);

	if (bMigrated)
	{
		UE_LOG(LogTemp, Log,
			TEXT("AIOSSaveGame: migrated save from version %d to %d."),
			SaveVersion, AIOS_SAVE_VERSION);

		SaveVersion  = AIOS_SAVE_VERSION;
		BuildVersion = FApp::GetBuildVersion();
		LastSavedAt  = FDateTime::UtcNow().ToIso8601();
	}

	return bMigrated;
}

bool UAIOSSaveGame::MigrateFromVersion(int32 OldVersion)
{
	// Add a case here for every breaking schema change:
	//
	// case 0 → 1 (initial version — nothing to migrate yet)
	//
	// Example pattern for a future version 2:
	//   if (OldVersion < 2)
	//   {
	//       Progress.SomeNewField = SomeSensibleDefault;
	//   }

	switch (OldVersion)
	{
	case 0:
		// Version 0 → 1: initial release, no structural changes needed.
		return true;

	default:
		UE_LOG(LogTemp, Warning,
			TEXT("AIOSSaveGame: unrecognised save version %d — keeping as-is."),
			OldVersion);
		return false;
	}
}
