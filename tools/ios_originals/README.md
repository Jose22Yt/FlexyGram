# Original Telegram-iOS artwork importer

Frozen source: TelegramMessenger/Telegram-iOS at `24638bc69bd083981b178dd1e7f921eebbf7fc46`.

`manifest.json` records original paths, exact Git blob/SHA-256, point dimensions, density variants, conversion kind and original Lottie frame. `upstream/` contains the unmodified files; they are build inputs, not Android runtime files. `UPSTREAM-README.md` preserves the source repository's notices. No root LICENSE exists in this source revision; do not fabricate one.

```sh
python tools/ios_originals/generate.py --check
python tools/ios_originals/generate.py
# Full conversion (build tools only; requires the frozen upstream checkout):
python -m pip install -r tools/ios_originals/requirements.txt
python tools/ios_originals/generate.py --sources /path/to/Telegram-iOS
# Optional isolated real-API type check, without building an APK:
python tools/ios_originals/check_android_types.py --android-jar /path/to/android.jar --core-jar /path/to/androidx-core.jar
```

Bindings are reviewed explicit action names, not approximate image matching. `coverage.json` lists unreplaced legacy aliases. This is not a certification that every iOS 27 system symbol or Telegram UI state has been ported.

PDF paths are copied as Bézier coordinates with fill rules, strokes and clips; SVG paths are decoded through MuPDF. A conservative same-renderer alpha comparison rejects uncertain vector conversions, including SVG renderer clip limitations. Rejected PDFs are rendered directly from their original source at five densities. Source raster artwork keeps alpha and native scale. Composer states are actual rlottie-rendered final displayable frames of the upstream JSON, not recreated paths or a port of the entire iOS animation engine. Template RGB is white for Android MULTIPLY/SRC_IN theme tinting; alpha/shape is preserved.

Native resource caching shares pixels/geometry. Per-control drawable state is independent. The wrapper caps enlargement, preserves the native point-to-dp size and fits down proportionally where an existing control is smaller. Touch regions are unchanged. No importer/rendering dependencies run in the APK.
