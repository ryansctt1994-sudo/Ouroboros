"""CathedralRunner — game-loop orchestrator for the Ouroboros Cathedral."""
from __future__ import annotations

import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure the repo root is on the path so eden_ecs and ABRAXIS are importable
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_DEFAULT_WORD = "ABRAXISASIXARBA"
_MANIFEST_FREQUENCY = 528.0
_STATUS_INTERVAL = 5  # seconds between status prints


class CathedralRunner:
    """
    Orchestrates the Cathedral game loop.

    1. Creates an ``EdenEcsBridge`` which builds a ``World`` and registers all
       four Tiamat systems (palindrome descent, coherence accumulator, veto,
       ternary register).
    2. Spawns *num_entities* entities via ``bridge.manifest()``.
    3. Ticks the world each iteration via ``bridge.pulse()``.
    4. Prints periodic status updates and final convergence statistics.
    """

    def __init__(
        self,
        num_entities: int = 17,
        mode: str = "terminal",
        duration: Optional[float] = None,
    ) -> None:
        self.num_entities = num_entities
        self.mode = mode
        self.duration = duration
        self._running = False
        self._tick_count = 0
        self._start_time: float = 0.0
        self._entity_ids: list[str] = []
        self._bridge: Any = None

    # ------------------------------------------------------------------
    # Public interface used by TerminalDashboard
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return current stats dict (safe to call from another thread)."""
        if self._bridge is None:
            return {}
        status = self._bridge.get_status()
        elapsed = time.time() - self._start_time if self._start_time else 0.0
        sys_stats = status.get("system_stats", {})
        pal_stats = sys_stats.get("palindrome", {})
        veto_stats = sys_stats.get("veto", {})
        return {
            "ticks": self._tick_count,
            "elapsed": elapsed,
            "entity_count": status.get("entity_count", 0),
            "tiamat_count": status.get("tiamat_entity_count", 0),
            "monad_count": pal_stats.get("entities_reached_monad", 0),
            "vetoed_count": pal_stats.get("entities_vetoed", 0),
            "veto_killed": veto_stats.get("killed", 0),
            "frequency": 417.0,
        }

    def get_entity_states(self) -> list[Dict[str, Any]]:
        """Return state dicts for all spawned entities."""
        if self._bridge is None:
            return []
        states = []
        for eid in self._entity_ids:
            state = self._bridge.get_entity_state(eid)
            if state:
                states.append(state)
        return states

    # ------------------------------------------------------------------
    # Main run loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Block until completion or Ctrl+C."""
        from ABRAXIS.eden_ecs_bridge import EdenEcsBridge  # type: ignore[import]

        self._bridge = EdenEcsBridge()
        self._start_time = time.time()
        self._running = True

        # Install signal handler for graceful shutdown
        original_sigint = signal.getsignal(signal.SIGINT)

        def _stop(_sig: int, _frame: object) -> None:
            self._running = False

        signal.signal(signal.SIGINT, _stop)

        # Spawn entities
        print(f"[Ouroboros] Spawning {self.num_entities} entities…")
        for i in range(self.num_entities):
            eid = self._bridge.manifest(word=_DEFAULT_WORD, frequency=_MANIFEST_FREQUENCY)
            if eid:
                self._entity_ids.append(eid)
        print(f"[Ouroboros] {len(self._entity_ids)} entities manifested.")

        last_status = self._start_time
        try:
            while self._running:
                # Check duration
                elapsed = time.time() - self._start_time
                if self.duration is not None and elapsed >= self.duration:
                    break

                self._bridge.pulse(frequency=417.0, cycles=1)
                self._tick_count += 1

                now = time.time()
                if now - last_status >= _STATUS_INTERVAL:
                    self._print_status()
                    last_status = now

                # Small sleep to avoid busy-loop
                time.sleep(1.0 / 417.0)
        finally:
            signal.signal(signal.SIGINT, original_sigint)
            self._print_final()

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def _print_status(self) -> None:
        stats = self.get_stats()
        elapsed = stats.get("elapsed", 0.0)
        print(
            f"[Ouroboros] tick={stats['ticks']:>6}  "
            f"elapsed={elapsed:>6.1f}s  "
            f"entities={stats['tiamat_count']:>4}  "
            f"monad={stats['monad_count']:>4}  "
            f"vetoed={stats['vetoed_count']:>4}"
        )

    def _print_final(self) -> None:
        stats = self.get_stats()
        print("\n── Cathedral Convergence Summary ──────────────────────")
        print(f"  Total ticks    : {stats.get('ticks', 0)}")
        print(f"  Elapsed time   : {stats.get('elapsed', 0.0):.2f}s")
        print(f"  Active entities: {stats.get('tiamat_count', 0)}")
        print(f"  Reached Monad  : {stats.get('monad_count', 0)}")
        print(f"  Vetoed         : {stats.get('vetoed_count', 0)}")
        print("────────────────────────────────────────────────────────")
        print("Inhale the 15. Exhale the 1.")
