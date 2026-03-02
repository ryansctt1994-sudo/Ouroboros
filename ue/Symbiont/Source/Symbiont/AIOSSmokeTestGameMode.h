// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// AIOS: Ouroboros — Smoke Test Game Mode
//
// Used by CI: boot the smoke map, verify core systems initialise, then quit.
// Exits with code 0 on success, 1 on any failure.
//
// Run via UAT:
//   UnrealEditor-Cmd.exe Symbiont.uproject /Game/Maps/SmokeTest
//     -game -nullrhi -nosound -unattended -ExecCmds="Automation RunTests AIOS.Smoke;Quit"

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "AIOSSmokeTestGameMode.generated.h"

UCLASS()
class SYMBIONT_API AAIOSSmokeTestGameMode : public AGameModeBase
{
	GENERATED_BODY()
protected:
	virtual void BeginPlay() override;
};
