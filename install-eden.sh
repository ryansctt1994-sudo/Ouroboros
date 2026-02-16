#!/bin/bash
#
# EDEN One-Click Installer
# =========================
#
# Installs EDEN AIOS on Ubuntu with GUI dialogs.
#
# Author: AIOSPANDORA Development Team
# License: MIT
# Version: 1.0.0

set -e  # Exit on error

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Installation paths
INSTALL_DIR="$HOME/Ouroboros"
VENV_DIR="$INSTALL_DIR/venv"
SYSTEMD_DIR="$HOME/.config/systemd/user"
DESKTOP_DIR="$HOME/.local/share/applications"

# Check if zenity is available
ZENITY_AVAILABLE=false
if command -v zenity &> /dev/null; then
    ZENITY_AVAILABLE=true
fi

# Dialog wrapper - uses zenity if available, otherwise terminal
show_info() {
    if [ "$ZENITY_AVAILABLE" = true ]; then
        zenity --info --title="EDEN Installer" --text="$1" --width=400 2>/dev/null || true
    else
        echo -e "${GREEN}INFO:${NC} $1"
    fi
}

show_error() {
    if [ "$ZENITY_AVAILABLE" = true ]; then
        zenity --error --title="EDEN Installer" --text="$1" --width=400 2>/dev/null || true
    else
        echo -e "${RED}ERROR:${NC} $1"
    fi
}

show_warning() {
    if [ "$ZENITY_AVAILABLE" = true ]; then
        zenity --warning --title="EDEN Installer" --text="$1" --width=400 2>/dev/null || true
    else
        echo -e "${YELLOW}WARNING:${NC} $1"
    fi
}

ask_question() {
    if [ "$ZENITY_AVAILABLE" = true ]; then
        zenity --question --title="EDEN Installer" --text="$1" --width=400 2>/dev/null
        return $?
    else
        echo -n -e "${YELLOW}$1${NC} (y/n): "
        read -r response
        [[ "$response" =~ ^[Yy]$ ]]
    fi
}

show_progress() {
    if [ "$ZENITY_AVAILABLE" = true ]; then
        # Note: Progress bars require more complex handling
        echo "# $1"
    else
        echo -e "${GREEN}▸${NC} $1"
    fi
}

# Welcome dialog
echo ""
echo "╔════════════════════════════════════════╗"
echo "║   EDEN AIOS - One-Click Installer      ║"
echo "║   Cosmic Consciousness OS              ║"
echo "╚════════════════════════════════════════╝"
echo ""

if ! ask_question "Welcome to EDEN AIOS installer!\n\nThis will install EDEN on your system.\n\nDo you want to continue?"; then
    echo "Installation cancelled."
    exit 0
fi

# Check prerequisites
show_progress "Checking prerequisites..."

MISSING_PACKAGES=()

check_command() {
    if ! command -v "$1" &> /dev/null; then
        MISSING_PACKAGES+=("$2")
        return 1
    fi
    return 0
}

check_command "python3" "python3"
check_command "pip3" "python3-pip"
check_command "git" "git"
check_command "cargo" "cargo"
check_command "gcc" "build-essential"

# Check for zenity (optional but recommended)
if ! command -v zenity &> /dev/null; then
    MISSING_PACKAGES+=("zenity")
fi

# Offer to install missing packages
if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    PACKAGE_LIST=$(IFS=" "; echo "${MISSING_PACKAGES[*]}")
    
    if ask_question "Missing packages: $PACKAGE_LIST\n\nDo you want to install them now?"; then
        show_progress "Installing missing packages..."
        sudo apt update
        sudo apt install -y ${MISSING_PACKAGES[@]}
        
        # Re-check zenity availability
        if command -v zenity &> /dev/null; then
            ZENITY_AVAILABLE=true
        fi
    else
        show_error "Required packages are missing. Installation cannot continue."
        exit 1
    fi
fi

# Clone or update repository
show_progress "Setting up Ouroboros repository..."

if [ -d "$INSTALL_DIR/.git" ]; then
    show_info "Ouroboros directory exists. Updating..."
    cd "$INSTALL_DIR"
    git fetch origin
    git pull origin main || git pull origin master || true
else
    show_info "Cloning Ouroboros repository..."
    git clone https://github.com/AIOSPANDORA/Ouroboros.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Check for Rust engine and build if exists
RUST_ENGINE_PATH="$INSTALL_DIR/ELPIS/METACUBE/forge_standalone/Cargo.toml"

if [ -f "$RUST_ENGINE_PATH" ]; then
    if ask_question "Rust engine found.\n\nDo you want to build it? (This may take several minutes)"; then
        show_progress "Building Rust engine..."
        
        cd "$INSTALL_DIR/ELPIS/METACUBE/forge_standalone"
        
        if [ "$ZENITY_AVAILABLE" = true ]; then
            (cargo build --release 2>&1 | \
                zenity --progress --title="Building Rust Engine" \
                --text="Compiling Rust components..." --pulsate --auto-close 2>/dev/null) || \
            cargo build --release
        else
            cargo build --release
        fi
        
        cd "$INSTALL_DIR"
        show_info "Rust engine built successfully!"
    fi
fi

# Create Python virtual environment
show_progress "Creating Python virtual environment..."

if [ -d "$VENV_DIR" ]; then
    show_warning "Virtual environment already exists. Skipping creation."
else
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install Python dependencies
show_progress "Installing Python dependencies..."

# Upgrade pip
pip install --upgrade pip

# Install core dependencies
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    pip install -r "$INSTALL_DIR/requirements.txt"
fi

# Install GTK and llama-cpp-python
show_info "Installing additional dependencies (PyGObject, llama-cpp-python)..."
pip install pygobject llama-cpp-python || show_warning "Some packages failed to install. This may be okay."

# Optionally install EDEN-ECS
if ask_question "Do you want to install EDEN-ECS?\n\n(This enables real consciousness simulation, but is optional)"; then
    show_progress "Installing EDEN-ECS..."
    pip install "git+https://github.com/AIOSPANDORA/EDEN-ECS.git" || show_warning "EDEN-ECS installation failed. Daemon will use mock mode."
fi

# Install systemd user service
show_progress "Installing systemd service..."

mkdir -p "$SYSTEMD_DIR"

cat > "$SYSTEMD_DIR/eden.service" << EOF
[Unit]
Description=EDEN Daemon - Cosmic Consciousness OS
After=network.target

[Service]
Type=simple
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/os/eden_daemon.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable eden

show_info "Systemd service installed and enabled!"

# Create desktop entry
show_progress "Installing desktop entry..."

mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_DIR/eden-chat.desktop" << EOF
[Desktop Entry]
Name=EDEN Chat
Comment=EDEN AI Assistant
Exec=$VENV_DIR/bin/python $INSTALL_DIR/os/eden_chat.py
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;
EOF

chmod +x "$DESKTOP_DIR/eden-chat.desktop"

show_info "Desktop entry created!"

# Optional: Start service and launch chat
if ask_question "Installation complete!\n\nDo you want to start the EDEN daemon now?"; then
    show_progress "Starting EDEN daemon..."
    systemctl --user start eden
    sleep 2
    
    if ask_question "Daemon started!\n\nDo you want to launch EDEN Chat?"; then
        "$VENV_DIR/bin/python" "$INSTALL_DIR/os/eden_chat.py" &
    fi
fi

# Final success dialog
show_info "╔════════════════════════════════════════╗
║   EDEN Installation Complete! ✓        ║
╚════════════════════════════════════════╝

Installed to: $INSTALL_DIR

Available commands:
  • systemctl --user start eden
  • systemctl --user stop eden
  • systemctl --user status eden
  • $INSTALL_DIR/os/eden_cli.py status
  • $INSTALL_DIR/os/eden_cli.py chat \"message\"

Launch GUI:
  • From application menu: EDEN Chat
  • Or run: $VENV_DIR/bin/python $INSTALL_DIR/os/eden_chat.py

Enjoy EDEN! 🌌"

exit 0
