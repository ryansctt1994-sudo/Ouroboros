// Copyright 2024 AIOSPANDORA. All Rights Reserved.

#include "SymbiontCoreEngine.h"
#include "Misc/DateTime.h"
#include "HAL/PlatformProcess.h"

// Logging category for Symbiont subsystem
DEFINE_LOG_CATEGORY_STATIC(LogSymbiont, Log, All);

USymbiontCoreEngine::USymbiontCoreEngine()
{
    // Initialize constitution with safe defaults
    Constitution.GiggleGrowthCoefficient = 0.5f;
    Constitution.bXR_COHERENCE_ACTIVE = false;
    Constitution.bZOREL_QUILLAN_FUSED = false;
    Constitution.bTHERMAL_NOMINAL = true;
    Constitution.bBATTERY_SUFFICIENT = true;
    Constitution.bUSER_CONSENTED = false;

    // Initialize vitals with nominal values
    Vitals.FPS = 60.0f;
    Vitals.ThermalState = TEXT("nominal");
    Vitals.BatteryLevel = 1.0f;
    Vitals.bNetworkAvailable = false;
    Vitals.bUserInteracting = false;
    Vitals.LastUpdateTimestamp = 0;

    bInferenceEnabled = false;
    bModelLoaded = false;
}

void USymbiontCoreEngine::InitializeSymbiont()
{
    UE_LOG(LogSymbiont, Log, TEXT("SymbiontCore initializing..."));
    
    // TODO v0.5: Load actual CoreML model
    // For now, just log initialization
    UE_LOG(LogSymbiont, Log, TEXT("Model loading stub - DeepSeek-R1 Distilled Q4 (local CoreML)"));
    
    // Simulate successful initialization
    bModelLoaded = false; // Will be true once actual model loading is implemented
    
    UE_LOG(LogSymbiont, Log, TEXT("SymbiontCore initialized (stub mode - no actual inference)"));
}

void USymbiontCoreEngine::RequestDeepReasoning(const FString& LogicalConflict, EDeepSeekModel Model)
{
    if (!bInferenceEnabled)
    {
        UE_LOG(LogSymbiont, Warning, TEXT("Inference disabled. User must consent via gesture gate first."));
        return;
    }

    // Log the request
    FString ModelName;
    switch (Model)
    {
        case EDeepSeekModel::DS_Reasoner:
            ModelName = TEXT("DeepSeek-R1 Reasoner");
            break;
        case EDeepSeekModel::DS_Chat:
            ModelName = TEXT("DeepSeek-R1 Chat");
            break;
        case EDeepSeekModel::DS_Coder:
            ModelName = TEXT("DeepSeek-Coder-V2");
            break;
        case EDeepSeekModel::DS_Distilled:
        default:
            ModelName = TEXT("DeepSeek-R1 Distilled Q4");
            break;
    }

    UE_LOG(LogSymbiont, Log, TEXT("Deep reasoning requested: Model=[%s], Prompt=[%s]"), *ModelName, *LogicalConflict);

    // TODO v0.5: Actual CoreML inference
    // - Tokenize the LogicalConflict prompt
    // - Call SymbiontCoreMLBridge::PredictWithModel(tokens)
    // - Detokenize output
    // - Trigger callback/event with result
    
    // For now, just log that we received the request
    UE_LOG(LogSymbiont, Verbose, TEXT("TODO: Implement CoreML inference pipeline"));
}

bool USymbiontCoreEngine::EvaluateConstitutionalInvariants(const FString& EnvironmentalData)
{
    bool bPassed = true;
    TArray<FString> Violations;

    // Check Giggle Growth Coefficient bounds
    if (Constitution.GiggleGrowthCoefficient < 0.0f || Constitution.GiggleGrowthCoefficient > 0.85f)
    {
        Violations.Add(FString::Printf(TEXT("GGC out of bounds: %.3f (valid: 0.0-0.85)"), 
            Constitution.GiggleGrowthCoefficient));
        bPassed = false;
    }

    // Check user consent
    if (!Constitution.bUSER_CONSENTED)
    {
        Violations.Add(TEXT("User consent not granted (gesture gate not activated)"));
        bPassed = false;
    }

    // Check thermal state
    if (!Constitution.bTHERMAL_NOMINAL)
    {
        Violations.Add(TEXT("Thermal state critical - inference should pause"));
        bPassed = false; // Non-fatal but requires action
    }

    // Check battery level
    if (!Constitution.bBATTERY_SUFFICIENT)
    {
        Violations.Add(TEXT("Battery level critical (<20%) - reduce inference frequency"));
        // Don't mark as complete failure, just warning
    }

    // Log results
    if (bPassed)
    {
        UE_LOG(LogSymbiont, Verbose, TEXT("Constitutional check PASSED | Environment: %s"), *EnvironmentalData);
    }
    else
    {
        UE_LOG(LogSymbiont, Warning, TEXT("Constitutional check FAILED | Violations:"));
        for (const FString& Violation : Violations)
        {
            UE_LOG(LogSymbiont, Warning, TEXT("  - %s"), *Violation);
        }
        UE_LOG(LogSymbiont, Warning, TEXT("Environment: %s"), *EnvironmentalData);
    }

    return bPassed;
}

FSymbiontConstitution USymbiontCoreEngine::GetConstitutionSnapshot() const
{
    return Constitution;
}

void USymbiontCoreEngine::SetGiggleGrowthCoefficient(float Coeff)
{
    float ClampedValue = ClampGGC(Coeff);
    
    if (ClampedValue != Coeff)
    {
        UE_LOG(LogSymbiont, Warning, TEXT("GGC clamped from %.3f to %.3f (constitutional bounds: 0.0-0.85)"), 
            Coeff, ClampedValue);
    }
    
    Constitution.GiggleGrowthCoefficient = ClampedValue;
    
    UE_LOG(LogSymbiont, Verbose, TEXT("GGC set to %.3f"), ClampedValue);
}

FSymbiontVitals USymbiontCoreEngine::GetDeviceVitals() const
{
    return Vitals;
}

void USymbiontCoreEngine::SetInferenceEnabled(bool bEnabled)
{
    bInferenceEnabled = bEnabled;
    
    if (bEnabled)
    {
        UE_LOG(LogSymbiont, Log, TEXT("Inference ENABLED (user consented via gesture gate)"));
        Constitution.bUSER_CONSENTED = true;
    }
    else
    {
        UE_LOG(LogSymbiont, Log, TEXT("Inference DISABLED"));
        Constitution.bUSER_CONSENTED = false;
    }
}

void USymbiontCoreEngine::UpdateDeviceVitals()
{
    // Get world for delta time calculation
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    // FPS from engine delta time
    float DeltaSeconds = World->GetDeltaSeconds();
    if (DeltaSeconds > 0.0f)
    {
        Vitals.FPS = 1.0f / DeltaSeconds;
    }

    // Thermal state (iOS-specific, requires bridge)
    #if PLATFORM_IOS
        // TODO v0.5: Call SymbiontCoreMLBridge::GetThermalState()
        // For now, assume nominal
        Vitals.ThermalState = TEXT("nominal"); // Stub
        Constitution.bTHERMAL_NOMINAL = true;
    #else
        Vitals.ThermalState = TEXT("unknown");
        Constitution.bTHERMAL_NOMINAL = true; // Assume nominal on non-iOS platforms
    #endif

    // Battery level (iOS-specific, requires bridge)
    #if PLATFORM_IOS
        // TODO v0.5: Call SymbiontCoreMLBridge::GetBatteryLevel()
        // For now, assume full battery
        Vitals.BatteryLevel = 1.0f; // Stub
        Constitution.bBATTERY_SUFFICIENT = true;
    #else
        Vitals.BatteryLevel = 1.0f; // Assume full on desktop
        Constitution.bBATTERY_SUFFICIENT = true;
    #endif

    // Network availability (UE5 platform abstraction)
    // TODO: Implement actual network check
    // For now, assume no network (local-only inference)
    Vitals.bNetworkAvailable = false;

    // User interaction (check if input received recently)
    // TODO v0.5: Query input system for last touch/key time
    Vitals.bUserInteracting = false; // Stub

    // Timestamp (Unix epoch milliseconds)
    Vitals.LastUpdateTimestamp = FDateTime::UtcNow().ToUnixTimestamp() * 1000;
}

bool USymbiontCoreEngine::LoadModel(const FString& ModelPath)
{
    UE_LOG(LogSymbiont, Log, TEXT("LoadModel called with path: %s"), *ModelPath);
    
    #if PLATFORM_IOS
        // TODO v0.5: Call SymbiontCoreMLBridge::LoadCoreMLModel(ModelPath)
        // Expected model: DeepSeek_R1_Distilled_Q4.mlmodelc
        UE_LOG(LogSymbiont, Warning, TEXT("CoreML model loading not implemented yet (v0 stub)"));
        UE_LOG(LogSymbiont, Warning, TEXT("Inference will be disabled until v0.5 implementation"));
        return false;
    #else
        UE_LOG(LogSymbiont, Warning, TEXT("CoreML not available on this platform. Inference disabled."));
        return false;
    #endif
}

float USymbiontCoreEngine::ClampGGC(float Value) const
{
    // Constitutional bounds: [0.0, 0.85]
    // >0.85 triggers chaos overflow and constitutional breach
    return FMath::Clamp(Value, 0.0f, 0.85f);
}
