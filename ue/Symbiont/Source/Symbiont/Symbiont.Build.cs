// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// AIOS: Ouroboros — Primary game module build rules

using UnrealBuildTool;

public class Symbiont : ModuleRules
{
	public Symbiont(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"OnlineSubsystem",
			"OnlineSubsystemUtils",
			"RHI",                 // AIOSGameUserSettings — GRHIAdapterName
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"SymbiontCore",
			"Slate",
			"SlateCore",
			"SaveGameSystem",      // UGameplayStatics::SaveGameToSlot
			"AutomationController",// Smoke test
		});

		DynamicallyLoadedModuleNames.AddRange(new string[]
		{
			"OnlineSubsystemSteam",
		});
	}
}
