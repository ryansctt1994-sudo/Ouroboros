# Release Checklist — AIOS: Ouroboros

Run this checklist for every public or beta release. Complete every item in
order. A single unchecked item that touches a red-star (🔴) category blocks
shipping. Yellow-star (🟡) items are strongly recommended but not absolute
blocks if a documented exception exists.

---

## Pre-Build

- [ ] All milestone tickets in "Done" or explicitly deferred with owner noted.
- [ ] `CHANGELOG.md` entry drafted (player-facing language, not commit hashes).
- [ ] Save compatibility confirmed: new build loads a save from the previous release.
- [ ] 🔴 No open P0/P1 bugs (crash / progression block / data loss).
- [ ] Version bumped in `scripts/build/generate-build-metadata.sh` (or via tag).

## Build & Smoke Test

- [ ] 🔴 `ue5-build.yml` CI passes (Win64 Shipping + Linux Shipping green).
- [ ] 🔴 Smoke test (`AIOS.Smoke`) exits 0 on both platform artifacts.
- [ ] Build string visible in main menu: `vX.Y.Z+SHA`.
- [ ] Artifact size within depot budget (Win64 < 4 GB; Linux < 4 GB).

## QA Sign-Off

- [ ] 🔴 Fresh-install test on clean Windows VM (Steam install, no dev tools).
- [ ] 🔴 Full critical-path playthrough without progression block.
- [ ] 🟡 Steam Deck test: boots, controller works, ≥ 40 fps on SteamDeck preset.
- [ ] 🟡 Save/Cloud: two-machine sync test passes.
- [ ] 🟡 Offline play → reconnect → Cloud sync without data loss.
- [ ] Controller-only playthrough: no mouse-required flows.
- [ ] Safe-mode launch (`-safemode`) boots to menu at 1280×720 Low.

## Steam Depot Upload

- [ ] `steam-upload.yml` dispatched; `internal` branch updated in Steamworks.
- [ ] 🔴 Verify depot in Steamworks partner portal (file count, depot size).
- [ ] `steam_appid.txt` absent from Win64 depot (automated check in VDF).
- [ ] VC++ redist depot (484) includes current `vcredist_x64.exe`.
- [ ] Patch notes added to Steamworks → Community → News (even for internal).

## Promotion Gates

- [ ] 🔴 QA lead sign-off on release-gate.md checklist.
- [ ] 🔴 Lead engineer sign-off.
- [ ] Internal → Beta: 48-hour soak with opt-in testers.
- [ ] 🔴 Beta → Public: no new P0/P1 found in beta soak.
- [ ] Rollback build pinned to `rollback` Steam branch before promoting to public.

## Post-Release (within 24 h)

- [ ] Monitor Steam Discussion boards + crash reporter.
- [ ] Monitor frame-time telemetry (if instrumented).
- [ ] Hotfix branch created and ready (`hotfix/vX.Y.Z+1`).
- [ ] Update `CHANGELOG.md` with release date.
