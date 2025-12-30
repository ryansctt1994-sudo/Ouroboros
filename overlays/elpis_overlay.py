"""Elpis overlay registration and glue for fabric_core.

This module provides a lightweight adapter so Elpis can run the
OuroborosVirtualProcessor natively as one of its principal overlays.

It attempts to be non-prescriptive about fabric_core's API: it will first
attempt to call a `register_overlay` function on the fabric, and if missing
will fall back to inserting into a fabric.overlays mapping.
"""
from typing import Any, Dict

from ouroboros_processor import create_elpis_processor, OuroborosVirtualProcessor


class ElpisOverlay:
    """Adapter that exposes the Ouroboros processor as a fabric overlay."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.processor: OuroborosVirtualProcessor = create_elpis_processor(self.config)
        self._attached = False

    def start(self, poll_interval: float = 1.0):
        """Start the overlay's execution loop in a non-blocking way."""
        # Example on_tick callback: could push snapshots into fabric ledgers
        def on_tick(proc: OuroborosVirtualProcessor):
            # Minimal heartbeat: record a snapshot; integration points may push this
            proc._state.setdefault("last_snapshot", proc.snapshot_state())

        self.processor.start_event_loop(poll_interval=poll_interval, on_tick=on_tick)

    def stop(self):
        self.processor.stop_event_loop()


def register_elpis_overlay(fabric: Any, name: str = "elpis", config: Dict[str, Any] = None) -> ElpisOverlay:
    """Register the Elpis overlay with the host fabric.

    Usage (inside fabric_core):
        from overlays.elpis_overlay import register_elpis_overlay
        register_elpis_overlay(self)

    The function attempts multiple registration strategies so it works with
    simple fabrics (exposing `register_overlay`) or with minimal mapping based
    fabrics (exposing `overlays` dict).
    """
    overlay = ElpisOverlay(config=config)

    # Preferred API: fabric.register_overlay(name, factory_or_instance)
    try:
        register_fn = getattr(fabric, "register_overlay", None)
        if callable(register_fn):
            register_fn(name, overlay)
            overlay._attached = True
            return overlay
    except Exception:
        pass

    # Fallback: fabric.overlays mapping
    try:
        overlays_map = getattr(fabric, "overlays", None)
        if isinstance(overlays_map, dict):
            overlays_map[name] = overlay
            overlay._attached = True
            return overlay
    except Exception:
        pass

    # If neither strategy succeeded, attach nothing but return the overlay so
    # the caller may manage it manually.
    return overlay


__all__ = ["ElpisOverlay", "register_elpis_overlay"]
