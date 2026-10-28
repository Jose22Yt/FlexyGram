# Flexy Motion Instant Navigation — P1 exposed-surface handoff

## Status and precise scope

**Experimental production integration, not physically accepted.**
Base: Alpha1279 / PR112, commit `d50677f723292d0e405eae8e1529f65416ff9cbd`.
Independent branch; no merge to main/develop, no APK/signing/release, no telemetry claims.

Existing PR108/112 already integrates shared motion clock and configurable motion
presets. This work **does not replace those animations**. It changes only one
touch-dispatch decision in `ActionBarLayout` and adds a small fail-closed policy.

## Real user-facing behavior: one tap opens B

When closing a regular `ChatActivity` to `MainTabsActivity` or `DialogsActivity`,
the departing chat translates to the right. The list is already attached and
visible behind it. During this limited exposed interval:

1. Android delivers **the original** `ACTION_DOWN` to `ActionBarLayout`.
2. The policy confirms the point is **well inside the exposed list area**,
   not in the outgoing chat, a modal, preview, sheet or gesture.
3. The existing native `onAnimationEndCheck(true)` completes the closing
   transition and its fragment/lifecycle cleanup.
4. `onInterceptTouchEvent` returns **false**. Android's normal
   `ViewGroup.dispatchTouchEvent` hit testing now dispatches the *same*
   original DOWN to the list, without synthetic taps.
5. The list's real row handler receives subsequent MOVE/UP normally. If the
   user completes a valid click on chat B, **B opens with the existing native
   animation without requiring a second tap**.

No interaction is fired merely because a finger touched down: scrolling,
gesture slop, cancellation and the click's own action ownership still belong
to the actual destination view.

### Eligibility

- A normal close transition is active, with a valid native close callback.
- Stack top is `ChatActivity`, below is `MainTabsActivity` or `DialogsActivity`.
- Previous container is attached/visible, outgoing container visible and
  translated right; `ACTION_DOWN` is inside a conservative left-hand region.
- At least 16dp from exposed boundary, container edges and top/bottom.
- No previews, popup/sheet ownership, Android predictive-back progress,
  active tracking, action mode, or layer/sheet layout.
- Bounds must be finite; no unknown geometry or no-exposure triggers.

For all other cases the original interception and transition guards remain
unchanged, including opening animations and non-chat screens.

### Why not call `performClick` or clone `MotionEvent`?

Touch streams need a consistent DOWN/MOVE/UP owner. Faking a second event or
replaying UP into a newly attached view can open the wrong item, trigger
double actions or violate gesture cancellation. The safer narrow P1 solution
commits the old close *before* the framework resolves the original DOWN's
target and then lets Android do standard dispatch.

### Known limitations / items Work 2 must extend

1. This **does not** make the entire app interruptible. It covers an
   exposed, directly touchable region of chat-list during a *standard close*.
2. Taps inside the still-visible outgoing chat remain owned/blocked as
   before; do not ghost-click a row hidden behind opaque content.
3. Opening A, reversing halfway; close via predictive-back; profile/settings
   transitions; tab switches; sheet gestures; transparent overlays; and
   rapid intent coalescing still need distinct, state-aware implementations.
4. Position/velocity-preserving spring retargeting needs a generation-owned
   transition coordinator; forcing completion may create a visible snap.
5. This P1 may still exhibit an unwanted snap on release or expose a hitbox
   that has moved under a shared animated surface. **Physical testing is
   mandatory before integration.**
6. Commit to **one owner** for each event. Never indiscriminately return
   false for every animation, disable native guards, or replay stale clicks.
7. The Work1 Alpha1279 Smart Preview hotfix / PR113 is a parallel branch.
   Rebase carefully and keep its reviewed changes and test contracts.

## Required testing and observed evidence

Quick host checks (no Android account, no APK):

```bash
python3 tools/connected_alpha/motion/verify_instant_handoff.py
mkdir -p /tmp/flexy-handoff-classes
javac -d /tmp/flexy-handoff-classes \
  TMessagesProj/src/main/java/org/telegram/ui/ActionBar/FlexyNavigationHandoffPolicy.java \
  tools/connected_alpha/motion/InstantHandoffPolicyTest.java
java -cp /tmp/flexy-handoff-classes InstantHandoffPolicyTest
```

The source-scope test reconstructs upstream ActionBarLayout **byte-for-byte**
and verifies its Git blob SHA; unknown upstream changes must be explicitly
reviewed, never silently normalized.

### Physical Poco acceptance matrix

Test Alpha1279 baseline vs this candidate with display refresh mode,
thermal state and settings fixed. For 0%, 10%, 25%, 50%, 75%, 95% close
progress: tap **only once** on an actually exposed row B. Observe whether
B opens, whether any first tap is lost, and whether the row under the finger
remains stable. Repeat with FLASH / FLOW / SIGNATURE and maximum elastic
setting, 30+ valid taps per condition, plus abort/cancel/scroll cases.

Include: RTL/large fonts; back-gesture and predictive back; keyboard open;
music mini player; spoilers/previews; dark/light theme; orientation;
concurrent rapid A -> list -> B -> list -> C; view detach; notifications;
and lifecycle interruption. Test no double navigation and no ghost clicks.

Record FrameTimeline/Perfetto touch-to-response, jank, p50/p95 transition
start, GC and thermal comparability. No fabricated FPS/latency. An
isolated Android API35 probe should exercise **real ViewGroup dispatch**
with the integration before calling this fully done.

**P1 acceptance:** original single DOWN/UP opens exposed B, exactly once,
without waiting for A's full animation; no regression in protected modes.
**Global Instant Navigation 1.0 remains unfinished** until Work2 builds a
coordinator for additional transitions and validates physical behavior.

## Rollback

Revert the ActionBarLayout-specific commit and delete
`FlexyNavigationHandoffPolicy.java`; the PR108/112 motion engine and all
settings remain intact. No user preferences, data, build identity or
migration changes.

## P2 coordinator checkpoint

The lazy, thread-confined FlexyInstantNavigationCoordinator stores logical intent IDs, states and generations. It has no clock, queue, retained callbacks or View references. Native accepted open/close operations report their ownership after the existing acceptance guards. The exposed-list DOWN transaction finalizes only its generation once; the actual row recognizer still decides which chat to open. Unknown/covered/modal input retains native handling. No cached or fabricated click is executed.

Native completion snapshots its old controllers before invoking fragment callbacks. If a callback accepts newer navigation, cleanup stops only the old spring/animator/runnable and preserves the new owner and transforms. A reentrant Animator cancellation cannot resume older close cleanup over a newer screen. Host tests execute the actual native completion bodies with explicit fragment/view/controller doubles, and fail when the new guard is disabled. Android tests use real ViewGroup dispatch and the actual coordinator/policy, but the fragment transaction remains an explicit double. Protocol stress covers10,000 replacements; it is not device latency or FPS evidence.

Alpha1280 PR115 head55e3a479 leaves ActionBarLayout unchanged relative to Alpha1279. Do not restore an older FlexyFrameMotion over its generation-batch fix. Future integration must combine both appended MotionEngine tests and compose the exact alpha1280/handoff contract projections; no Work1 branch has been modified or merged. The following P3/P4 checkpoints add ordinary opening interrupted by Back and scoped geometric/velocity reversal. Native gestures and broad surface coverage remain subsequent stages. No app identity, version, authentication, certificate or distribution changes.

The native spring end-listener also checks its generation after central completion before resetting innerTranslationX. A callback may accept another screen during that completion; the old listener must not resume its trailing reset over the new transition. The host ownership regression executes this exact native listener and fails if that final generation check alone is removed. This is a functional/source-level regression, not physical ANR or latency evidence.

## P3 ready chat opening interrupted by native Back

For an ordinary opening ChatActivity with an attached destination and a running known spring/timeline, the same native Back may finalize the pending opening and immediately continue through the original Back handler. The native fragment may still veto closing. Previews, swipe/predictive gestures, sheets, modals, right/layer panes, deferred keyboard/open callbacks, detached views and unknown custom Animator ownership retain their native path. A newly accepted destination or a newly shown modal consumes the old Back instead of redirecting it. Modal/sheet/story ownership is checked both before and after the native completion callback.

Android probes compile the exact Back, preparation and native completion bodies with real FrameLayouts, the real SpringAnimation bridge and coordinator. At the P3 checkpoint fragment/account/modal services and the subsequent closing transaction remained explicit doubles; P4 upgrades the closing renderer as described below. Tests cover all local profiles/system animator scales, a two-second timeline, slow low-damping spring settings, reduced motion, rapid duplicate Back, native veto, preexisting and newly shown modals, deferred keyboard and reentrant navigation. They establish request/state/lifecycle behavior, not real IME, physical latency or full-chat-stack acceptance.

The P3 checkpoint finished the opening before closing, without preserving position/velocity. P4 below adds a scoped continuation; broader gesture/surface integration and physical acceptance remain pending.


## P4 ordinary analytic opening → Back continuity

A running ordinary analytic chat opening can now seed its native closing renderer with `q = 1000 - p` and inverse physical velocity. In the unchanged native geometry this preserves outgoing chat translation/scale, underlying screen translation, inner translation and action-bar crossfade. A bounded overshoot is retained instead of clamped. No new clock, renderer geometry, input event, preference or waiting period is introduced.

The bridge exposes snapshots only while an attached, visible analytic trajectory is active. Timed/legacy, queued completion, reduced motion, active IME, custom owners and all earlier modal/preview/gesture exclusions keep their safe native fallback. The seed contains only primitives and is consumed once in the same native Back call; `finally` clears it on veto, search, PIP, custom animation, deferred keyboard or any early return. Accepted destinations invalidate stale seeds. Initial rendering of the seeded actor is opt-in, synchronous and guarded against cancellation/restart.

The standard actor captures its generation once at construction, not anew every frame. Before and after fragment progress callbacks, obsolete ownership stops that actor and its writes. This also covers an accepted destination whose replacement actor is deferred. Its end listener cannot reset a newer scene. Work1's separate FrameMotion generation-batch fix is not altered here; it must remain when integrating PR115.

The Android probe now compiles the exact standard opening **and closing renderer**, factory, Back and completion bodies using real FrameLayouts and the actual spring/coordinator. Only fragment/account/dialog services and fragment-stack transactions remain explicit doubles. Regressions compare transforms and inverted physical velocity in the same UI call under Flow/Signature and several speeds/progress points, including overshoot; they exercise timed/IME fallback, veto/seed cleanup, hidden/legacy snapshot refusal, reentrant/deferred replacement and first-render cancel/restart. These are API35 Robolectric checks compiled against API37, not a full-app run, touch-latency measurement or Poco/Android17 acceptance.

Remaining: close A → exposed row B still uses P1 early completion and has no full geometric/velocity handoff; swipe/predictive Back continuity and broader surfaces are not completed. Physical comparison, FrameTimeline/jank and integration over Work1 remain pending. Rollback of this P4 commit removes only its bridge snapshot/seed and ownership additions, leaving P1–P3 and all application data/settings unchanged.
