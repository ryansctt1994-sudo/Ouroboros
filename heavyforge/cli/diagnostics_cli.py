from __future__ import annotations

import argparse
import json
from pathlib import Path

from heavyforge.diagnostics import LocalDiagnosticAudit
from heavyforge.enums import KernelPanicCode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="heavyforge-diagnostics")
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_cmd = subparsers.add_parser("verify")
    verify_cmd.add_argument("--path", required=True)

    summary_cmd = subparsers.add_parser("summary")
    summary_cmd.add_argument("--path", required=True)

    latest_cmd = subparsers.add_parser("latest")
    latest_cmd.add_argument("--path", required=True)

    tail_cmd = subparsers.add_parser("tail")
    tail_cmd.add_argument("--path", required=True)
    tail_cmd.add_argument("--last", type=int, default=20)

    find_cmd = subparsers.add_parser("find")
    find_cmd.add_argument("--path", required=True)
    find_cmd.add_argument("--code", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    audit = LocalDiagnosticAudit(Path(args.path))

    if args.command == "verify":
        return 0 if audit.verify_diagnostic_stream() else 2

    if args.command == "summary":
        print(json.dumps(audit.summarize_panics(), sort_keys=True))
        return 0

    if args.command == "latest":
        latest = audit.latest()
        print(latest.model_dump_json() if latest else "{}")
        return 0

    if args.command == "tail":
        for receipt in audit.tail(args.last):
            print(receipt.model_dump_json())
        return 0

    if args.command == "find":
        code = KernelPanicCode(args.code)
        for receipt in audit.find_by_code(code):
            print(receipt.model_dump_json())
        return 0

    return 99


if __name__ == "__main__":
    raise SystemExit(main())
