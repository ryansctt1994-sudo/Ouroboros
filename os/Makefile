# EDEN Daemon Makefile
# Installation and deployment for macOS and Linux

PREFIX ?= /usr/local
BINDIR = $(PREFIX)/bin
SYSTEMD_USER_DIR = $(HOME)/.config/systemd/user
LAUNCHD_DIR = $(HOME)/Library/LaunchAgents
OPENRC_DIR = /etc/init.d

# Detect platform
UNAME_S := $(shell uname -s)

.PHONY: all install uninstall install-systemd install-launchd install-openrc clean help

all: help

help:
	@echo "EDEN Daemon Installation"
	@echo "========================"
	@echo ""
	@echo "Targets:"
	@echo "  install         Install daemon and CLI (auto-detects platform)"
	@echo "  uninstall       Uninstall daemon and CLI"
	@echo "  install-systemd Install systemd user unit (Linux)"
	@echo "  install-launchd Install launchd plist (macOS)"
	@echo "  install-openrc  Install OpenRC script (Linux)"
	@echo "  clean           Remove temporary files"
	@echo ""
	@echo "Platform detected: $(UNAME_S)"

install:
	@echo "Installing EDEN daemon..."
	
	# Create bin directory
	mkdir -p $(BINDIR)
	
	# Install daemon
	cp eden_daemon.py $(BINDIR)/eden-daemon
	chmod +x $(BINDIR)/eden-daemon
	@echo "Installed: $(BINDIR)/eden-daemon"
	
	# Install CLI
	cp eden_cli.py $(BINDIR)/eden
	chmod +x $(BINDIR)/eden
	@echo "Installed: $(BINDIR)/eden"
	
	# Install IPC module
	cp eden_ipc.py $(BINDIR)/eden_ipc.py
	@echo "Installed: $(BINDIR)/eden_ipc.py"
	
	# Platform-specific installation
ifeq ($(UNAME_S),Darwin)
	@echo "Detected macOS, installing launchd plist..."
	$(MAKE) install-launchd
else ifeq ($(UNAME_S),Linux)
	@echo "Detected Linux, installing systemd unit..."
	$(MAKE) install-systemd
endif
	
	@echo ""
	@echo "Installation complete!"
	@echo ""
	@echo "To start the daemon:"
ifeq ($(UNAME_S),Darwin)
	@echo "  launchctl load ~/Library/LaunchAgents/org.ouroboros.eden.plist"
	@echo "  launchctl start org.ouroboros.eden"
else ifeq ($(UNAME_S),Linux)
	@echo "  systemctl --user enable eden.service"
	@echo "  systemctl --user start eden.service"
endif
	@echo ""
	@echo "Or run manually:"
	@echo "  $(BINDIR)/eden-daemon"
	@echo ""
	@echo "Use the CLI:"
	@echo "  $(BINDIR)/eden status"

uninstall:
	@echo "Uninstalling EDEN daemon..."
	
	# Remove binaries
	rm -f $(BINDIR)/eden-daemon
	rm -f $(BINDIR)/eden
	rm -f $(BINDIR)/eden_ipc.py
	@echo "Removed binaries from $(BINDIR)"
	
	# Remove systemd unit
	rm -f $(SYSTEMD_USER_DIR)/eden.service
	@echo "Removed systemd unit (if present)"
	
	# Remove launchd plist
	rm -f $(LAUNCHD_DIR)/org.ouroboros.eden.plist
	@echo "Removed launchd plist (if present)"
	
	@echo "Uninstallation complete!"

install-systemd:
	@echo "Installing systemd user unit..."
	mkdir -p $(SYSTEMD_USER_DIR)
	cp eden.service $(SYSTEMD_USER_DIR)/eden.service
	@echo "Installed: $(SYSTEMD_USER_DIR)/eden.service"
	@echo ""
	@echo "To enable and start:"
	@echo "  systemctl --user daemon-reload"
	@echo "  systemctl --user enable eden.service"
	@echo "  systemctl --user start eden.service"

install-launchd:
	@echo "Installing launchd plist..."
	mkdir -p $(LAUNCHD_DIR)
	cp org.ouroboros.eden.plist $(LAUNCHD_DIR)/org.ouroboros.eden.plist
	@echo "Installed: $(LAUNCHD_DIR)/org.ouroboros.eden.plist"
	@echo ""
	@echo "To load and start:"
	@echo "  launchctl load $(LAUNCHD_DIR)/org.ouroboros.eden.plist"
	@echo "  launchctl start org.ouroboros.eden"

install-openrc:
	@echo "Installing OpenRC script..."
	@echo "Note: This requires root privileges"
	sudo cp openrc/eden $(OPENRC_DIR)/eden
	sudo chmod +x $(OPENRC_DIR)/eden
	@echo "Installed: $(OPENRC_DIR)/eden"
	@echo ""
	@echo "To enable and start:"
	@echo "  sudo rc-update add eden default"
	@echo "  sudo rc-service eden start"

clean:
	@echo "Cleaning temporary files..."
	rm -f *.pyc
	rm -rf __pycache__
	@echo "Clean complete!"
