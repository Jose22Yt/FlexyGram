> Restauración: Cupertino ya no sustituye los iconos generales. Los archivos y la fuente se archivaron en `tools/cupertino/reference`, fuera del código y assets de la app; se conservan sus licencias como referencia; los recursos nativos y los conjuntos elegidos por el usuario vuelven a tener su comportamiento anterior. La documentación siguiente describe la implementación anterior.

# Cupertino default icons and touch feedback

The built-in Default icon pack now loads the bundled Cupertino Icons glyphs through
both LaunchActivity's existing IconsResources and ApplicationLoader's resources.
Explicit Solar/Remix selections and installed user packs keep their precedence.
The default pack is labelled Cupertino Icons in both existing pack selectors.

`tools/cupertino/mapping.json` maps 2,011 static resources (including pack variants)
to 150 Cupertino/project symbols. It is the explicit resource-to-glyph/dimensions/color
manifest. `CupertinoIconMap.java` uses sorted packed primitive arrays and binary
search without runtime name searches or per-lookup allocations. It supports AGP
non-final resource IDs without requiring a global Gradle flag change.
The original drawable resources remain intact for other packs, original previews,
stateful graphics and unrecognised resources. `unmapped.json` records retained
compositions, brand marks and native status/progress indicators. This is not
an assertion that every manually drawn or animated icon has been replaced.

The packaged MIT-licensed font is 257,628 bytes. It is rendered using Android's
Typeface/Paint, with one shared Typeface and an instance-local paint for each icon.
No Flutter engine, Dart runtime, runtime downloads, bitmap conversion, polling or
background service is added. Intrinsic dimensions, automatic RTL mirroring and literal monochrome source
colors are generated from the original resources; native tint/filter/alpha remain
supported. Clones have independent paint state. Apple SF Symbols are not included.
Four project-drawn outline companions cover baseball, fingerprint and crown on/off,
which are absent from the upstream catalog. They reuse cached immutable Paths.
Font and catalog provenance/hashes are recorded in `tools/cupertino/UPSTREAM.json`;
the upstream MIT and Flutter BSD notices ship in assets/licenses.

Touch feedback observes native events in activities, action-bar popups, alerts and
bottom sheets. On a confirmed single tap, the icon shrinks to 94% and returns over
160 ms. Reduce Animations uses a smaller 98%, 80 ms gesture. On API26+, Android's disabled
animators suppress the feedback. Native click dispatch never waits for the effect.
Dragging past touch slop, cancellation, multiple pointers and long presses do not
start it. One finite Choreographer callback owns the current pulse; a new touch,
replacement icon, detachment or completion restores the original image matrix.
No view scale, row geometry or text scale is changed.

Settings category tiles scale only their white symbol. SendButton scales only its
send glyph, keeping its background, price and counters steady. Compound Cupertino
icons in TextViews retain their reserved bounds and use a floating-point draw
transform, avoiding rounded-pixel jumps or text-layout changes. Message-menu options use
Cupertino glyphs and no longer apply the old row-wide spring. Telegram's functional
media/morph animations, status layers, logos and multicolor artwork are retained;
the existing iOS chevron mode is now BackDrawable's default.

Validation uses the actual production Java against Android API37 and Android API35
native Canvas/Typeface with explicit application/theme hosts. It covers every
mapped glyph, dimensions, tint, alpha, cloning, touch cancellation, matrix cleanup,
click dispatch and back/close poses. This is not a physical-device frame-time,
startup-time or full APK acceptance result. No APK is built by these checks.

Verified in this workspace: 310 Python/JVM suite tests passed (31 platform-dependent
checks skipped), plus 11 native graphics/touch tests covering the 2,011 mappings
with non-final R IDs and the final generated registry. The existing menu and
Settings3 native hosts also exercise the updated option rows and category tiles.
No integrated APK or physical-device FPS claim is made.
