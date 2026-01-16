# Giggle-Forest Demo Content

**Location:** `ue/Symbiont/Content/Demos/GiggleForest/`  
**Status:** Placeholder directory (no binary assets committed)

---

## Purpose

This directory is reserved for Giggle-Forest demo assets that must be created manually in the UE5 editor. Binary Unreal assets (`.uasset`, `.umap`) are excluded from version control per repository policy.

---

## What Should Be Here (When You Build The Demo)

After following the instructions in `docs/DEMO_GIGGLE_FOREST_BLUEPRINT_SPEC.md`, you should create the following assets in this directory:

### Level
- **GiggleForest_Main.umap** - The main AR forest level
  - Contains landscape, lighting, fog, and spawn points
  - See Blueprint spec for detailed setup instructions

### Blueprints
- **BP_Symbiont_IntroUI.uasset** - Widget Blueprint (gesture gate UI)
- **BP_SymbiontManager.uasset** - Actor managing symbiont agents
- **BP_ZorelAgent.uasset** - Chaos agent actor
- **BP_QuillanAgent.uasset** - Stabilizer agent actor
- **BP_SymbiontHUD.uasset** - HUD displaying constitutional metrics

### Materials
- **M_Zorel_Iridescent.uasset** - Velocity-driven hue-shifting material
- **M_Quillan_Matte.uasset** - Pulsating emissive material
- **M_ForestGround.uasset** - Landscape material (optional)

### Niagara Systems
- **NS_Lumen_Ignition_Burst.uasset** - Gold particle burst on consent
- **NS_ChaoticTrail.uasset** - Zorel movement trail particles

### Audio
- **SFX_SOISOISOI_Resonance_111Hz.uasset** - 111Hz sine wave sound
- **SFX_Fusion_Chime.uasset** - Agent fusion audio cue
- **SFX_Warning_Beep.uasset** - Constitutional threshold alert

### Textures
- **T_ConstitutionalSeal.uasset** - Badge/emblem for HUD (512x512)

---

## Creating Assets

1. Open UE5 editor with the Symbiont project
2. Right-click in this directory within the Content Browser
3. Create assets using the "Blueprint Class", "Material", "Niagara System", etc. menus
4. Follow the node graph specifications in `docs/DEMO_GIGGLE_FOREST_BLUEPRINT_SPEC.md`
5. Assign materials, sounds, and particles to Blueprint components

---

## Why Aren't These Committed?

Binary Unreal assets are excluded from the repository because:
- They are large files (often 1-10MB each)
- They create merge conflicts easily
- They are platform-specific (cooked data differs between Windows/Mac/iOS)
- The specifications in `docs/` provide sufficient instructions to recreate them

---

## Testing Without Assets

If you open the Symbiont project without creating these assets:
- The level will not exist (create a blank level to test C++ code)
- Blueprints will show "missing class" errors (expected until plugin is compiled)
- The C++ plugin (`SymbiontCore`) will compile successfully regardless

To test the C++ engine without full demo assets:
1. Compile the SymbiontCore plugin
2. Create a minimal test level
3. Add a Blueprint actor with a `USymbiontCoreEngine` component
4. Call `InitializeSymbiont()` and `RequestDeepReasoning()` from BeginPlay
5. Check logs for stub messages

---

## File Size Expectations

Once created, this directory will contain approximately:
- **Level files:** ~5-10MB (GiggleForest_Main.umap + sublevels)
- **Blueprint files:** ~2-5MB total (all BP_* assets)
- **Materials:** ~1-2MB total (all M_* assets)
- **Niagara systems:** ~1-2MB total (all NS_* assets)
- **Audio:** ~500KB total (short SFX files)
- **Textures:** ~500KB total (T_ConstitutionalSeal)

**Total estimated:** ~10-20MB (not included in git repository)

---

## Questions?

Refer to:
- `docs/DEMO_GIGGLE_FOREST_BLUEPRINT_SPEC.md` - Complete Blueprint node graphs
- `docs/LOCAL_INFERENCE_SPINE_PLAN.md` - Architecture and design principles
- UE5 Documentation: https://docs.unrealengine.com/5.3/

---

*"The forest exists in potential until realized by the developer. Specifications precede manifestation."*
