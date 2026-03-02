// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.

#include "AIOSGameUserSettings.h"
#include "HAL/FileManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Paths.h"
#include "RHI.h"

// ---------------------------------------------------------------------------
// Preset quality tables
// ---------------------------------------------------------------------------

namespace AIOSPreset
{
	struct FPresetConfig
	{
		int32 AntiAliasingQuality;   // 0–4
		int32 ShadowQuality;         // 0–4
		int32 PostProcessQuality;    // 0–4
		int32 TextureQuality;        // 0–4
		int32 EffectsQuality;        // 0–4
		int32 FoliageQuality;        // 0–4
		bool  bLumen;
		int32 ScreenPercentage;      // 50–100
	};

	static const TMap<EAIOSGraphicsPreset, FPresetConfig> Presets =
	{
		{ EAIOSGraphicsPreset::Ultra,     { 4, 4, 4, 4, 4, 4, true,  100 } },
		{ EAIOSGraphicsPreset::High,      { 3, 3, 3, 3, 3, 3, true,  100 } },
		{ EAIOSGraphicsPreset::Medium,    { 2, 2, 2, 2, 2, 2, true,   90 } },
		{ EAIOSGraphicsPreset::Low,       { 1, 1, 1, 1, 1, 1, false,  80 } },
		{ EAIOSGraphicsPreset::SteamDeck, { 2, 2, 2, 2, 1, 1, false,  80 } },
	};
}

// ---------------------------------------------------------------------------

UAIOSGameUserSettings::UAIOSGameUserSettings()
{
}

UAIOSGameUserSettings* UAIOSGameUserSettings::GetAIOSGameUserSettings()
{
	return Cast<UAIOSGameUserSettings>(UGameUserSettings::GetGameUserSettings());
}

// ---------------------------------------------------------------------------
// Load / Apply
// ---------------------------------------------------------------------------

void UAIOSGameUserSettings::LoadSettings(bool bForceReload)
{
	Super::LoadSettings(bForceReload);

	// Safe mode: command-line flag or crash sentinel from last run.
	bSafeMode = FParse::Param(FCommandLine::Get(), TEXT("safemode")) ||
	            SentinelExists();

	if (bSafeMode)
	{
		UE_LOG(LogTemp, Warning, TEXT("AIOS: Safe mode active."));
	}
}

void UAIOSGameUserSettings::ApplySettings(bool bCheckForCommandLineOverrides)
{
	if (bSafeMode)
	{
		ApplySafeModeSettings();
		return;
	}

	// Write sentinel — removed on clean shutdown (see AIOSGameInstance::Shutdown).
	WriteSentinel();

	// Apply active preset if not Custom.
	if (ActivePreset != EAIOSGraphicsPreset::Custom)
	{
		ApplyPreset(ActivePreset);
	}

	Super::ApplySettings(bCheckForCommandLineOverrides);
}

// ---------------------------------------------------------------------------
// Presets
// ---------------------------------------------------------------------------

void UAIOSGameUserSettings::ApplyPreset(EAIOSGraphicsPreset Preset)
{
	const AIOSPreset::FPresetConfig* Cfg = AIOSPreset::Presets.Find(Preset);
	if (!Cfg)
	{
		return; // Custom — do not override
	}

	SetAntiAliasingQuality(Cfg->AntiAliasingQuality);
	SetShadowQuality(Cfg->ShadowQuality);
	SetPostProcessingQuality(Cfg->PostProcessQuality);
	SetTextureQuality(Cfg->TextureQuality);
	SetVisualEffectQuality(Cfg->EffectsQuality);
	SetFoliageQuality(Cfg->FoliageQuality);
	SetResolutionScaleValueEx((float)Cfg->ScreenPercentage);

	// Lumen toggle via console variable.
	static IConsoleVariable* LumenGI = IConsoleManager::Get().FindConsoleVariable(
		TEXT("r.Lumen.GlobalIllumination.Allow"));
	static IConsoleVariable* LumenRef = IConsoleManager::Get().FindConsoleVariable(
		TEXT("r.Lumen.Reflections.Allow"));
	if (LumenGI) LumenGI->Set(Cfg->bLumen ? 1 : 0);
	if (LumenRef) LumenRef->Set(Cfg->bLumen ? 1 : 0);

	ActivePreset = Preset;
	SaveSettings();
}

EAIOSGraphicsPreset UAIOSGameUserSettings::AutoDetectPreset() const
{
	// Crude heuristic based on dedicated VRAM.
	// A proper implementation queries GRHIDeviceId against a known list.
	const int64 VRAM = GRHIDedicatedVideoMemory;
	if (VRAM >= 8LL * 1024 * 1024 * 1024) return EAIOSGraphicsPreset::Ultra;
	if (VRAM >= 4LL * 1024 * 1024 * 1024) return EAIOSGraphicsPreset::High;
	if (VRAM >= 2LL * 1024 * 1024 * 1024) return EAIOSGraphicsPreset::Medium;
	return EAIOSGraphicsPreset::Low;
}

// ---------------------------------------------------------------------------
// Safe mode
// ---------------------------------------------------------------------------

void UAIOSGameUserSettings::ApplySafeModeSettings()
{
	SetScreenResolution(FIntPoint(1280, 720));
	SetFullscreenMode(EWindowMode::Windowed);
	ApplyPreset(EAIOSGraphicsPreset::Low);
	bCameraShake  = false;
	bReduceMotion = true;
	UE_LOG(LogTemp, Warning, TEXT("AIOS: Safe mode settings applied."));
	Super::ApplySettings(false);
}

// ---------------------------------------------------------------------------
// Crash sentinel helpers
// ---------------------------------------------------------------------------

FString UAIOSGameUserSettings::GetSentinelPath()
{
	return FPaths::ProjectSavedDir() / TEXT("AIOS_CrashSentinel.tmp");
}

void UAIOSGameUserSettings::WriteSentinel()
{
	FFileHelper::SaveStringToFile(TEXT("1"), *GetSentinelPath());
}

void UAIOSGameUserSettings::DeleteSentinel()
{
	IFileManager::Get().Delete(*GetSentinelPath());
}

bool UAIOSGameUserSettings::SentinelExists() const
{
	return IFileManager::Get().FileExists(*GetSentinelPath());
}
