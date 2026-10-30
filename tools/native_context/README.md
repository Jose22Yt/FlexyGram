# Native context and fixed Home — Alpha 1288 candidate

Base: PR134 `6ed4d9154a032eebd22e6c236701308e388bcb17`, descendant of PR133, PR132 and PR131. No merge or Beta identity change.

## Reference analysis

`50957.mp4` shows the existing menu working, but the message and options appear as separate movements. `50124(8).mp4` is the visual target: selected message stays readable between reactions and a compact vertical action card; opening, interruption and return must feel connected. Frames were inspected from both owner videos. They are private review inputs and are not committed. No claim of reproducing proprietary Apple code or physical acceptance.

PR134 handed off X/Y scale but discarded velocity; it reset the real cell before an optional language-detection wait, and reactions had an independent timed animator. The candidate samples live position AND velocity at actual popup display, reuses the existing `app.exteraless.player.Spring` integrator and drives message recovery, action-card appearance and native reaction progress from one frame callback. Close retargets that running state and completes native dismissal after settling. Detach and non-animated dismissal finish cleanup immediately. Within native touch slop, drag retargets subtle squash resistance without assigning position. Gesture cancellation releases from current momentum; hard reset is reserved for recycle/detach and ownership transfer. No frame work remains at rest. Native action permission checks, overflow, reaction dispatch and media controls are retained. Photo/video/voice/file/sticker/group surfaces receive non-consuming tactile observation; native media/link/button taps retain their actions. Only eligible, otherwise unclaimed message surfaces use the single-tap menu.

Chats contains one selector: Classic / Signature iOS 27. Retired per-effect flags cannot override the selected style. Fixed motion uses a frame clock, independent of developer animator/window duration scales; the app's `view_animations` reduced-motion choice and screen-reader accessibility policy suppress motion.

Home keeps the existing solid bar, icons, theme and selection indicator at its former default profile: 60 dp, 23 dp icons, 10 dp sides, 9 dp gap plus system insets. Four default destinations; narrow layouts retain native overflow. Visual/tab customization screens and navigation-style switches are removed. Only named Home keys migrate; other preferences and the chat composer remain intact. Alpha increments to 1288; Beta stays 1287 with its approved official certificate.

## Verification

`python3 -m unittest discover -s tools/connected_alpha -p test_native_context135.py -v` compiles the **actual** integrator and motion controllers with explicit host frame-delivery doubles. Checks 60/90/120/144 Hz simulated cadence, 4140 frames, live velocity handoff, interrupted close, finite bounded geometry, stale callback disposal, lifecycle cleanup and no idle redraw. These are not measured FPS, nor Android/device evidence.

Android isolated suites: `liquid_navigation`, `context_panel`, `interaction2`; updated for the fixed bar and single style selector. Full application compilation/signing and APK verification are additional mandatory gates. Test results belong to the exact candidate commit, never an earlier APK.

Physical acceptance remains pending without the Poco: own/incoming text/media, clear/dark, RTL and fonts, native media actions, repeated open/close, Back during entry, outside dismissal, chat switch/recycle, preview and folder/scroll regressions. Confirm one contact -> compression -> reaction/action presentation -> damped return. Compare reference and candidate with equivalent conditions using `tools/performance_p0`; do not convert simulated frames into physical FPS/jank/latency claims.
