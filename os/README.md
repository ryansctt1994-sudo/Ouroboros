# EDEN Daemon System

Background service for the EDEN Mycelial Engine with integrated AI assistant, sandboxed code execution, and patch management.

## Overview

The EDEN daemon runs the ECS world from `python-bridge/eden_ecs/` as a background service, enabling:

- **Continuous simulation** of consciousness evolution and mycelial synchronization
- **AI Assistant** - Local GGUF model integration via llama-cpp-python
- **Sandboxed code execution** - Secure Python/shell execution via bubblewrap
- **Patch management** - Apply unified diffs with dry-run support
- **IPC control** via Unix domain socket (`/tmp/eden.sock`)
- **Cross-platform support** for macOS and Linux
- **Multiple init systems**: systemd, launchd, OpenRC, or manual execution

## Prerequisites

- **Python 3.8+** (tested with 3.8, 3.9, 3.10, 3.11, 3.12)
- **EDEN ECS** (from `python-bridge/eden_ecs/`) - optional, daemon will work with mock world if unavailable
- **Rust ForgeEngine** (optional) - for consensus and synchronization

### Optional Dependencies

For AI features:
- **llama-cpp-python** - `pip install llama-cpp-python`
- **GGUF model file** - Place in `~/.local/eden/models/` (e.g., DeepSeek 8B or similar)

For secure sandboxing:
- **bubblewrap** - `apt-get install bubblewrap` (Ubuntu/Debian) or `dnf install bubblewrap` (Fedora/RHEL)
- **patch** - Usually pre-installed on most systems

## Quick Start

### 1. Manual Execution (Development)

Run the daemon directly in foreground mode:

```bash
cd os/
python3 eden_daemon.py
```

In another terminal, use the CLI:

```bash
python3 eden_cli.py status
python3 eden_cli.py start
python3 eden_cli.py entities
```

### 2. Installation

Install the daemon and CLI to system paths:

```bash
cd os/
make install
```

This installs:
- `eden-daemon` to `/usr/local/bin/`
- `eden` CLI to `/usr/local/bin/`
- Platform-specific init files (systemd on Linux, launchd on macOS)

Then start the daemon:

**macOS (launchd):**
```bash
launchctl load ~/Library/LaunchAgents/org.ouroboros.eden.plist
launchctl start org.ouroboros.eden
```

**Linux (systemd):**
```bash
systemctl --user enable eden.service
systemctl --user start eden.service
```

**Linux (OpenRC):**
```bash
sudo make install-openrc
sudo rc-update add eden default
sudo rc-service eden start
```

## CLI Usage

Once the daemon is running, use the `eden` CLI to control it:

### Core Commands

```bash
# Show daemon status
eden status

# Start the tick loop (continuous simulation)
eden start

# Stop the tick loop
eden stop

# Run a single tick
eden step

# List all entities
eden entities

# Show detailed entity info (7D consciousness, phase, gamma)
eden entity <entity-id>

# Show network graph topology
eden graph

# Show network metrics (mean gamma, coherence, consensus)
eden metrics

# Shut down the daemon
eden shutdown

# Show help
eden help
```

### AI Assistant Commands

```bash
# Chat with the AI assistant
eden chat "Hello EDEN"
eden chat "Explain the mycelial synchronization system"

# Note: Requires llama-cpp-python and a GGUF model file
# If not available, returns error message with installation instructions
```

### Sandbox Execution Commands

```bash
# Execute Python code in sandbox
eden execute "print('Hello, World!')"
eden execute "import sys; print(sys.version)"

# Execute shell commands in sandbox
eden execute "echo 'test'" --language shell

# Note: Uses bubblewrap for secure sandboxing on Linux
# Falls back to basic subprocess execution if bubblewrap not available
```

### Patch Management Commands

```bash
# Test applying a patch (dry-run)
eden patch changes.patch --dry-run

# Apply a patch for real
eden patch changes.patch

# Note: Uses the 'patch' command with unified diff format
```

## Architecture

```
┌─────────────────┐
│  eden_daemon.py │  ──►  Unix socket (/tmp/eden.sock)  ◄──  eden_cli.py
│                 │              │
│  ECS World      │         JSON protocol
│  - Entities     │
│  - Systems      │
│  - Components   │
└─────────────────┘
```

### Components

- **`eden_daemon.py`** - Main daemon service
  - Initializes ECS world with 8 AI agent entities
  - Adds `ConsciousnessSystem` and `MycelialSyncSystem`
  - Runs tick loop at 60 Hz when started
  - Handles JSON-RPC requests over Unix socket
  - Thread-safe entity/system access
  - Integrates AI, sandbox, and patch manager services

- **`eden_ai.py`** - AI service
  - Loads GGUF models via llama-cpp-python (CPU-only)
  - Generates responses to chat messages
  - Searches vectors.json for code context
  - Graceful degradation when model not available

- **`eden_sandbox.py`** - Sandboxed code execution
  - Uses bubblewrap for secure sandboxing on Linux
  - Falls back to subprocess with timeout if bwrap unavailable
  - Supports Python and shell script execution
  - 5-second timeout by default

- **`eden_patch.py`** - Patch manager
  - Applies unified diffs using the `patch` command
  - Supports dry-run mode for testing
  - Can restart EDEN systemd service after patching

- **`eden_cli.py`** - Command-line client
  - Connects to daemon socket
  - Sends JSON-RPC requests
  - Pretty-prints results
  - Supports all core, AI, sandbox, and patch commands

- **`eden_ipc.py`** - IPC protocol definition
  - JSON-RPC request/response serialization
  - Socket path and PID file paths

- **`eden.service`** / **`eden-ai.service`** - systemd user units
- **`org.ouroboros.eden.plist`** - launchd plist for macOS
- **`openrc/eden`** - OpenRC init script
- **`Dockerfile.ai`** - Optional Docker container with AI runtime
- **`Makefile`** - Installation targets

## IPC Protocol Reference

The daemon uses a JSON-RPC-like protocol over Unix domain socket.

### Request Format

```json
{"method": "get_status", "id": 1}
{"method": "get_entity", "id": 2, "params": {"entity_id": "abc-123"}}
```

Messages are newline-delimited JSON.

### Response Format

**Success:**
```json
{"id": 1, "result": {"running": true, "tick": 42, ...}}
```

**Error:**
```json
{"id": 1, "error": {"code": -1, "message": "Method not found"}}
```

### Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `get_status` | - | Daemon status (running, tick count, consensus, gamma) |
| `get_entities` | - | List all entities with phase/gamma/coherence |
| `get_entity` | `entity_id` | Full entity details (7D consciousness, hyphal node) |
| `get_graph` | - | Network graph (nodes + edges) |
| `get_metrics` | - | Network metrics (mean gamma, coherence, consensus) |
| `start` | - | Start tick loop |
| `stop` | - | Stop tick loop |
| `step` | - | Run single tick |
| `chat` | `message` | Send message to AI assistant, returns response |
| `execute_code` | `code`, `language` | Execute code in sandbox, returns output |
| `apply_patch` | `diff`, `dry_run` | Apply unified diff, returns success status |
| `shutdown` | - | Gracefully shut down daemon |

## Graceful Degradation

The daemon is designed to work even if optional components are unavailable:

1. **No EDEN ECS**: Uses a **mock world** with simulated entities
2. **No MycelialSyncSystem**: Runs with just `ConsciousnessSystem`
3. **No llama-cpp-python**: AI features return helpful error messages with installation instructions
4. **No AI model file**: Chat requests return error explaining where to place model file
5. **No bubblewrap**: Sandbox falls back to basic subprocess (with warning about reduced security)
6. **No patch command**: Patch management returns error if `patch` utility not installed

This allows testing and using the daemon even without all dependencies installed.

## Logging

Logs are written to:
- **macOS:** `~/Library/Logs/eden.log`
- **Linux:** `~/.local/share/eden/eden.log`
- **Foreground mode:** stdout

## Files and Paths

| File | Path | Description |
|------|------|-------------|
| Socket | `/tmp/eden.sock` | Unix domain socket for IPC |
| PID file | `~/Library/Application Support/eden/eden.pid` (macOS)<br>`~/.local/share/eden/eden.pid` (Linux) | Process ID file |
| Logs | `~/Library/Logs/eden.log` (macOS)<br>`~/.local/share/eden/eden.log` (Linux) | Daemon logs |

## Troubleshooting

### Daemon won't start

**Check if it's already running:**
```bash
eden status
```

**Check logs:**
```bash
# macOS
tail -f ~/Library/Logs/eden.log

# Linux
tail -f ~/.local/share/eden/eden.log
```

**Kill stale processes:**
```bash
# Find PID
ps aux | grep eden_daemon

# Kill process
kill <PID>

# Remove stale socket
rm /tmp/eden.sock
```

### "EDEN daemon is not running" error

The daemon is not running. Start it:

```bash
# Foreground (for debugging)
python3 os/eden_daemon.py

# Background (with init system)
systemctl --user start eden.service  # Linux
launchctl start org.ouroboros.eden   # macOS
```

### "Connection refused" error

The socket file exists but the daemon is not listening. Remove the stale socket:

```bash
rm /tmp/eden.sock
python3 os/eden_daemon.py
```

### Import errors

If you get errors about missing modules:

1. Make sure `python-bridge/` is in the parent directory
2. Or set `PYTHONPATH`:
   ```bash
   export PYTHONPATH=/path/to/Ouroboros/python-bridge:$PYTHONPATH
   python3 os/eden_daemon.py
   ```

### Graceful shutdown not working

Send SIGTERM:
```bash
kill -TERM $(cat ~/.local/share/eden/eden.pid)
```

Or force kill:
```bash
kill -9 $(cat ~/.local/share/eden/eden.pid)
rm /tmp/eden.sock
```

## Development

### Setting Up the AI Assistant

To use the AI chat feature:

1. **Install llama-cpp-python:**
   ```bash
   pip install llama-cpp-python
   ```

2. **Download a GGUF model:**
   - Download a compatible GGUF model (e.g., DeepSeek 8B, Llama 2, etc.)
   - Recommended sources: Hugging Face (search for "GGUF")
   - Example: [TheBloke's GGUF models](https://huggingface.co/TheBloke)

3. **Place model in the default location:**
   ```bash
   mkdir -p ~/.local/eden/models
   mv your-model.gguf ~/.local/eden/models/
   ```

4. **Restart the daemon:**
   ```bash
   eden shutdown  # If running
   python3 os/eden_daemon.py
   ```

5. **Test the AI:**
   ```bash
   eden chat "Hello, can you hear me?"
   ```

### Running tests

```bash
cd os/
python3 -m pytest tests/ -v

# Or run specific test files
python3 -m pytest tests/test_ipc.py
python3 -m pytest tests/test_ai.py
python3 -m pytest tests/test_sandbox.py
python3 -m pytest tests/test_patch.py
```

### Debugging

Run in foreground with verbose logging:
```bash
python3 eden_daemon.py -v
```

### Modifying the protocol

Edit `eden_ipc.py` to add new methods or change the protocol. Then update:
1. `eden_daemon.py` - Add handler in `handle_request()`
2. `eden_cli.py` - Add CLI command function
3. Update this README

## Security Considerations

- **Unix socket permissions**: By default, the socket is created with user-only permissions
- **No authentication**: Any process running as the same user can connect
- **Local only**: Unix sockets are not accessible over the network
- **PID file**: Used to prevent multiple instances

For production deployments, consider:
- Running as a dedicated user account
- Using socket permissions to restrict access
- Adding authentication to the IPC protocol

## License

MIT License - See LICENSE file in repository root.

## Author

AIOSPANDORA Development Team
