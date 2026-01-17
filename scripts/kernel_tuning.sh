#!/bin/bash
# Unified Kernel Tuning Script for Ouroboros
# Auto-detects hardware and applies optimal settings

set -e

detect_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        echo "nvidia"
    elif command -v rocm-smi &> /dev/null; then
        echo "amd"
    elif [ -d "/sys/class/drm/card0/device/driver" ]; then
        driver=$(basename $(readlink /sys/class/drm/card0/device/driver))
        echo "$driver"
    else
        echo "none"
    fi
}

detect_cpu() {
    if grep -q "GenuineIntel" /proc/cpuinfo; then
        echo "intel"
    elif grep -q "AuthenticAMD" /proc/cpuinfo; then
        echo "amd"
    else
        echo "unknown"
    fi
}

apply_nvidia_optimizations() {
    echo "Applying NVIDIA optimizations..."
    # Lock graphics clock for consistent performance
    sudo nvidia-smi -lgc 1500,1500 2>/dev/null || true
    # Enable GPU firmware if available
    if [ -f /etc/modprobe.d/nvidia.conf ]; then
        grep -q "NVreg_EnableGpuFirmware" /etc/modprobe.d/nvidia.conf || \
            echo "options nvidia NVreg_EnableGpuFirmware=1" | sudo tee -a /etc/modprobe.d/nvidia.conf
    fi
}

apply_intel_optimizations() {
    echo "Applying Intel optimizations..."
    export MKL_ENABLE_INSTRUCTIONS=AVX512
    export OMP_NUM_THREADS=$(nproc)
}

apply_amd_cpu_optimizations() {
    echo "Applying AMD CPU optimizations..."
    # Set performance EPP
    for cpu in /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference; do
        echo "performance" | sudo tee "$cpu" 2>/dev/null || true
    done
}

main() {
    echo "=== Ouroboros Kernel Tuning Script ==="
    
    GPU=$(detect_gpu)
    CPU=$(detect_cpu)
    
    echo "Detected GPU: $GPU"
    echo "Detected CPU: $CPU"
    
    case $GPU in
        nvidia) apply_nvidia_optimizations ;;
        amd) echo "AMD GPU detected - ROCm optimizations available" ;;
    esac
    
    case $CPU in
        intel) apply_intel_optimizations ;;
        amd) apply_amd_cpu_optimizations ;;
    esac
    
    echo "=== Tuning complete ==="
}

main "$@"
