"""CLI entrypoint for the Geodesic Mycelium Agent.

Usage
-----
    python -m geodesic_mycelium_agent [OPTIONS] [PROMPT]

Options
-------
--dry-run           Run without real LLM or tool calls (default).
--no-dry-run        Allow real LLM/tool calls (requires provider configuration).
--iterations N      Maximum agent iterations per turn (default 10).
--show-docs         Print a summary of loaded ABRAXIS docs then exit.
--interactive       Enter a REPL loop instead of processing a single prompt.

Examples
--------
    # Smoke-test the agent (dry-run, one prompt):
    python -m geodesic_mycelium_agent --dry-run "Explain the Two-Rail Encoding"

    # Show loaded docs summary:
    python -m geodesic_mycelium_agent --show-docs

    # Interactive session (dry-run):
    python -m geodesic_mycelium_agent --interactive
"""

from __future__ import annotations

import argparse
import sys

from geodesic_mycelium_agent.agent import (
    AgentConfig,
    GeodesicMyceliumAgent,
    load_canonical_progression,
    load_docs_index,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geodesic_mycelium_agent",
        description="Geodesic Mycelium Agent — minimal Abraxis/Cathedral-OS agent scaffold",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Prompt to send to the agent (omit when using --interactive or --show-docs).",
    )
    dry_group = parser.add_mutually_exclusive_group()
    dry_group.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=True,
        help="Run without real LLM / tool calls (default).",
    )
    dry_group.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="Allow real LLM / tool calls.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        metavar="N",
        help="Maximum agent iterations per turn (default: 10).",
    )
    parser.add_argument(
        "--show-docs",
        action="store_true",
        help="Print a summary of loaded ABRAXIS docs then exit.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enter a REPL loop instead of processing a single prompt.",
    )
    return parser


def show_docs_summary() -> None:
    canonical = load_canonical_progression()
    index = load_docs_index()

    if canonical:
        print("=== CANONICAL_PROGRESSION.md ===")
        lines = canonical.splitlines()
        # Print first 20 non-empty lines as a teaser
        shown = 0
        for line in lines:
            if shown >= 20:
                break
            print(line)
            if line.strip():
                shown += 1
        print(f"  ... ({len(lines)} lines total)\n")
    else:
        print("[WARN] ABRAXIS/CANONICAL_PROGRESSION.md not found.\n")

    if index:
        print("=== INDEX.md ===")
        idx_lines = index.splitlines()
        for line in idx_lines[:20]:
            print(line)
        print(f"  ... ({len(idx_lines)} lines total)\n")
    else:
        print("[WARN] ABRAXIS/INDEX.md not found.\n")


def run_once(agent: GeodesicMyceliumAgent, prompt: str) -> None:
    print(f"\n[agent] Processing: {prompt!r}\n")
    for chunk in agent.run(prompt):
        print(chunk)
    print()


def run_interactive(agent: GeodesicMyceliumAgent) -> None:
    print("Geodesic Mycelium Agent — interactive mode (Ctrl-C or Ctrl-D to exit)\n")
    while True:
        try:
            prompt = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[agent] Goodbye.")
            break
        if not prompt:
            continue
        run_once(agent, prompt)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.show_docs:
        show_docs_summary()
        return 0

    config = AgentConfig(
        max_iterations=args.iterations,
        dry_run=args.dry_run,
    )
    agent = GeodesicMyceliumAgent(config=config)

    if args.interactive:
        run_interactive(agent)
        return 0

    prompt = args.prompt
    if prompt is None:
        # Default smoke-test prompt
        prompt = "Summarise the Abraxis/Cathedral-OS progression in one paragraph."

    run_once(agent, prompt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
