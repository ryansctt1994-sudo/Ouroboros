// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// AIOS: Ouroboros — Extended User Settings
//
// Extends UGameUserSettings with:
//   • Named graphics presets (Ultra / High / Medium / Low / SteamDeck)
//   • Accessibility options (subtitle size, colorblind mode, motion reduction)
//   • Safe-mode detection (detected via a crash sentinel file)

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameUserSettings.h"
#include "AIOSGameUserSettings.generated.h"

// ---------------------------------------------------------------------------
// Enumerations
// ---------------------------------------------------------------------------

UENUM(BlueprintType)
enum class EAIOSGraphicsPreset : uint8
{
	Ultra      UMETA(DisplayName = "Ultra"),
	High       UMETA(DisplayName = "High"),
	Medium     UMETA(DisplayName = "Medium"),
	Low        UMETA(DisplayName = "Low"),
	SteamDeck  UMETA(DisplayName = "Steam Deck"),
	Custom     UMETA(DisplayName = "Custom"),
};

UENUM(BlueprintType)
enum class EAIOSColorblindMode : uint8
{
	None         UMETA(DisplayName = "None"),
	Deuteranopia UMETA(DisplayName = "Deuteranopia (Red-Green)"),
	Protanopia   UMETA(DisplayName = "Protanopia (Red-Green)"),
	Tritanopia   UMETA(DisplayName = "Tritanopia (Blue-Yellow)"),
};

// ---------------------------------------------------------------------------
// Settings class
// ---------------------------------------------------------------------------

UCLASS()
class SYMBIONT_API UAIOSGameUserSettings : public UGameUserSettings
{
	GENERATED_BODY()

public:
	UAIOSGameUserSettings();

	/** Returns the singleton, cast to this type. */
	static UAIOSGameUserSettings* GetAIOSGameUserSettings();

	// -----------------------------------------------------------------------
	// Graphics presets
	// -----------------------------------------------------------------------

	/** Apply a named preset (sets shadow, AA, post-process, lumen quality). */
	UFUNCTION(BlueprintCallable, Category = "Settings|Graphics")
	void ApplyPreset(EAIOSGraphicsPreset Preset);

	/** Detect the most appropriate preset for the current hardware. */
	UFUNCTION(BlueprintCallable, Category = "Settings|Graphics")
	EAIOSGraphicsPreset AutoDetectPreset() const;

	UFUNCTION(BlueprintPure, Category = "Settings|Graphics")
	EAIOSGraphicsPreset GetCurrentPreset() const { return ActivePreset; }

	// -----------------------------------------------------------------------
	// Accessibility
	// -----------------------------------------------------------------------

	UPROPERTY(Config, BlueprintReadWrite, Category = "Settings|Accessibility")
	bool bSubtitlesEnabled = true;

	UPROPERTY(Config, BlueprintReadWrite, Category = "Settings|Accessibility")
	float SubtitleFontScale = 1.0f;

	UPROPERTY(Config, BlueprintReadWrite, Category = "Settings|Accessibility")
	bool bSubtitleBackground = true;

	UPROPERTY(Config, BlueprintReadWrite, Category = "Settings|Accessibility")
	EAIOSColorblindMode ColorblindMode = EAIOSColorblindMode::None;

	UPROPERTY(Config, BlueprintReadWrite, Category = "Settings|Accessibility")
	bool bReduceMotion = false;

	UPROPERTY(Config, BlueprintReadWrite, Category = "Settings|Accessibility")
	bool bCameraShake = true;

	UPROPERTY(Config, BlueprintReadWrite, Category = "Settings|Accessibility")
	float FOVScale = 1.0f;    // 1.0 = default FOV; range 0.75–1.5

	UPROPERTY(Config, BlueprintReadWrite, Category = "Settings|Accessibility")
	float UIScale = 1.0f;     // Range 0.75–2.0; important for TV and Deck

	// -----------------------------------------------------------------------
	// Safe mode
	// -----------------------------------------------------------------------

	/**
	 * Returns true when the game was launched in safe mode.
	 * Safe mode is activated when:
	 *   - The command line contains "-safemode", OR
	 *   - A crash-sentinel file exists from the previous session.
	 */
	UFUNCTION(BlueprintPure, Category = "Settings|SafeMode")
	bool IsSafeMode() const { return bSafeMode; }

	/** Force safe-mode settings (low preset, windowed 1280×720, no shakes). */
	UFUNCTION(BlueprintCallable, Category = "Settings|SafeMode")
	void ApplySafeModeSettings();

	// UGameUserSettings interface
	virtual void ApplySettings(bool bCheckForCommandLineOverrides) override;
	virtual void LoadSettings(bool bForceReload) override;

private:
	UPROPERTY(Config)
	EAIOSGraphicsPreset ActivePreset = EAIOSGraphicsPreset::High;

	bool bSafeMode = false;

	// Crash sentinel file — written at startup, deleted on clean shutdown.
	static FString GetSentinelPath();
	void WriteSentinel();
	void DeleteSentinel();
	bool SentinelExists() const;
};
