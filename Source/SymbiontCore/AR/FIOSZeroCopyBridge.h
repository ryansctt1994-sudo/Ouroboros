// Copyright Epic Games, Inc. All Rights Reserved.
// iOS Zero-Copy Bridge - CVPixelBuffer for ARKit/Metal/Neural Engine

#pragma once

#include "CoreMinimal.h"

#if PLATFORM_IOS

// Forward declarations for iOS types
typedef struct __CVBuffer *CVBufferRef;
typedef CVBufferRef CVImageBufferRef;
typedef CVImageBufferRef CVPixelBufferRef;

/**
 * Texture handle for zero-copy sharing
 */
struct FZeroCopyTextureHandle
{
    void* PixelBufferHandle;    // CVPixelBufferRef
    void* MetalTexture;         // MTLTexture
    uint32 Width;
    uint32 Height;
    uint32 PixelFormat;
    bool bIsValid;
    
    FZeroCopyTextureHandle()
        : PixelBufferHandle(nullptr)
        , MetalTexture(nullptr)
        , Width(0)
        , Height(0)
        , PixelFormat(0)
        , bIsValid(false)
    {
    }
};

/**
 * FIOSZeroCopyBridge - Zero-copy texture sharing for iOS
 * 
 * Implements a zero-copy bridge using CVPixelBuffer handles for shared textures
 * between ARKit, Metal, and Neural Engine to bypass CPU copies.
 * 
 * Key Features:
 * - Shared memory via CVPixelBuffer (IOSurface-backed)
 * - Direct Metal texture mapping
 * - No CPU memcpy required
 * - Suitable for ARKit camera frames and Neural Engine inference
 */
class FIOSZeroCopyBridge
{
public:
    FIOSZeroCopyBridge();
    ~FIOSZeroCopyBridge();
    
    /**
     * Create a zero-copy texture handle from CVPixelBuffer
     * 
     * @param PixelBuffer - CVPixelBufferRef from ARKit or camera
     * @return Texture handle for use with Metal/Unreal
     */
    static FZeroCopyTextureHandle CreateFromPixelBuffer(CVPixelBufferRef PixelBuffer);
    
    /**
     * Create a CVPixelBuffer for zero-copy sharing
     * 
     * @param Width - Texture width
     * @param Height - Texture height
     * @param PixelFormat - Metal pixel format (e.g., BGRA8Unorm)
     * @return Zero-copy texture handle
     */
    static FZeroCopyTextureHandle CreateSharedBuffer(uint32 Width, uint32 Height, uint32 PixelFormat);
    
    /**
     * Map CVPixelBuffer to Metal texture (zero-copy)
     * 
     * @param Handle - Texture handle with PixelBufferHandle
     * @return Metal texture pointer
     */
    static void* MapToMetalTexture(FZeroCopyTextureHandle& Handle);
    
    /**
     * Release zero-copy texture handle
     * 
     * @param Handle - Handle to release
     */
    static void ReleaseHandle(FZeroCopyTextureHandle& Handle);
    
    /**
     * Lock pixel buffer for CPU access (use sparingly)
     * 
     * @param Handle - Texture handle
     * @param OutBaseAddress - Base address of locked buffer
     * @param OutBytesPerRow - Bytes per row
     * @return true if locked successfully
     */
    static bool LockPixelBuffer(FZeroCopyTextureHandle& Handle, void** OutBaseAddress, size_t* OutBytesPerRow);
    
    /**
     * Unlock pixel buffer
     * 
     * @param Handle - Texture handle to unlock
     */
    static void UnlockPixelBuffer(FZeroCopyTextureHandle& Handle);
    
    /**
     * Check if zero-copy is supported on current device
     */
    static bool IsZeroCopySupported();
    
private:
    /**
     * Internal: Create IOSurface-backed CVPixelBuffer
     */
    static CVPixelBufferRef CreateIOSurfaceBackedPixelBuffer(uint32 Width, uint32 Height, uint32 PixelFormat);
    
    /**
     * Internal: Get Metal pixel format from CV pixel format
     */
    static uint32 GetMetalPixelFormat(uint32 CVPixelFormat);
};

#endif // PLATFORM_IOS
