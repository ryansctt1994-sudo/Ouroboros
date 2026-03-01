#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# ABRAXIS Cathedral-OS — .deb package builder
# SPDX-License-Identifier: MIT
# Copyright (c) 2025-2026 The Ouroboros Foundation
#
# Requirements:  dpkg-deb, fakeroot, cargo (Rust toolchain)
#
# Usage:
#   bash ABRAXIS/packaging/build_deb.sh [VERSION]
#
# Produces:
#   dist/ouroboros-cathedral_<VERSION>_amd64.deb
# ──────────────────────────────────────────────────────────────────
set -euo pipefail

VERSION="${1:-0.1.0}"
PKG="ouroboros-cathedral"
ARCH="amd64"
DEB_DIR="$(pwd)/dist/${PKG}_${VERSION}_${ARCH}"
DIST_DIR="$(pwd)/dist"

echo "==> Building ${PKG} v${VERSION} (.deb)"

# ── 1. Build Rust release binary ─────────────────────────────────
echo "==> Compiling Rust binary..."
cargo build --release --bin ouroboros-cathedral
BINARY="$(pwd)/target/release/ouroboros-cathedral"

# ── 2. Build DEBIAN control structure ────────────────────────────
rm -rf "${DEB_DIR}"
mkdir -p "${DEB_DIR}/DEBIAN"
mkdir -p "${DEB_DIR}/usr/bin"
mkdir -p "${DEB_DIR}/usr/lib/ouroboros-cathedral"
mkdir -p "${DEB_DIR}/usr/share/doc/${PKG}"
mkdir -p "${DEB_DIR}/usr/share/${PKG}/docs"
mkdir -p "${DEB_DIR}/lib/systemd/system"

# ── 3. Copy files ─────────────────────────────────────────────────
cp "${BINARY}"                                    "${DEB_DIR}/usr/bin/ouroboros-cathedral"
cp -r ABRAXIS/                                    "${DEB_DIR}/usr/lib/ouroboros-cathedral/ABRAXIS"
cp -r EDEN-ECS/                                   "${DEB_DIR}/usr/lib/ouroboros-cathedral/EDEN-ECS"
cp -r python-bridge/                              "${DEB_DIR}/usr/lib/ouroboros-cathedral/python-bridge"
cp docs/observer-dashboard.html                   "${DEB_DIR}/usr/share/${PKG}/docs/"
cp LICENSE                                        "${DEB_DIR}/usr/share/doc/${PKG}/copyright"
cp README.md                                      "${DEB_DIR}/usr/share/doc/${PKG}/README.md" 2>/dev/null || true

# ── 4. Systemd unit ───────────────────────────────────────────────
cat > "${DEB_DIR}/lib/systemd/system/ouroboros-cathedral.service" <<'UNIT'
[Unit]
Description=ABRAXIS Cathedral-OS — Phase H Voice-to-Gnosis Dashboard
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/ouroboros-cathedral --mode dashboard --host 0.0.0.0 --port 8765
Restart=on-failure
RestartSec=5s
Environment=RUST_LOG=ouroboros_cathedral=info

[Install]
WantedBy=multi-user.target
UNIT

# ── 5. DEBIAN/control ─────────────────────────────────────────────
cat > "${DEB_DIR}/DEBIAN/control" <<CONTROL
Package: ${PKG}
Version: ${VERSION}
Section: misc
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.10)
Recommends: python3-websockets
Maintainer: The Ouroboros Foundation <https://github.com/AIOSPANDORA/Ouroboros>
Description: ABRAXIS Cathedral-OS — Phase H/I runtime
 Provides the Phase H multi-user WebSocket voice-to-gnosis dashboard
 and the Phase I autonomous node runtime (self-healing, spore factory,
 governance thresholds) for the AIOSPANDORA/Ouroboros project.
Homepage: https://github.com/AIOSPANDORA/Ouroboros
CONTROL

# ── 6. DEBIAN/postinst ────────────────────────────────────────────
cat > "${DEB_DIR}/DEBIAN/postinst" <<'POST'
#!/bin/sh
set -e
systemctl daemon-reload || true
echo "ouroboros-cathedral installed. Enable and start with:"
echo "  systemctl enable --now ouroboros-cathedral"
POST
chmod 0755 "${DEB_DIR}/DEBIAN/postinst"

# ── 7. Build .deb ─────────────────────────────────────────────────
mkdir -p "${DIST_DIR}"
fakeroot dpkg-deb --build "${DEB_DIR}" "${DIST_DIR}/${PKG}_${VERSION}_${ARCH}.deb"

echo "==> Package built: ${DIST_DIR}/${PKG}_${VERSION}_${ARCH}.deb"
