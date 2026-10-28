# Flexy Motion Instant Navigation — P1 exposed-surface handoff

## Status and precise scope

**Experimental production integration, not physically accepted.**
Base: Alpha1279 / PR112, commit `d50677f723292d0e405eae8e1529f65416ff9cbd`.
Independent branch; no merge to main/develop, no APK/signing/release, no telemetry claims.

Existing PR108/112 already integrates shared motion clock and configurable motion
presets. This work **does not replace those animations**. P1 below describes the initial
exposed-surface touch policy. The P2–P5 checkpoints add generation ownership,
ordinary opening/Back continuity and settling callback safety; the full-client
mission remains in progress.

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

Outside P1 the original interception guards remain; the separately guarded
ordinary chat opening/Back route is described in P3–P4 below.

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
3. P4 adds ordinary analytic opening A → Back reversal. Predictive-back
   continuity, profile/settings transitions, sheet gestures, transparent overlays
   and broader intent handoff still need distinct, state-aware integration.
4. P4 preserves position/velocity in its scoped reversal. P1 close A → list B
   still forces completion and may create a visible snap.
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

## P5 settling ownership checkpoint (not full gesture continuity)

A regression reproduced the old predictive end/cancel listener clearing `backAnimator` after the slide-completion callback had accepted a replacement. Predictive and native non-M3 listeners now release only their own field **before** invoking slide completion and ignore obsolete end/cancel events. The existing `onBackStarted` settling prefix retains a replacement installed synchronously by the finishing animator; it no longer unconditionally clears that newer owner.

Tests execute the exact predictive renderer/end/cancel bodies, the exact non-M3 listener (with an explicitly synthetic test-only timeline), and the exact settling prefix of `onBackStarted`. They cover normal end, cancellation, stale cancellation and replacement accepted by the slide-completion double. The slide/fragment-stack transaction remains a double: these tests do **not** validate the full `onSlideAnimationEnd` lifecycle or prove the physical preview P0 fixed. Reentrant cleanup inside that native transaction and continuous swipe/predictive reversal remain pending. There are no new gesture effects, geometry changes, synthetic input, delivery changes or Work1 edits. Reverting this checkpoint restores the prior callback ownership behavior without data changes.

## P6 released edge-swipe → original list touch

A committed ordinary spring edge-swipe now exposes the same one-touch list handoff as P1 while it settles after release. A narrowly owned flag is set only by the native committed spring branch, cleared before its completion callback and on accepted open/close. The helper requires that exact visible analytic actor, no VelocityTracker/Animator/predictive input, an attached exposed list and the existing modal/preview/sheet/pane exclusions. It finishes the exact actor synchronously; its native end listener runs the original full `onSlideAnimationEnd(false)` before Android hit-tests the original DOWN. The real row retains MOVE/UP/cancel semantics. Reverting/cancelled or actively dragged gestures cannot use this route.

The new Android probe compiles the **entire actual native slide-completion body**, the actual settling spring branch, handoff/modal methods and interception body. Containers, Button, dispatch and springs are real; fragment/services are explicit doubles and the initial released edge-swipe state is staged. Tests assert lifecycle counts, stack ownership, one DOWN/UP with unchanged timestamps and one click; covered/modal/predictive/reverting owners and cancelled/dragged touches cannot ghost-click. This does not exercise a complete physical edge gesture or account stack.

Like P1 this completes the old visual settle; it does not preserve an outgoing A surface across opening B. Full A→B geometric continuity, live predictive interruption and physical frame/latency acceptance remain unfinished. `SpringAnimation.finishNow` refuses inactive/timed/legacy/hidden/reduced-motion-queued trajectories; it has no background work or additional animation clock. Work1's FrameMotion remains unchanged.

## P7 known native screens and exact continuation owner

The ordinary opening/Back route now explicitly admits SettingsActivity, ProfileActivity, ContactsActivity and SignatureMatteSettingsActivity subclasses in addition to ChatActivity. It still requires the native attached spring route and all previous modal/gesture/pane/IME guards. A concurrent custom Animator or legacy frame Runnable is rejected. Unknown screens, including authentication, are not added to the allowlist; their original Back handling remains intact.

The native fragment's existing `getClassGuid()` identifies the exact continuation owner, separately from a chat's dialog ID. Two fragments showing the same dialog cannot exchange a seed. Non-chat coordinator destinations use this existing per-instance guid, without storing Views or changing any preference, session or request API. Zero/unidentified owners fall back to native handling.

The Android tests execute the same Back/factory/rendering bodies for each admitted type under Flow and Signature, comparing geometry and physical velocity. Fragment classes and lifecycle remain explicit doubles, so these checks do not replace real Settings/Profile/Contacts/login or full-app acceptance. Unknown/custom/deferred/zero-guid paths stay blocked by native guards, and a separately accepted fragment with the same dialog ID rejects the old seed. No component of those screens, authentication, Work1 or distribution is modified.

## P8 OS Back input takes an ordinary spring opening

When the current visual route is the existing **Spring** style, a valid Android Back start may now take a ready ordinary opening from its current progress. It uses P7's explicit screen allowlist, exact fragment guid and existing modal/custom/IME/preview/pane guards. M3 Predictive and Slide visual styles retain their original admission during opening; this is not a claim that every Back visual style is complete.

The old opening is completed through its native lifecycle and the already-attached native gesture preparation runs. Complementary progress restores the outgoing/underlying geometry before returning from the same UI call. During input, OS progress and the existing native deceleration curve control that geometry; **no animation actor is active while dragging**. Event-time velocity is sampled without another timer/clock. Native spring settlement starts at that normalized progress and physical velocity; stale velocity after a finger dwell is discarded without delaying release. A distinct content/container-width regression failed before the normalized seed fix and passes after it.

Dragging and settlement report their generations to the existing coordinator. Only that gesture's callbacks can write its transforms. A replaced gesture consumes its old terminal event rather than routing it as Back into a newer screen; a later ordinary/new Back retains native handling. A modal shown by native begin-slide causes native rollback without dismissing that modal. Initial/reentrant opening completion, cancellation, reduced motion, detach cleanup, route changes and opaque/custom owners are covered. The native backdrop is obtained once at adoption and released by the existing slide cleanup. Each settling frame selects one geometry path, avoiding duplicate transform writes.

The new probe compiles exact native Back admission/progress/terminal bodies, opening renderer, continuation helpers and the native spring settling branch against API37, executing in Robolectric API35 with real containers/bridge/coordinator. Fragment/services, prepareForMoving and slide stack transactions are explicit doubles; the separate P6 probe still compiles the full real slide-completion body. Platform registration, private accounts, actual chat services/IME, physical API37, perceptual continuity, jank and touch latency are not validated by these probes.

Reference for callback roles: [Android OnBackAnimationCallback](https://developer.android.com/reference/android/window/OnBackAnimationCallback). No SDK target, manifest, distribution, signing, Work1 or FrameMotion change is required by this checkpoint. Full departing A → incoming B geometric continuity, M3/Slide opening takeover and physical/integrated acceptance remain pending.

## P9 consumed launcher terminal releases the captured gesture owner

The actual LaunchActivity callback forwards Android input through its existing lazy start and priority gates. An isolated probe of that complete callback reproduced two failures: when a higher-priority surface consumed commit, the child layout or drawer did not receive cancellation. This left the previous gesture's input/tracking state active. The callback now captures the current layout/drawer before asking the original priority gate, and cancels only that captured owner when the gate consumes the event. Its priority decision, normal commit, tablet/API33 paths, authentication and other activity code remain unchanged.

The full native callback body is compiled with real BackEvent/OnBackAnimationCallback APIs and the real child continuation probe. Activity services, drawer and notification locker are explicit doubles. Tests cover lazy progress forwarding, balanced notification locks, an overlay present before admission, an overlay appearing before terminal, drawer priority and replacement of the current layout inside the consuming gate. The two terminal tests fail before the change and pass after it. This is not full Activity/OS registration, private account or physical acceptance.

The source scope checker now reconstructs **all of LaunchActivity** to its original reviewed Git blob, in addition to all of ActionBarLayout. Work1 PR115 does not modify LaunchActivity; its branch remains untouched. No polling, replayed input, new delivery, identity, preferences, certificate or animation engine is introduced.

## P10 native timed opening → M3 / Slide predictive input

Known ordinary M3/Slide timed openings now transfer the visible native translation and alpha after native opening completion and Back admission, with the same GUID/generation and modal/IME/custom/preview exclusions. This captures View properties, not analytic velocity. No screenshot, polling, new renderer thread or animation engine is introduced. Spring P8 stays on its own original geometry/physical velocity path.

M3 retains the native geometry helper and settlement clock. Its bounded opening residual preserves the rear full-screen rectangle, front position/opacity and initial scrim, fades into the canonical gesture, and fades back to full screen on cancellation. Commit snapshots the current opacity and corner radius rather than flashing to their endpoints. Reset/start clear only the optional residual; default helper geometry remains unchanged. Slide keeps its native AnimatorSet, duration/interpolator and both custom fragment transitions; guarded FloatProperty targets preserve X/inner/alpha ownership. Its translucent opening retains the full rear surface while the gesture/settlement is owned. At zero system animator scale the owned slide cannot resurrect a finished animation flag.

A regression exposed the timed renderer writing after a fragment progress callback replaced its actor before any coordinator existed. Actor identity now remains mandatory even without a coordinator. The actual timed renderer also checks its captured generation before/after progress callbacks and before completion. A stale M3/Slide actor stops without resetting or closing its replacement.

Tests compile the actual timed opening, full M3 factory/listeners, full native Slide settlement and property bindings against API37; Android framework animation/containers/helper/coordinator execute under API35 Robolectric. Fragment/account services, prepareForMoving and slide transactions are explicitly doubled. Tests cover both native styles, cancel/commit, no progress, route changes, custom callbacks, unknown/IME/modal/preview paths, zero duration, detach and reentrant replacement. Exact scoped hunks must reverse before the complete ActionBarLayout/LaunchActivity/helper/bridge byte checks pass. Host/isolated tests are not physical performance measurements.

Integration: preserve Work1 PR115's FrameMotion batch-generation fix; no Work1 files/branch are replaced here. Revert P10 as a unit to remove timed snapshot, residual helper, owned properties and probes without preferences/data migration. Full visual close-A → open-B continuity, broader surface coverage and physical API37/FrameTimeline/touch-latency acceptance remain pending; P1/P6 still synchronously finish the old close on the original DOWN.

P10 follow-up: a new regression failed when reduce-motion was enabled during Slide input: its native AnimatorSet continued for the original duration. The owned native set now uses zero duration for instant/reduced-motion or an already hidden/detached owner, including its existing custom child animations. Owned animation/layout flags are installed before start so a synchronous completion cannot reinstall them afterwards. Unowned native ordering remains unchanged. No system settings are altered. The new test fails before and passes after the change.

## P11 exposed chat-body touch → native B opening

P11 keeps a ready ordinary analytic close/released swipe running on the original DOWN. Only the body's normal chat row is eligible: a bounded DOWN-only search (128 nodes, depth 24) requires a native RecyclerListView/DialogCell, interior coordinates, identity scales and the existing exposed-surface/modal/IME/preview/pane guards. Headers, stories/avatars, trailing controls, unknown/custom/timed owners and mismatched swipe/content widths retain the P1/P6 fallback. No Work1 component or screen is changed.

The real surface's **initial** translation is frozen for hit testing. The existing close renderer stores its current visual translation as a primitive; the original drawChild applies only their difference on Canvas. This preserves both the complete painted scene on DOWN and the original local coordinates on UP. Normal unowned MOVE/UP dispatch has a direct native fast path. No event is copied, modified, replayed or injected; no click is manufactured. There is no screenshot, bitmap, extra actor, delay, observer or polling loop. The bounded coordinate array is initialized only on an eligible closing DOWN.

Only a synchronous original-UP native Chat presentation may take over. All original delegate/fragment-creation guards remain, then native close finalization runs once. If it accepts a newer scene reentrantly, B is destroyed without replacing that scene. The explicit target GUID/generation owns a single opening seed: p = 1000 - closing p; physical velocity is reversed. The same native opening renderer preserves outgoing translation/scale and the home backdrop's painted position. A scoped public presentation wrapper clears the seed on custom/deferred/failed/early-return paths. Cancel/drag restores the current painted translation without opening anything. Natural close completion retains hit coordinates until the touch ends. Detach and accepted navigation release the touch's View/actor references.

A reduced-motion change can leave an analytic completion queued before UP. The bridge can drain only that already queued, non-cancelled, attached/visible analytic completion; active, timed, cancelled and detached actors cannot use that entry point. No seed is retained for that instant opening. Existing finishNow eligibility stays unchanged.

The new RevealProbe compiles the actual scoped native dispatch/presentation wrappers and admission, helpers, both analytic renderers, native click decoder and callback ownership. Android Views, GestureDetector, MotionEvent, Canvas, clock and bridge are real; RecyclerView hit lookup, account/services, fragment creation/stack mutation and slide transactions are explicit doubles. Separate legacy fallback probes keep P1/P6 coverage; the active probe exercises P11. Pixel comparison is isolated synthetic Android UI, not an application screenshot or hardware/GPU measurement. Tests cover original DOWN/UP coordinates, no DOWN finalization, B geometry/physical velocity, cancel/drag, natural completion, padding, reduced motion, GUID/generation/reentry, veto/defer/modal exclusions and detach. A counterfactual disabling only P11 admission exercises the actual earlier P1/P6 fallback and fails the DOWN-continuity assertion; restoring admission passes.

Source checks reverse exact P11 hunks before the existing whole-class P1–P10 reconstruction; historical manifests remain frozen. Rollback P11 production/helpers/tests/review as a unit, retaining P1–P10. No preference, account or data migration is involved. Integration must retain Work1 PR115's FrameMotion batch-generation fix.

Limits: this proves selected production paths with explicit doubles under Robolectric API35, compiled against API37. Full application dispatch, actual adapters/data, avatar/story/bot controls, physical Android17, high-refresh FrameTimeline/jank/touch latency and integrated Work1 acceptance remain pending. Non-analytic close A → B and special surfaces retain the existing safe fallback, without a claim of full visual continuation.

## P12 native destination fallback and swipe-width continuity

Two new active-Android tests reproduced a P11 functional regression: a valid row UP opening a non-Chat destination (such as forum topics), or explicitly requesting no animation, was rejected by the still-active close guard. The public presentation scope now completes only that already approved exposed-row close before handing these requests back to the unchanged native delegate/create/presentation path. It creates no animation seed for them and preserves preview/remove/no-animation parameters. Current modal/IME/pane/preview/owner exclusions still veto finalization. A generation captured after fallback prevents an older delegate/create callback from overwriting a subsequently accepted destination. The two tests failed before the correction and pass after it; earlier negative expectations for unknown/remove/preview admission were corrected to preserve these native actions, not discarded.

The incoming analytic Chat after a released swipe now captures which native width convention produced its seed. Its first measured container must match the outgoing container; that actor then uses the current container width for its existing native renderer, exactly as the swipe does. Ordinary/default actors retain the original width minus padding. Position, scale, inner translation, backdrop and physical velocity remain continuous with symmetric/asymmetric root padding; later container resize follows the same native convention. Width ownership is captured once per actor and cleared with the seed, without a new clock, renderer, observer, cache or allocation during frames. A mismatched incoming width declines the seed safely.

Tests extend the existing active RevealProbe with padded swipe → B, width-scope cleanup, container resize, mismatched-owner rejection, native forum/no-animation admission, fallback delegate veto and fallback create reentry. The complete isolated suite is 151 passing API35 tests compiled against API37. Fragment/account/stack and Recycler lookup remain explicit doubles; these are not physical API37 or full-app tests. Production changes remain limited to ActionBarLayout; Work1, authentication/protocol, preferences, identity, version and delivery are unchanged. Reverse P12 then P11 as coordinated source/test/review changes; original class-byte proofs remain required. Timed/custom/special-surface visual continuation and integrated device/performance acceptance remain pending.
