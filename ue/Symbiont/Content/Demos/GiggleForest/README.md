# Giggle Forest Demo - Content Overview

## Purpose

This directory will contain the **Giggle Forest** demo level and associated assets that showcase the Constitutional Symbiont's ritual invocation flow and AI inference capabilities.

## Level Structure

**Main Level**: `GiggleForestLevel.umap`

This level will be created in-editor and committed via Git LFS (Large File Storage) to handle the binary `.umap` file format.

### Level Contents (Planned)

1. **Tutorial Area**
   - Interactive consent prompt UI
   - Visual explanation of gavel-tap gesture
   - Device vitals display (FPS, thermal, battery)

2. **Ritual Invocation Zone**
   - Gavel-tap detector component demo
   - Visual feedback for tap count and hold progress
   - Constitutional gates status display

3. **Symbiont Interaction Area**
   - Active inference visualization
   - Giggle Growth Coefficient slider
   - Model selection UI (DS_Reasoner, DS_Chat, DS_Coder, DS_Distilled)

4. **Settings Panel**
   - Consent management (grant/revoke)
   - Thermal/battery thresholds (debug only)
   - Analytics/telemetry toggles

## Asset Inventory (To Be Created)

### Blueprints

- `BP_GiggleForestPlayerController.uasset` - Player controller with gavel detector
- `BP_ConsentWidget.uasset` - UMG widget for consent dialog
- `BP_RitualVisualization.uasset` - Visual effects for ritual progress
- `BP_DeviceVitalsHUD.uasset` - HUD displaying FPS, thermal, battery status
- `BP_SymbiontCoreManager.uasset` - Blueprint wrapper for USymbiontCoreEngine

### UI Widgets (UMG)

- `WBP_ConsentDialog.uasset` - Native-style consent prompt
- `WBP_GavelTapIndicator.uasset` - Tap count and hold timer display
- `WBP_ConstitutionalGates.uasset` - Visual status for all 4 gates
- `WBP_MainMenu.uasset` - Demo main menu with instructions
- `WBP_SettingsPanel.uasset` - Consent and debug settings

### Materials

- `M_RitualGlow.uasset` - Glowing material for ritual activation
- `M_ConstitutionStatus.uasset` - Color-coded status indicators (green/yellow/red)
- `M_NeuralEngineViz.uasset` - Abstract visualization of inference activity

### Audio

- `SFX_GavelTap.uasset` - Sound effect for each tap
- `SFX_RitualBegin.uasset` - Sound when all gates pass
- `SFX_RitualBlocked.uasset` - Sound when a gate fails
- `SFX_ConsentGranted.uasset` - Confirmation sound for consent

### Particles/VFX

- `PS_RitualParticles.uasset` - Particle system for ritual activation
- `NS_ConstitutionAura.uasset` - Niagara system for constitutional state

## Git LFS Configuration

Binary asset files (`.uasset`, `.umap`, `.uexp`) will be tracked via Git LFS to avoid bloating the repository.

**Required `.gitattributes` entry** (to be added):
```
*.uasset filter=lfs diff=lfs merge=lfs -text
*.umap filter=lfs diff=lfs merge=lfs -text
*.uexp filter=lfs diff=lfs merge=lfs -text
*.ubulk filter=lfs diff=lfs merge=lfs -text
```

## Creating the Level

### In Unreal Editor:

1. Open the Symbiont project
2. Navigate to `Content/Demos/GiggleForest/`
3. Create new level: File → New Level → Empty Level
4. Save as `GiggleForestLevel`
5. Add the following actors:
   - Player Start
   - Post Process Volume (for visual polish)
   - Directional Light
   - Sky Atmosphere
   - Exponential Height Fog (optional)

6. Add demo-specific actors:
   - BP_GiggleForestPlayerController (set as default controller)
   - BP_DeviceVitalsHUD (spawned at BeginPlay)
   - BP_ConsentWidget (shown on first launch)

### Blueprint Setup:

**Player Controller**:
```
BeginPlay:
  ├─ Get ConsentManager subsystem
  ├─ Check HasUserConsent()
  ├─ If false: Show BP_ConsentWidget
  └─ If true: Enable gavel detector
```

**Gavel Detector Event**:
```
OnGavelTapDetected:
  ├─ Spawn USymbiontCoreEngine
  ├─ SetGiggleGrowthCoefficient (from UI slider)
  ├─ InvokeSymbiontRitual()
  └─ Listen for OnRitualBegin
```

## Committing Assets

Once assets are created in-editor:

1. Ensure Git LFS is initialized: `git lfs install`
2. Stage assets: `git add ue/Symbiont/Content/Demos/GiggleForest/`
3. Commit: `git commit -m "Add Giggle Forest demo level and assets"`
4. Push: `git push` (LFS automatically handles large files)

## Testing the Demo

### Functional Tests:

1. **Consent Flow**:
   - Launch level → Consent dialog appears
   - Deny consent → AI features disabled
   - Grant consent → Gavel detector enabled

2. **Gavel Tap Ritual**:
   - Tap twice quickly → Hold indicator appears
   - Hold for 1 second → Ritual completes
   - Tap count and hold timer display correctly

3. **Constitutional Gates**:
   - All gates green → InvokeSymbiontRitual succeeds
   - Set low battery (debug) → Battery gate red, ritual blocked
   - Simulate thermal stress → Thermal gate red, ritual blocked

4. **Model Loading**:
   - Ritual success → OnRitualBegin fires
   - Model loading logs appear
   - (If model files present) Inference begins

### Performance Tests:

1. **Frame Rate**: Run at 60 FPS on target device (iPhone 15 Pro+)
2. **Memory**: Monitor with Xcode Instruments (< 1GB RAM for demo)
3. **Thermal**: Run for 5 minutes, verify thermal state stays below "serious"
4. **Battery**: Measure drain rate (< 10% per hour of active inference)

## Asset Sources

All assets should be created in Unreal Editor or sourced from:
- Unreal Marketplace (free/licensed content)
- Royalty-free sound libraries (e.g., Freesound.org)
- Custom-created VFX using Niagara

**Do NOT include**:
- Copyrighted third-party assets
- Real CoreML model files (proprietary to DeepSeek)
- User data or analytics logs

## Integration with Other Demos

This demo is standalone but can be extended to integrate with:
- AR Foundation demos (camera feed + world tracking)
- Hand tracking demos (physical gavel gesture detection)
- Voice command demos (spoken ritual invocation)

## Notes for Contributors

- **Binary Assets**: Only commit necessary binary files; prefer text-based Blueprints where possible
- **Documentation**: Add inline comments to Blueprints explaining ritual flow
- **Naming Convention**: Use `BP_` prefix for Blueprints, `WBP_` for widgets, `M_` for materials
- **Organization**: Keep assets in appropriate subdirectories (Blueprints/, UI/, Materials/, etc.)
- **Testing**: Test on device before committing; simulator is insufficient for thermal/battery testing

## Future Enhancements

- Multiplayer ritual invocation (synchronized gavel taps)
- Analytics dashboard showing ritual success/failure rates
- A/B testing for different Giggle Growth Coefficient values
- Tutorial video or guided walkthrough
- Accessibility features (audio feedback, colorblind-safe indicators)
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
