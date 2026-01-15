// Copyright AIOSPANDORA. All Rights Reserved.

#include "GavelTapDetectorComponent.h"
#include "Engine/World.h"

UGavelTapDetectorComponent::UGavelTapDetectorComponent()
	: CurrentTapCount(0)
	, bIsHolding(false)
	, HoldTimeAccumulated(0.0f)
	, LastTapTime(0.0f)
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UGavelTapDetectorComponent::BeginPlay()
{
	Super::BeginPlay();
	
	UE_LOG(LogTemp, Log, TEXT("GavelTapDetectorComponent initialized - RequiredTaps: %d, HoldDuration: %.2fs"),
		RequiredTaps, HoldDuration);
	
	ResetDetector();
}

void UGavelTapDetectorComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	const float CurrentTime = GetWorld()->GetTimeSeconds();

	// Check if tap sequence has timed out
	if (CurrentTapCount > 0 && (CurrentTime - LastTapTime) > TapSequenceTimeout)
	{
		UE_LOG(LogTemp, Verbose, TEXT("Gavel tap sequence timed out - resetting"));
		ResetDetector();
	}

	// If we're holding, accumulate hold time
	if (bIsHolding)
	{
		HoldTimeAccumulated += DeltaTime;
		
		// Check if hold duration requirement is met
		if (HoldTimeAccumulated >= HoldDuration)
		{
			CheckRitualCompletion();
		}
	}
}

void UGavelTapDetectorComponent::NotifyTouchBegan(const FVector2D& TouchLocation)
{
	const float CurrentTime = GetWorld()->GetTimeSeconds();
	
	// If we have enough taps and user starts holding, enter hold state
	if (CurrentTapCount >= RequiredTaps)
	{
		bIsHolding = true;
		HoldTimeAccumulated = 0.0f;
		UE_LOG(LogTemp, Verbose, TEXT("Gavel tap hold started at location (%.1f, %.1f)"), 
			TouchLocation.X, TouchLocation.Y);
	}
}

void UGavelTapDetectorComponent::NotifyTouchEnded(const FVector2D& TouchLocation)
{
	// If we were holding but released early, reset
	if (bIsHolding && HoldTimeAccumulated < HoldDuration)
	{
		UE_LOG(LogTemp, Verbose, TEXT("Gavel tap hold released too early (%.2fs < %.2fs) - resetting"), 
			HoldTimeAccumulated, HoldDuration);
		ResetDetector();
	}
	
	bIsHolding = false;
}

void UGavelTapDetectorComponent::NotifyTap()
{
	const float CurrentTime = GetWorld()->GetTimeSeconds();
	
	// Increment tap count if within sequence timeout
	if (CurrentTapCount == 0 || (CurrentTime - LastTapTime) <= TapSequenceTimeout)
	{
		CurrentTapCount++;
		LastTapTime = CurrentTime;
		
		UE_LOG(LogTemp, Verbose, TEXT("Gavel tap detected (%d/%d)"), CurrentTapCount, RequiredTaps);
		
		// If we've reached required taps, log and wait for hold
		if (CurrentTapCount >= RequiredTaps)
		{
			UE_LOG(LogTemp, Log, TEXT("Required taps reached - waiting for hold (%.2fs)"), HoldDuration);
		}
	}
	else
	{
		// Timeout - restart sequence
		UE_LOG(LogTemp, Verbose, TEXT("Tap sequence timed out - restarting"));
		CurrentTapCount = 1;
		LastTapTime = CurrentTime;
	}
}

void UGavelTapDetectorComponent::ResetDetector()
{
	CurrentTapCount = 0;
	bIsHolding = false;
	HoldTimeAccumulated = 0.0f;
	LastTapTime = 0.0f;
}

void UGavelTapDetectorComponent::CheckRitualCompletion()
{
	if (CurrentTapCount >= RequiredTaps && HoldTimeAccumulated >= HoldDuration)
	{
		UE_LOG(LogTemp, Warning, TEXT("GAVEL TAP RITUAL COMPLETED - Broadcasting OnGavelTapDetected"));
		
		// Fire the Blueprint event
		OnGavelTapDetected.Broadcast();
		
		// Reset for next ritual
		ResetDetector();
	}
}
