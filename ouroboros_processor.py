# Updated Ouroboros virtual processor with overlay entrypoints for Elpis native execution
import math
import threading
import time
from typing import List, Optional, Dict, Any

class OuroborosVirtualProcessor:
    """Virtual Ouroboros processor emulating ternary cycles and geodesic flows.

    This module is intentionally stdlib-only so it can run air-gapped and be
    embedded as a native overlay within Elpis or other fabric runtimes.
    """

    def __init__(self, radius: float = 1.0, lambda_: float = 0.3, threshold: float = 0.4):
        self.R = radius  # Torus radius
        self.lambda_ = lambda_
        self.threshold = threshold
        self.EPS = 1e-12
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._state: Dict[str, Any] = {}

    def ternary_cycle(self, V: List[float]) -> List[float]:
        """Simulate +1 expansion, 0 reconciliation, -1 collapse on torus.

        Returns a non-negative normalized vector representing the toroidal state.
        """
        norm = sum(V) or 3 * self.EPS
        return [max(0.0, v / norm) for v in V]

    def geodesic_flow(self, phi: float, theta: float) -> tuple[float, float, float]:
        """Parametric horn torus: x, y, z at cusp (phi=pi, hyperbolic K-> -inf)."""
        x = self.R * (1 + math.cos(phi)) * math.cos(theta)
        y = self.R * (1 + math.cos(phi)) * math.sin(theta)
        z = self.R * math.sin(phi)
        return x, y, z

    def delta_check(self, V_exp: List[float], V_obs: List[float]) -> dict:
        """Ternary Delta-check with torus curvature penalty.

        Returns a dict with delta (float) and verdict ("PASS"/"FAIL").
        """
        V_e = self.ternary_cycle(V_exp)
        V_o = self.ternary_cycle(V_obs)
        d = math.sqrt(sum((e - o) ** 2 for e, o in zip(V_e, V_o)))
        H = -sum(p * math.log(p + self.EPS) for p in V_o if p > 0)
        max_H = math.log(3)
        norm_H = H / max_H if max_H > 0 else 0.0
        delta = d + self.lambda_ * (1 - norm_H)
        verdict = "PASS" if delta <= self.threshold else "FAIL"
        return {"delta": delta, "verdict": verdict}

    # --- Overlay integration helpers (for Elpis native overlay) ---
    def start_event_loop(self, poll_interval: float = 1.0, on_tick: Optional[callable] = None):
        """Start a lightweight event loop suitable for embedding in a fabric.

        The loop runs in a background thread and calls `on_tick(processor)` each
        poll interval when provided. This keeps the overlay cooperative and
        friendly to fabric schedulers.
        """
        if self._running:
            return
        self._running = True

        def _loop():
            while self._running:
                try:
                    # Heartbeat: preserve last-known state and allow callbacks
                    if on_tick:
                        on_tick(self)
                except Exception:
                    # Overlay should never crash the fabric; swallow and record
                    self._state.setdefault("errors", []).append("tick-error")
                time.sleep(poll_interval)

        self._thread = threading.Thread(target=_loop, name="OuroborosOverlayLoop", daemon=True)
        self._thread.start()

    def stop_event_loop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

    # Convenience entrypoints for integration
    def snapshot_state(self) -> Dict[str, Any]:
        """Return a minimal snapshot suitable for federated ledgers or audits."""
        return {
            "radius": self.R,
            "lambda": self.lambda_,
            "threshold": self.threshold,
            "meta": self._state,
        }


def create_elpis_processor(config: Optional[Dict[str, Any]] = None) -> OuroborosVirtualProcessor:
    """Factory to create a configured processor instance for Elpis.

    Keeps wiring options minimal so a fabric can call this natively.
    """
    cfg = config or {}
    radius = float(cfg.get("radius", 1.0))
    lambda_ = float(cfg.get("lambda", 0.3))
    threshold = float(cfg.get("threshold", 0.4))
    return OuroborosVirtualProcessor(radius=radius, lambda_=lambda_, threshold=threshold)


__all__ = ["OuroborosVirtualProcessor", "create_elpis_processor"]


if __name__ == "__main__":
    # Example: run a small self-check loop when executed directly
    processor = create_elpis_processor()
    V_exp = [0.4, 0.2, 0.4]
    V_obs = [0.35, 0.25, 0.4]
    print(processor.delta_check(V_exp, V_obs))
