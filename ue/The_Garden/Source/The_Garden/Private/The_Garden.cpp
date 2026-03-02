// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// The Garden — Primary Game Module entry point
//
// Build identity is logged here so every session (and every crash log)
// begins with an unambiguous version string.

#include "The_Garden.h"
#include "TheGardenBuildVersion.h"
#include "Modules/ModuleManager.h"

class FThe_GardenModule : public FDefaultGameModuleImpl
{
public:
	virtual void StartupModule() override
	{
		UE_LOG(LogTemp, Log,
			TEXT("The Garden | %s | platform %s"),
			TEXT(THEGARDEN_BUILD_STRING),
			FPlatformProperties::PlatformName());
	}
};

IMPLEMENT_PRIMARY_GAME_MODULE(FThe_GardenModule, The_Garden, "The_Garden");
