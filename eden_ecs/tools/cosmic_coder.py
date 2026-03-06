#!/usr/bin/env python3
"""
Cosmic Coder — EDEN-ECS Terminal Agent
=======================================

Local coder terminal agent for the eden_ecs / Weaver / Engram paradigm.

Upgraded from an interactive prompt-printer into a full execution agent:

* **cargo** — test, build, run examples directly from Python
* **sakib_ab** — launch A/B Sakib experiments, parse CSV, score ΔSakib
* **sakib_aba** — run A→B→A engram persistence experiment, parse recovery
* **sweep** — grid search over cultures × steps × flow_gain
* **analyze** — parse and summarize any saved CSV result file
* **validate** — run ``tools/pre_build_hook.py`` integrity gate
* **observatory** — optional EngramObservatory telemetry bridge

Three operational personalities (kept from the original, now actually do things):

    Alice (528 Hz) — Analytical & Structured: full stats, verbose output
    Bunny (417 Hz) — Quick & Practical: compact one-liner results
    Zorel (852 Hz) — Visionary & Strategic: comparative sweeps, regime maps

Usage (one-shot CLI)
--------------------
    python cosmic_coder.py test
    python cosmic_coder.py ab engramum_competitive
    python cosmic_coder.py ab engramum 6 2.0 0.05        # with noise
    python cosmic_coder.py aba 200 2.0
    python cosmic_coder.py sweep
    python cosmic_coder.py analyze results/ab_engramum.csv
    python cosmic_coder.py validate
    python cosmic_coder.py --personality bunny ab hebbium

Usage (interactive REPL — no subcommand)
-----------------------------------------
    python cosmic_coder.py
    python cosmic_coder.py --personality zorel
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import subprocess
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Repo layout ───────────────────────────────────────────────────────────────

# This file lives at eden_ecs/tools/cosmic_coder.py
# parents: [tools/, eden_ecs/, REPO_ROOT]
_THIS_FILE = Path(__file__).resolve()
REPO_ROOT = _THIS_FILE.parents[2]
EDEN_ECS_DIR = REPO_ROOT / "eden_ecs"
TOOLS_DIR = REPO_ROOT / "tools"

# ── Optional EngramObservatory ────────────────────────────────────────────────

_OBSERVATORY_AVAILABLE = False
_EngramObservatory = None

try:
    sys.path.insert(0, str(REPO_ROOT))
    from arc_agi_3.engram_observatory import EngramObservatory as _EngramObservatory  # noqa: E402
    import numpy as _np  # noqa: E402
    _OBSERVATORY_AVAILABLE = True
except ImportError:
    pass

# ── ANSI colours (disabled on non-TTY / --no-color) ──────────────────────────

_COLORS = {
    "routing":   "\033[92m",  # green
    "amplifier": "\033[93m",  # yellow
    "collapse":  "\033[91m",  # red
    "reset":     "\033[0m",
    "dim":       "\033[2m",
    "bold":      "\033[1m",
}


def _c(name: str, enabled: bool = True) -> str:
    return _COLORS.get(name, "") if enabled else ""


# ── Personalities ─────────────────────────────────────────────────────────────

class CosmicPersonality:
    """Operational mode — controls output verbosity and framing."""

    def __init__(self, name: str, frequency: int, style: str, verbosity: str) -> None:
        self.name = name
        self.frequency = frequency
        self.style = style
        self.verbosity = verbosity  # "full" | "compact" | "strategic"

    def banner(self) -> str:
        return f"[{self.name}@{self.frequency}Hz · {self.style}]"

    def prompt(self, task: str) -> str:
        return f"{self.banner()} {task}"


ALICE = CosmicPersonality("Alice", 528, "Analytical & Structured", "full")
BUNNY = CosmicPersonality("Bunny", 417, "Quick & Practical",       "compact")
ZOREL = CosmicPersonality("Zorel", 852, "Visionary & Strategic",   "strategic")

PERSONALITIES: Dict[str, CosmicPersonality] = {
    "alice": ALICE,
    "bunny": BUNNY,
    "zorel": ZOREL,
}

# ── Subprocess helpers ────────────────────────────────────────────────────────


def _run_streaming(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str]:
    """Run a command, stream stdout+stderr to terminal, return (rc, combined_output)."""
    cwd = cwd or REPO_ROOT
    buf = io.StringIO()
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    for line in proc.stdout:  # type: ignore[union-attr]
        buf.write(line)
        print(line, end="", flush=True)
    proc.wait()
    return proc.returncode, buf.getvalue()


def _run_example(
    example: str,
    args: List[str],
    stream_stderr: bool = True,
) -> Tuple[int, str, str]:
    """Run a cargo example, capturing stdout (CSV) while streaming stderr.

    Returns (returncode, stdout_str, stderr_str).
    """
    cmd = [
        "cargo", "run", "-p", "eden_ecs",
        "--example", example, "--release", "--",
    ] + args

    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    stderr_lines: List[str] = []

    def _drain_stderr() -> None:
        for line in proc.stderr:  # type: ignore[union-attr]
            stderr_lines.append(line)
            if stream_stderr:
                print(line, end="", file=sys.stderr, flush=True)

    t = threading.Thread(target=_drain_stderr, daemon=True)
    t.start()
    stdout_data = proc.stdout.read()  # type: ignore[union-attr]
    proc.wait()
    t.join()

    return proc.returncode, stdout_data, "".join(stderr_lines)


# ── CSV analysis ──────────────────────────────────────────────────────────────


def _parse_ab_csv(csv_text: str) -> Dict:
    """Parse sakib_ab CSV → summary dict with regime classification."""
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    if not rows:
        return {}

    learning = [float(r["sakib_learning"]) for r in rows]
    frozen   = [float(r["sakib_frozen"])   for r in rows]
    culture  = rows[0].get("culture", "?")

    n = len(learning)
    tail = max(1, n // 10)

    delta_final = learning[-1] - frozen[-1]
    delta_tail  = (
        sum(learning[-tail:]) / tail - sum(frozen[-tail:]) / tail
    )
    max_learning = max(learning)

    # Regime classification.
    if learning[-1] < 0.3 and delta_tail < 0.05:
        regime = "collapse"
    elif max_learning > 1.8 and learning[-1] < learning[max(0, n // 5)]:
        regime = "amplifier"
    else:
        regime = "routing"

    return {
        "culture":              culture,
        "n_ticks":              n,
        "sakib_learning_final": learning[-1],
        "sakib_frozen_final":   frozen[-1],
        "delta_final":          delta_final,
        "delta_tail_mean":      delta_tail,
        "max_learning":         max_learning,
        "regime":               regime,
    }


def _parse_aba_csv(csv_text: str) -> Dict[str, Dict]:
    """Parse sakib_aba CSV → per-culture recovery summary."""
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    if not rows:
        return {}

    data: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        data[r["culture"]][r["phase"]].append(float(r["sakib"]))

    summary: Dict[str, Dict] = {}
    for culture, phases in data.items():
        a_vals  = phases.get("A",  [])
        a2_vals = phases.get("A2", [])

        peak_a = max(a_vals) if a_vals else 0.0
        target = 0.9 * peak_a

        recovery = next(
            (t for t, s in enumerate(a2_vals) if s >= target), None
        )

        summary[culture] = {
            "peak_a":         peak_a,
            "target_90pct":   target,
            "recovery_ticks": recovery,
        }

    return summary


# ── Main agent class ──────────────────────────────────────────────────────────


class CosmicAgent:
    """EDEN-ECS terminal agent with configurable personality."""

    def __init__(
        self,
        personality: CosmicPersonality = ALICE,
        color: bool = True,
        save_dir: Optional[Path] = None,
    ) -> None:
        self.p = personality
        self.color = color
        self.save_dir = save_dir
        self._obs: Optional[object] = None  # EngramObservatory instance

    # ── Formatting helpers ────────────────────────────────────────────────────

    def _header(self, title: str) -> None:
        bold  = _c("bold",  self.color)
        reset = _c("reset", self.color)
        print(f"\n{bold}{self.p.banner()} — {title}{reset}")
        print("─" * 62)

    def _regime_str(self, regime: str) -> str:
        color = _c(regime, self.color)
        reset = _c("reset", self.color)
        return f"{color}{regime}{reset}"

    # ── cargo commands ────────────────────────────────────────────────────────

    def cmd_test(self) -> int:
        """cargo test -p eden_ecs"""
        self._header("cargo test -p eden_ecs")
        rc, _ = _run_streaming(["cargo", "test", "-p", "eden_ecs"])
        status = "✅ PASSED" if rc == 0 else "❌ FAILED"
        print(f"\n{status} (exit code {rc})")
        return rc

    def cmd_build(self) -> int:
        """cargo build -p eden_ecs --release"""
        self._header("cargo build --release")
        rc, _ = _run_streaming(["cargo", "build", "-p", "eden_ecs", "--release"])
        return rc

    # ── sakib_ab ──────────────────────────────────────────────────────────────

    def cmd_ab(
        self,
        culture: str = "engramum_competitive",
        steps: int = 6,
        gain: float = 2.0,
        noise: float = 0.0,
    ) -> int:
        """Run sakib_ab and report ΔSakib + regime."""
        self._header(
            f"sakib_ab  culture={culture}  steps={steps}  "
            f"gain={gain}  noise={noise}"
        )
        verbose = (self.p.verbosity != "compact")
        rc, stdout, _ = _run_example(
            "sakib_ab",
            [culture, str(steps), str(gain), str(noise)],
            stream_stderr=verbose,
        )

        if rc != 0:
            print(f"❌ sakib_ab failed (exit {rc})")
            return rc

        result = _parse_ab_csv(stdout)
        if result:
            self._display_ab_result(result)
            self._maybe_feed_observatory(stdout)
            self._maybe_save(stdout, f"ab_{culture}_s{steps}_g{gain}_n{noise}.csv")

        return rc

    def _display_ab_result(self, r: Dict) -> None:
        regime_str = self._regime_str(r["regime"])
        if self.p.verbosity == "compact":
            print(f"  ΔSakib={r['delta_final']:+.4f}  regime={regime_str}")
        else:
            print(f"  Culture          : {r['culture']}")
            print(f"  Ticks            : {r['n_ticks']}")
            print(f"  Sakib (learning) : {r['sakib_learning_final']:.4f}")
            print(f"  Sakib (frozen)   : {r['sakib_frozen_final']:.4f}")
            print(f"  ΔSakib (final)   : {r['delta_final']:+.4f}")
            print(f"  ΔSakib (tail)    : {r['delta_tail_mean']:+.4f}")
            print(f"  Max Sakib        : {r['max_learning']:.4f}")
            print(f"  Regime           : {regime_str}")
            if self.p.verbosity == "strategic":
                self._print_regime_guidance(r["regime"])

    def _print_regime_guidance(self, regime: str) -> None:
        guidance = {
            "collapse":   "→ Try: raise flow_gain, reduce decay_rate, or increase alpha",
            "amplifier":  "→ Try: lower flow_gain, reduce alpha, or enable noise σ > 0",
            "routing":    "→ Good: sustained learning gap. Try EngramumCompetitive next.",
        }
        print(f"  {_c('dim', self.color)}{guidance.get(regime, '')}{_c('reset', self.color)}")

    # ── sakib_aba ─────────────────────────────────────────────────────────────

    def cmd_aba(self, n_ticks: int = 200, gain: float = 2.0) -> int:
        """Run sakib_aba A→B→A experiment and display recovery summary."""
        self._header(f"sakib_aba  n_ticks={n_ticks}  gain={gain}")
        verbose = (self.p.verbosity != "compact")
        rc, stdout, _ = _run_example(
            "sakib_aba",
            [str(n_ticks), str(gain)],
            stream_stderr=verbose,
        )

        if rc != 0:
            print(f"❌ sakib_aba failed (exit {rc})")
            return rc

        summary = _parse_aba_csv(stdout)
        if summary:
            self._display_aba_summary(summary)
            self._maybe_save(stdout, f"aba_t{n_ticks}_g{gain}.csv")

        return rc

    def _display_aba_summary(self, summary: Dict[str, Dict]) -> None:
        print()
        hdr = f"  {'Culture':<24}  {'Peak-A':>8}  {'90% Target':>12}  {'Recovery':>10}"
        print(hdr)
        print("  " + "─" * 60)

        # Sort: fastest recovery first, "never" last.
        def _sort_key(item: Tuple[str, Dict]) -> int:
            v = item[1]["recovery_ticks"]
            return v if v is not None else 10 ** 9

        for culture, data in sorted(summary.items(), key=_sort_key):
            rec = data["recovery_ticks"]
            rec_str = str(rec) if rec is not None else "never"
            print(
                f"  {culture:<24}  {data['peak_a']:>8.4f}  "
                f"{data['target_90pct']:>12.4f}  {rec_str:>10}"
            )

        if self.p.verbosity == "strategic":
            print(
                f"\n  {_c('dim', self.color)}"
                "Expected ordering (fastest): engramum_competitive > engramum > hebbium > baseline"
                f"{_c('reset', self.color)}"
            )

    # ── parameter sweep ───────────────────────────────────────────────────────

    def cmd_sweep(
        self,
        cultures:    Optional[List[str]]   = None,
        steps_list:  Optional[List[int]]   = None,
        gains:       Optional[List[float]] = None,
    ) -> List[Dict]:
        """Grid search cultures × steps × gains; rank by ΔSakib tail mean."""
        cultures   = cultures   or ["baseline", "hebbium", "engramum", "engramum_competitive"]
        steps_list = steps_list or [4, 6, 8]
        gains      = gains      or [1.5, 2.0, 3.0]

        total = len(cultures) * len(steps_list) * len(gains)
        self._header(f"parameter sweep  ({total} runs)")

        results: List[Dict] = []

        combos = [
            (c, s, g)
            for c in cultures
            for s in steps_list
            for g in gains
        ]
        for run_n, (culture, steps, gain) in enumerate(combos, start=1):
            print(
                f"  [{run_n:3d}/{total}] {culture:<24} steps={steps} "
                f"gain={gain:.1f} ... ",
                end="", flush=True,
            )
            t0 = time.monotonic()
            rc, stdout, _ = _run_example(
                "sakib_ab",
                [culture, str(steps), str(gain)],
                stream_stderr=False,
            )
            elapsed = time.monotonic() - t0

            if rc != 0 or not stdout.strip():
                print("FAIL")
                continue

            r = _parse_ab_csv(stdout)
            r["steps"]     = steps
            r["gain"]      = gain
            r["elapsed_s"] = round(elapsed, 1)
            results.append(r)

            print(
                f"ΔSakib={r['delta_final']:+.4f}  "
                f"{self._regime_str(r['regime'])}  ({elapsed:.1f}s)"
            )

        # Rank by tail-mean ΔSakib descending.
        results.sort(key=lambda x: x.get("delta_tail_mean", 0.0), reverse=True)

        # Top-10 table.
        print(f"\n  {'#':<3}  {'Culture':<24}  {'Stp':>3}  {'Gain':>5}  "
              f"{'ΔSakib(tail)':>13}  Regime")
        print("  " + "─" * 66)
        for i, r in enumerate(results[:10], 1):
            print(
                f"  {i:<3}  {r['culture']:<24}  {r.get('steps','?'):>3}  "
                f"{r.get('gain','?'):>5}  {r['delta_tail_mean']:>+13.4f}  "
                f"{self._regime_str(r['regime'])}"
            )

        self._maybe_save(
            json.dumps(results, indent=2), "sweep_results.json", binary=False
        )

        return results

    # ── analyze CSV ───────────────────────────────────────────────────────────

    def cmd_analyze(self, csv_path: Path) -> Dict:
        """Parse and display an existing result CSV (auto-detects ab vs aba)."""
        self._header(f"analyze {csv_path.name}")
        if not csv_path.exists():
            print(f"  ❌ File not found: {csv_path}")
            return {}

        text = csv_path.read_text()
        header = text.split("\n")[0].strip()

        if "sakib_learning" in header:
            result = _parse_ab_csv(text)
            self._display_ab_result(result)
            return result
        elif "phase" in header and "sakib" in header:
            summary = _parse_aba_csv(text)
            self._display_aba_summary(summary)
            return {"aba": summary}
        else:
            print(f"  ⚠ Unrecognised CSV header: {header!r}")
            return {}

    # ── pre-build validation ──────────────────────────────────────────────────

    def cmd_validate(self) -> int:
        """Run tools/pre_build_hook.py."""
        self._header("pre-build validation")
        hook = TOOLS_DIR / "pre_build_hook.py"
        if not hook.exists():
            print(f"  ❌ Hook not found: {hook}")
            return 1
        rc, _ = _run_streaming([sys.executable, str(hook)], cwd=TOOLS_DIR)
        return rc

    # ── EngramObservatory bridge ──────────────────────────────────────────────

    def start_observatory(self, log_dir: str = "runs/cosmic_coder") -> bool:
        """Start the background EngramObservatory telemetry daemon."""
        if not _OBSERVATORY_AVAILABLE:
            print("  ⚠ EngramObservatory unavailable (install torch or tensorboardX)")
            return False
        self._obs = _EngramObservatory(log_dir=log_dir)  # type: ignore[misc]
        self._obs.start()  # type: ignore[union-attr]
        print(f"  ✓ EngramObservatory started (log_dir={log_dir})")
        return True

    def stop_observatory(self) -> None:
        if self._obs is not None:
            self._obs.stop()  # type: ignore[union-attr]
            self._obs = None
            print("  ✓ EngramObservatory stopped")

    def _maybe_feed_observatory(self, csv_text: str) -> None:
        """Feed learning Sakib curve into EngramObservatory (downsampled 10×)."""
        if self._obs is None or not _OBSERVATORY_AVAILABLE or _np is None:
            return
        rows = list(csv.DictReader(io.StringIO(csv_text)))
        if not rows:
            return
        vals = _np.array([float(r["sakib_learning"]) for r in rows])
        for step, val in enumerate(vals[::10]):
            self._obs.push(activations=_np.array([val]), step=step)  # type: ignore[union-attr]

    # ── file persistence ──────────────────────────────────────────────────────

    def _maybe_save(self, content: str, filename: str) -> None:
        if self.save_dir is None:
            return
        self.save_dir.mkdir(parents=True, exist_ok=True)
        out = self.save_dir / filename
        out.write_text(content)
        print(f"  ✓ Saved → {out}")

    # ── interactive REPL ──────────────────────────────────────────────────────

    def repl(self) -> None:
        """Start the interactive command loop."""
        bold  = _c("bold",  self.color)
        reset = _c("reset", self.color)
        print(f"""{bold}╔══════════════════════════════════════════════════════════╗
║   🌌 COSMIC CODER — EDEN-ECS Terminal Agent             ║
╚══════════════════════════════════════════════════════════╝{reset}
Personality : {self.p.name} ({self.p.frequency} Hz) — {self.p.style}
Repo root   : {REPO_ROOT}

Commands
  test                              cargo test -p eden_ecs
  build                             cargo build --release
  ab  [culture] [steps] [gain]      run sakib_ab experiment
  aba [n_ticks] [gain]              run sakib_aba A→B→A experiment
  sweep [cultures…]                 parameter grid sweep
  analyze <file>                    parse & display a CSV file
  validate                          tools/pre_build_hook.py
  obs start [log_dir]               start EngramObservatory
  obs stop                          stop EngramObservatory
  help                              show this message
  q / quit / exit                   quit
""")

        while True:
            try:
                line = input(f"🌌 {self.p.name}> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n🐇 Cosmic Coder shutting down…")
                self.stop_observatory()
                break

            if not line:
                continue
            if line.lower() in ("q", "quit", "exit"):
                self.stop_observatory()
                break

            parts = line.split()
            cmd   = parts[0].lower()
            args  = parts[1:]

            try:
                if cmd == "test":
                    self.cmd_test()
                elif cmd == "build":
                    self.cmd_build()
                elif cmd == "ab":
                    self.cmd_ab(
                        culture=args[0] if args else "engramum_competitive",
                        steps=int(args[1]) if len(args) > 1 else 6,
                        gain=float(args[2]) if len(args) > 2 else 2.0,
                        noise=float(args[3]) if len(args) > 3 else 0.0,
                    )
                elif cmd == "aba":
                    self.cmd_aba(
                        n_ticks=int(args[0]) if args else 200,
                        gain=float(args[1]) if len(args) > 1 else 2.0,
                    )
                elif cmd == "sweep":
                    self.cmd_sweep(
                        cultures=args if args else None
                    )
                elif cmd == "analyze" and args:
                    self.cmd_analyze(Path(args[0]))
                elif cmd == "validate":
                    self.cmd_validate()
                elif cmd == "obs":
                    sub = args[0].lower() if args else ""
                    if sub == "start":
                        self.start_observatory(args[1] if len(args) > 1 else "runs/cosmic_coder")
                    elif sub == "stop":
                        self.stop_observatory()
                    else:
                        print("  ⚠ obs: use 'obs start [log_dir]' or 'obs stop'")
                elif cmd in ("help", "?"):
                    print(
                        "  test / build / ab / aba / sweep / analyze / "
                        "validate / obs start|stop / quit"
                    )
                else:
                    print(f"  ⚠ Unknown command: {cmd!r}  (type 'help')")
            except Exception as exc:
                print(f"  ❌ {type(exc).__name__}: {exc}")


# ── CLI entry point ───────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cosmic_coder",
        description="EDEN-ECS Terminal Agent — Weaver / Engram paradigm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Run with no subcommand to enter the interactive REPL.\n\n"
            "Cultures: baseline  hebbium  engramum  engramum_competitive"
        ),
    )
    p.add_argument(
        "--personality", "-p",
        choices=["alice", "bunny", "zorel"],
        default="alice",
        help="Output personality (default: alice)",
    )
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colours")
    p.add_argument(
        "--save-dir", "-d", type=Path, default=None, metavar="DIR",
        help="Directory to save CSV/JSON results",
    )

    sub = p.add_subparsers(dest="command", metavar="COMMAND")

    sub.add_parser("test",  help="cargo test -p eden_ecs")
    sub.add_parser("build", help="cargo build -p eden_ecs --release")

    ab = sub.add_parser("ab", help="Run sakib_ab A/B experiment")
    ab.add_argument("culture", nargs="?", default="engramum_competitive",
                    help="Weaver culture (default: engramum_competitive)")
    ab.add_argument("steps",   nargs="?", type=int,   default=6,
                    help="Message-passing depth (default: 6)")
    ab.add_argument("gain",    nargs="?", type=float, default=2.0,
                    help="Flow gain (default: 2.0)")
    ab.add_argument("noise",   nargs="?", type=float, default=0.0,
                    help="Flow noise σ (default: 0.0)")

    aba = sub.add_parser("aba", help="Run sakib_aba A→B→A persistence experiment")
    aba.add_argument("n_ticks", nargs="?", type=int,   default=200,
                     help="Ticks per phase (default: 200)")
    aba.add_argument("gain",    nargs="?", type=float, default=2.0,
                     help="Flow gain (default: 2.0)")

    sw = sub.add_parser("sweep", help="Grid-search cultures × steps × gains")
    sw.add_argument("cultures", nargs="*",
                    help="Cultures to sweep (default: all 4)")
    sw.add_argument("--steps",  nargs="+", type=int,   default=None)
    sw.add_argument("--gains",  nargs="+", type=float, default=None)

    an = sub.add_parser("analyze", help="Parse and summarize a saved CSV file")
    an.add_argument("csv", type=Path, metavar="FILE")

    sub.add_parser("validate", help="Run tools/pre_build_hook.py")

    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    personality = PERSONALITIES.get(args.personality, ALICE)
    agent = CosmicAgent(
        personality=personality,
        color=not args.no_color,
        save_dir=args.save_dir,
    )

    cmd = args.command

    if cmd is None:
        agent.repl()
    elif cmd == "test":
        sys.exit(agent.cmd_test())
    elif cmd == "build":
        sys.exit(agent.cmd_build())
    elif cmd == "ab":
        sys.exit(agent.cmd_ab(args.culture, args.steps, args.gain, args.noise))
    elif cmd == "aba":
        sys.exit(agent.cmd_aba(args.n_ticks, args.gain))
    elif cmd == "sweep":
        agent.cmd_sweep(
            cultures=args.cultures if args.cultures else None,
            steps_list=args.steps,
            gains=args.gains,
        )
    elif cmd == "analyze":
        agent.cmd_analyze(args.csv)
    elif cmd == "validate":
        sys.exit(agent.cmd_validate())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
