// Copyright 2024 AIOSPANDORA. All Rights Reserved.

#include "SymbiontCore.h"

#define LOCTEXT_NAMESPACE "FSymbiontCoreModule"

void FSymbiontCoreModule::StartupModule()
{
	// This code will execute after your module is loaded into memory
	UE_LOG(LogTemp, Log, TEXT("SymbiontCore module starting up"));
}

void FSymbiontCoreModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module
	UE_LOG(LogTemp, Log, TEXT("SymbiontCore module shutting down"));
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FSymbiontCoreModule, SymbiontCore)
