#!/usr/bin/env bash
# AIOS: Ouroboros — macOS Steam packaging script
# Produces a notarised py2app bundle for Steam distribution.
#
# Prerequisites:
#   - Python 3.11 with py2app installed  (pip install py2app)
#   - Apple Developer ID Application certificate in Keychain
#   - APPLE_ID, TEAM_ID, APP_PASSWORD env vars set (see Keychain / CI secrets)
#   - Xcode Command Line Tools installed
#   - Run from the repository root
#
# Usage:
#   bash scripts/steam/package_macos.sh [version]

set -euo pipefail

VERSION="${1:-1.0.0}"
OUT_DIR="dist"
APP_NAME="AIOS-Ouroboros"
BUNDLE_ID="com.aiospandora.ouroboros"
STEAM_APP_ID="480"   # Replace with real AppID before shipping

echo "=== AIOS macOS Steam Build ==="
echo "Version : ${VERSION}"
echo "Output  : ${OUT_DIR}/${APP_NAME}.app"
echo ""

mkdir -p "${OUT_DIR}"

# --- [1/4] Build universal2 py2app bundle ----------------------------------
echo "[1/4] Building py2app bundle (universal2) ..."
python setup.py py2app --arch universal2

# --- [2/4] Code-sign all binaries / frameworks ----------------------------
echo "[2/4] Code-signing ..."
find "${OUT_DIR}/${APP_NAME}.app" -name "*.dylib" -o -name "*.so" | while read -r lib; do
    codesign --force --sign "Developer ID Application: ${TEAM_ID}" \
             --options runtime "${lib}"
done
codesign --force --sign "Developer ID Application: ${TEAM_ID}" \
         --options runtime --entitlements scripts/steam/entitlements.plist \
         "${OUT_DIR}/${APP_NAME}.app"

# --- [3/4] Notarise -------------------------------------------------------
echo "[3/4] Submitting for notarisation (this may take a few minutes) ..."
xcrun notarytool submit \
    "${OUT_DIR}/${APP_NAME}.app" \
    --apple-id  "${APPLE_ID}" \
    --team-id   "${TEAM_ID}" \
    --password  "${APP_PASSWORD}" \
    --wait

xcrun stapler staple "${OUT_DIR}/${APP_NAME}.app"

# --- [4/4] Verify ---------------------------------------------------------
echo "[4/4] Verifying Gatekeeper acceptance ..."
spctl --assess --type exec --verbose "${OUT_DIR}/${APP_NAME}.app"

# Write steam_appid.txt next to the bundle (required during dev)
echo -n "${STEAM_APP_ID}" > "${OUT_DIR}/steam_appid.txt"

echo ""
echo "=== Build complete ==="
echo "  ${OUT_DIR}/${APP_NAME}.app"
echo ""
echo "Next step: run 'steamcmd +runscript scripts/steam/steam_build_macos.vdf' to upload to Steam."
