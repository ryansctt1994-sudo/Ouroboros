// Copyright AIOSPANDORA. All Rights Reserved.

#if PLATFORM_IOS

#import <Foundation/Foundation.h>
#import <CoreML/CoreML.h>

#include "SymbiontTypes.h"

/**
 * FIOSCoreMLBridge - iOS-specific bridge for CoreML model loading and inference.
 * 
 * This Objective-C++ bridge provides the platform interface for loading and running
 * DeepSeek models on iOS devices using Apple's CoreML framework.
 * 
 * Key iOS Optimizations:
 * - MLModelConfiguration.computeUnits can be set to:
 *   - MLComputeUnitsCPUAndGPU (default, good balance)
 *   - MLComputeUnitsCPUAndNeuralEngine (A17/A18 Pro optimization)
 *   - MLComputeUnitsAll (use all available compute)
 * 
 * - For A17 Pro and A18/A18 Pro chips, prefer Neural Engine for inference:
 *   - 16-core Neural Engine on A17 Pro (iPhone 15 Pro/Pro Max)
 *   - 16-core Neural Engine on A18 (iPhone 16/16 Plus)
 *   - 16-core Neural Engine on A18 Pro (iPhone 16 Pro/Pro Max)
 *   - Provides up to 35 trillion operations per second
 * 
 * Model Files:
 * - Models should be compiled to .mlmodelc format and bundled in the app
 * - Place in Resources/ folder or use On-Demand Resources for large models
 * - Typical naming: DeepSeekReasoner.mlmodelc, DeepSeekChat.mlmodelc, etc.
 * 
 * Memory Management:
 * - CoreML models are memory-intensive; monitor with os_proc_available_memory()
 * - Unload models when not in use to prevent memory pressure
 * - Consider using MLModelConfiguration.allowLowPrecisionAccumulationOnGPU for memory savings
 */
class FIOSCoreMLBridge
{
public:
	FIOSCoreMLBridge();
	~FIOSCoreMLBridge();

	/**
	 * Load a CoreML model asynchronously.
	 * 
	 * @param Model - Which DeepSeek model variant to load
	 */
	void LoadModelAsync(EDeepSeekModel Model);

	/**
	 * Check if a model is currently loaded and ready.
	 * 
	 * @return true if model is loaded, false otherwise
	 */
	bool IsModelLoaded() const;

	/**
	 * Unload the currently loaded model to free memory.
	 */
	void UnloadModel();

private:
	/**
	 * Get the CoreML model filename for a given DeepSeek variant.
	 * 
	 * @param Model - DeepSeek model enum
	 * @return Model filename without extension (e.g., "DeepSeekReasoner")
	 */
	NSString* GetModelFilename(EDeepSeekModel Model) const;

	/**
	 * Configure MLModel for optimal performance on current device.
	 * 
	 * @return Configured MLModelConfiguration instance
	 */
	MLModelConfiguration* CreateOptimalConfiguration() const;

	/** Currently loaded CoreML model (nil if no model loaded) */
	id<MLFeatureProvider> LoadedModel;
};

// Implementation

FIOSCoreMLBridge::FIOSCoreMLBridge()
	: LoadedModel(nil)
{
	NSLog(@"[FIOSCoreMLBridge] Bridge initialized");
}

FIOSCoreMLBridge::~FIOSCoreMLBridge()
{
	UnloadModel();
	NSLog(@"[FIOSCoreMLBridge] Bridge destroyed");
}

void FIOSCoreMLBridge::LoadModelAsync(EDeepSeekModel Model)
{
	NSString* ModelName = GetModelFilename(Model);
	NSLog(@"[FIOSCoreMLBridge] Loading model asynchronously: %@", ModelName);

	// Create optimal configuration for current device
	MLModelConfiguration* Config = CreateOptimalConfiguration();

	// TODO: Actual model loading implementation
	// In production:
	// 1. Get model URL from bundle: [[NSBundle mainBundle] URLForResource:ModelName withExtension:@"mlmodelc"]
	// 2. Load model asynchronously: [MLModel loadModelAsset:modelURL configuration:Config completionHandler:...]
	// 3. Store loaded model in LoadedModel
	// 4. Notify Unreal Engine when loading completes (success or failure)
	// 5. Handle errors (model not found, insufficient memory, etc.)

	NSLog(@"[FIOSCoreMLBridge] Model loading stub - actual .mlmodelc file required for real loading");
	NSLog(@"[FIOSCoreMLBridge] Configuration: computeUnits=%ld", (long)Config.computeUnits);
}

bool FIOSCoreMLBridge::IsModelLoaded() const
{
	return LoadedModel != nil;
}

void FIOSCoreMLBridge::UnloadModel()
{
	if (LoadedModel != nil)
	{
		NSLog(@"[FIOSCoreMLBridge] Unloading model");
		LoadedModel = nil;
	}
}

NSString* FIOSCoreMLBridge::GetModelFilename(EDeepSeekModel Model) const
{
	switch (Model)
	{
		case EDeepSeekModel::DS_Reasoner:
			return @"DeepSeekReasoner";
		case EDeepSeekModel::DS_Chat:
			return @"DeepSeekChat";
		case EDeepSeekModel::DS_Coder:
			return @"DeepSeekCoder";
		case EDeepSeekModel::DS_Distilled:
			return @"DeepSeekDistilled";
		default:
			return @"DeepSeekReasoner";
	}
}

MLModelConfiguration* FIOSCoreMLBridge::CreateOptimalConfiguration() const
{
	MLModelConfiguration* Config = [[MLModelConfiguration alloc] init];

	// Prefer Neural Engine + CPU for A17/A18 chips
	// Falls back gracefully on older devices
	Config.computeUnits = MLComputeUnitsCPUAndNeuralEngine;

	// Allow low precision accumulation to save memory on GPU
	// (Neural Engine is preferred anyway)
	if (@available(iOS 14.0, *))
	{
		Config.allowLowPrecisionAccumulationOnGPU = YES;
	}

	NSLog(@"[FIOSCoreMLBridge] Created configuration optimized for A17/A18 Neural Engine");

	return Config;
}

#endif // PLATFORM_IOS
