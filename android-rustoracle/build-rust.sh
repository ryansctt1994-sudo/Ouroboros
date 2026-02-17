#!/bin/bash
# Build script for Rust Oracle Android library

set -e

echo "Building Rust Oracle for Android..."

# Check if cargo-ndk is installed
if ! command -v cargo-ndk &> /dev/null; then
    echo "cargo-ndk not found. Installing..."
    cargo install cargo-ndk
fi

# Check if Android targets are installed
echo "Checking Rust Android targets..."
rustup target add aarch64-linux-android 2>/dev/null || true
rustup target add armv7-linux-androideabi 2>/dev/null || true
rustup target add i686-linux-android 2>/dev/null || true
rustup target add x86_64-linux-android 2>/dev/null || true

# Build for all Android architectures
cd rustoracle

echo "Building for arm64-v8a, armeabi-v7a, x86, x86_64..."
cargo ndk \
    -t arm64-v8a \
    -t armeabi-v7a \
    -t x86 \
    -t x86_64 \
    -o ../app/src/main/jniLibs \
    build --release

echo "Rust Oracle build complete!"
echo "Libraries installed to app/src/main/jniLibs/"

ls -lh ../app/src/main/jniLibs/*/librustoracle.so
