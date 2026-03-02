// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// AIOS: Ouroboros — Editor target rules

using UnrealBuildTool;
using System.Collections.Generic;

public class SymbiontEditorTarget : TargetRules
{
	public SymbiontEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.V2;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_3;

		ExtraModuleNames.Add("Symbiont");
	}
}
