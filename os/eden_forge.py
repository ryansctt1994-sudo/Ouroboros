#!/usr/bin/env python3
"""
Æthel Forge — Unified EDEN Terminal
=====================================

Unifies all EDEN terminal interfaces into a single interactive REPL and
one-shot CLI:

  • os/eden_tui.py      — daemon IPC, file dropbox, ECS control
  • os/eden_cli.py      — one-shot CLI commands
  • eden_ecs/tools/cosmic_coder.py — cargo test/build, sakib_ab, sweep
  • geodesic_mycelium_agent/cli.py — Geodesic Mycelium Agent

Session state is persisted to disk so force-quitting and reopening the
terminal restores the full working context.

Interactive REPL (no args):
    python os/eden_forge.py

One-shot CLI:
    python os/eden_forge.py status
    python os/eden_forge.py ecs test
    python os/eden_forge.py agent "Explain Two-Rail Encoding"

Copyright (c) 2025-2026 The Ouroboros Foundation
License: MIT + Ethical Use Covenant
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import readline
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Repo / script layout ──────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.absolute()
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from eden_ipc import SOCKET_PATH, make_request, parse_message  # noqa: E402

# ── Platform-aware state directory ───────────────────────────────────────────


def _state_dir() -> Path:
    """Return the platform-appropriate persistent state directory."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "eden"
    return Path.home() / ".local" / "share" / "eden"


STATE_DIR = _state_dir()
SESSION_FILE = STATE_DIR / "forge_session.json"
HISTORY_FILE = STATE_DIR / "forge_history"


# ── Terminal Colors ───────────────────────────────────────────────────────────

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


# ── Persistent Session ────────────────────────────────────────────────────────

class ForgeSession:
    """
    Persistent REPL session state.

    Survives force-quit: on next launch the Forge restores dropbox file
    paths, cwd, and preferences from SESSION_FILE.
    """

    def __init__(self) -> None:
        self.dropbox_paths: Dict[str, str] = {}   # name → absolute filepath
        self.cwd: str = os.getcwd()
        self.preferences: Dict[str, Any] = {}
        self.last_active: float = time.time()
        self._load()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Restore session from disk if available."""
        if not SESSION_FILE.exists():
            return
        try:
            with open(SESSION_FILE, encoding="utf-8") as f:
                data = json.load(f)
            self.cwd = data.get("cwd", self.cwd)
            self.preferences = data.get("preferences", {})
            self.last_active = data.get("last_active", self.last_active)
            # Only restore paths that still exist on disk
            for name, path in data.get("dropbox_paths", {}).items():
                if os.path.isfile(path):
                    self.dropbox_paths[name] = path
        except Exception:
            pass  # Corrupt session file — start fresh

    def save(self) -> None:
        """Flush session state to disk."""
        self.last_active = time.time()
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "cwd": self.cwd,
                        "dropbox_paths": self.dropbox_paths,
                        "preferences": self.preferences,
                        "last_active": self.last_active,
                    },
                    f,
                    indent=2,
                )
        except Exception:
            pass  # Non-fatal — just don't persist this time

    def register_file(self, name: str, filepath: str) -> None:
        self.dropbox_paths[name] = filepath
        self.save()

    def unregister_file(self, name: str) -> None:
        self.dropbox_paths.pop(name, None)
        self.save()


# ── File Dropbox ──────────────────────────────────────────────────────────────

class FileDropbox:
    """
    Manages parsed file context for AI conversation.

    Loaded file *contents* live in memory; the absolute path is saved to
    ForgeSession so files can be re-parsed after a restart.
    """

    MAX_FILES = 5
    MAX_FILE_SIZE = 50_000

    def __init__(self, session: ForgeSession) -> None:
        self.session = session
        self.files: Dict[str, str] = {}  # name → content
        self._restore_from_session()

    def _restore_from_session(self) -> None:
        """Re-parse files that were loaded in a previous session."""
        for name, filepath in list(self.session.dropbox_paths.items()):
            _, err = self.parse(filepath, _register=False)
            if err:
                # File gone — remove stale entry from session
                self.session.unregister_file(name)

    def parse(self, filepath: str, _register: bool = True) -> Tuple[str, Optional[str]]:
        path = Path(filepath).expanduser().resolve()
        if not path.exists():
            return "", f"File not found: {path}"
        if not path.is_file():
            return "", f"Not a file: {path}"
        try:
            content = path.read_text(errors="replace")
        except Exception as e:
            return "", f"Read error: {e}"

        if len(content) > self.MAX_FILE_SIZE:
            content = content[: self.MAX_FILE_SIZE] + (
                f"\n\n... [TRUNCATED at {self.MAX_FILE_SIZE} chars]"
            )

        name = path.name
        self.files[name] = content

        # Evict oldest if over limit
        while len(self.files) > self.MAX_FILES:
            oldest = next(iter(self.files))
            del self.files[oldest]
            self.session.unregister_file(oldest)

        lines = content.count("\n") + 1
        size = path.stat().st_size
        lang = mimetypes.guess_type(str(path))[0] or "text"

        if _register:
            self.session.register_file(name, str(path))

        return f"{name} ({lines} lines, {size:,} bytes, {lang})", None

    def drop(self, name: str) -> bool:
        if name in self.files:
            del self.files[name]
            self.session.unregister_file(name)
            return True
        return False

    def clear(self) -> int:
        count = len(self.files)
        names = list(self.files.keys())
        self.files.clear()
        for n in names:
            self.session.unregister_file(n)
        return count

    def list_files(self) -> List[str]:
        return list(self.files.keys())

    def build_context(self) -> str:
        if not self.files:
            return ""
        parts = []
        for name, content in self.files.items():
            parts.append(f"--- FILE: {name} ---\n{content}\n--- END {name} ---")
        return "\n".join(parts)


# ── IPC helpers ───────────────────────────────────────────────────────────────

def _ipc_send(method: str, params: Optional[Dict] = None) -> Tuple[Any, Optional[str]]:
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


def _daemon_online() -> bool:
    return os.path.exists(SOCKET_PATH)


def _get_status_quick() -> Optional[Dict]:
    result, err = _ipc_send("get_status")
    return result if not err else None


# ── Subprocess runner ─────────────────────────────────────────────────────────

def _run_cmd(args: List[str], cwd: Optional[str] = None) -> int:
    """Run a subprocess with streamed output. Returns exit code."""
    cwd = cwd or str(REPO_ROOT)
    try:
        proc = subprocess.Popen(
            args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(f"  {C.DIM}{line}", end=C.RESET)
        proc.wait()
        return proc.returncode
    except FileNotFoundError:
        print(f"  {C.RED}✗ Command not found: {args[0]}{C.RESET}")
        return 1


# ── Display helpers ───────────────────────────────────────────────────────────

def _term_width() -> int:
    return shutil.get_terminal_size((80, 24)).columns


def _draw_header(status: Optional[Dict], start_time: datetime) -> None:
    w = _term_width()
    now = datetime.now()
    uptime = now - start_time
    h = int(uptime.total_seconds() // 3600)
    m = int((uptime.total_seconds() % 3600) // 60)
    s = int(uptime.total_seconds() % 60)
    uptime_str = f"{h:02d}:{m:02d}:{s:02d}"
    ts = now.strftime("%H:%M:%S")

    if status:
        state = (
            f"{C.GREEN}● ONLINE{C.RESET}"
            if status.get("running")
            else f"{C.YELLOW}○ IDLE{C.RESET}"
        )
        tick = status.get("tick", 0)
        agents = status.get("agents", 0)
        gamma = status.get("gamma", 0)
        info = f"{state}  Tick:{tick}  Agents:{agents}  γ:{gamma:.4f}"
    else:
        info = f"{C.RED}● DAEMON OFFLINE{C.RESET}"

    print(f"\033[2J\033[H", end="")
    print(f"{C.BOLD}{C.CYAN}{'─' * w}")
    print(
        f"  Æthel Forge v1.0 · Unified EDEN Terminal"
        f"{' ' * max(1, w - 55)}⏱ {uptime_str}  🕐 {ts}"
    )
    print(f"{'─' * w}{C.RESET}")
    print(f"  {info}")
    print(f"{C.CYAN}{'─' * w}{C.RESET}")
    print()


def _draw_dropbox_status(dropbox: FileDropbox) -> None:
    files = dropbox.list_files()
    if files:
        flist = ", ".join(f"{C.MAGENTA}{f}{C.RESET}" for f in files)
        print(
            f"  {C.DIM}📂 Dropbox [{len(files)}/{dropbox.MAX_FILES}]:{C.RESET} {flist}"
        )
        print()


def _print_help() -> None:
    print(f"""
  {C.BOLD}Daemon (IPC):{C.RESET}
  {C.CYAN}/status{C.RESET}                  Daemon status
  {C.CYAN}/start{C.RESET}  {C.CYAN}/stop{C.RESET}  {C.CYAN}/step{C.RESET}    Control tick loop
  {C.CYAN}/entities{C.RESET}                List AI agents
  {C.CYAN}/metrics{C.RESET}                 Network metrics
  {C.CYAN}/graph{C.RESET}                   Network topology
  {C.CYAN}/shutdown{C.RESET}                Kill daemon

  {C.BOLD}ECS / Rust (subprocess):{C.RESET}
  {C.CYAN}/test{C.RESET}                    cargo test -p eden_ecs
  {C.CYAN}/build{C.RESET}                   cargo build -p eden_ecs --release
  {C.CYAN}/ab [culture] [steps] [gain]{C.RESET}  sakib_ab experiment
  {C.CYAN}/fmt{C.RESET}                     cargo fmt --check
  {C.CYAN}/clippy{C.RESET}                  cargo clippy

  {C.BOLD}Forge / METACUBE:{C.RESET}
  {C.CYAN}/forge{C.RESET}                   Run consensus round via ForgeBridge

  {C.BOLD}Lima VM:{C.RESET}
  {C.CYAN}/lima{C.RESET}                    Lima VM status
  {C.CYAN}/lima shell{C.RESET}              Open Lima shell

  {C.BOLD}Agent:{C.RESET}
  {C.CYAN}/agent "prompt"{C.RESET}          Run Geodesic Mycelium Agent
  {C.CYAN}/agent -i{C.RESET}               Interactive agent session

  {C.BOLD}Runner:{C.RESET}
  {C.CYAN}/run{C.RESET}                     Cathedral runner
  {C.CYAN}/dashboard{C.RESET}               Rich dashboard

  {C.BOLD}Dropbox:{C.RESET}
  {C.CYAN}/parse <file>{C.RESET}            Load file into AI context
  {C.CYAN}/drop <file>{C.RESET}             Remove file from context
  {C.CYAN}/files{C.RESET}                   List loaded files
  {C.CYAN}/clear{C.RESET}                   Clear all files

  {C.BOLD}Session:{C.RESET}
  {C.CYAN}/refresh{C.RESET}                 Redraw screen
  {C.CYAN}/help{C.RESET}                    Show this help
  {C.CYAN}/quit{C.RESET}                    Exit (session saved)

  {C.DIM}Anything else is sent to EDEN as a chat message.
  Loaded files are automatically included as context.{C.RESET}
""")


# ── Command implementations ───────────────────────────────────────────────────

def _cmd_status() -> None:
    result, err = _ipc_send("get_status")
    if err:
        print(f"  {C.RED}✗ {err}{C.RESET}")
        return
    running = (
        f"{C.GREEN}● Online{C.RESET}"
        if result["running"]
        else f"{C.YELLOW}○ Idle{C.RESET}"
    )
    print(f"""
  {C.BOLD}Daemon Status{C.RESET}
  {'─' * 30}
  State:     {running}
  Tick:      {result['tick']}
  Agents:    {result['agents']}
  Consensus: {'✓' if result['consensus'] else '✗'}
  Gamma:     {result['gamma']:.4f}
""")


def _cmd_entities() -> None:
    result, err = _ipc_send("get_entities")
    if err:
        print(f"  {C.RED}✗ {err}{C.RESET}")
        return
    print(
        f"  {C.BOLD}{'Name':<12} {'Coherence':<11} {'Phase':<9} "
        f"{'Gamma':<9} {'Sync'}{C.RESET}"
    )
    print(f"  {C.DIM}{'─' * 52}{C.RESET}")
    for e in result:
        name = e.get("name", "?")[:12]
        coh = e.get("coherence", 0)
        phase = e.get("phase", 0)
        gamma = e.get("gamma", 0)
        synced = f"{C.GREEN}✓{C.RESET}" if e.get("synced") else f"{C.DIM}✗{C.RESET}"
        print(f"  {name:<12} {coh:<11.4f} {phase:<9.4f} {gamma:<9.4f} {synced}")
    print()


def _cmd_metrics() -> None:
    result, err = _ipc_send("get_metrics")
    if err:
        print(f"  {C.RED}✗ {err}{C.RESET}")
        return
    print(f"""
  {C.BOLD}Network Metrics{C.RESET}
  {'─' * 30}
  Mean Gamma:     {result.get('mean_gamma', 0.0):.4f}
  Mean Coherence: {result.get('mean_coherence', 0.0):.4f}
  Consensus:      {result.get('consensus', False)}
  Total Entities: {result.get('total_entities', 0)}
  Synchronized:   {result.get('synchronized_entities', 0)}
""")


def _cmd_graph() -> None:
    result, err = _ipc_send("get_graph")
    if err:
        print(f"  {C.RED}✗ {err}{C.RESET}")
        return
    nodes = result.get("nodes", [])
    edges = result.get("edges", [])
    print(f"\n  {C.BOLD}Network Topology{C.RESET}")
    print(f"  {'─' * 30}")
    print(f"  Nodes: {len(nodes)}  Edges: {len(edges)}")
    for node in nodes[:10]:
        nid = node["id"][:8] + "..."
        name = node.get("name", "?")
        phase = node.get("phase", 0.0)
        gamma = node.get("gamma", 0.0)
        print(f"  {nid:<15} {name:<15} phase={phase:.4f} γ={gamma:.4f}")
    if len(nodes) > 10:
        print(f"  {C.DIM}… and {len(nodes) - 10} more{C.RESET}")
    print()


def _cmd_ecs_test() -> int:
    print(f"\n  {C.BOLD}cargo test -p eden_ecs{C.RESET}")
    return _run_cmd(["cargo", "test", "-p", "eden_ecs"])


def _cmd_ecs_build() -> int:
    print(f"\n  {C.BOLD}cargo build -p eden_ecs --release{C.RESET}")
    return _run_cmd(["cargo", "build", "-p", "eden_ecs", "--release"])


def _cmd_ecs_fmt() -> int:
    print(f"\n  {C.BOLD}cargo fmt --check{C.RESET}")
    return _run_cmd(["cargo", "fmt", "--check"])


def _cmd_ecs_clippy() -> int:
    print(f"\n  {C.BOLD}cargo clippy{C.RESET}")
    return _run_cmd(["cargo", "clippy"])


def _cmd_ecs_ab(parts: List[str]) -> int:
    """Run sakib_ab via cosmic_coder.py.

    /ab [culture] [steps] [gain]
    """
    cosmic = REPO_ROOT / "eden_ecs" / "tools" / "cosmic_coder.py"
    if not cosmic.exists():
        print(f"  {C.RED}✗ cosmic_coder.py not found at {cosmic}{C.RESET}")
        return 1
    cmd = [sys.executable, str(cosmic), "ab"] + parts
    print(f"\n  {C.BOLD}sakib_ab: {' '.join(parts) or 'engramum_competitive'}{C.RESET}")
    return _run_cmd(cmd, cwd=str(REPO_ROOT))


def _cmd_forge() -> None:
    try:
        from forge_bridge import ForgeBridge  # type: ignore
        fb = ForgeBridge()
        result = fb.consensus_round()
        print(f"  {C.GREEN}✓ Forge consensus:{C.RESET} {result}")
    except ImportError:
        print(f"  {C.YELLOW}⚠ ForgeBridge not available (forge_bridge module missing){C.RESET}")


def _cmd_lima(shell: bool = False) -> int:
    if shell:
        return _run_cmd(["limactl", "shell", "default"])
    return _run_cmd(["limactl", "list"])


def _cmd_agent(prompt: Optional[str] = None, interactive: bool = False) -> int:
    """Run the Geodesic Mycelium Agent."""
    cmd = [sys.executable, "-m", "geodesic_mycelium_agent"]
    if interactive:
        cmd.append("--interactive")
    elif prompt:
        cmd += ["--no-dry-run", prompt]
    else:
        cmd.append("--show-docs")
    return _run_cmd(cmd, cwd=str(REPO_ROOT))


def _cmd_run() -> int:
    """Cathedral runner."""
    main_py = REPO_ROOT / "main.py"
    if not main_py.exists():
        print(f"  {C.RED}✗ main.py not found{C.RESET}")
        return 1
    return _run_cmd([sys.executable, str(main_py)])


def _cmd_dashboard() -> int:
    """Rich dashboard — launch performance monitor if available."""
    perf = SCRIPT_DIR / "performance.py"
    if perf.exists():
        return _run_cmd([sys.executable, str(perf)])
    print(f"  {C.YELLOW}⚠ performance.py not found{C.RESET}")
    return 1


# ── readline history ──────────────────────────────────────────────────────────

def _init_readline() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if HISTORY_FILE.exists():
        try:
            readline.read_history_file(str(HISTORY_FILE))
        except Exception:
            pass
    readline.set_history_length(1000)


def _save_readline() -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        readline.write_history_file(str(HISTORY_FILE))
    except Exception:
        pass


# ── Interactive REPL ──────────────────────────────────────────────────────────

def _repl(session: ForgeSession) -> None:
    """Interactive Forge REPL."""
    _init_readline()
    dropbox = FileDropbox(session)
    start_time = datetime.now()

    # Restore notification
    if session.dropbox_paths:
        restored = list(session.dropbox_paths.keys())
        print(
            f"  {C.DIM}🔄 Session restored — dropbox: "
            f"{', '.join(restored)}{C.RESET}"
        )

    status = _get_status_quick()
    _draw_header(status, start_time)
    _draw_dropbox_status(dropbox)
    _print_help()

    def _on_exit() -> None:
        session.save()
        _save_readline()
        print(f"\n  {C.DIM}Session saved. Farewell, Architect. 🛡️{C.RESET}")

    signal.signal(signal.SIGTERM, lambda *_: (_on_exit(), sys.exit(0)))

    while True:
        try:
            prompt = f"  {C.GREEN}forge{C.RESET}{C.DIM}:{C.RESET}{C.CYAN}~{C.RESET}$ "
            msg = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            _on_exit()
            break

        if not msg:
            continue

        # ── Session / meta ────────────────────────────────────────────────
        if msg in ("/quit", "/exit"):
            _on_exit()
            break

        elif msg in ("/help", "/?"):
            _print_help()

        elif msg == "/refresh":
            status = _get_status_quick()
            _draw_header(status, start_time)
            _draw_dropbox_status(dropbox)

        # ── Daemon IPC ────────────────────────────────────────────────────
        elif msg == "/status":
            _cmd_status()

        elif msg == "/start":
            r, e = _ipc_send("start")
            print(
                f"  {C.GREEN}✓ Tick loop started{C.RESET}"
                if r and r.get("success")
                else f"  {C.RED}✗ {e or 'Failed'}{C.RESET}"
            )

        elif msg == "/stop":
            r, e = _ipc_send("stop")
            print(
                f"  {C.YELLOW}✓ Tick loop stopped{C.RESET}"
                if r and r.get("success")
                else f"  {C.RED}✗ {e or 'Failed'}{C.RESET}"
            )

        elif msg == "/step":
            r, e = _ipc_send("step")
            print(
                f"  {C.GREEN}✓ Single tick executed{C.RESET}"
                if r and r.get("success")
                else f"  {C.RED}✗ {e or 'Failed'}{C.RESET}"
            )

        elif msg == "/entities":
            _cmd_entities()

        elif msg == "/metrics":
            _cmd_metrics()

        elif msg == "/graph":
            _cmd_graph()

        elif msg == "/shutdown":
            r, e = _ipc_send("shutdown")
            print(
                f"  {C.YELLOW}✓ Daemon shutting down{C.RESET}"
                if r and r.get("success")
                else f"  {C.RED}✗ {e or 'Failed'}{C.RESET}"
            )

        # ── ECS / Rust ────────────────────────────────────────────────────
        elif msg == "/test":
            rc = _cmd_ecs_test()
            _result_line(rc)

        elif msg == "/build":
            rc = _cmd_ecs_build()
            _result_line(rc)

        elif msg == "/fmt":
            rc = _cmd_ecs_fmt()
            _result_line(rc)

        elif msg == "/clippy":
            rc = _cmd_ecs_clippy()
            _result_line(rc)

        elif msg.startswith("/ab"):
            parts = msg[3:].split()
            rc = _cmd_ecs_ab(parts)
            _result_line(rc)

        # ── Forge / Lima / Agent / Runner ─────────────────────────────────
        elif msg == "/forge":
            _cmd_forge()

        elif msg == "/lima shell":
            _result_line(_cmd_lima(shell=True))

        elif msg == "/lima":
            _result_line(_cmd_lima())

        elif msg == "/agent -i":
            _result_line(_cmd_agent(interactive=True))

        elif msg.startswith("/agent "):
            prompt_text = msg[7:].strip().strip('"').strip("'")
            _result_line(_cmd_agent(prompt=prompt_text))

        elif msg == "/run":
            _result_line(_cmd_run())

        elif msg == "/dashboard":
            _result_line(_cmd_dashboard())

        # ── Dropbox ───────────────────────────────────────────────────────
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
                _draw_dropbox_status(dropbox)

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
                _draw_dropbox_status(dropbox)
            else:
                print(f"  {C.DIM}📂 Dropbox empty{C.RESET}")

        elif msg == "/clear":
            count = dropbox.clear()
            print(f"  {C.YELLOW}✓ Cleared {count} file(s) from dropbox{C.RESET}")

        # ── Unknown command ───────────────────────────────────────────────
        elif msg.startswith("/"):
            print(f"  {C.RED}Unknown command: {msg.split()[0]}{C.RESET}")
            print(f"  {C.DIM}Type /help for commands{C.RESET}")

        # ── Chat ──────────────────────────────────────────────────────────
        else:
            context = dropbox.build_context()
            full_msg = (
                f"[Context from loaded files]\n{context}\n\n[User message]\n{msg}"
                if context
                else msg
            )
            result, err = _ipc_send("chat", {"message": full_msg})
            if err:
                print(f"  {C.RED}✗ {err}{C.RESET}")
            else:
                response = result.get("response", "(no response)")
                print(f"\n  {C.BOLD}{C.CYAN}EDEN:{C.RESET} {response}\n")


def _result_line(rc: int) -> None:
    if rc == 0:
        print(f"  {C.GREEN}✓ Done (exit 0){C.RESET}")
    else:
        print(f"  {C.RED}✗ Failed (exit {rc}){C.RESET}")


# ── One-shot CLI ──────────────────────────────────────────────────────────────

def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="forge",
        description="Æthel Forge — Unified EDEN Terminal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
One-shot commands:
  forge status              Daemon status
  forge start / stop / step Control tick loop
  forge entities            List AI agents
  forge metrics             Network metrics
  forge graph               Network topology
  forge shutdown            Kill daemon
  forge ecs test            cargo test -p eden_ecs
  forge ecs build           cargo build -p eden_ecs --release
  forge ecs fmt             cargo fmt --check
  forge ecs clippy          cargo clippy
  forge ecs ab [culture]    sakib_ab experiment
  forge agent "prompt"      Run Geodesic Mycelium Agent
  forge agent -i            Interactive agent session
  forge run                 Cathedral runner
  forge dashboard           Rich dashboard
""",
    )
    sub = parser.add_subparsers(dest="command")

    # Daemon commands
    for name in ("status", "start", "stop", "step", "entities", "metrics", "graph", "shutdown"):
        sub.add_parser(name, help=f"Daemon: {name}")

    # ECS sub-command group
    ecs = sub.add_parser("ecs", help="ECS/Rust commands")
    ecs_sub = ecs.add_subparsers(dest="ecs_command")
    ecs_sub.add_parser("test")
    ecs_sub.add_parser("build")
    ecs_sub.add_parser("fmt")
    ecs_sub.add_parser("clippy")
    ab_p = ecs_sub.add_parser("ab")
    ab_p.add_argument("culture", nargs="?", default="engramum_competitive")
    ab_p.add_argument("steps", nargs="?", default=None)
    ab_p.add_argument("gain", nargs="?", default=None)

    # Agent
    agent_p = sub.add_parser("agent", help="Geodesic Mycelium Agent")
    agent_p.add_argument("prompt", nargs="?", default=None)
    agent_p.add_argument("-i", "--interactive", action="store_true")

    # Runner / dashboard
    sub.add_parser("run", help="Cathedral runner")
    sub.add_parser("dashboard", help="Rich dashboard")

    return parser


def _run_oneshot(args: argparse.Namespace) -> int:
    """Execute a one-shot CLI command and return an exit code."""
    cmd = args.command

    if cmd == "status":
        _cmd_status()
    elif cmd == "start":
        r, e = _ipc_send("start")
        print("Tick loop started" if r and r.get("success") else f"Failed: {e}")
        return 0 if r and r.get("success") else 1
    elif cmd == "stop":
        r, e = _ipc_send("stop")
        print("Tick loop stopped" if r and r.get("success") else f"Failed: {e}")
        return 0 if r and r.get("success") else 1
    elif cmd == "step":
        r, e = _ipc_send("step")
        print("Tick executed" if r and r.get("success") else f"Failed: {e}")
        return 0 if r and r.get("success") else 1
    elif cmd == "entities":
        _cmd_entities()
    elif cmd == "metrics":
        _cmd_metrics()
    elif cmd == "graph":
        _cmd_graph()
    elif cmd == "shutdown":
        r, e = _ipc_send("shutdown")
        print("Daemon shutting down" if r and r.get("success") else f"Failed: {e}")
        return 0 if r and r.get("success") else 1
    elif cmd == "ecs":
        ec = getattr(args, "ecs_command", None)
        if ec == "test":
            return _cmd_ecs_test()
        elif ec == "build":
            return _cmd_ecs_build()
        elif ec == "fmt":
            return _cmd_ecs_fmt()
        elif ec == "clippy":
            return _cmd_ecs_clippy()
        elif ec == "ab":
            parts = [args.culture]
            if args.steps:
                parts.append(args.steps)
            if args.gain:
                parts.append(args.gain)
            return _cmd_ecs_ab(parts)
        else:
            print("Usage: forge ecs {test|build|fmt|clippy|ab}")
            return 1
    elif cmd == "agent":
        return _cmd_agent(
            prompt=args.prompt,
            interactive=getattr(args, "interactive", False),
        )
    elif cmd == "run":
        return _cmd_run()
    elif cmd == "dashboard":
        return _cmd_dashboard()
    else:
        print(f"Unknown command: {cmd}")
        return 1

    return 0


# ── Entry point ───────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    session = ForgeSession()
    argv = argv if argv is not None else sys.argv[1:]

    if not argv:
        # Interactive REPL mode
        _repl(session)
        return 0

    parser = _build_cli_parser()
    args, _ = parser.parse_known_args(argv)

    if args.command is None:
        # No recognised subcommand — drop into REPL
        _repl(session)
        return 0

    return _run_oneshot(args)


if __name__ == "__main__":
    sys.exit(main())
