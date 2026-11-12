# Duotono Monet and compact settings

The FlexyGram settings hubs now use the reviewed, polished Duotono Monet collection. Dark settings pages use an opaque `#000000` background; cards use charcoal mixed with 8% of `windowBackgroundWhiteBlueHeader`. Light pages retain the active light palette. These overrides are scoped through `SettingsTheme`; they do not write preferences or modify chat/theme colour tables.

Navigation rows use 22dp glyphs, 15sp regular labels, a 48dp minimum content height, 20dp outer corners and a narrower text/icon column. Native cards retain their 4dp separation and existing touch/ripple ownership. Labels remain multiline; rows expand with available width and font scaling. Setting descriptions and native switch/value callbacks remain native.

## Approved assets and rendering

`tools/settings_monet/import_approved.py` imports the 85 original PNGs directly from `tools/settings_monet/sources/approved-icons.zip`. Their bytes are unchanged. A second, lossless RGB PNG stores body coverage in red, accent coverage in green and total coverage in blue; only empty margins are removed. No glyph geometry is retraced or resampled during import.

`DuotoneSettingsIcon` combines the two coverage channels once per palette. Body is white in dark mode and black in light mode; accent comes from the active header/accent token. Numerical composition retains the original total alpha rather than compositing two overlapping translucent masks. Parent monochrome icon filters cannot collapse the duotone. Native image alpha/disabled state remains supported.

The final tinted bitmap is shared through a UI-owned, 2MiB LRU cache, partitioned by resource and palette. Resource/configuration changes clear the shared cache. Bitmap decoding and pixel processing occur on first use or palette changes, not on steady drawing. A regular frame only checks two colours and draws one filtered bitmap. Cache eviction never recycles a bitmap still referenced by a visible drawable. No animators, blur, shader layers, frame callbacks, workers or touch interceptors are added.

The ten root entries, compact section plans, specialized editor links and FlexyStudio transfer rows use explicit semantic glyphs. Legacy settings resource names resolve to the same collection. Unrecognized plugin icons retain their original resources and behaviour. Auxiliary glyphs are available to the settings renderer without replacing conversation controls globally.

## Local presentation and lifecycle

Settings hosts, embedded controllers and specialized managers share their scoped provider. Specialized manager navigation forwards it explicitly; saved fragment arguments preserve the presentation after restoration. UniversalAdapter plugin/permission/navigation destinations use the same page/card palette. Theme delegates refresh page, card and navigation colours when a theme/accent changes while visible.

## Validation without APK

- Reviewed asset provenance and resource/coverage inventory.
- Executable JVM checks for navigation, lifecycle, row recycling, card painting, geometry and theme updates.
- Isolated Robolectric native graphics tests exercise the actual renderer, provider and settings row: both theme modes, live accents, inherited tint rejection, coverage/alpha preservation, bounded shared decoding, all 85 glyphs, large labels, RTL and native clicks.
- Full Python/JVM regression run: 428 passed, 39 skipped and one outdated icon-name fixture. After updating that fixture, its targeted rerun plus the two new asset/provider checks passed (3/3). All 429 distinct applicable regression checks are verified. Native graphics: 6/6 passed, including compilation with non-final Android resource IDs. After integrating the two incoming reaction/animation commits, their checks plus the asset/provider checks also passed (12/12). No APK was built.

Reproduce native graphics checks with `tools/settings_monet/run_native.py --output <temporary-output> --maven <mvn> --android-jar <android.jar> --runtime-aar <directory-with-monitor.jar-and-espresso-idling-resource.jar>`. This runner uses an already provisioned local Maven/Robolectric runtime in offline mode. It does not invoke Gradle, package an APK, start an emulator or claim device frame-time measurements.

Phone validation of the integrated screens and scrolling remains pending the next explicitly requested APK build. Commit messages use `[skip ci]` so publishing the source does not start that build.
