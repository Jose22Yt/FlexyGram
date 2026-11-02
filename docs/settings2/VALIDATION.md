# Validation status — draft, not accepted for release

## Executed

- `python3 tools/settings2/checks.py`: 12 focused checks passed. Ownership, exact root order, route graph, EN/ES/RU resources, original handler preservation, protected backend exclusions, conditional adapter notifications, Studio moves, aliases and PR158 non-overlap.
- `PATH=<javac-shim>:$PATH python3 -m pytest tests/ -q -rs`: **144 passed, 31 skipped**. Optional plugin corpus and R8 usage artifacts are unavailable; omissions were not bypassed.
- `python3 tools/settings2/android/run.py --sdk-root <sdk> --output-dir build/settings2-native`: **9 passed**. Real API37 resources/AAPT2 and real Java compilation of new Settings2 production sources; Robolectric API35 runtime. Telegram host, list/controller and transport doubles are explicit. Original ConfigItem persistence and original FlexyFiles getter/setter use real Android preferences. This is not compilation or execution of the complete application.
- Existing Android resource checks: main resources and isolated link passed, with inherited legacy formatting warnings. Integrated merged manifest/APK not validated.
- Original frozen Beta contract also fails on the pristine approved base with `Unknown Beta delivery scope`. This branch does not weaken that check or alter source approvals/workflows.

## Visual evidence

`visual/*-isolated.png` renders implemented Settings2 views using Android Canvas in the isolated probe. These are **not full-app, emulator or physical-device screenshots**. Telegram toolbar/host and list plumbing are test doubles. No real accounts or private conversations were used. Dark and light layouts, grouping, icon surfaces, spacing, long labels, 1.0/1.5/2.0 font scales and RTL row bounds have isolated coverage.

Comparison to supplied references: eight categories, three groups, colored rounded-square monochrome glyph tiles, compact descriptions, thin separators, clean submenus and separate About destination. Existing controls remain native/adaptive Matte cells; this is not a wholesale Material library migration. Nested source-specific supplemental pages are retained where needed to preserve original conditional handlers rather than inventing merged controls.

The full Gradle wrapper was attempted: downloading the pinned Gradle 9.7.1 distribution failed with `java.net.SocketException: Network is unreachable`. No full production compilation is claimed.

## Not yet established

- Full production Android module/Gradle/JNI/Chaquopy build. Isolated compilation uses host doubles and cannot detect every integration signature or lifecycle issue.
- Complete duplicate-preference and conditional visibility acceptance across every nested editor.
- Every existing preference persisting after update/restart; only representative original-key persistence is tested in isolation.
- Native Back, rotation, theme changes, large fonts, RTL, search/deep-link value import across the full application.
- PR158 combined runtime acceptance; source-level non-overlap only.
- Device framestats, touch latency, jank, memory or comparative performance. No physical-device numbers are claimed.

## Poco X8 Pro acceptance

Use Work 1's normally reviewed signed Beta update without uninstalling or clearing data. Record old preference values before update. Check all eight categories, every visible row destination, original Telegram screens, all conditional toggles, dependent row insertion/removal, country/language/RTL, light/dark/theme switching and font scales. Export/import/share Studio; select a storage path; toggle FlexyFiles and reopen; verify all pre-existing values. Exercise Back and rapid repeated taps with music, keyboard and previews active. Verify no duplicate launcher/translator/system-account controls and that legacy tabs controls only appear where applicable. Repeat after process restart. Capture sanitized screenshots and run the existing performance lab with the same device conditions and workload. Do not use private content in traces.

## Reproduction prerequisites

API37 platform (`platforms/android-37.0`), build-tools36, Maven and Java17 are required for the isolated API35 test. `javac` must be on PATH; a Java17 modular compiler shim is supported. The probe reuses the existing music visual runner infrastructure; its inherited final log banner mentions music, but Settings2AndroidTest is the actual suite. No playback or APK claim follows from that banner.
