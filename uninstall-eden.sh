#!/bin/bash
#
# EDEN Uninstaller
# ================
#
# Removes EDEN AIOS installation.
#
# Author: AIOSPANDORA Development Team
# License: MIT
# Version: 1.0.0

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Installation paths
INSTALL_DIR="$HOME/Ouroboros"
SYSTEMD_DIR="$HOME/.config/systemd/user"
DESKTOP_DIR="$HOME/.local/share/applications"

# Check if zenity is available
ZENITY_AVAILABLE=false
if command -v zenity &> /dev/null; then
    ZENITY_AVAILABLE=true
fi

show_info() {
    if [ "$ZENITY_AVAILABLE" = true ]; then
        zenity --info --title="EDEN Uninstaller" --text="$1" --width=400 2>/dev/null || true
    else
        echo -e "${GREEN}INFO:${NC} $1"
    fi
}

show_warning() {
    if [ "$ZENITY_AVAILABLE" = true ]; then
        zenity --warning --title="EDEN Uninstaller" --text="$1" --width=400 2>/dev/null || true
    else
        echo -e "${YELLOW}WARNING:${NC} $1"
    fi
}

ask_question() {
    if [ "$ZENITY_AVAILABLE" = true ]; then
        zenity --question --title="EDEN Uninstaller" --text="$1" --width=400 2>/dev/null
        return $?
    else
        echo -n -e "${YELLOW}$1${NC} (y/n): "
        read -r response
        [[ "$response" =~ ^[Yy]$ ]]
    fi
}

# Welcome
echo ""
echo "╔════════════════════════════════════════╗"
echo "║   EDEN AIOS - Uninstaller              ║"
echo "╚════════════════════════════════════════╝"
echo ""

if ! ask_question "This will remove EDEN from your system.\n\nAre you sure you want to continue?"; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Stop and disable service
if systemctl --user is-active --quiet eden 2>/dev/null; then
    show_info "Stopping EDEN daemon..."
    systemctl --user stop eden || true
fi

if systemctl --user is-enabled --quiet eden 2>/dev/null; then
    show_info "Disabling EDEN service..."
    systemctl --user disable eden || true
fi

# Remove systemd service file
if [ -f "$SYSTEMD_DIR/eden.service" ]; then
    show_info "Removing systemd service..."
    rm -f "$SYSTEMD_DIR/eden.service"
    systemctl --user daemon-reload
fi

# Remove desktop entry
if [ -f "$DESKTOP_DIR/eden-chat.desktop" ]; then
    show_info "Removing desktop entry..."
    rm -f "$DESKTOP_DIR/eden-chat.desktop"
fi

# Remove socket file if exists
SOCKET_PATH="/tmp/eden.sock"
if [ -S "$SOCKET_PATH" ]; then
    show_info "Removing socket file..."
    rm -f "$SOCKET_PATH"
fi

# Remove PID file if exists
PID_FILE="$HOME/.local/share/eden/eden.pid"
if [ -f "$PID_FILE" ]; then
    rm -f "$PID_FILE"
fi

# Optionally remove source directory
if [ -d "$INSTALL_DIR" ]; then
    if ask_question "Do you want to remove the source directory?\n\n$INSTALL_DIR\n\n(This will delete all EDEN files)"; then
        show_info "Removing source directory..."
        rm -rf "$INSTALL_DIR"
    else
        show_info "Source directory kept at: $INSTALL_DIR"
    fi
fi

show_info "╔════════════════════════════════════════╗
║   EDEN Uninstalled Successfully        ║
╚════════════════════════════════════════╝

The following were removed:
  • Systemd service
  • Desktop entry
  • Runtime files

Thank you for using EDEN! 🌌"

exit 0
