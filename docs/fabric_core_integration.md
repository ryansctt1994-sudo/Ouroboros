# Integrating OuroborosProcessor as an Elpis overlay in fabric_core

This document explains how to wire the OuroborosVirtualProcessor into your
fabric_core so that Elpis can run it natively as a principal overlay.

1) Place the files

- `ouroboros_processor.py` — provides `create_elpis_processor(...)` and the
  `OuroborosVirtualProcessor` class.
- `overlays/elpis_overlay.py` — adapter with `register_elpis_overlay(fabric)`.

2) Register the overlay from `fabric_core.py`

Add a call during your fabric initialization. Examples below assume `fabric`
is `self` inside a `FabricCore` class. Adjust as appropriate for your codebase.

```python
# fabric_core.py (excerpt)
from overlays.elpis_overlay import register_elpis_overlay

# inside your fabric initialization
elpis_overlay = register_elpis_overlay(self, name="elpis")
# Optionally start the overlay with desired poll interval
elpis_overlay.start(poll_interval=1.0)
```

The registration function will try to call `self.register_overlay(name, overlay)`
if available or fall back to inserting into `self.overlays[name]` when that is
a dict. If your fabric has a different registration convention, instantiate
`ElpisOverlay` directly and manage it:

```python
from overlays.elpis_overlay import ElpisOverlay
elpis = ElpisOverlay(config={"threshold": 0.35})
elpis.start()
```

3) Auditing and Ledgers

The processor exposes `snapshot_state()` to allow fabrics to capture checkpoints
and push them into a ledger or audit trail. Use `processor.snapshot_state()`
inside your fabric's scheduler or heartbeat to record provenance.

4) Notes on native execution

- The implementation is stdlib-only and lightweight so it can run in
  constrained or air-gapped environments.
- Keep `on_tick` callbacks idempotent and fast; heavy work should be
  delegated to the fabric's job queue.

If you want, I can also update `fabric_core.py` directly to add a registration
call — provide the file path and I will patch it in-place.
