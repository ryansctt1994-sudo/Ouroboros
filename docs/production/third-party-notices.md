# Third-Party Notices — AIOS: Ouroboros

This file documents third-party software, libraries, and assets used in
AIOS: Ouroboros and the licenses under which they are distributed.

**Maintainer duty**: update this file whenever a new dependency is added.
Licenses must be reviewed before inclusion. GPL-licensed code may not be
included in a commercial product without satisfying GPL terms.

---

## Unreal Engine 5.3

- **License**: Unreal Engine End User License Agreement (EULA)
- **URL**: https://www.unrealengine.com/en-US/eula/unreal
- Requires: "Powered by Unreal Engine" credit in credits screen for public release.

## Steam / Steamworks SDK

- **License**: Steamworks API license (part of Steam Distribution Agreement)
- **URL**: https://partner.steamgames.com/documentation/sdk
- The Steamworks SDK is integrated via UE5's OnlineSubsystemSteam plugin.
  Redistribution of `steam_api64.dll` is permitted under the SDK license.

## Rust Standard Library & Cargo dependencies

- Cargo dependencies are listed in `Cargo.toml` / `Cargo.lock`.
- Run `cargo license` to generate a current SPDX dependency report.
- All dependencies must be Apache-2.0, MIT, BSD-2, BSD-3, or ISC licensed
  for inclusion in a shipped product.

## UE5 Marketplace / Fab assets (if any)

> Document each Marketplace asset here with its license type (Standard/Plus).
> Standard license: single product, no resale of raw assets.

| Asset Name | Publisher | License | URL |
|------------|-----------|---------|-----|
| *(none at this time)* | | | |

## Fonts

> Document any fonts embedded in Content/Fonts/ here.

| Font Name | License | URL |
|-----------|---------|-----|
| *(none at this time)* | | |

## Audio

> Document any licensed audio/music tracks here.

| Track / Pack Name | License | URL |
|-------------------|---------|-----|
| *(none at this time)* | | |

---

## Legal Checklist (before shipping)

- [ ] All Marketplace/Fab licenses allow commercial use in a shipped game.
- [ ] "Powered by Unreal Engine" credit appears in credits screen.
- [ ] No GPL-licensed code in the shipping product.
- [ ] Privacy policy published if any telemetry or crash reporting is enabled.
- [ ] EULA / Terms of Service linked from the Steam store page.
- [ ] Third-party notices file included in the packaged build
      (`Content/Legal/ThirdPartyNotices.txt` or equivalent).
