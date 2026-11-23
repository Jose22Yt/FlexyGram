# Signature Floating: inline status and fitted photo

Style ID 4 is preserved; no preference migration or additional setting is needed.

- The center card is 48dp high, with the existing width and 48dp native action targets.
- Name (15sp) and native subtitle (10sp) share the entire card center axis.
- Both lines are inside the card. The detached status surface/reveal is removed.
- The native ImageReceiver draws one fitted portrait. Its inward edge fades across the final 65% of the visible image width.
- Missing and pending photos use a compact circular placeholder with the same directional fade.
- Rendering restores receiver coordinates/aspect-fit state, supports RTL and uses
  the portrait-sized alpha mask. Large fonts/narrow layouts retain Adaptive fallback.
- The settings preview shares the same geometry/font sizes; its avatar remains synthetic.

Run isolated Android layout and raster tests (not an APK build):

```sh
python tools/connected_alpha/header_visual/floating_run.py --sdk-root "$ANDROID_HOME"
```

The fixture compiles the production adapter, preview, fit/mask classes and extracted
native layout/draw methods against Android API 35 graphics. Image decoding, wallpaper,
navigation and services are explicit doubles. Tests cover inline layout, font scaling,
preview geometry, light/dark/RTL masks and fitted portrait/square/landscape composition.
Full application rendering, animated avatar playback and device performance remain
pending physical-device validation.
