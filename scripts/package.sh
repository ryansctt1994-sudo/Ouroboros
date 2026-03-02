#!/usr/bin/env bash
# scripts/package.sh
# One-command packaging for The Garden — Win64, Linux, macOS Shipping.
#
# Prerequisites:
#   UE_ROOT  env var pointing to UE 5.4 install, e.g.:
#     Windows: C:\Program Files\Epic Games\UE_5.4
#     Linux:   /opt/UnrealEngine/5.4
#     macOS:   /Users/Shared/Epic\ Games/UE_5.4
#
# Usage:
#   bash scripts/package.sh [version] [platform]
#
#   version   optional, e.g. 0.1.0  (defaults to git describe)
#   platform  optional: Win64 | Linux | Mac | all  (default: all)
#
# Output: dist/Win64/  dist/Linux/  dist/Mac/

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="$REPO_ROOT/ue/The_Garden/The_Garden.uproject"
DIST="$REPO_ROOT/dist"
VERSION="${1:-}"
PLATFORM="${2:-all}"
export BUILD_CONFIG="Shipping"

# --- generate build metadata first ---
bash "$REPO_ROOT/scripts/build/generate-build-metadata.sh" "$VERSION"

# --- resolve UAT path from UE_ROOT ---
if [[ -z "${UE_ROOT:-}" ]]; then
    echo "ERROR: UE_ROOT is not set."
    echo "  Example: export UE_ROOT=/opt/UnrealEngine/5.4"
    exit 1
fi

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || -f "$UE_ROOT/Engine/Build/BatchFiles/RunUAT.bat" ]]; then
    UAT="$UE_ROOT/Engine/Build/BatchFiles/RunUAT.bat"
    UAT_CMD() { cmd.exe /c "\"$UAT\" $*"; }
else
    UAT="$UE_ROOT/Engine/Build/BatchFiles/RunUAT.sh"
    UAT_CMD() { bash "$UAT" "$@"; }
fi

package_platform() {
    local PLAT="$1"
    local OUT="$DIST/$PLAT"
    echo ""
    echo "=== Packaging $PLAT → $OUT ==="
    mkdir -p "$OUT"

    UAT_CMD BuildCookRun \
        -project="$PROJECT" \
        -noP4 \
        -platform="$PLAT" \
        -clientconfig=Shipping \
        -cook \
        -allmaps \
        -build \
        -stage \
        -pak \
        -archive \
        -archivedirectory="$OUT" \
        -compressed \
        -prereqs \
        -nodebuginfo

    echo "=== $PLAT DONE ==="
}

case "$PLATFORM" in
    Win64) package_platform Win64 ;;
    Linux) package_platform Linux ;;
    Mac)   package_platform Mac   ;;
    all)
        package_platform Win64
        package_platform Linux
        package_platform Mac
        ;;
    *)
        echo "Unknown platform: $PLATFORM (valid: Win64 Linux Mac all)"
        exit 1
        ;;
esac

echo ""
echo "All requested platforms packaged."
echo "Output: $DIST"
ls -lh "$DIST" 2>/dev/null || true
