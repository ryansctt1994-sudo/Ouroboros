// Copyright AIOSPANDORA. All Rights Reserved.

using UnrealBuildTool;

public class SymbiontCore : ModuleRules
{
	public SymbiontCore(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"OnlineSubsystem",
			}
		);

		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"CoreUObject",
				"Engine",
				"OnlineSubsystemUtils",
			}
		);

		DynamicallyLoadedModuleNames.AddRange(
			new string[]
			{
				"OnlineSubsystemSteam",
			}
		);

		if (Target.Platform == UnrealTargetPlatform.IOS)
		{
			// iOS-specific configuration for CoreML
			PublicFrameworks.AddRange(
				new string[]
				{
					"CoreML",
					"Foundation"
				}
			);
		}
	}
}
