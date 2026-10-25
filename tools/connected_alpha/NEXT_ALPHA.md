# Next Alpha — stage A checkpoint

Base verified: PR91 / 8619ba40fbd8fd9d9d898ff307fb0c0716661254. PR89 and PR90 heads match the supplied references. Keep draft; no stable branch merge.

## P0 input ownership

The existing sibling-detach fix remains intact. A separate reproducible source path leaves DialogsActivity.blurredView VISIBLE with alpha zero and a click listener. MainTabsActivity receives onBecomeFullyVisible after preview close, but its ViewPagerActivity.FragmentState does not emit a child transition end if both springs complete before any fractional visibility update. A previously fully visible child also receives no new onBecomeFullyVisible in that sequence. The overlay's click handler only attempts to close a preview that no longer exists: the list below stays blocked, while the separate bottom tab bar can respond.

DialogsActivity now implements the existing TabFragmentDelegate.onParentBecomeFullyVisible ownership hook. It clears the overlay only when the shared navigation layout reports neither a preview nor a transition. Ordinary direct-fragment visibility uses the same idempotent cleanup. No timers, exception masking, animation removal, chat data, or navigation replacement.

`test_preview_input1273.py` executes the real FragmentState and MainTabs callback bodies with explicit UI doubles, comparing original1272 and candidate over2000cycles. Original: alpha-zero clickable overlay survives. Candidate: GONE, background released; active preview/transition preserved; repeated return harmless. This is a source behavior regression, not an Android framework touch or physical phone test.

Current stage:152host tests PASS,144general PASS/31optional external-corpus/R8 skips; resources compile/link against API37 PASS. First P0 commit CI40155398757 PASS including40native graphics tests and original detach reproducer. New isolated API35 native input:2tests PASS; real ViewGroup/MotionEvent at alpha zero blocks list taps before cleanup and passes100repetitions after cleanup; active preview/transition preserved. Original source/security contracts retained through exact inverse patch. Full compilation checkpoint and physical Poco acceptance pending. New theme/header/Music3/blur work has not started in this checkpoint. No new APK exists yet.

Diagnostic: overlay ACTION_DOWN logs only preview/transition booleans and alpha, gated by existing BuildVars.LOGS_ENABLED. No account or message data.

## Completed full P0 checkpoint

HEAD43e14d876601d16890b8c6f24c515103e6ece54f: actual assembleConnectedAlpha BUILD SUCCESSFUL in15m54s,279actionable tasks (227executed,52cached), Java/Kotlin/JNI/Chaquopy included. Verified internal checkpoint: versionCode1272; package io.github.jose22yt.flexygram.alpha; authorized certificate SHA256 c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c;96AArch64 ELF,16KiB alignment, ZIP/signature checks. Size95,337,858bytes, SHA2564eb14f2aa3be726a8ac6fed38f9090aa2da40f80fdc2fb509ffca529e287980f. This was an internal pre-effect compilation, not the final next-Alpha delivery. The transient local APK was lost when the execution environment restarted; no download is offered for that file. Build evidence is recorded from the successful tool result, not inferred from isolated tests. Final integrated APK must be rebuilt and verified at a versionCode above1272. Physical P0 acceptance remains pending.

## Stage B in progress

MessageDrawable now derives incoming/outgoing/selection colors from native Theme, reuses its gradient shader/matrix and retains the inside contour without the extra flat selection overlay. Its short rounded tail uses mirrored original cubic geometry; MEDIA, grouping, measurement and message heights are preserved. Before the environment restart, the two added native palette/gradient/mirrored-tail tests passed; the equivalent tests are committed for CI rerun alongside the preview changes.

BubblePreviewView now uses four synthetic grouped MessageDrawable bubbles, native text/time paints and tick assets, local translated ES/EN/RU samples, and a still representation of the active global wallpaper. Theme/wallpaper observers exist only while attached. No real chat/account, continuous wallpaper animation or per-draw layout/graphics allocations. Slider invalidation stays local; rows are measured only on size/font/theme layout. New preview native rendering/lifecycle tests and synthetic light/dark image generation are awaiting CI; full integrated app rebuild remains pending. No cached blur, new header or Music3 implementation is claimed at this checkpoint.

## Native theme/settings consolidation

SignatureChatThemeActivity now opens the real ThemeActivity with a focused presentation mode, replacing the two-link placeholder. It contains wallpaper, native user color, themes, accents, native preview, local editing/creation, Monet and automatic night mode. The classic entry retains text size, list layout, icons, swipe, in-app browser, media and all other original controls; theme/wallpaper controls appear once in the focused page. The in-app browser is a different feature and remains classic. Original unfiltered ThemeActivity constructor remains unchanged in row allocation/order; no keys are moved or renamed. Native click-handler body is byte-identical to the checkpoint.

A dedicated native Drawable supplies grouped Matte corners and native outline clipping, reused across binds; no dynamic blur/shadow or frame allocations. Two executable row-allocation tests cover legacy Alpha/non-Alpha, optional raise/sensitive rows, union of all original features and absence of duplicate theme controls. Focused screen skips the unnecessary sensitive-settings fetch, preventing a notification for the deliberately absent row. New native group-surface graphics test is pending CI.

Bubble/preview HEAD586cd2bf40aeb00e237ace6b3c21a334da40a49a CI40176271058 SUCCESS:154host,144general/31optional skips, resourcesAPI37 and46isolated Android graphics tests (including palette/gradient/tail and full synthetic-preview rendering/lifecycle). No full app/Poco validation is implied.

## Stage C cached blur — implementation pending native validation

New preference signature_cached_blur defaults false and preserves all legacy keys. The native cell/root wallpaper callback is reused only as a coordinate bridge; its old Glass/navbar source renderer is replaced. Static software bitmap wallpapers (including fully loaded, unrotated, unmirrored per-chat images with their native draw-region/dim amount) use a shared cache with at most2entries and384px maximum edge. Telegram globalQueue scales/box-blurs once off UI; native BitmapShader/paint are prepared on UI result publication and reused. Each bubble draws the same native path with that texture, then its unchanged theme fill, contour and content. No screen capture, bitmap per message, per-scroll blur, draw-time shader allocation, new queue/animation engine or navigation callback.

Attached chat/preview owners cancel queued work, stop the bounded running kernel at row boundaries, reject obsolete generations/results, remove weak waiters and clear shaders/source references on detach. The last owner releases the shared pixels. A released cache slot wakes an attached waiting owner without a timer. Changing the source, bitmap generation, background color or native dim amount invalidates the entry; ordinary scroll/size changes reuse pixels through native coordinates. Motion, patterns/tiling, rotated/mirrored/fading images, unknown direct color filters, hardware-only sources, failures and memory pressure keep Matte. The settings explain compatible static-image support; the preview uses the same cache and renderer and shows a still wallpaper.

Validation so far: read-only native static-source eligibility executes with explicit receiver doubles, rejecting incomplete/moving/rotated/mirrored/patterned/recycled sources. New native cache tests cover actual worker/UI handoff, shared bounded pixels, smoothing, root/scroll alignment, renderer opt-in, cancellation/late results, source-generation invalidation and cache-slot retry. A synthetic native preview produces blur-off/on images. These native tests and integrated app rebuild have not passed yet at this checkpoint. Physical frame times, memory/jank comparison and Poco acceptance remain pending.


## Selective PR90 performance integration

Reviewed upstream production commits0e24b6ada0713914d63ef5102d4f4c0057c4f073 and1f059b067f0fca68b87927749559736dbcb900da apply cleanly without restoring any older Work1 source: LyricsFill reuses the identical gradient for unchanged colors, and LyricsView owns/cancels its coalesced scroll/follow work and releases line shaders on detach. The full PR90 lab and its20host regressions are retained. Native pixel-equivalence/shader-reuse/lifecycle probes are added to the existing CI graphics gate; no device speedup or final integrated build is claimed. Existing historical bubble audit now uses the exact reviewed reverse-patch chain to test the preserved legacy renderer; current optional-cache behavior is covered by the separate actual cache/preview tests.


## Validated B/C + PR90 checkpoint

HEADbf2c5703c4ec2ce75cffc4ff09c8a29bbe77b14e CI40179982727/job121128784272 SUCCESS:177host tests,144general PASS/31optional external-corpus/R8 skips, AndroidAPI37 resources,55isolated API35 native graphics tests. This includes actual bounded blur/kernel/shader alignment/cancellation/retry, synthetic blur-off/on previews, grouped Matte theme surfaces, cached lyric-shader pixel equivalence and detach cancellation, all prior login/music/composer/home probes, native input recovery and the independent original detach-NPE reproducer. Original P0 full module checkpoint remains separate; no new full app build or physical performance claim follows from these isolated probes.

Local15bubble/preview/cache graphics tests also PASS. A local-first failure exposed fixture leakage of CONNECTED_ALPHA/density from an earlier test; CachedBlurVisualTest now resets its complete mode/theme/preferences/geometry inputs in @Before, without changing production or relaxing pixel assertions. Synthetic blur-off/on images were visually inspected: source texture is softened inside native bubble paths; text/ticks/contour remain sharp. The fixtures do not contain private chat data or reference screenshots.


## Optional blur / native-alpha regression

A stronger isolated native test reproduced an opaque wallpaper ghost at drawable alpha zero: the legacy coordinate callback has no alpha parameter, so its cached image ignored MessageDrawable.setAlpha while native fill/contour faded correctly. Reverting only the new alpha gate in the generated probe reproduces expected0/actual255; candidate15bubble/preview/cache tests PASS with the gate, including alpha0/64/128/254 and unchanged pixel assertions. During these native transitions the optional cache stays warm but rendering conservatively uses Matte; normal alpha255 restores cached sampling. No saveLayer, offscreen compositing, timer, cell measurement, native animation or navigation changes. Physical smoothness of this conservative transition fallback remains pending.


## Music3 recovered presentation checkpoint

Full-sheet hero now spans the width and fades into the controls surface with one shader rebuilt only on size/color changes. Artwork palette uses the existing PlayerArt queue and a bounded8entry cache; mini/pills keep their previous palette. Alpha has deterministic decorative columns without a playback invalidation loop; seeking/cancel/accessibility handlers and audio transport remain native. Main order is shuffle/previous/play/next/repeat, with the existing accessible two-row fallback only where five48dp targets cannot fit. Four tiles remain Speed/Lyrics/Queue/More. No owner reference artwork is included.

Before the environment reset these14isolated native Music tests and4host boundary tests passed, including theme contrast, stable columns, bounded palette, shader reuse, responsive/large-font layout and unchanged compact controls. Recovered source is checkpointed for a new CI run; this is not a complete-module/device pass. Header and selective PR93 integration remain pending. PR93 metadata verified at0602aadcccbba39936e9fb161901dee88e785f62; no duplicate PR90 integration. No final next-Alpha APK exists.


## Header integration checkpoint — native/full-module validation pending

Connected Alpha now binds a shared HeaderGeometry/HeaderSurface adapter to the existing ActionBar and ChatAvatarContainer. All three outer surfaces use one height; the title is centered in the useful window width regardless of counter width or RTL. Font measurements adapt the common height, with secondary status collapsing only when a narrow large-font window cannot fit both lines; native accessibility text remains available. Native back/profile/menu views own their original actions. The separate non-clickable counter is sourced from the native cached main/archive/filter unread totals only when origin arguments exist; unavailable context shows only Back. No new navigation flags, animation engine, observers, timers or per-frame graphics objects. Legacy native unread badge rendering is scoped out only while this presentation owns the back component.

Chats gains one dedicated header entry and native Matte settings: Signature/classic, count, normal/compact, opacity, synthetic preview. Old explicit appearance choices remain conservative; fresh auto-migration is tagged without replacing legacy values. The duplicate Alpha Appearance toggle is hidden, preserving non-Alpha behavior and its keys. Native avatar/profile/menu callbacks and the P0 layout/Dialogs sources remain preserved. Cleanup removes the counter only during explicit view reconstruction, never from a child window-detach callback.

Java syntax passes for all changed header/native classes. Four host regressions pass, including1920actual geometry cases across width/density/font/RTL, exact original native menu body and frozen P0/auth/audio sources. A new isolated Android renderer/controller/input suite uses actual new controller and extracted native avatar methods with explicitly declared ActionBar/navigation/image-service doubles; CI/native/full-module results are pending. No Poco or final APK claim.


## PR93 selective integration

Verified PR93 HEAD0602aadcccbba39936e9fb161901dee88e785f62 and production commitd28f7c2bd1b545b1da1061373c3c8c11d0faeadc. ImageReceiver had no later Work1 changes; the applied candidate is byte-identical to PR93. Its isolated production integration is commitcfa949b1fbcf6cf2be469eff9c802ef68f9d7d89 and can be reverted independently; no second PR90 change was applied.

All17Performance2 host tests pass locally, including30000differential transitions, virtual-overload/callback preservation and the explicitly HotSpot-only allocation experiment. The four-cohort clock/environment/thermal/refresh/privacy guards remain. Work1 Music3/header changes after340cd323 are preserved via a separate exact inverse patch for original PR93 reserved-source assertions; actual source inventory hashes remain actual, and normalized reservation counts are labeled. Unreviewed mutations fail. Two earlier UI tests now reverse the approved header delta for their historical menu/row assertions; new header tests execute the real geometry and original menu handler. Header Android/controller suite and full integrated app compilation remain pending. No Android FPS, latency, GC or superiority claim.
