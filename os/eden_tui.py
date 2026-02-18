#!/usr/bin/env python3
"""
EDEN TUI - Lightweight Terminal Chat
=====================================

Persistent chat client for terminals without GTK (Termux, SSH, etc).
Keeps a single socket-like session to the daemon for conversation memory.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import json
import os
import socket
import sys
import readline  # enables arrow keys + history in input()
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

from eden_ipc import SOCKET_PATH, make_request, parse_message

BANNER = """
╔═══════════════════════════════════════════╗
║          EDEN · Sovereign Terminal        ║
║     Pocket Cathedral · Session Active     ║
╚═══════════════════════════════════════════╝
  Type your message. Commands: /status /start /stop /entities /quit
"""

def send(method, params=None):
    """Send a request to the daemon and return the result."""
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(SOCKET_PATH)
        request = make_request(method, params)
        sock.sendall(request.encode("utf-8"))

        data = b""
        while b"\n" not in data:
            chunk = sock.recv(8192)
            if not chunk:
                break
            data += chunk

        response = parse_message(data.decode("utf-8"))
        if "error" in response:
            err = response["error"]
            return None, f"Error {err['code']}: {err['message']}"
        return response.get("result", {}), None
    except (ConnectionRefusedError, FileNotFoundError):
        return None, "EDEN daemon is not running. Start with: python os/eden_daemon.py &"
    finally:
        sock.close()


def print_status():
    result, err = send("get_status")
    if err:
        print(f"  ✗ {err}")
        return
    running = "● Online" if result["running"] else "○ Offline"
    print(f"  {running} │ Agents: {result['agents']} │ Tick: {result['tick']} │ γ: {result['gamma']:.4f}")


def print_entities():
    result, err = send("get_entities")
    if err:
        print(f"  ✗ {err}")
        return
    print(f"  {'Name':<12} {'Coherence':<11} {'Phase':<9} {'Gamma':<9} {'Synced'}")
    print(f"  {'─'*52}")
    for e in result:
        name = e.get("name", "?")[:12]
        coh = e.get("coherence", 0)
        phase = e.get("phase", 0)
        gamma = e.get("gamma", 0)
        synced = "✓" if e.get("synced") else "✗"
        print(f"  {name:<12} {coh:<11.4f} {phase:<9.4f} {gamma:<9.4f} {synced}")


def main():
    if not os.path.exists(SOCKET_PATH):
        print("✗ EDEN daemon is not running.")
        print(f"  Start it with: python os/eden_daemon.py &")
        sys.exit(1)

    print(BANNER)
    print_status()
    print()

    while True:
        try:
            msg = input("  › ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Farewell, Architect. 🛡️")
            break

        if not msg:
            continue

        # Slash commands
        if msg == "/quit":
            print("  Farewell, Architect. 🛡️")
            break
        elif msg == "/status":
            print_status()
            continue
        elif msg == "/start":
            r, e = send("start")
            print(f"  {'✓ Tick loop started' if r and r.get('success') else e or '✗ Failed'}")
            continue
        elif msg == "/stop":
            r, e = send("stop")
            print(f"  {'✓ Tick loop stopped' if r and r.get('success') else e or '✗ Failed'}")
            continue
        elif msg == "/entities":
            print_entities()
            continue

        # Chat
        result, err = send("chat", {"message": msg})
        if err:
            print(f"  ✗ {err}")
        else:
            response = result.get("response", "(no response)")
            print(f"\n  EDEN: {response}\n")


if __name__ == "__main__":
    main()
