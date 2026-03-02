// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
using UnrealBuildTool;

public class The_Garden : ModuleRules
{
	public The_Garden(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicIncludePaths.AddRange(new string[] {
			"The_Garden/Public"
		});

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"OnlineSubsystem",
			"OnlineSubsystemUtils",
			"RHI",
			"NetCore",
		});

		PrivateDependencyModuleNames.AddRange(new string[] {
			"Slate",
			"SlateCore",
		});

		DynamicallyLoadedModuleNames.AddRange(new string[] {
			"OnlineSubsystemSteam",
		});
	}
}
