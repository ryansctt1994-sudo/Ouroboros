// Copyright Epic Games, Inc. All Rights Reserved.
// iOS Zero-Copy Bridge - CVPixelBuffer for ARKit/Metal/Neural Engine

#include "FIOSZeroCopyBridge.h"

#if PLATFORM_IOS

#import <Foundation/Foundation.h>
#import <CoreVideo/CoreVideo.h>
#import <Metal/Metal.h>
#import <UIKit/UIKit.h>

FIOSZeroCopyBridge::FIOSZeroCopyBridge()
{
}

FIOSZeroCopyBridge::~FIOSZeroCopyBridge()
{
}

FZeroCopyTextureHandle FIOSZeroCopyBridge::CreateFromPixelBuffer(CVPixelBufferRef PixelBuffer)
{
    FZeroCopyTextureHandle Handle;
    
    if (!PixelBuffer)
    {
        return Handle;
    }
    
    // Retain the pixel buffer
    CVPixelBufferRetain(PixelBuffer);
    Handle.PixelBufferHandle = (void*)PixelBuffer;
    
    // Get dimensions
    Handle.Width = static_cast<uint32>(CVPixelBufferGetWidth(PixelBuffer));
    Handle.Height = static_cast<uint32>(CVPixelBufferGetHeight(PixelBuffer));
    Handle.PixelFormat = static_cast<uint32>(CVPixelBufferGetPixelFormatType(PixelBuffer));
    
    // Map to Metal texture
    Handle.MetalTexture = MapToMetalTexture(Handle);
    Handle.bIsValid = (Handle.MetalTexture != nullptr);
    
    return Handle;
}

FZeroCopyTextureHandle FIOSZeroCopyBridge::CreateSharedBuffer(uint32 Width, uint32 Height, uint32 PixelFormat)
{
    FZeroCopyTextureHandle Handle;
    
    // Create IOSurface-backed pixel buffer for zero-copy sharing
    CVPixelBufferRef PixelBuffer = CreateIOSurfaceBackedPixelBuffer(Width, Height, PixelFormat);
    
    if (!PixelBuffer)
    {
        return Handle;
    }
    
    Handle.PixelBufferHandle = (void*)PixelBuffer;
    Handle.Width = Width;
    Handle.Height = Height;
    Handle.PixelFormat = PixelFormat;
    
    // Map to Metal texture
    Handle.MetalTexture = MapToMetalTexture(Handle);
    Handle.bIsValid = (Handle.MetalTexture != nullptr);
    
    return Handle;
}

void* FIOSZeroCopyBridge::MapToMetalTexture(FZeroCopyTextureHandle& Handle)
{
    if (!Handle.PixelBufferHandle)
    {
        return nullptr;
    }
    
    CVPixelBufferRef PixelBuffer = (CVPixelBufferRef)Handle.PixelBufferHandle;
    
    // Get IOSurface from pixel buffer (zero-copy backing)
    IOSurfaceRef Surface = CVPixelBufferGetIOSurface(PixelBuffer);
    if (!Surface)
    {
        return nullptr;
    }
    
    // Get Metal device (using default device)
    id<MTLDevice> Device = MTLCreateSystemDefaultDevice();
    if (!Device)
    {
        return nullptr;
    }
    
    // Create Metal texture descriptor
    MTLTextureDescriptor* TextureDescriptor = [MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatBGRA8Unorm
                                                                                                  width:Handle.Width
                                                                                                 height:Handle.Height
                                                                                              mipmapped:NO];
    TextureDescriptor.usage = MTLTextureUsageShaderRead | MTLTextureUsageShaderWrite;
    TextureDescriptor.storageMode = MTLStorageModeShared;
    
    // Create Metal texture from IOSurface (zero-copy mapping)
    id<MTLTexture> MetalTexture = [Device newTextureWithDescriptor:TextureDescriptor
                                                          iosurface:Surface
                                                              plane:0];
    
    // Return as void* (caller must cast back to id<MTLTexture>)
    return (__bridge_retained void*)MetalTexture;
}

void FIOSZeroCopyBridge::ReleaseHandle(FZeroCopyTextureHandle& Handle)
{
    if (Handle.MetalTexture)
    {
        // Release Metal texture
        id<MTLTexture> MetalTexture = (__bridge_transfer id<MTLTexture>)Handle.MetalTexture;
        MetalTexture = nil;
        Handle.MetalTexture = nullptr;
    }
    
    if (Handle.PixelBufferHandle)
    {
        // Release pixel buffer
        CVPixelBufferRef PixelBuffer = (CVPixelBufferRef)Handle.PixelBufferHandle;
        CVPixelBufferRelease(PixelBuffer);
        Handle.PixelBufferHandle = nullptr;
    }
    
    Handle.bIsValid = false;
}

bool FIOSZeroCopyBridge::LockPixelBuffer(FZeroCopyTextureHandle& Handle, void** OutBaseAddress, size_t* OutBytesPerRow)
{
    if (!Handle.PixelBufferHandle)
    {
        return false;
    }
    
    CVPixelBufferRef PixelBuffer = (CVPixelBufferRef)Handle.PixelBufferHandle;
    
    // Lock base address for CPU access
    CVPixelBufferLockBaseAddress(PixelBuffer, 0);
    
    if (OutBaseAddress)
    {
        *OutBaseAddress = CVPixelBufferGetBaseAddress(PixelBuffer);
    }
    
    if (OutBytesPerRow)
    {
        *OutBytesPerRow = CVPixelBufferGetBytesPerRow(PixelBuffer);
    }
    
    return true;
}

void FIOSZeroCopyBridge::UnlockPixelBuffer(FZeroCopyTextureHandle& Handle)
{
    if (!Handle.PixelBufferHandle)
    {
        return;
    }
    
    CVPixelBufferRef PixelBuffer = (CVPixelBufferRef)Handle.PixelBufferHandle;
    CVPixelBufferUnlockBaseAddress(PixelBuffer, 0);
}

bool FIOSZeroCopyBridge::IsZeroCopySupported()
{
    // Zero-copy is supported on all iOS devices with Metal support (iOS 8+)
    // Since we target iOS 16+, this is always true
    return true;
}

CVPixelBufferRef FIOSZeroCopyBridge::CreateIOSurfaceBackedPixelBuffer(uint32 Width, uint32 Height, uint32 PixelFormat)
{
    // Create pixel buffer attributes for IOSurface backing
    NSDictionary* PixelBufferAttributes = @{
        (id)kCVPixelBufferIOSurfacePropertiesKey: @{},  // Enable IOSurface backing
        (id)kCVPixelBufferMetalCompatibilityKey: @YES,   // Enable Metal compatibility
        (id)kCVPixelBufferWidthKey: @(Width),
        (id)kCVPixelBufferHeightKey: @(Height),
        (id)kCVPixelBufferPixelFormatTypeKey: @(PixelFormat)
    };
    
    CVPixelBufferRef PixelBuffer = nullptr;
    CVReturn Result = CVPixelBufferCreate(kCFAllocatorDefault,
                                         Width,
                                         Height,
                                         PixelFormat,
                                         (__bridge CFDictionaryRef)PixelBufferAttributes,
                                         &PixelBuffer);
    
    if (Result != kCVReturnSuccess)
    {
        return nullptr;
    }
    
    return PixelBuffer;
}

uint32 FIOSZeroCopyBridge::GetMetalPixelFormat(uint32 CVPixelFormat)
{
    // Map CV pixel format to Metal pixel format
    switch (CVPixelFormat)
    {
        case kCVPixelFormatType_32BGRA:
            return static_cast<uint32>(MTLPixelFormatBGRA8Unorm);
        case kCVPixelFormatType_32RGBA:
            return static_cast<uint32>(MTLPixelFormatRGBA8Unorm);
        default:
            return static_cast<uint32>(MTLPixelFormatBGRA8Unorm);
    }
}

float FIOSZeroCopyBridge::QueryThermalState()
{
    NSProcessInfo *processInfo = [NSProcessInfo processInfo];
    NSProcessInfoThermalState thermalState = processInfo.thermalState;
    
    switch (thermalState) {
        case NSProcessInfoThermalStateNominal:  return 50.0f;  // Cool
        case NSProcessInfoThermalStateFair:     return 70.0f;  // Warm
        case NSProcessInfoThermalStateSerious:  return 85.0f;  // Hot
        case NSProcessInfoThermalStateCritical: return 95.0f;  // Emergency
        default: return 50.0f;
    }
}

float FIOSZeroCopyBridge::QueryBatteryLevel()
{
    [[UIDevice currentDevice] setBatteryMonitoringEnabled:YES];
    float level = [[UIDevice currentDevice] batteryLevel];
    return (level < 0.0f) ? 100.0f : level * 100.0f;  // -1 means unknown, default to 100%
}

#endif // PLATFORM_IOS
