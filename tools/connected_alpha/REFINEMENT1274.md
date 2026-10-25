# Alpha1274 — corrective integration in progress

Base: physically accepted Alpha1273 (`751c926d91acd536d96b427af5f34f2fe6bedbc4`).
Work2 Studio: original commits45815ad651a69e72c146557ef536217a807484fb and534b30c4edea3dffa0fc726eaec254ed8ebadbc1 are ancestors; do not apply its patch again.
PR95 remains draft. No main/develop merges.

References inspected locally: ios27_namefit_pill(1).plugin (static reading only), physical screenshots49439/49440/49443–49447/49452/49457/49463/49464, video49451, approved Music49284(1).png and Studio reference. No private screenshots, video, chats or plugin code are committed or uploaded as CI evidence.

## Corrective mechanisms

- Header: the classic title had6+12dp vertical padding, while Signature budgeted only font sizes. The corrective path clears that padding only in Signature and restores it for Classic. Name/status are measured and centered as one block. Font metrics drive equal44–46dp normal /40dp compact surfaces; narrow windows fit the two lines together. Classic title translations cannot escape the measured block. Real unread source/model and original navigation handlers remain.
- Counter: legacy boolean remains authoritative for on/off; additive counter_mode1/2 preserves integrated/badge presentation. Modes do not increase header height. ES/EN/RU labels; capped large counts.
- Wallpaper: native SizeNotifierFrameLayout reports its completed wallpaper draw, so a conversation snapshots its own crop/insets. Message sampling no longer re-reads mutable shared Drawable bounds. The alpha-aware native bridge draws the same cached shader through partial-alpha transitions; older embedders retain conservative Matte fallback. Animated wallpaper/crossfade remains Matte; no capture or per-message blur.
- Contours: separate native bubble palette, fill alpha, cached wallpaper, contour mode and intensity. Intelligent color increases native chroma/contrast; Pearl mixes the actual bubble color with white. Gradient palettes use their native colors, not wallpaper. Per-drawable color policy cache; explicit contour toggle; thickness remains0.5–2.0dp. Shared native Path/cache retained.
- Tail: mirrored cubic contour with vertical tangent, short rounded tip, smooth return and horizontal body join. Native message size/group/media rules are unchanged. Android mirrored-region/group/media cases must pass before release acceptance.
- Music: the same full sheet/engine/actions; elongated full-width artwork fades underneath the title, adaptive cached artwork button color with contrast checks, centered title/artist, exact Speed/Lyrics/Queue/More localizations. Four native actions reflow only for narrow/large-font screens; no alternative playback engine.
- Launcher: FlexyBlueIcon is the sole manifest default before process startup; historical primary alias is disabled by default but retained. Package-replaced receiver reconciles explicit alternatives using existing PackageManager logic. HyperOS cache behavior still needs physical clean-install/update validation; do not claim all visible cache effects are fixed.

## Studio compatibility

21 explicitly registered preferences in four categories, no extra advertised categories:
- Bubbles: glass,border,edges (legacy), transparency,borderTenths,cachedBlur,outlineEnabled,outlineStyle,pearlIntensity.
- Header: style,compact,counter,counterPresentation,opacity.
- Composer: style,glass,position,density,icons,gap.
- Launcher: selected.

The JSON format remains schema1 because its grammar did not change. Additive new keys require minApp1274; valid previous files remain accepted with their original checksum semantics. Unknown keys/types/ranges/versions remain rejected. Worker preparation, journal, rollback, undo and targeted view refresh are Work2's implementation. Music, themes, animations and sessions are not part of the export schema.

## Validation and delivery gates

Keep the P0 regression, auth/audio/native-engine and Performance1/2 contracts. Historical checks reverse the new exact patch first, then the original patches; unexpected deltas still fail.
Isolated Android evidence uses synthetic data and declared Telegram/navigation doubles. It does not prove full application behavior, physical performance, API37 device behavior or Poco installation.

VersionCode1274; applicationId and authorized certificate must remain unchanged. Full ARM64 build is pending until isolated checks pass. Deliver only a verified native APK to an unpublished authenticated draft destination and verify authenticated roundtrip plus anonymous denial before runner cleanup. No AGE, auxiliary installer or public APK Actions artifact.

Poco acceptance: repeated previews/back/cancel + music, header long names/status/RTL/fonts/counters/search/keyboard/translator, wallpaper scroll and transitions, both contour styles/off and grouped/media/replies/reactions, player full/mini/bubble/background actions, Studio import/export/share/download/undo/errors/legacy files, fresh launcher/update/alternative persistence. Alpha1273 P0 is physically confirmed fixed by the owner; preserving it does not certify this new build.

Performance: run the existing four-cohort lab under matched conditions. No FPS/jank/p95/memory superiority is claimed without physical captures.
