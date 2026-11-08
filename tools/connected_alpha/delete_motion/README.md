# Native deletion regression probe

Runs production renderer, snapshot lifecycle, compact settings previews and shared
wallpaper/card classes with Robolectric API 35 native graphics. Explicit Telegram
host doubles are in `run.py`; the animator ownership fixture extracts the real
prepare/take/custom-remove methods. This does not launch Telegram, test server
message deletion, validate grouped albums, measure device FPS or build an APK.

```sh
python tools/connected_alpha/delete_motion/run.py --sdk-root "$ANDROID_HOME" \
  --output-dir build/reports/ui-beta/delete-motion
```

Requires JDK 17+, Maven and the existing API 37/build-tools 36 SDK, like the music
probe it shares. Covers completion/cancellation, reduced-effects fallback,
allocation budgets, capture failure, source loss, theme/wallpaper changes, large
fonts, pause cleanup and 32 exact pixel hashes across the four effects. PNGs show
the actual isolated settings gallery in light/dark themes.

`golden.json` records ARGB SHA-256 hashes from the Java sources embedded in the
user-supplied Bubble Fracture v1.0 plugin by @larrat23. Original and port were
rendered with the same image, seed 9911, 220×74 bounds, density 1, 2000 ms duration,
650 fall distance and 640×420 canvas, at 0/120/400/800/1200/1600/1960/2000 ms.
The sources, Python plugin and embedded DEX are not shipped with the probe.
To independently reproduce the oracle, statically extract only its five Java
render/math sources to a private directory and pass `--reference-dir DIRECTORY`.
The reference is compiled solely in the temporary test project, never installed,
hooked or loaded as a plugin. Compare before changing golden hashes.
