// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
using UnrealBuildTool;

public class The_GardenTarget : TargetRules
{
	public The_GardenTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.V4;
		IncludeOrderVersion  = EngineIncludeOrderVersion.Unreal5_4;
		ExtraModuleNames.Add("The_Garden");
	}
}
