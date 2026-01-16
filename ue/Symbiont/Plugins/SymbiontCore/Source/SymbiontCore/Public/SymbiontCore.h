// Copyright AIOSPANDORA. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

/**
 * Symbiont Core Module
 * Provides AI inference and constitutional oversight for UE5 projects
 */
class FSymbiontCoreModule : public IModuleInterface
{
public:
	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
