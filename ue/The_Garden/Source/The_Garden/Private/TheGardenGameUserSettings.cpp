// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
#include "TheGardenGameUserSettings.h"
#include "HAL/FileManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Paths.h"
#include "RHI.h"

namespace GardenPreset
{
	struct FCfg { int32 AA,Sh,PP,Tx,Fx,Fo; bool Lumen; int32 SP; };
	static const TMap<EGardenGraphicsPreset,FCfg> Table =
	{
		{EGardenGraphicsPreset::Ultra,     {4,4,4,4,4,4,true,100}},
		{EGardenGraphicsPreset::High,      {3,3,3,3,3,3,true,100}},
		{EGardenGraphicsPreset::Medium,    {2,2,2,2,2,2,true, 90}},
		{EGardenGraphicsPreset::Low,       {1,1,1,1,1,1,false,80}},
		{EGardenGraphicsPreset::SteamDeck, {2,2,2,2,1,1,false,80}},
	};
}

UTheGardenGameUserSettings* UTheGardenGameUserSettings::Get()
{
	return Cast<UTheGardenGameUserSettings>(UGameUserSettings::GetGameUserSettings());
}

void UTheGardenGameUserSettings::LoadSettings(bool bForceReload)
{
	Super::LoadSettings(bForceReload);
	bSafeMode = FParse::Param(FCommandLine::Get(), TEXT("safemode")) || SentinelExists();
	if (bSafeMode) UE_LOG(LogTemp, Warning, TEXT("TheGarden: safe mode active."));
}

void UTheGardenGameUserSettings::ApplySettings(bool bCheck)
{
	if (bSafeMode) { ApplySafeModeSettings(); return; }
	WriteSentinel();
	if (ActivePreset != EGardenGraphicsPreset::Custom) ApplyPreset(ActivePreset);
	Super::ApplySettings(bCheck);
}

void UTheGardenGameUserSettings::ApplyPreset(EGardenGraphicsPreset Preset)
{
	const GardenPreset::FCfg* C = GardenPreset::Table.Find(Preset);
	if (!C) return;
	SetAntiAliasingQuality(C->AA);
	SetShadowQuality(C->Sh);
	SetPostProcessingQuality(C->PP);
	SetTextureQuality(C->Tx);
	SetVisualEffectQuality(C->Fx);
	SetFoliageQuality(C->Fo);
	SetResolutionScaleValueEx((float)C->SP);
	auto CVar = [](const TCHAR* N){ return IConsoleManager::Get().FindConsoleVariable(N); };
	if (auto* V = CVar(TEXT("r.Lumen.GlobalIllumination.Allow"))) V->Set(C->Lumen?1:0);
	if (auto* V = CVar(TEXT("r.Lumen.Reflections.Allow")))        V->Set(C->Lumen?1:0);
	// Steam Deck: cap framerate to 40 fps for best battery/perf balance
	if (auto* V = CVar(TEXT("t.MaxFPS")))
		V->Set(Preset == EGardenGraphicsPreset::SteamDeck ? 40 : 0);
	ActivePreset = Preset;
	SaveSettings();
}

EGardenGraphicsPreset UTheGardenGameUserSettings::AutoDetectPreset() const
{
	const int64 VRAM = GRHIDedicatedVideoMemory;
	if (VRAM >= 8LL<<30) return EGardenGraphicsPreset::Ultra;
	if (VRAM >= 4LL<<30) return EGardenGraphicsPreset::High;
	if (VRAM >= 2LL<<30) return EGardenGraphicsPreset::Medium;
	return EGardenGraphicsPreset::Low;
}

void UTheGardenGameUserSettings::ApplySafeModeSettings()
{
	SetScreenResolution(FIntPoint(1280,720));
	SetFullscreenMode(EWindowMode::Windowed);
	ApplyPreset(EGardenGraphicsPreset::Low);
	bCameraShake = false; bReduceMotion = true;
	Super::ApplySettings(false);
}

FString UTheGardenGameUserSettings::SentinelPath()
{ return FPaths::ProjectSavedDir() / TEXT("TheGarden_CrashSentinel.tmp"); }
void UTheGardenGameUserSettings::WriteSentinel()
{ FFileHelper::SaveStringToFile(TEXT("1"), *SentinelPath()); }
void UTheGardenGameUserSettings::DeleteSentinel()
{ IFileManager::Get().Delete(*SentinelPath()); }
bool UTheGardenGameUserSettings::SentinelExists() const
{ return IFileManager::Get().FileExists(*SentinelPath()); }
