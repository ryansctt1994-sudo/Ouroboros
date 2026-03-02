# Steam Operations — AIOS: Ouroboros

Single reference for everything Steam-related: AppID, depots, branches,
CI credentials, store assets, Steam Deck, and the pre-launch checklist.

---

## 0) AppID

| Environment | AppID | Notes |
|-------------|-------|-------|
| Development | **480** | Valve's public "Spacewar" test title — valid for SDK testing |
| Production | **YOUR_REAL_ID** | Obtained from Steamworks partner portal after app creation |

**To swap AppID from 480 to your real ID:**
1. `grep -r "480" ue/Symbiont/Config/ steam/ scripts/steam/` — list every occurrence.
2. Replace all `480` with your real AppID.
3. Rename `steam/input/game_actions_480.vdf` → `game_actions_<REAL_ID>.vdf`.
4. Update depot IDs (481 → real Win64 depot, 482 → real Linux depot) in
   `steam/depots/app_build_win64.vdf` and `steam/depots/app_build_linux.vdf`.
5. Commit and push. CI will use the updated values.

---

## 1) Depot Map

| Depot ID (placeholder) | Platform | Contents |
|------------------------|----------|----------|
| 481 | Win64 | Game binary + cooked content |
| 482 | Linux | Game binary + cooked content |
| 484 | Win64 | VC++ 2022 Redistributable install script |

> Replace placeholder IDs with real depot IDs from Steamworks → App Admin → Depots.

---

## 2) Branch Strategy

| Branch | Audience | How to promote |
|--------|----------|---------------|
| `internal` | Team only | CI auto-uploads on every successful Shipping build |
| `beta` | Opt-in testers | Manual dispatch of `steam-upload.yml` with `branch=beta` |
| `public` | All users | Manual approval only; requires release-gate sign-off |
| `rollback` | Fallback | Pin the last known-good build before every public push |

**Rule**: nothing reaches `public` without a human pressing "Approve" in GitHub Actions.

---

## 3) CI / Upload Credentials

Store as **GitHub Actions Secrets** (Settings → Secrets → Actions):

| Secret | Value |
|--------|-------|
| `STEAM_USERNAME` | Dedicated Steam build account username |
| `STEAM_PASSWORD` | Password for build account |
| `STEAM_TOTP_SECRET` | Base-32 TOTP secret from Steam Guard Mobile Authenticator |

Store as **GitHub Actions Variables** (Settings → Variables):

| Variable | Value |
|----------|-------|
| `STEAM_APP_ID` | Your real AppID |
| `STEAM_DEPOT_WIN64` | Your Win64 depot ID |
| `STEAM_DEPOT_LINUX` | Your Linux depot ID |
| `UE_ROOT` | Path to UE 5.3 on your self-hosted runner |

**Never commit credentials.** If a secret leaks: revoke immediately, rotate,
and audit Steamworks access logs.

---

## 4) Steam Input

Action manifest: `steam/input/game_actions_480.vdf`
(rename to `game_actions_<REAL_ID>.vdf` for shipping).

Place next to the game executable in the depot, or configure the path via:
```cpp
SteamInput()->SetInputActionManifestFilePath(...)
```

Default bindings provided for: **Xbox 360**, **PS4**, **Steam Deck**.
Add PS5 and Switch Pro bindings before launch.

---

## 5) Steam Cloud Save Configuration

In Steamworks partner portal → App Admin → Cloud:

| Setting | Value |
|---------|-------|
| Byte quota per user | 100 MB (adjust as needed) |
| File sync pattern | `SaveGames\*` (Windows), `SaveGames/*` (Linux) |
| Root path override | UE default (`%LOCALAPPDATA%\AIOS\Saved\`) |

Test matrix before every beta promotion:
- [ ] Machine A saves → Machine B loads → data intact.
- [ ] Conflict prompt → choose either option → game works.
- [ ] Offline play → sync → no data loss.

See `docs/production/save-compatibility.md` for schema versioning policy.

---

## 6) Steam Achievements

Achievements are defined in `ue/Symbiont/Config/DefaultGame.ini` and must
be **registered in Steamworks partner portal** before they can be unlocked.

Steps:
1. Steamworks → App Admin → Stats & Achievements.
2. Create each achievement with the same ID string as in DefaultGame.ini
   (e.g. `ACH_FIRST_RITUAL`).
3. Upload achievement icons (64×64 and 256×256 PNG).
4. Publish changes.

**Golden rule**: if Steam is unavailable, achievements queue locally
(`AIOSGameInstance::AchievementQueue`) and flush on next session.
The game never crashes due to a missing Steam connection.

---

## 7) Steam Deck Checklist

Before submitting for Deck Verified / Playable review:

- [ ] Game boots in Gaming Mode without keyboard.
- [ ] All text readable at 1280×800 (no sub-12pt effective size).
- [ ] "Steam Deck" graphics preset exists and delivers ≥ 40 fps.
- [ ] Controller glyphs match Steam Deck hardware (A/B/X/Y, trackpads).
- [ ] No flow requires mouse or keyboard.
- [ ] Suspend / resume works (test × 10 cycles).
- [ ] No "Requires Agreement" modal on first launch (EULA must use Steam's overlay).
- [ ] `steam/input/game_actions_<ID>.vdf` present in depot.

Proton testing (before native Linux depot, if any):
- Install via Steam on Linux with Proton Experimental.
- Test same checklist above.

---

## 8) Store Page Assets (required before going public)

| Asset | Size | Format | Notes |
|-------|------|--------|-------|
| Header capsule | 460×215 px | JPG/PNG | Main store tile |
| Small capsule | 231×87 px | JPG/PNG | Search results |
| Large capsule | 616×353 px | JPG/PNG | Featured carousel |
| Main capsule | 630×360 px | JPG/PNG | |
| Screenshots | 1280×720 minimum | JPG/PNG | ≥ 5; show gameplay, UI readable |
| Trailer | — | MP4/MOV | Show core verb in first 5 seconds |
| Background | 1438×810 px | JPG/PNG | Store page background (optional) |
| Icon | 32×32 px | ICO | Windows taskbar |

**Do not use placeholder capsules in the public store** — they are a common
cause of low wishlist conversion.

---

## 9) Pre-Launch Checklist (Steam-specific)

- [ ] Real AppID configured everywhere (grep for `480`).
- [ ] Depot IDs correct in all VDF files.
- [ ] `steam_appid.txt` excluded from all shipping depots.
- [ ] Store page complete: capsules, ≥ 5 screenshots, trailer.
- [ ] System requirements accurate (min / recommended spec).
- [ ] Tags accurate (do not bait-and-switch genre tags).
- [ ] EULA / Terms linked from store page (required if multiplayer or telemetry).
- [ ] Privacy policy linked if any data collection occurs.
- [ ] Steam Cloud enabled and tested.
- [ ] Achievements registered and icons uploaded.
- [ ] Steam Input manifest in depot.
- [ ] VC++ redist depot built and included.
- [ ] Release-gate checklist (`docs/production/release-gate.md`) signed off.
