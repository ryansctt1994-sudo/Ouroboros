# AIOS: Ouroboros — Windows Steam packaging script
# Produces a single-binary PyApp executable for Steam distribution.
#
# Prerequisites:
#   - Rust toolchain (cargo) installed and on PATH
#   - Python 3.11 runtime available
#   - Run from the repository root
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/steam/package_windows.ps1

param(
    [string]$Version = "1.0.0",
    [string]$OutDir  = "dist"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Configuration — replace SteamAppId with the real ID before shipping.
# 480 = Spacewar (Valve Steamworks SDK development test title).
# ---------------------------------------------------------------------------
$env:PYAPP_PROJECT_NAME       = "AIOS-Ouroboros"
$env:PYAPP_PROJECT_VERSION    = $Version
$env:PYAPP_PYTHON_VERSION     = "3.11"
$env:PYAPP_DISTRIBUTION_EMBED = "1"
$SteamAppId                   = "480"
$BinaryName                   = "AIOS-Ouroboros-$Version-windows-x86_64.exe"

Write-Host "=== AIOS Windows Steam Build ===" -ForegroundColor Cyan
Write-Host "Version : $Version"
Write-Host "Output  : $OutDir\$BinaryName"
Write-Host ""

# Ensure output directory exists
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# Install / update pyapp
Write-Host "[1/3] Installing pyapp via cargo ..." -ForegroundColor Yellow
cargo install pyapp --force

# Package
Write-Host "[2/3] Packing single-binary executable ..." -ForegroundColor Yellow
pyapp pack --output "$OutDir\$BinaryName"

# Verify
Write-Host "[3/3] Verifying binary ..." -ForegroundColor Yellow
$size = (Get-Item "$OutDir\$BinaryName").length / 1MB
if ($size -gt 80) {
    Write-Error "Binary exceeds 80 MB limit ($([math]::Round($size,1)) MB). Check for bundled debug symbols."
}

# Write steam_appid.txt next to the binary (required for Steam overlay during dev)
"$SteamAppId" | Out-File -FilePath "$OutDir\steam_appid.txt" -Encoding ASCII -NoNewline

Write-Host ""
Write-Host "=== Build complete ===" -ForegroundColor Green
Write-Host "  $OutDir\$BinaryName  ($([math]::Round($size,1)) MB)"
Write-Host ""
Write-Host "Next step: run 'steamcmd +runscript scripts/steam/steam_build_windows.vdf' to upload to Steam."
