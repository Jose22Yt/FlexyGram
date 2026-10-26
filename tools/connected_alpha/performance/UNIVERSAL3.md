# Universal Native Performance 3.0

## Scope and integration

Base: approved Alpha1275 / PR96 `8c47e5532a600f9a8b4ccbfdac5090d09a1075a0`.
PR98 contains pending Work1 changes, so it is inspected, not used to replace the approved base.
`work1_boundary3.json` records the checked head and changed paths. Recheck that boundary
before integrating. PR90/93 changes already in this base are not cherry-picked again.
PR97 identity work remains independent. No version, identity, signing, APK delivery,
authentication, JNI, navigation, visual effect or animation duration changes.

Two production helpers are changed. Their baseline implementations are byte-identical
to historical Exteraless `1ad6a60a6834ffca722b1a22f4fba27ecb29a061`.
Apply the two production commits individually after reviewing their tests. Apply the lab
commit for measurement and source contracts. Do not apply `motion3.patch` without Work1 review.
Revert an individual production commit or reverse its recorded `flicker3.patch`/`clip3.patch`
to restore its exact baseline. Do not reverse those patches over later Work1 edits blindly.

## Confirmed findings and bounded changes

| Component / method | Evidence and cause | Candidate / risk | Status |
| --- | --- | --- | --- |
| `CellFlickerDrawable.setColors` | `BotButtons.draw` calls this while drawing; unchanged effective colors allocated two gradients and their arrays again. Native API35 fixture observes 2,000 distinct Java Shader identities for 1,000 stable calls. | Reuse the existing two shaders if effective colors AND gradient size match. Three additional ints per instance. Constructor does not call an overridable setter. Preserve invalid-alpha exceptions and mutable-size behavior. | Implemented; two identities in the same isolated workload. Not GPU compilation counts or ART allocation profiling. |
| `ClipRoundedDrawable.updatePath` / `draw` | Every draw rewound and rebuilt the rounded clip even after setters prepared identical geometry. A counting native Path observes 1,000 `addRoundRect` calls after preparation. | Dirty geometry plus copied bounds snapshot: zero rebuilds during those 1,000 draws. One Rect and boolean per instance; direct mutable `getBounds()` changes are detected. | Implemented. Padding, radii, alpha, bounds, child replacement and null child exercised. |
| `ReplaceableIconDrawable.setIcon` / animation end | Clearing retains animator update callbacks and resource ID. Re-selecting the same resource stays empty; stale animation end can clear a newer outgoing drawable. | Cancel/remove listeners; reset resource ID; identity guard on animation end. Native ValueAnimator and 150ms duration retained. | Reproduced baseline failures; separate UNAPPLIED `motion3.patch`. Manual late ValueAnimator seek invalidates baseline once, candidate zero times. This is not a measured scheduled-frame callback rate. |

No global caches, bitmaps, worker threads, idle tasks, new renderer or animation engine
are introduced. Shaders remain two per drawable; clip storage is constant-sized.
Bounds, alpha and animation progress remain inputs to native drawing. No model, vendor,
Android skin, chipset or refresh-rate production branches are added.

## Audit boundary and unresolved hypotheses

| Area | Finding / next evidence | Action |
| --- | --- | --- |
| Header, bubbles, glass, composer, chat opening/closing, previews | Work1 is actively editing these areas. Source complexity alone does not establish a bottleneck. | Preserve production files. Use existing navigation scenarios and Perfetto before proposing changes. |
| Render resources | Two confirmed redundant construction paths above are inherited from Exteraless. | Narrow bounded reuse, pixel regression tests. |
| Motion lifecycle | Confirmed callback/resource identity defects in shared icon helper. | Tested patch only; coordinate compositor callers with Work1. |
| Cached blur / layers / GPU | No device trace available; cannot quantify GPU, RenderThread or layer overdraw. | Keep approved effects; measure glass_on/off with identical content before proposing cache changes. |
| Startup, image decode, observers, audio/background services | No new evidence of a regression in this mission. | No speculative thread/lifecycle changes. Existing capture and music scenarios retained. |
| Signature Motion | Dynamic geometry or animation-owned callbacks require explicit ownership/invalidation. | Future work only: measure first, reuse native cancelable transitions; no duration shortening here. |

## Executed evidence and limits

Host validation: **243 Connected Alpha tests pass**, **144 general tests pass**, with
31 optional corpus/R8-report omissions. Real AAPT2 resource compile/link passes against
API37; the probe does not validate the full application merged manifest.

The new isolated suite passes **12 tests**, using actual API35 Android Canvas/Path/Shader/
ValueAnimator via Robolectric native graphics. Complete baseline/candidate drawable
sources compile against Android; Telegram dependencies are explicitly named doubles in
`native3/stubs.py`. This is NOT the full app, device HWUI, RenderThread, physical GPU,
ART allocation profiling or an Android17 acceptance run.

Baseline failures were observed before applying each fix: stable shader identities
2,000 rather than 2; repeated clip rebuilds 1,000 rather than 0; motion clear/resource/
stale callback regressions. Candidate tests compare 576 shader pixel cases plus alpha,
frame and Path modes; 1,000 deterministic clip state changes; and interrupted native
animator fractions. Reports are written under `build/connected-alpha-performance3-native/`.
Their counts do not imply a wall-time, FPS, energy or touch-latency percentage.
The isolated baseline/candidate PNGs are byte-identical (SHA-256
`83eff62fac3832c671ba08224e594d54e237a3b84e6ed1758ba51fd54edde8aa`);
they depict a drawable fixture, not a FlexyGram application screenshot.

Real module compilation was attempted with
`./gradlew :TMessagesProj:compileConnectedAlphaJavaWithJavac --no-daemon`.
Gradle9.7.1 distribution download failed with `Network is unreachable` before module
configuration. No credentials were invented, no JNI/Chaquopy tasks bypassed, and no
complete integrated Android compilation is claimed. CI runs resource and isolated suites.

## Reproduce host and isolated checks

```sh
python3 tools/connected_alpha/run_checks.py
python3 tools/connected_alpha/performance/native3/run.py --sdk-root "$ANDROID_HOME"
```

The second command uses the existing music/native test pipeline and Maven. Its shared
runner's historical music label is followed by the explicit Performance3 scope statement.
The production source restoration contracts admit only exact reversible helper deltas.
Two historical host tests recognize these reviewed changes through exact reverse patches;
their tamper-rejection assertions remain active, including for the test deltas themselves.
The dedicated CI has read-only repository permissions and uploads numerical/test evidence,
never APKs or user traces. The integration branch uses the existing no-APK workflow policy without modifying it.

## Physical measurement using the existing lab

Use consenting TEST installations/accounts with prepared equivalent non-private content.
Measure original Exteraless, approved Alpha1275 and the integrated candidate on EACH test
device. Cover lower/middle/higher capacity devices and available refresh rates; these
are validation cohorts, never production heuristics. Alternate run order and cool the
device between cohorts; hold theme, cache state, battery/charging, build mode, music,
fixture and animation scales constant. Do not change system settings automatically.

Run `python3 -m tools.connected_alpha.performance.capture --help` for the existing ADB
capture flags. Select label `exteraless`, `alpha1275` or `candidate`, the exact source SHA,
scenario, same declared build mode, and at least 20 repetitions. All capture condition
flags remain mandatory; health drift rejects the run. New operator-driven scenarios:
`multitap`, `image_messages`, `stickers`, `typing`, `player_idle`, `glass_on`, `glass_off`.
Also retain chat open/close, list/message scroll, keyboard, music and background scenarios.
No synthetic taps, account actions or private conversation reads were added.

```sh
python3 -m tools.connected_alpha.performance.universal3 original.json alpha1275.json candidate.json --out comparison.json
```

Comparison groups by hashed test-instrument identity and scenario. It will not compare
FPS between different phones, accept missing cohorts, mismatched conditions/build modes,
insufficient repetitions or missing raw frame samples. It adds pooled median/p95 and
p99 only with at least 1,000 valid samples. Per-frame FrameInterval takes precedence over
an explicitly verified refresh fallback; no fixed 60/120Hz production budget.

Use existing Perfetto/FrameTimeline tools for native frame deadlines/jank, main thread,
CPU/RenderThread and input-to-present analysis. Frame duration is NOT input latency.
First useful frame / first interaction stay null without valid semantic instrumentation.
Do not upload raw traces containing user content. Memory/GC and physical acceptance remain
pending. A successful comparison does not automatically establish superiority or universal
acceptance. Test rapid interruption, Back, recreate/resume, bounds/font/density/theme
changes, music, keyboard and glass on/off before integrating into Work1's single Alpha.

Official technical references:
- https://developer.android.com/develop/ui/views/layout/custom-views/optimizing-view
- https://developer.android.com/topic/performance/issues/render
- https://perfetto.dev/docs/data-sources/frametimeline
