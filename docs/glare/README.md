# Chat · Glare effects

Independent functional adaptation of Cherrygram's three-mode selector to FlexyGram's existing native glass outline engine. No new renderer, animation engine, blur or preference store.

## Source and attribution

Functional reference inspected: [Cherrygram](https://github.com/arsLan4k1390/Cherrygram/tree/3050af6d948acc27db446f6cd27a8e200b205c1b), commit `3050af6d948acc27db446f6cd27a8e200b205c1b`.
Relevant files: `CherrygramAppearanceConfig.kt`, `AppearancePreferencesEntry.java` and `Components/blur3/drawable/BlurredBackgroundDrawable.java`. Its root LICENSE contains GPL version 2. This change does **not** import those classes, configuration implementation, or nontrivial source; it implements equivalent behavior independently using FlexyGram's existing GPL-covered components. Existing copyright and blur3 attributions remain intact. Cherrygram's numeric preference ordering must not be substituted for FlexyGram's ordering.

## Location and compatibility

**FlexyGram → Chat → Efectos de brillo → Tipo** (after the existing Composer controls). A native radio dialog offers exactly three modes. Header, Bubble and Composer previews remain the originals; no duplicate decorative preview is added. The previous `appearance:glassOutline` control is removed from the visible Universal/effects scope. Legacy links and search target Chat.

| Visible selection | Existing stored value | Existing enum |
|---|---:|---|
| Desactivar | 2 | HIDDEN |
| Por defecto | 0 | GLARE |
| Contorno sólido | 1 | SOLID |

The original `OEAppearanceGlassOutlineStyle` key/default/setter and weak drawable listeners are unchanged. Existing saved values survive; opening/canceling the selector writes nothing. Unknown saved values display Default, matching the existing renderer fallback. Only selecting a value writes the original preference and dispatches the existing changed-only notification. The selected row refreshes without rebuilding the page.

This setting changes **native glass outlines**, wherever the existing blur3 pipeline is used, including header/composer when native glass is active. It does not enable glass, disable blur, change message bubble styles or replace Signature Matte geometry. Native glass depends on the existing device/LiteMode/settings conditions. Turning glare off is not a performance switch or a guarantee of zero GPU cost. Shared glass components may also respond, as they already do to the original preference.

## Renderer correction

Two static `drawStroke` overloads previously returned immediately for both HIDDEN and SOLID. SOLID consequently had no outline on callers using those paths. Default still executes the exact original code; Hidden draws nothing; Solid draws one inset perimeter on the top pass and consumes the bottom pass without double drawing. Existing instance/cache/full-stroke paths are untouched. Borrowed Paint style, width and shader are restored in `finally`.

The uniform-radius path allocates no Java objects while drawing. The nonuniform path reuses one Path/RectF/radii array per existing rendering thread through ThreadLocal (no new thread, no View/Activity references, no bitmap or unbounded cache). Existing weak listeners perform invalidation; no observers, workers or polling are added by the settings section.

## Validation and reproducibility

From repository root:

```sh
python3 -m pytest -q tests
python3 tools/settings2/checks.py
python3 tools/glare/android/run.py --sdk-root "$ANDROID_HOME" --output-dir build/glare-native
python3 tools/settings3/android/run.py --sdk-root "$ANDROID_HOME" --output-dir build/settings3-glare-regression
```

The isolated probes compile against Android API 37 resources/classes and execute native Android Canvas with Robolectric API 35 plus AndroidX RecyclerView. Telegram hosts, the native dialog host and the Kotlin AppearanceConfig bridge are explicit doubles; the original Java ConfigItem, original GlassOutlineStyle, new selector/mapper/helper and extracted production static stroke methods are compiled. This is **not a complete application build**. The inherited music harness prints its historical music banner; the final Glare/Settings3 banner states the actual scope.

- Glare probe: **9 passed**, 0 failed/skipped. Includes saved-mode mapping, selector writes, unrelated preference retention, changed-only listeners, both static overloads, no fill when disabled/solid, no double stroke, Paint state restoration, inverted bounds and **pixel-identical Default versus base `4679f74`**.
- Settings3 isolated regression: **10 passed**, 0 failed/skipped.
- Java21 syntax parsing: **8 changed/new production Java files passed**; syntax is not semantic compilation.
- Existing migration source checks: **12 passed**.
- Host suite results are recorded in `validation-results.json`.

`visual/glare-light-isolated.png` and `visual/glare-dark-isolated.png` are real raster outputs of the extracted Android Canvas methods on synthetic contour samples. They are **not full Chat UI screenshots, physical-device captures or exact reproductions of the user's personal screenshots**.

No physical device is connected. No measured touch latency, FPS, jank, RenderThread time or memory claim is made. Full Gradle app compilation remains pending: the environment's Gradle distribution download failed with Java networking in the preceding Settings3 work. No build/security checks have been disabled. Existing Settings3 source-scope CI blockers remain documented in `docs/settings3/VALIDATION.md`.

## Integration and physical acceptance

Stacked on PR #163 HEAD `4679f74ebd312acc4968dd2e044a6c6b7478445a`; do not restore older settings code or cherry-pick PR #163 twice. Merge/rebase this isolated feature only after the Settings3 base is integrated and approved. No main/Work1 branch is changed; no version, package, certificate, distribution or APK changes.

On the Poco X8 Pro: compile the full Beta with normal security gates, open Chat settings, verify one selector/search result and all three saved modes across process restart. Check native Header/Composer glass plus existing previews in light/dark/custom themes, glass disabled and LiteMode fallback. Change modes during scrolling, keyboard/music/navigation, cancel the radio dialog, rotate, and reopen settings; verify no account/scroll loss or preview/navigation regression. Compare framestats at the measured effective refresh rate before/after; the default mode should remain behaviorally unchanged. Check RenderNode and nine-patch-backed surfaces physically; isolated Canvas tests do not exercise their complete lifecycle.

Revert this feature commit to restore the old control location and static behavior. No data migration/rollback is required because the storage schema never changes.
