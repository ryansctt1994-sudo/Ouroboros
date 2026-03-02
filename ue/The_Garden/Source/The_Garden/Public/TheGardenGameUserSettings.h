// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// The Garden — User Settings (presets + accessibility + safe mode)
#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameUserSettings.h"
#include "TheGardenGameUserSettings.generated.h"

UENUM(BlueprintType)
enum class EGardenGraphicsPreset : uint8
{
	Ultra     UMETA(DisplayName="Ultra"),
	High      UMETA(DisplayName="High"),
	Medium    UMETA(DisplayName="Medium"),
	Low       UMETA(DisplayName="Low"),
	SteamDeck UMETA(DisplayName="Steam Deck"),
	Custom    UMETA(DisplayName="Custom"),
};

UENUM(BlueprintType)
enum class EGardenColorblindMode : uint8
{
	None         UMETA(DisplayName="None"),
	Deuteranopia UMETA(DisplayName="Deuteranopia"),
	Protanopia   UMETA(DisplayName="Protanopia"),
	Tritanopia   UMETA(DisplayName="Tritanopia"),
};

UCLASS()
class THE_GARDEN_API UTheGardenGameUserSettings : public UGameUserSettings
{
	GENERATED_BODY()
public:
	static UTheGardenGameUserSettings* Get();

	UFUNCTION(BlueprintCallable, Category="Settings|Graphics")
	void ApplyPreset(EGardenGraphicsPreset Preset);

	UFUNCTION(BlueprintPure, Category="Settings|Graphics")
	EGardenGraphicsPreset GetActivePreset() const { return ActivePreset; }

	UFUNCTION(BlueprintCallable, Category="Settings|Graphics")
	EGardenGraphicsPreset AutoDetectPreset() const;

	// Accessibility
	UPROPERTY(Config, BlueprintReadWrite, Category="Settings|Accessibility")
	bool bSubtitlesEnabled = true;
	UPROPERTY(Config, BlueprintReadWrite, Category="Settings|Accessibility")
	float SubtitleFontScale = 1.f;
	UPROPERTY(Config, BlueprintReadWrite, Category="Settings|Accessibility")
	bool bSubtitleBackground = true;
	UPROPERTY(Config, BlueprintReadWrite, Category="Settings|Accessibility")
	EGardenColorblindMode ColorblindMode = EGardenColorblindMode::None;
	UPROPERTY(Config, BlueprintReadWrite, Category="Settings|Accessibility")
	bool bReduceMotion = false;
	UPROPERTY(Config, BlueprintReadWrite, Category="Settings|Accessibility")
	bool bCameraShake = true;
	UPROPERTY(Config, BlueprintReadWrite, Category="Settings|Accessibility")
	float FOVScale = 1.f;
	UPROPERTY(Config, BlueprintReadWrite, Category="Settings|Accessibility")
	float UIScale = 1.f;

	// Safe mode
	UFUNCTION(BlueprintPure,     Category="Settings|SafeMode") bool IsSafeMode() const { return bSafeMode; }
	UFUNCTION(BlueprintCallable, Category="Settings|SafeMode") void ApplySafeModeSettings();

	virtual void ApplySettings(bool bCheckForCommandLineOverrides) override;
	virtual void LoadSettings(bool bForceReload) override;

private:
	UPROPERTY(Config) EGardenGraphicsPreset ActivePreset = EGardenGraphicsPreset::High;
	bool bSafeMode = false;
	static FString SentinelPath();
	void  WriteSentinel();
	void  DeleteSentinel();
	bool  SentinelExists() const;
};
