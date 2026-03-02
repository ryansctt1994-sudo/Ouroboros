# Archive

## v1-core/

This directory contains the historical v1.0 copies of the root-level ECS packages:

- `core/` — v1.0 Entity Component System core (Entity, Component, System, World)
- `components/` — v1.0 component implementations (metacube, loyalty)
- `systems/` — v1.0 system implementations (consciousness)

These packages are **superseded** by the v2.0 implementation in [`eden_ecs/`](../eden_ecs/).

Do **not** import from these directories in new code. Use `eden_ecs` instead:

```python
from eden_ecs import World, EntityType, TimestepMode
from eden_ecs.core.world import World
from eden_ecs.components import METACUBEComponent, MemoryLattice
from eden_ecs.systems import VetoSystem, PalindromeDescentSystem
```

These files are retained here for historical reference only.
