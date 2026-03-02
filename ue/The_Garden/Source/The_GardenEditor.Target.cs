// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
using UnrealBuildTool;

public class The_GardenEditorTarget : TargetRules
{
	public The_GardenEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.V4;
		IncludeOrderVersion  = EngineIncludeOrderVersion.Unreal5_4;
		ExtraModuleNames.Add("The_Garden");
	}
}
