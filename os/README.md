# EDEN Daemon System

Background service for the EDEN Mycelial Engine, exposing control via Unix domain socket with JSON-RPC protocol.

## Overview

The EDEN daemon runs the ECS world from `python-bridge/eden_ecs/` as a background service, enabling:

- **Continuous simulation** of consciousness evolution and mycelial synchronization
- **IPC control** via Unix domain socket (`/tmp/eden.sock`)
- **Cross-platform support** for macOS and Linux
- **Multiple init systems**: systemd, launchd, OpenRC, or manual execution

## Prerequisites

- **Python 3.8+** (tested with 3.8, 3.9, 3.10, 3.11)
- **EDEN ECS** (from `python-bridge/eden_ecs/`) - optional, daemon will work with mock world if unavailable
- **Rust ForgeEngine** (optional) - for consensus and synchronization

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

- **`eden_cli.py`** - Command-line client
  - Connects to daemon socket
  - Sends JSON-RPC requests
  - Pretty-prints results

- **`eden_ipc.py`** - IPC protocol definition
  - JSON-RPC request/response serialization
  - Socket path and PID file paths

- **`eden.service`** - systemd user unit
- **`org.ouroboros.eden.plist`** - launchd plist for macOS
- **`openrc/eden`** - OpenRC init script
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
| `shutdown` | - | Gracefully shut down daemon |

## Graceful Degradation

The daemon is designed to work even if EDEN ECS modules are unavailable:

1. If `python-bridge/eden_ecs/` is not found, it uses a **mock world** with simulated entities
2. If `MycelialSyncSystem` is unavailable, it runs with just `ConsciousnessSystem`
3. Warnings are logged but the daemon remains functional

This allows testing the daemon system without building the full ECS.

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

### Running tests

```bash
cd os/
python3 -m unittest tests/test_ipc.py
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
