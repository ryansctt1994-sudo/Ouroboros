// Copyright AIOSPANDORA. All Rights Reserved.

#include "SymbiontCoreEngine.h"
#include "SymbiontConsentManager.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"

USymbiontCoreEngine::USymbiontCoreEngine()
{
	// Initialize with default safe state
	CurrentConstitution.bUserConsentGranted = false;
	CurrentConstitution.bThermalSanctuaryIntact = true;
	CurrentConstitution.bFrameSoulSynchronized = true;
	CurrentConstitution.bBatteryCommunionMaintained = true;
	CurrentConstitution.GiggleGrowthCoefficient = 0.0f;
}

bool USymbiontCoreEngine::InvokeSymbiontRitual()
{
	UE_LOG(LogTemp, Log, TEXT("=== SYMBIONT RITUAL INVOCATION REQUESTED ==="));

	// Gate 1: User Consent
	if (!CurrentConstitution.bUserConsentGranted)
	{
		NotifyUser(TEXT("Ritual blocked: User consent not granted. Please grant consent in settings."), true);
		UE_LOG(LogTemp, Warning, TEXT("Ritual BLOCKED - User consent not granted"));
		return false;
	}

	// Gate 2: Thermal Sanctuary
	const int32 ThermalState = GetThermalState();
	CurrentConstitution.bThermalSanctuaryIntact = (ThermalState < 3); // 3 = critical
	
	if (!CurrentConstitution.bThermalSanctuaryIntact)
	{
		NotifyUser(TEXT("Ritual blocked: Device thermal state critical. Please let device cool down."), true);
		UE_LOG(LogTemp, Error, TEXT("Ritual BLOCKED - Thermal state critical: %d"), ThermalState);
		return false;
	}

	// Gate 3: Frame Soul Synchronization (placeholder - check FPS)
	// In production, get actual FPS from engine stats
	if (!CurrentConstitution.bFrameSoulSynchronized)
	{
		NotifyUser(TEXT("Ritual blocked: Frame rate too low. Close other apps or reduce graphics settings."), true);
		UE_LOG(LogTemp, Warning, TEXT("Ritual BLOCKED - Frame soul not synchronized (low FPS)"));
		return false;
	}

	// Gate 4: Battery Communion (placeholder)
	if (!CurrentConstitution.bBatteryCommunionMaintained)
	{
		NotifyUser(TEXT("Ritual blocked: Battery level too low. Please charge device."), true);
		UE_LOG(LogTemp, Warning, TEXT("Ritual BLOCKED - Battery communion not maintained"));
		return false;
	}

	// All gates passed - broadcast ritual begin event
	UE_LOG(LogTemp, Warning, TEXT("=== ALL CONSTITUTIONAL GATES PASSED ==="));
	UE_LOG(LogTemp, Warning, TEXT("Giggle Growth Coefficient: %.3f"), CurrentConstitution.GiggleGrowthCoefficient);
	
	OnRitualBegin.Broadcast();
	
	// Initiate async model loading
	// Default to DS_Reasoner for now
	LoadModelAsync(EDeepSeekModel::DS_Reasoner);
	
	NotifyUser(TEXT("Symbiont ritual begun - loading model..."), false);
	
	return true;
}

void USymbiontCoreEngine::SetGiggleGrowthCoefficient(float Coeff)
{
	// Clamp to safe range [0.0, 0.85]
	const float ClampedCoeff = FMath::Clamp(Coeff, 0.0f, 0.85f);
	
	if (ClampedCoeff != Coeff)
	{
		UE_LOG(LogTemp, Warning, TEXT("Giggle Growth Coefficient clamped from %.3f to %.3f (max: 0.85)"), 
			Coeff, ClampedCoeff);
	}
	
	CurrentConstitution.GiggleGrowthCoefficient = ClampedCoeff;
	
	UE_LOG(LogTemp, Log, TEXT("Giggle Growth Coefficient set to: %.3f"), ClampedCoeff);
}

FSymbiontConstitution USymbiontCoreEngine::GetConstitutionSnapshot() const
{
	return CurrentConstitution;
}

void USymbiontCoreEngine::UpdateConstitution(const FSymbiontVitals& Vitals)
{
	// Update thermal sanctuary
	CurrentConstitution.bThermalSanctuaryIntact = (Vitals.ThermalState < 3);
	
	// Update frame soul (assuming 30 FPS minimum)
	CurrentConstitution.bFrameSoulSynchronized = (Vitals.FPS >= 30.0f);
	
	// Update battery communion (assuming 15% minimum)
	CurrentConstitution.bBatteryCommunionMaintained = (Vitals.BatteryLevel >= 0.15f);
	
	UE_LOG(LogTemp, Verbose, TEXT("Constitution updated - Thermal: %d, Frame: %.1f FPS, Battery: %.0f%%"),
		Vitals.ThermalState, Vitals.FPS, Vitals.BatteryLevel * 100.0f);
}

int32 USymbiontCoreEngine::GetThermalState() const
{
	// TODO: Implement platform-specific thermal monitoring
	// iOS: [[NSProcessInfo processInfo] thermalState]
	//   - NSProcessInfoThermalStateNominal = 0
	//   - NSProcessInfoThermalStateFair = 1
	//   - NSProcessInfoThermalStateSerious = 2
	//   - NSProcessInfoThermalStateCritical = 3
	// Android: PowerManager.getCurrentThermalStatus()
	
	// Placeholder: return nominal state
	return 0;
}

void USymbiontCoreEngine::NotifyUser(const FString& Message, bool bIsError) const
{
	// TODO: Implement proper notification system
	// - Show HUD message
	// - Display toast notification
	// - Update UI widget
	
	if (bIsError)
	{
		UE_LOG(LogTemp, Error, TEXT("[USER NOTIFICATION] %s"), *Message);
	}
	else
	{
		UE_LOG(LogTemp, Log, TEXT("[USER NOTIFICATION] %s"), *Message);
	}
}

void USymbiontCoreEngine::LoadModelAsync(EDeepSeekModel Model)
{
	// This will be implemented by the iOS CoreML bridge
	// See FIOSCoreMLBridge.mm for platform-specific implementation
	
	UE_LOG(LogTemp, Log, TEXT("LoadModelAsync called for model: %d"), static_cast<int32>(Model));
	UE_LOG(LogTemp, Log, TEXT("TODO: Implement platform-specific model loading"));
	
	// On iOS, this would call into the Objective-C++ bridge
	// On other platforms, this might use ONNX Runtime or similar
}
