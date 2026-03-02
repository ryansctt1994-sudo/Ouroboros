# Asset Naming Conventions — AIOS: Ouroboros

Consistent naming prevents duplicates, missing references, and cook errors.
All contributors must follow this scheme. Violations are caught by the
Editor Utility Widget validator (planned: `Content/Tools/NamingValidator`).

---

## General Rules

1. **PascalCase** for all assets: `PlayerCharacterMesh`, not `player_character_mesh`.
2. **Prefix** every asset with its type code (see table below).
3. **No spaces**, no special characters except `_`.
4. **Folder mirrors function**: `Characters/Player/`, `Environments/Cathedral/`, etc.
5. Generated/auto-imported assets (FBX → UE): rename immediately on import.

---

## Prefix Table

| Asset Type | Prefix | Example |
|------------|--------|---------|
| Blueprint (Actor) | `BP_` | `BP_SovereignCharacter` |
| Blueprint (Component) | `BPC_` | `BPC_RitualInvoker` |
| Blueprint (Interface) | `BPI_` | `BPI_ConstitutionalGate` |
| Blueprint (Function Library) | `BPFL_` | `BPFL_AIOSUtils` |
| Static Mesh | `SM_` | `SM_CathedralPillar` |
| Skeletal Mesh | `SKM_` | `SKM_SovereignBody` |
| Skeleton | `SK_` | `SK_Sovereign` |
| Physics Asset | `PA_` | `PA_SovereignRagdoll` |
| Animation Sequence | `AS_` | `AS_Sovereign_Idle` |
| Animation Blueprint | `ABP_` | `ABP_Sovereign` |
| Blend Space | `BS_` | `BS_Sovereign_Walk` |
| Material | `M_` | `M_CathedralStone` |
| Material Instance | `MI_` | `MI_CathedralStone_Worn` |
| Material Function | `MF_` | `MF_PBR_Roughness` |
| Texture (diffuse/base) | `T_` | `T_CathedralStone_D` |
| Texture (normal) | `T_` | `T_CathedralStone_N` |
| Texture (packed ORM) | `T_` | `T_CathedralStone_ORM` |
| Texture (UI) | `T_UI_` | `T_UI_RitualButton` |
| Particle System (Niagara) | `NS_` | `NS_RitualInvocation` |
| Sound Wave | `SW_` | `SW_RitualChime` |
| Sound Cue | `SC_` | `SC_Ambient_Cathedral` |
| Sound Attenuation | `ATT_` | `ATT_Indoor` |
| Data Asset | `DA_` | `DA_AchievementList` |
| Data Table | `DT_` | `DT_EnemyStats` |
| Widget Blueprint | `WBP_` | `WBP_HUD_Main` |
| Level | `L_` | `L_AIOS_MainMenu` |
| Level (sub-level) | `LS_` | `LS_Cathedral_Lighting` |
| Map (test) | `TEST_` | `TEST_SmokeTest` |

---

## Texture Suffix Conventions

| Suffix | Contents |
|--------|----------|
| `_D` | Diffuse / Base Colour (sRGB) |
| `_N` | Normal map (linear) |
| `_ORM` | Occlusion (R) / Roughness (G) / Metallic (B) |
| `_E` | Emissive |
| `_M` | Mask |
| `_A` | Alpha |

---

## Content Folder Structure

```
Content/
├── Characters/
│   ├── Sovereign/
│   └── NPCs/
├── Environments/
│   ├── Cathedral/
│   └── Shared/
├── FX/
│   ├── Niagara/
│   └── Materials/
├── Maps/
│   ├── AIOS_MainMenu.umap
│   ├── SmokeTest.umap
│   └── ...
├── Sound/
├── UI/
│   ├── Menus/
│   └── HUD/
└── Tools/        ← Editor Utility Widgets, validators
```
