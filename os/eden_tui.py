#!/usr/bin/env python3
"""
EDEN TUI - Sovereign Terminal v2.0
====================================

VM-style terminal interface with file parsing dropbox.
Designed for Termux, SSH, and headless environments.

Copyright (c) 2025-2026 The Ouroboros Foundation
License: MIT + Ethical Use Covenant
Version: 2.0.0
"""

import json
import os
import socket
import sys
import time
import readline
import shutil
import mimetypes
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

from eden_ipc import SOCKET_PATH, make_request, parse_message


# ── Terminal Colors ──────────────────────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    GREEN   = "\033[32m"
    CYAN    = "\033[36m"
    YELLOW  = "\033[33m"
    RED     = "\033[31m"
    MAGENTA = "\033[35m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"


# ── File Dropbox ─────────────────────────────────────────────────
class FileDropbox:
    """Manages parsed file context for AI conversation."""

    MAX_FILES = 5
    MAX_FILE_SIZE = 50_000

    def __init__(self):
        self.files: dict = {}

    def parse(self, filepath: str):
        path = Path(filepath).expanduser()
        if not path.exists():
            return "", f"File not found: {path}"
        if not path.is_file():
            return "", f"Not a file: {path}"
        try:
            content = path.read_text(errors="replace")
        except Exception as e:
            return "", f"Read error: {e}"

        if len(content) > self.MAX_FILE_SIZE:
            content = content[:self.MAX_FILE_SIZE] + f"\n\n... [TRUNCATED at {self.MAX_FILE_SIZE} chars]"

        name = path.name
        self.files[name] = content

        while len(self.files) > self.MAX_FILES:
            oldest = next(iter(self.files))
            del self.files[oldest]

        lines = content.count("\n") + 1
        size = path.stat().st_size
        lang = mimetypes.guess_type(str(path))[0] or "text"
        return f"{name} ({lines} lines, {size:,} bytes, {lang})", None

    def drop(self, name: str) -> bool:
        if name in self.files:
            del self.files[name]
            return True
        return False

    def list_files(self) -> list:
        return list(self.files.keys())

    def build_context(self) -> str:
        if not self.files:
            return ""
        parts = []
        for name, content in self.files.items():
            parts.append(f"--- FILE: {name} ---\n{content}\n--- END {name} ---")
        return "\n".join(parts)


# ── IPC ─────────────────────────���────────────────────────────────
def send(method, params=None):
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
        return None, "Daemon offline"
    finally:
        sock.close()


def get_status_quick():
    result, err = send("get_status")
    return result if not err else None


# ── Display ──────────────────────────────────────────────────────
def term_width():
    return shutil.get_terminal_size((80, 24)).columns


def draw_header(status, start_time):
    w = term_width()
    now = datetime.now()
    uptime = now - start_time
    h = int(uptime.total_seconds() // 3600)
    m = int((uptime.total_seconds() % 3600) // 60)
    s = int(uptime.total_seconds() % 60)
    uptime_str = f"{h:02d}:{m:02d}:{s:02d}"
    ts = now.strftime("%H:%M:%S")

    if status:
        state = f"{C.GREEN}● ONLINE{C.RESET}" if status["running"] else f"{C.YELLOW}○ IDLE{C.RESET}"
        tick = status.get("tick", 0)
        agents = status.get("agents", 0)
        gamma = status.get("gamma", 0)
        info = f"{state}  Tick:{tick}  Agents:{agents}  γ:{gamma:.4f}"
    else:
        info = f"{C.RED}● OFFLINE{C.RESET}"

    print(f"\033[2J\033[H", end="")
    print(f"{C.BOLD}{C.CYAN}{'─' * w}")
    print(f"  EDEN v0.2 · Sovereign Terminal{' ' * max(1, w - 55)}⏱ {uptime_str}  🕐 {ts}")
    print(f"{'─' * w}{C.RESET}")
    print(f"  {info}")
    print(f"{C.CYAN}{'─' * w}{C.RESET}")
    print()


def draw_dropbox_status(dropbox):
    files = dropbox.list_files()
    if files:
        flist = ", ".join(f"{C.MAGENTA}{f}{C.RESET}" for f in files)
        print(f"  {C.DIM}📂 Dropbox [{len(files)}/{dropbox.MAX_FILES}]:{C.RESET} {flist}")
        print()


def print_help():
    print(f"""
  {C.BOLD}Commands:{C.RESET}
  {C.CYAN}/start{C.RESET}              Start ECS tick loop
  {C.CYAN}/stop{C.RESET}               Stop ECS tick loop
  {C.CYAN}/status{C.RESET}             Show daemon status
  {C.CYAN}/entities{C.RESET}           List AI agents

  {C.BOLD}Dropbox:{C.RESET}
  {C.CYAN}/parse <file>{C.RESET}       Load file into AI context
  {C.CYAN}/drop <file>{C.RESET}        Remove file from context
  {C.CYAN}/files{C.RESET}              List loaded files
  {C.CYAN}/clear{C.RESET}              Clear all files from context

  {C.BOLD}System:{C.RESET}
  {C.CYAN}/refresh{C.RESET}            Redraw screen
  {C.CYAN}/help{C.RESET}               Show this help
  {C.CYAN}/quit{C.RESET}               Exit terminal

  {C.DIM}Anything else is sent to EDEN as a chat message.
  Loaded files are automatically included as context.{C.RESET}
""")


def print_entities():
    result, err = send("get_entities")
    if err:
        print(f"  {C.RED}✗ {err}{C.RESET}")
        return
    print(f"  {C.BOLD}{'Name':<12} {'Coherence':<11} {'Phase':<9} {'Gamma':<9} {'Sync'}{C.RESET}")
    print(f"  {C.DIM}{'─' * 52}{C.RESET}")
    for e in result:
        name = e.get("name", "?")[:12]
        coh = e.get("coherence", 0)
        phase = e.get("phase", 0)
        gamma = e.get("gamma", 0)
        synced = f"{C.GREEN}✓{C.RESET}" if e.get("synced") else f"{C.DIM}✗{C.RESET}"
        print(f"  {name:<12} {coh:<11.4f} {phase:<9.4f} {gamma:<9.4f} {synced}")
    print()


def print_status_full():
    result, err = send("get_status")
    if err:
        print(f"  {C.RED}✗ {err}{C.RESET}")
        return
    running = f"{C.GREEN}● Online{C.RESET}" if result["running"] else f"{C.YELLOW}○ Idle{C.RESET}"
    print(f"""
  {C.BOLD}Daemon Status{C.RESET}
  {'─' * 30}
  State:     {running}
  Tick:      {result['tick']}
  Agents:    {result['agents']}
  Consensus: {'✓' if result['consensus'] else '✗'}
  Gamma:     {result['gamma']:.4f}
""")


# ── Main Loop ────────────────────────────────────────────────────
def main():
    if not os.path.exists(SOCKET_PATH):
        print(f"{C.RED}✗ EDEN daemon is not running.{C.RESET}")
        print(f"  Start with: python os/eden_daemon.py &")
        sys.exit(1)

    dropbox = FileDropbox()
    start_time = datetime.now()
    status = get_status_quick()

    draw_header(status, start_time)
    draw_dropbox_status(dropbox)
    print_help()

    while True:
        try:
            prompt = f"  {C.GREEN}eden{C.RESET}{C.DIM}:{C.RESET}{C.CYAN}~{C.RESET}$ "
            msg = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {C.DIM}Session terminated. 🛡️{C.RESET}")
            break

        if not msg:
            continue

        if msg in ("/quit", "/exit"):
            print(f"  {C.DIM}Farewell, Architect. 🛡️{C.RESET}")
            break
        elif msg == "/help":
            print_help()
        elif msg == "/refresh":
            status = get_status_quick()
            draw_header(status, start_time)
            draw_dropbox_status(dropbox)
        elif msg == "/status":
            print_status_full()
        elif msg == "/start":
            r, e = send("start")
            print(f"  {C.GREEN}✓ Tick loop started{C.RESET}" if r and r.get("success") else f"  {C.RED}✗ {e or 'Failed'}{C.RESET}")
        elif msg == "/stop":
            r, e = send("stop")
            print(f"  {C.YELLOW}✓ Tick loop stopped{C.RESET}" if r and r.get("success") else f"  {C.RED}✗ {e or 'Failed'}{C.RESET}")
        elif msg == "/entities":
            print_entities()
        elif msg.startswith("/parse "):
            filepath = msg[7:].strip()
            if not filepath:
                print(f"  {C.YELLOW}Usage: /parse <filepath>{C.RESET}")
                continue
            summary, err = dropbox.parse(filepath)
            if err:
                print(f"  {C.RED}✗ {err}{C.RESET}")
            else:
                print(f"  {C.GREEN}✓ Loaded:{C.RESET} {summary}")
                draw_dropbox_status(dropbox)
        elif msg.startswith("/drop "):
            name = msg[6:].strip()
            if dropbox.drop(name):
                print(f"  {C.YELLOW}✓ Dropped: {name}{C.RESET}")
            else:
                print(f"  {C.RED}✗ Not in dropbox: {name}{C.RESET}")
                files = dropbox.list_files()
                if files:
                    print(f"  {C.DIM}Loaded: {', '.join(files)}{C.RESET}")
        elif msg == "/files":
            files = dropbox.list_files()
            if files:
                draw_dropbox_status(dropbox)
            else:
                print(f"  {C.DIM}📂 Dropbox empty{C.RESET}")
        elif msg == "/clear":
            count = len(dropbox.list_files())
            dropbox.files.clear()
            print(f"  {C.YELLOW}✓ Cleared {count} file(s) from dropbox{C.RESET}")
        elif msg.startswith("/"):
            print(f"  {C.RED}Unknown command: {msg.split()[0]}{C.RESET}")
            print(f"  {C.DIM}Type /help for commands{C.RESET}")
        else:
            # Chat with context injection
            context = dropbox.build_context()
            full_msg = f"[Context from loaded files]\n{context}\n\n[User message]\n{msg}" if context else msg

            result, err = send("chat", {"message": full_msg})
            if err:
                print(f"  {C.RED}✗ {err}{C.RESET}")
            else:
                response = result.get("response", "(no response)")
                print(f"\n  {C.BOLD}{C.CYAN}EDEN:{C.RESET} {response}\n")


if __name__ == "__main__":
    main()
