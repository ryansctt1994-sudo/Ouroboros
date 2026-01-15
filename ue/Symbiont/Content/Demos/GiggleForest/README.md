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
