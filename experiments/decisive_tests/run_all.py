"""
vΩ.7 Decisive Tests — Master Orchestration Script
==================================================
Runs the full suite of four lethal stress tests defined in the vΩ.7
Master Manifest and writes a unified JSON report.

Usage (from repository root):
    python -m experiments.decisive_tests.run_all
    python -m experiments.decisive_tests.run_all --output results.json
    python -m experiments.decisive_tests.run_all --seed 123

The JSON report contains a top-level ``results`` key with one entry per
test plus a ``summary`` section.  The file is written to
``experiments/decisive_tests/report.json`` by default.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Default output path (relative to repository root)
DEFAULT_OUTPUT = os.path.join(
    os.path.dirname(__file__), "report.json"
)


# ---------------------------------------------------------------------------
# Individual test runners (imported lazily to give clean error messages)
# ---------------------------------------------------------------------------

def _run_adversarial_inversion(seed: int, verbose: bool) -> Dict[str, Any]:
    from experiments.decisive_tests.adversarial_inversion import run
    return run(seed=seed, verbose=verbose)


def _run_depth_extrapolation(seed: int, verbose: bool) -> Dict[str, Any]:
    from experiments.decisive_tests.depth_extrapolation import run
    return run(seed=seed, verbose=verbose)


def _run_width_sweep(seed: int, verbose: bool) -> Dict[str, Any]:
    from experiments.decisive_tests.width_sweep import run
    return run(seed=seed, verbose=verbose)


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------

TESTS = [
    ("adversarial_inversion", _run_adversarial_inversion),
    ("depth_extrapolation",   _run_depth_extrapolation),
    ("width_sweep",           _run_width_sweep),
]


def run_suite(
    seed: int = 42,
    verbose: bool = True,
    output_path: str = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    """Execute all decisive tests and write a unified JSON report.

    Args:
        seed:        Random seed forwarded to every test.
        verbose:     Whether each test prints its own results table.
        output_path: Destination path for the JSON report.

    Returns:
        The full report dictionary.
    """
    suite_start = time.perf_counter()

    individual_results: List[Dict[str, Any]] = []
    failed: List[str] = []

    for name, runner in TESTS:
        print(f"\n{'='*60}")
        print(f"Running test: {name}")
        print(f"{'='*60}")
        try:
            result = runner(seed=seed, verbose=verbose)
            individual_results.append(result)
            logger.info(f"[OK] {name}")
        except Exception as exc:  # noqa: BLE001
            logger.error(f"[FAIL] {name}: {exc}", exc_info=True)
            individual_results.append({
                "test":  name,
                "error": str(exc),
                "status": "FAILED",
            })
            failed.append(name)

    suite_elapsed = time.perf_counter() - suite_start

    # Build summary
    summary: Dict[str, Any] = {
        "total_tests":    len(TESTS),
        "passed":         len(TESTS) - len(failed),
        "failed":         len(failed),
        "failed_tests":   failed,
        "suite_elapsed_seconds": round(suite_elapsed, 3),
    }

    # Harvest verdicts
    verdicts: Dict[str, str] = {}
    for r in individual_results:
        test_name = r.get("test", "unknown")
        if "error" in r:
            verdicts[test_name] = "ERROR"
        else:
            # Each test stores its verdict at the top level or inside sub-keys
            verdict = r.get("verdict")
            if verdict:
                verdicts[test_name] = verdict
            else:
                # adversarial_inversion stores verdicts inside baseline/vo
                verdicts[test_name] = (
                    f"baseline={r.get('baseline', {}).get('verdict', '?')},"
                    f"vo={r.get('vo', {}).get('verdict', '?')}"
                )
    summary["verdicts"] = verdicts

    report: Dict[str, Any] = {
        "schema_version": "vo.7",
        "seed":           seed,
        "results":        individual_results,
        "summary":        summary,
    }

    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    print(f"\n{'='*60}")
    print(f"Suite complete in {suite_elapsed:.2f}s")
    print(f"Passed: {summary['passed']}/{summary['total_tests']}")
    if failed:
        print(f"Failed: {failed}")
    print(f"Report written to: {output_path}")
    print(f"{'='*60}\n")

    return report


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="vΩ.7 Decisive Tests — run the full stress-test suite.",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed forwarded to all tests (default: 42).",
    )
    parser.add_argument(
        "--output", type=str, default=DEFAULT_OUTPUT,
        help=f"Output path for the JSON report (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-test result tables.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )
    args = _parse_args()
    run_suite(seed=args.seed, verbose=not args.quiet, output_path=args.output)
