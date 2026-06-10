from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .engine import analyze_diff_file
from .models import Decision
from .receipt_renderer import render_markdown_receipt


EXIT_CODES = {
    Decision.PASS: 0,
    Decision.WARN: 1,
    Decision.FAIL: 2,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Kaskal Code Governance pure-function MVP")
    parser.add_argument("--diff", required=True, help="Path to a unified diff file")
    parser.add_argument("--config", default=None, help="Path to .kaskal.yml")
    parser.add_argument("--out", default=None, help="Optional path for JSON receipt output")
    parser.add_argument("--comment", default=None, help="Optional path for Markdown PR comment output")
    parser.add_argument("--project", default="unknown")
    parser.add_argument("--commit-sha", default=None)
    parser.add_argument("--pr-number", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        receipt = analyze_diff_file(
            diff_path=args.diff,
            config_path=args.config,
            project=args.project,
            commit_sha=args.commit_sha,
            pr_number=args.pr_number,
        )
    except Exception as exc:  # pragma: no cover - CLI defensive boundary
        print(f"Kaskal input/config error: {exc}", file=sys.stderr)
        return 3

    comment = render_markdown_receipt(receipt)

    if args.out:
        Path(args.out).write_text(receipt.model_dump_json(indent=2), encoding="utf-8")
    if args.comment:
        Path(args.comment).write_text(comment, encoding="utf-8")
    if not args.out and not args.comment:
        print(comment)

    return EXIT_CODES[receipt.decision]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
