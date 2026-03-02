"""Ouroboros CLI — argument parser and subcommand dispatch."""
from __future__ import annotations

import argparse
import sys

from .version import __version__


def _cmd_run(args: argparse.Namespace) -> None:
    from .runner import CathedralRunner

    runner = CathedralRunner(
        num_entities=args.entities,
        mode=args.mode,
        duration=args.duration,
    )
    runner.run()


def _cmd_dashboard(args: argparse.Namespace) -> None:  # noqa: ARG001
    from .terminal_ui import TerminalDashboard

    dash = TerminalDashboard()
    dash.run()


def _cmd_version(args: argparse.Namespace) -> None:  # noqa: ARG001
    print(f"ouroboros {__version__}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="ouroboros",
        description="Ouroboros Cathedral — palindrome descent orchestrator",
    )
    sub = parser.add_subparsers(dest="command")

    # ouroboros run
    run_p = sub.add_parser("run", help="Run the Cathedral game loop")
    run_p.add_argument(
        "--entities", "-n", type=int, default=17, metavar="N",
        help="Number of entities to spawn (default: 17)",
    )
    run_p.add_argument(
        "--mode", choices=["terminal", "websocket"], default="terminal",
        help="Output mode (default: terminal)",
    )
    run_p.add_argument(
        "--duration", "-d", type=float, default=None, metavar="SECONDS",
        help="Auto-stop after SECONDS (default: run until Ctrl+C)",
    )

    # ouroboros dashboard
    sub.add_parser("dashboard", help="Launch rich terminal dashboard")

    # ouroboros version
    sub.add_parser("version", help="Print version and exit")

    args = parser.parse_args(argv)

    if args.command == "run":
        _cmd_run(args)
    elif args.command == "dashboard":
        _cmd_dashboard(args)
    elif args.command == "version":
        _cmd_version(args)
    else:
        parser.print_help()
        sys.exit(0)
