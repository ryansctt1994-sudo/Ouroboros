# Save Compatibility Policy — AIOS: Ouroboros

Saves are a **trust contract** with the player. A build that corrupts or
silently discards a save destroys that trust permanently.

---

## Schema Versioning

Every save file written by `UAIOSSaveGame` contains:

```cpp
int32 SaveVersion;   // incremented on every breaking schema change
FString BuildVersion; // e.g. "1.2.0+abc1234"
FString LastSavedAt; // ISO 8601 UTC
```

`AIOS_SAVE_VERSION` is a compile-time constant in `AIOSSaveGame.h`.

**Rule**: increment `AIOS_SAVE_VERSION` and add a migration case whenever
you make a breaking schema change (field removed, type changed, semantics
changed). Additive changes (new field with a safe default) do not require
a version bump but should be documented here.

---

## Migration Rules

1. **Every version delta has a migration case** in `UAIOSSaveGame::MigrateFromVersion()`.
2. Migrations are **forward-only**: version N → N+1 → … → CURRENT.
3. Migrations must be **idempotent**: calling them twice produces the same result.
4. If migration is impossible (e.g. fundamentally incompatible format), the game
   must: back up the old save, warn the player, and start a new slot.
   It must **never crash**.

### Adding a migration (checklist)

- [ ] Increment `AIOS_SAVE_VERSION` in `AIOSSaveGame.h`.
- [ ] Add `case (N):` block in `MigrateFromVersion()` with safe defaults.
- [ ] Write a save-compatibility test: create a v(N-1) save payload, load with
      current build, assert state is correct.
- [ ] Note the change in this document under **Version History**.

---

## Steam Cloud Conflict Policy

When Steam detects a conflict (local save vs. cloud save with different
timestamps), it prompts the player. Our policy:

- **Either choice must produce a working game.** We do not make assumptions
  about which copy the player picks.
- If the chosen save is an older schema version, `MigrateToCurrentVersion()`
  runs automatically on load.
- Test matrix (must pass before every beta promotion):
  1. Play on machine A → save → close. Play on machine B offline → save →
     open → conflict prompt → choose "cloud" → game works.
  2. Same, but choose "local" → game works.

---

## Save Location

| Platform | Path |
|----------|------|
| Windows | `%LOCALAPPDATA%\AIOS\Saved\SaveGames\AIOSProgress.sav` |
| Linux / Steam Deck | `~/.local/share/AIOS/Saved/SaveGames/AIOSProgress.sav` |
| Steam Cloud | Synced automatically by UE's SaveGame + Steam OSS |

---

## Version History

| Save Version | Build Version | Change |
|-------------|---------------|--------|
| 1 | 1.0.0 | Initial release schema |
