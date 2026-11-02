# FlexyGram Signature Delete Motion — implementation preview (Work 1 integration)

Independent Java/Android implementation; user-provided BubbleFracture plugin used as a visual reference only, no code copied.

## Four animation styles

1. Crystal Fracture: 25 irregular Voronoi-like pieces clipped from one bitmap, displacement/rotation/gravity.
2. Liquid Fall: momentum, subtle anisotropic compression, tilt and downward fade.
3. Liquid Vortex: 16 radial pieces, vortex rotation and contraction.
4. TNT Dispersion: 36 tiles, directional scatter, gravity, fast restrained flash.

Settings: `DeleteMotionSettings.DEFAULT`, `CRYSTAL_FRACTURE`, `LIQUID_FALL`, `LIQUID_VORTEX`, `TNT_DISPERSION`; preference defaults to native Telegram deletion.

## Hook into real Telegram deletion (required in Work 1)

On the **successful and user-confirmed** delete operation, before removing the cells from the list, capture bounds in `ChatMessageCell` local coordinates; do not capture the entire row. Pass multiple targets on multi-delete, call **original Telegram deletion unchanged** exactly once in the callback. Example (integration pseudocode; not drop-in exact API):

```java
List<DeleteMotionOverlay.Target> targets = new ArrayList<>();
// add only currently attached, visible message cells; use real bubble drawing bounds
// targets.add(new DeleteMotionOverlay.Target(cell, new RectF(left, top, right, bottom)));
DeleteMotionOverlay.runNativeDelete(chatListRoot, targets,
    DeleteMotionSettings.get(context), () -> nativeDeleteExactlyAsBefore());
```

The engine does not modify Telegram permissions, delete-for-all, undo semantics, server state, or messages. If deletion is postponed until an undo expires, capture **at the actual native removal**, not earlier.

## Settings integration

Expose a single radio selector under **Animaciones → Animaciones de mensajes → Al borrar** with five rows including Clásico. Keep the existing FlexyGram Signature touch/reaction selector unchanged. Reuse localization keys; don't label this "iOS 27". A reusable `DeleteMotionSettingsDialog.show(Activity)` already provides five radio options and a live preview (including Clásico). Work 1 only needs to add a navigation row to the existing **Animaciones de mensajes** settings. The dialog currently uses Spanish temporary strings; move them to localized string resources for production.

## Safety / optimization gates

- One snapshot per visible message (bitmap area cap 900k px), no bitmap allocations during frames.
- Up to four simultaneous overlay snapshots; further messages use the native list transition.
- Use `getOverlay()` rather than touching the RecyclerView item lifetime.
- Respect existing animation/reduced-motion preferences and accessibility.
- Hardware accelerated Canvas path clipping; avoid effects that capture private content to disk.
- Always invoke original deletion even if capture fails.
- Work 1: integrate `DeleteMotionSettingsDialog.show(Activity)` into the existing settings; verify `ViewGroupOverlay` lifecycle on device, source bubble region, back/rotation, Android 17, RTL, theme/light/dark, grouped and media messages; polish rendering/cell reflow and wire settings navigation. Verify no recycled View or bitmap remains after lifecycle interruption.

## Test (host)

```
javac -d /tmp/flexy_test src/app/flexygram/bubbles/deletion/DeleteMotionMath.java tests/DeleteMotionMathTest.java
java -cp /tmp/flexy_test DeleteMotionMathTest
```

**Status:** isolated Android implementation and host math tests, not integrated/compiled as FlexyGram APK. Work 1 must wire deletion flow and UI selector, run ARM64 build/physical acceptance before claiming completion.
