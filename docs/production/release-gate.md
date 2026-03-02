# Release Gate Checklist — AIOS: Ouroboros

Every build promoted to **beta** or **public** must pass every gate below.
A single FAIL blocks promotion. No exceptions.

---

## G0 — Clean Install Boot
| Check | Pass Criteria |
|-------|---------------|
| Fresh Steam install on clean Windows 10 VM | Game reaches main menu without user intervention |
| No extra runtime prompts | VC++ / DX runtime handled silently via Steam redist depot |
| Steam overlay functional | Shift+Tab opens overlay in-game |
| `steam_appid.txt` absent from depot | File must not ship in the Win64 depot |

## G1 — Stability
| Check | Pass Criteria |
|-------|---------------|
| 10-hour soak test (idle + gameplay loops) | Zero crashes; no memory growth > 200 MB over baseline |
| No known P0/P1 crashers | Zero open crash bugs with repro steps |
| No progression blockers | Player can complete the critical path start → finish |
| Alt-tab × 50 | No crash, no corrupted render state |
| Controller disconnect/reconnect mid-session | Graceful prompt; no crash |

## G2 — Save & Cloud
| Check | Pass Criteria |
|-------|---------------|
| Save written and loaded in same session | Slot reloads with identical state |
| Save from build N-1 loads on build N | Migration runs; no data loss |
| Steam Cloud: new machine pulls save | Progress present on second machine |
| Steam Cloud: conflict prompt | Either choice (local / remote) produces working game |
| Offline play → reconnect → sync | Progress synced; no duplicate slot corruption |

## G3 — Steam Deck (via Proton)
| Check | Pass Criteria |
|-------|---------------|
| Boots in Gaming Mode | Reaches main menu within 60 s |
| Steam Deck preset applied | Stable ≥ 40 fps in representative scene |
| All text readable at native 1280×800 | No strings clipped or sub-12pt effective size |
| Controller-only playthrough | No flow requires mouse or keyboard |
| Suspend / resume × 10 | No crash; audio resumes correctly |

## G4 — Reproducible Build
| Check | Pass Criteria |
|-------|---------------|
| CI produces Shipping artifact from clean checkout | Build succeeds with zero manual steps |
| Build string visible in main menu | Shows `version+commitSHA` |
| Artifact size within budget | Win64 depot < 4 GB (adjust per content plan) |
| Smoke test passes in CI | `AIOS.Smoke` automation tests exit 0 |

## G5 — Steam Upload
| Check | Pass Criteria |
|-------|---------------|
| `steam-upload.yml` uploads to `internal` branch | Depot visible in Steamworks partner portal |
| Promotion to `beta` requires manual approval | No auto-push to beta or public |
| Rollback available | Previous build accessible on `rollback` branch |
| No secrets in build artifacts or logs | CI log scan shows no credentials |

---

## Release Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Lead Engineer | | | |
| QA Lead | | | |
| Producer | | | |
