"""
ABRAXIS Phase H — Multi-User WebSocket Voice-to-Gnosis Dashboard
================================================================
MIT License — © 2025-2026 The Ouroboros Foundation
See /LICENSE for the Ethical Use Covenant.

This module provides a multi-user WebSocket server that accepts voice
transcriptions (or raw text) from connected clients and routes them
through the gnosis pipeline (knowledge synthesis, coherence scoring,
phasonic scheduling) before broadcasting results to all observers.

Architecture
------------
  Browser / mic client
      │  WebSocket (ws://host:8765)
      ▼
  GnosisHub (asyncio server)
      │  route_voice() → GnosisProcessor
      ▼
  GnosisProcessor
      │  EDEN-ECS bridge  →  coherence score
      │  phasonic gate    →  admission decision
      │  knowledge reply  →  gnosis response
      ▼
  broadcast to all connected observers
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Set

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class VoicePacket:
    """A voice/text packet received from a client."""

    client_id: str
    transcript: str
    timestamp: float = field(default_factory=time.time)
    packet_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class GnosisResponse:
    """Synthesised gnosis response sent back to all observers."""

    packet_id: str
    client_id: str
    transcript: str
    gnosis: str
    coherence: float
    phase_admitted: bool
    timestamp: float = field(default_factory=time.time)


# ---------------------------------------------------------------------------
# Gnosis processor
# ---------------------------------------------------------------------------


class GnosisProcessor:
    """
    Routes a VoicePacket through the knowledge-synthesis pipeline.

    In production this would call into the EDEN-ECS bridge and the
    phasonic scheduler.  This implementation provides a deterministic
    reference behaviour that the bridge can be swapped in over.
    """

    GNOSIS_THRESHOLD = 0.50   # minimum coherence to admit a packet
    PHASE_FREQ_HZ = 0.0997    # "Chuckle Constant" — phasonic scheduler freq

    def __init__(self) -> None:
        self._phase: float = 0.0
        self._last_tick: float = time.time()

        # Optional EDEN-ECS bridge (injected if available)
        self._eden_bridge: Any | None = None

    # ------------------------------------------------------------------
    # Phase clock
    # ------------------------------------------------------------------

    def _advance_phase(self) -> float:
        """Advance the PLL phase and return the current value in [0, 2π)."""
        import math
        now = time.time()
        dt = now - self._last_tick
        self._last_tick = now
        self._phase = (self._phase + 2 * math.pi * self.PHASE_FREQ_HZ * dt) % (
            2 * math.pi
        )
        return self._phase

    def _phase_admitted(self, phase: float) -> bool:
        """Return True when the phase is in the authorised admission sector."""
        import math
        # Admit when phase is within π/4 of 0 (top of cycle)
        return phase < math.pi / 4 or phase > 7 * math.pi / 4

    # ------------------------------------------------------------------
    # Coherence scoring
    # ------------------------------------------------------------------

    def _coherence_score(self, transcript: str) -> float:
        """
        Produce a coherence score ∈ [0, 1] for the given transcript.

        Uses the EDEN-ECS bridge when available; falls back to a simple
        length-normalised heuristic so the pipeline remains functional
        without external dependencies.
        """
        if self._eden_bridge is not None:
            try:
                return float(self._eden_bridge.score(transcript))
            except Exception:  # pylint: disable=broad-except
                pass
        # Heuristic fallback: longer, richer transcripts score higher
        words = transcript.split()
        score = min(1.0, len(words) / 20.0)
        return round(score, 4)

    # ------------------------------------------------------------------
    # Knowledge synthesis
    # ------------------------------------------------------------------

    def _synthesise_gnosis(self, transcript: str, coherence: float) -> str:
        """Return a gnosis string summarising the synthesised knowledge."""
        level = (
            "high" if coherence >= 0.75
            else "moderate" if coherence >= 0.50
            else "low"
        )
        return (
            f"[gnosis:{level}] Processed transcript of {len(transcript.split())} words "
            f"(coherence={coherence:.3f}). "
            "Knowledge integrated into the mycelial substrate."
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, packet: VoicePacket) -> GnosisResponse:
        """Process a voice packet and return a gnosis response."""
        phase = self._advance_phase()
        admitted = self._phase_admitted(phase)
        coherence = self._coherence_score(packet.transcript)

        if not admitted or coherence < self.GNOSIS_THRESHOLD:
            gnosis = (
                "[gnosis:vetoed] Packet did not meet admission criteria "
                f"(phase_admitted={admitted}, coherence={coherence:.3f})."
            )
        else:
            gnosis = self._synthesise_gnosis(packet.transcript, coherence)

        return GnosisResponse(
            packet_id=packet.packet_id,
            client_id=packet.client_id,
            transcript=packet.transcript,
            gnosis=gnosis,
            coherence=coherence,
            phase_admitted=admitted,
        )

    def attach_eden_bridge(self, bridge: Any) -> None:
        """Attach an EDEN-ECS bridge for enhanced coherence scoring."""
        self._eden_bridge = bridge


# ---------------------------------------------------------------------------
# WebSocket hub
# ---------------------------------------------------------------------------


class GnosisHub:
    """
    Asyncio WebSocket server hub for Phase H.

    Each connected client is assigned a unique ``client_id``.  Incoming
    messages are JSON-decoded as ``{"transcript": "..."}``; the hub
    processes them through ``GnosisProcessor`` and broadcasts the result
    to **all** connected observers (including the sender).
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        self.host = host
        self.port = port
        self._clients: Dict[str, Any] = {}   # client_id → websocket
        self._processor = GnosisProcessor()

    # ------------------------------------------------------------------
    # Client lifecycle
    # ------------------------------------------------------------------

    async def _register(self, websocket: Any) -> str:
        client_id = str(uuid.uuid4())[:8]
        self._clients[client_id] = websocket
        logger.info("Client connected: %s (total=%d)", client_id, len(self._clients))
        await websocket.send(
            json.dumps({"event": "connected", "client_id": client_id})
        )
        return client_id

    async def _unregister(self, client_id: str) -> None:
        self._clients.pop(client_id, None)
        logger.info("Client disconnected: %s (total=%d)", client_id, len(self._clients))

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    async def _handle(self, websocket: Any) -> None:
        client_id = await self._register(websocket)
        try:
            async for raw in websocket:
                try:
                    data = json.loads(raw)
                    transcript = str(data.get("transcript", "")).strip()
                    if not transcript:
                        continue
                    packet = VoicePacket(
                        client_id=client_id, transcript=transcript
                    )
                    response = self._processor.process(packet)
                    await self._broadcast(response)
                except (json.JSONDecodeError, KeyError) as exc:
                    logger.warning("Bad message from %s: %s", client_id, exc)
        finally:
            await self._unregister(client_id)

    async def _broadcast(self, response: GnosisResponse) -> None:
        """Send the gnosis response to every connected observer."""
        payload = json.dumps(asdict(response))
        dead: Set[str] = set()
        for cid, ws in list(self._clients.items()):
            try:
                await ws.send(payload)
            except Exception:  # pylint: disable=broad-except
                dead.add(cid)
        for cid in dead:
            self._clients.pop(cid, None)

    # ------------------------------------------------------------------
    # Server lifecycle
    # ------------------------------------------------------------------

    async def serve(self) -> None:
        """Start the WebSocket server (runs until cancelled)."""
        try:
            import websockets  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "Phase H requires the 'websockets' package: pip install websockets"
            ) from exc

        logger.info("Phase H GnosisHub listening on ws://%s:%d", self.host, self.port)
        async with websockets.serve(self._handle, self.host, self.port):
            await asyncio.Future()  # run forever

    def attach_eden_bridge(self, bridge: Any) -> None:
        """Propagate an EDEN-ECS bridge to the processor."""
        self._processor.attach_eden_bridge(bridge)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="ABRAXIS Phase H — Voice-to-Gnosis WebSocket Dashboard"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8765, help="Bind port")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    hub = GnosisHub(host=args.host, port=args.port)
    asyncio.run(hub.serve())


if __name__ == "__main__":
    main()
