# FlexyGram Native Instant Touch — integration review

Base: PR #119 native Exteraless animation restoration HEAD `2fd05e955c494a9eb0112c23e2ff9511a459e6c8`.
Candidate: PR #120, standalone branch `feature/native-instant-touch-first-tap`.

## Invariant
- Built in by default. **No preference toggle / profile / speed slider**.
- Exteraless/Telegram still draw all the native opening and closing animations.
- Do not import cancelled `app.flexygram.motion.*` or resurrect PR #114's spring/animation owner.
- Never synthesize or replay MotionEvent; the same original DOWN flows through `super.dispatchTouchEvent(ev)`, and original native RecyclerListView handles UP and click.

## What was actually changed
1. A conservative single-DOWN hook in ActionBarLayout, after native sheet routing and before original View dispatch.
2. Native close is eligible only while ChatActivity is exiting and the **previous fragment is an actual visible DialogsActivity**, directly or through MainTabsActivity.
3. Original visible DialogCell hit-test, taking the native view bounds/clipping; outgoing top surface must not cover that touch. Modal, preview, story, keyboard, sheet, swipe, predictive back and action mode disable the handoff.
4. Eligibility calls the **existing** `onAnimationEndCheck(true)` completion to dispose the native closing animator and unwind the old chat before passing the genuine DOWN along.
5. Everything else retains the original native behavior. If the destination row is not yet visible, do not guess or click through Chat A.

## What CI does NOT prove
The isolated policy and source test only verify gates, wired dispatch and zero user settings; it is not physical touch delivery or the full Android app build. The restored Alpha source lineage has an exact historical change scope and its old alpha verification may reject *newly added* PR120 paths until Work1 creates an independently reviewed integration snapshot. **Do not overwrite historical frozen contracts.**

## Physical acceptance
- A open -> Back closes -> B visible during closing -> original first DOWN/UP on B opens B. Repeat at different release timings and along the exposed list edge; no second touch.
- Back, predictive Back, animation cancel, panel/IME, preview, shortcuts, settings, multi-account, nested tabs, folders, drag/scroll and touch slop preserve native behavior.
- Never jump to an unseen B while opaque outgoing Chat A covers that location.
- No duplicate actions, orphan views, broken focus, animated button regressions, callback reentrancy/detach exceptions.
- Collect touch-to-open timing and p50/p95 frame metrics on Poco X8 Pro / Android 17; compare original Exteraless and PR119.
- Ensure user sees original Exteraless animation duration/curve, no custom spring or visual effect.
- Only after full Android build, real input and APK testing should PR120 be marked ready to merge.

**Scope limitation**: this first patch implements ChatActivity close → visible dialog cell, not arbitrary chat-open interruption, all custom tabs or media sheets. Broader guaranteed instant navigation requires separate, physically verified native routes; do not claim universal coverage.
