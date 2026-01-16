// Copyright (c) 2026 AIOSPANDORA. All Rights Reserved.
// Project Symbiont: Constitutional Symbiosis Framework
// 
// This file is part of the Constitutional Symbiont Core plugin for Unreal Engine 5.
// It provides the central orchestration point for the four technical pillars:
// - The Bridge (Metal/CoreML texture sharing)
// - The Gavel (Formal verification of AI proposals)
// - The Forest (VRS thermal-aware rendering)
// - The Notary (Compliance logging)

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "SymbiontManager.generated.h"

// Forward declarations
class UBridgeInterface;
class UGavelVerifier;
class UForestVRSController;
class UNotaryLogger;

/**
 * Symbiont Proposal Status
 * Tracks the lifecycle of AI-generated proposals through the Constitutional verification system
 */
UENUM(BlueprintType)
enum class ESymbiontProposalStatus : uint8
{
	Pending			UMETA(DisplayName = "Pending Verification"),
	Verified		UMETA(DisplayName = "Verified - Awaiting Execution"),
	Rejected		UMETA(DisplayName = "Rejected - Failed Verification"),
	Executed		UMETA(DisplayName = "Executed Successfully"),
	Overridden		UMETA(DisplayName = "Overridden by User"),
	Failed			UMETA(DisplayName = "Execution Failed")
};

/**
 * Symbiont Proposal Structure
 * Represents an AI-generated action proposal that must pass Constitutional verification
 */
USTRUCT(BlueprintType)
struct FSymbiontProposal
{
	GENERATED_BODY()

	/** Unique identifier for this proposal */
	UPROPERTY(BlueprintReadOnly, Category = "Symbiont")
	FGuid ProposalID;

	/** Human-readable description of the proposed action */
	UPROPERTY(BlueprintReadOnly, Category = "Symbiont")
	FString ActionDescription;

	/** Timestamp when proposal was generated */
	UPROPERTY(BlueprintReadOnly, Category = "Symbiont")
	FDateTime Timestamp;

	/** Current status of the proposal */
	UPROPERTY(BlueprintReadOnly, Category = "Symbiont")
	ESymbiontProposalStatus Status;

	/** Symbolic proof payload (serialized, used by Gavel) */
	UPROPERTY(BlueprintReadOnly, Category = "Symbiont")
	FString VerificationProof;

	/** Hash of the action payload for audit trail */
	UPROPERTY(BlueprintReadOnly, Category = "Symbiont")
	FString PayloadHash;

	FSymbiontProposal()
		: ProposalID(FGuid::NewGuid())
		, Timestamp(FDateTime::UtcNow())
		, Status(ESymbiontProposalStatus::Pending)
	{}
};

/**
 * USymbiontManager
 * 
 * Central orchestrator for the Constitutional Symbiont system.
 * 
 * This manager implements the "Hypercube Scheduler" - a multi-dimensional task scheduler
 * that coordinates AI proposals across the four technical pillars while maintaining
 * Constitutional supremacy (user override capability).
 * 
 * Key Responsibilities:
 * - Accept AI-generated proposals and route them through verification (Gavel)
 * - Coordinate zero-copy texture sharing for ML inference (Bridge)
 * - Manage thermal-aware rendering quality (Forest)
 * - Ensure all actions are logged for compliance (Notary)
 * - Enforce user override capability at all times
 * 
 * Thread Safety: This class is designed to be called from the game thread.
 * Background verification work is offloaded to async tasks.
 */
UCLASS(BlueprintType, Blueprintable)
class SYMBIONTCORE_API USymbiontManager : public UObject
{
	GENERATED_BODY()

public:
	USymbiontManager();

	/**
	 * Initialize the Symbiont system and all subsystems
	 * @param bEnableStrictVerification - If true, all proposals require formal verification (recommended)
	 * @return True if initialization succeeded
	 */
	UFUNCTION(BlueprintCallable, Category = "Symbiont")
	bool Initialize(bool bEnableStrictVerification = true);

	/**
	 * Shutdown the Symbiont system and release all resources
	 */
	UFUNCTION(BlueprintCallable, Category = "Symbiont")
	void Shutdown();

	/**
	 * Submit an AI-generated proposal for Constitutional verification
	 * @param Proposal - The proposal to submit
	 * @return True if proposal was accepted for verification
	 */
	UFUNCTION(BlueprintCallable, Category = "Symbiont")
	bool SubmitProposal(const FSymbiontProposal& Proposal);

	/**
	 * User override: Force-approve a proposal bypassing verification
	 * Use with caution - logs override event to Notary
	 * @param ProposalID - ID of the proposal to override
	 * @return True if override succeeded
	 */
	UFUNCTION(BlueprintCallable, Category = "Symbiont")
	bool OverrideProposal(const FGuid& ProposalID);

	/**
	 * User veto: Reject a proposal regardless of verification status
	 * Constitutional supremacy - always succeeds
	 * @param ProposalID - ID of the proposal to veto
	 */
	UFUNCTION(BlueprintCallable, Category = "Symbiont")
	void VetoProposal(const FGuid& ProposalID);

	/**
	 * Get current system status for debugging/monitoring
	 * @return Human-readable status string
	 */
	UFUNCTION(BlueprintCallable, Category = "Symbiont")
	FString GetSystemStatus() const;

protected:
	// ========================================================================
	// HYPERCUBE SCHEDULER LOGIC
	// ========================================================================
	// The Hypercube Scheduler is a multi-dimensional task coordination system
	// that treats proposals as points in a 4D space defined by:
	// - Dimension 1: Verification complexity (Gavel)
	// - Dimension 2: Resource requirements (Bridge, Forest)
	// - Dimension 3: User urgency / priority
	// - Dimension 4: Thermal/power constraints
	//
	// Proposals are scheduled to maximize throughput while respecting
	// Constitutional constraints and device limitations.
	//
	// TODO: Implement the following Hypercube scheduling functions:
	// - ScheduleProposal(): Assign proposal to execution slot based on 4D coordinates
	// - ComputeSchedulingPriority(): Calculate priority score from proposal metadata
	// - BalanceResourceAllocation(): Distribute GPU/CPU resources across active proposals
	// - EnforceConstitutionalInvariants(): Verify no scheduling decision violates user override
	// ========================================================================

	/**
	 * Internal: Process a verified proposal
	 * Called after Gavel verification succeeds
	 */
	void ExecuteVerifiedProposal(const FSymbiontProposal& Proposal);

	/**
	 * Internal: Handle verification failure
	 * Logs failure to Notary and escalates to user if needed
	 */
	void HandleVerificationFailure(const FSymbiontProposal& Proposal, const FString& FailureReason);

private:
	/** Reference to Bridge subsystem (Metal/CoreML texture sharing) */
	UPROPERTY()
	TObjectPtr<UBridgeInterface> BridgeSubsystem;

	/** Reference to Gavel subsystem (Formal verification) */
	UPROPERTY()
	TObjectPtr<UGavelVerifier> GavelSubsystem;

	/** Reference to Forest subsystem (VRS thermal management) */
	UPROPERTY()
	TObjectPtr<UForestVRSController> ForestSubsystem;

	/** Reference to Notary subsystem (Compliance logging) */
	UPROPERTY()
	TObjectPtr<UNotaryLogger> NotarySubsystem;

	/** Active proposals awaiting verification or execution */
	TMap<FGuid, FSymbiontProposal> ActiveProposals;

	/** Is strict verification enabled? */
	bool bStrictVerificationEnabled;

	/** Is the system initialized? */
	bool bIsInitialized;

	/** Critical section for thread-safe proposal management */
	FCriticalSection ProposalLock;
};
