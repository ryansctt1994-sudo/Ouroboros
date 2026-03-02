# ──────────────────────────────────────────────────────────────────
# ABRAXIS / Cathedral-OS — Multi-stage Docker image
# ──────────────────────────────────────────────────────────────────
# Stage 1: Rust builder (ouroboros-cathedral binary)
# Stage 2: Python runtime (Phase H/I + EDEN-ECS bridge)
# Stage 3: Final minimal image
#
# SPDX-License-Identifier: MIT
# Copyright (c) 2025-2026 The Ouroboros Foundation

# ── Stage 1: Rust build ──────────────────────────────────────────
FROM rust:1.77-slim-bookworm AS rust-builder

WORKDIR /build

# Cache dependency compilation
COPY Cargo.toml Cargo.lock* ./
COPY ELPIS/METACUBE/forge_standalone/Cargo.toml \
     ELPIS/METACUBE/forge_standalone/
RUN mkdir -p src ELPIS/METACUBE/forge_standalone/src && \
    echo 'fn main(){}' > src/main.rs && \
    echo '' > ELPIS/METACUBE/forge_standalone/src/lib.rs && \
    cargo build --release --bin ouroboros-cathedral 2>/dev/null || true && \
    rm -f target/release/ouroboros-cathedral

# Real build
COPY src/ src/
COPY ELPIS/METACUBE/forge_standalone/src/ ELPIS/METACUBE/forge_standalone/src/
RUN cargo build --release --bin ouroboros-cathedral

# ── Stage 2: Python dependency installation ──────────────────────
FROM python:3.11-slim-bookworm AS py-builder

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt && \
    pip install --no-cache-dir --prefix=/install websockets

# ── Stage 3: Final image ─────────────────────────────────────────
FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.title="ABRAXIS Cathedral-OS"
LABEL org.opencontainers.image.description="Phase H/I autonomous nodes + voice-to-gnosis dashboard"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/AIOSPANDORA/Ouroboros"

WORKDIR /app

# Copy Python deps
COPY --from=py-builder /install /usr/local

# Copy Rust binary
COPY --from=rust-builder /build/target/release/ouroboros-cathedral /usr/local/bin/ouroboros-cathedral

# Copy ABRAXIS Python package and related modules
COPY ABRAXIS/            ./ABRAXIS/
COPY eden_ecs/           ./eden_ecs/
COPY python-bridge/      ./python-bridge/
COPY src/                ./src/
COPY docs/observer-dashboard.html ./docs/observer-dashboard.html

# Expose WebSocket port (Phase H)
EXPOSE 8765

# Default: run Phase H dashboard
ENV PYTHONUNBUFFERED=1
CMD ["ouroboros-cathedral", "--mode", "dashboard", "--host", "0.0.0.0", "--port", "8765"]
