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
