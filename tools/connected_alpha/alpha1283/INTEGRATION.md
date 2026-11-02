# Alpha1283 continuation from Work1 PR122

Base: `bb3af73e085f3cdb3e9e92f35f6d1b692c04afcb`. Its signed private build40787796477 succeeded; preserve it as a checkpoint, not this candidate. No Work1/stable branch or historical PR is rewritten.

## Implemented

- Native Matte Context Panel retains native permission checks/actions/overflow. A direct Chats → Message interactions route opens the same persistent opt-in, OFF by default. Native reactions, selected-message scrim and native fallback remain.
- Reuse only compatible PR117 encoder/spec/metadata/workflow/policy. Never import BubbleTapMotion or the cancelled engine.
- Explicit Sticker tab for **fully visible, unrestricted text bubbles** in ordinary writable cloud chats. Native parent background + actual cell draw + native outbounds passes are captured once on UI into at most512×512. No whole-chat screenshot, native renderer rewrite or hidden-message capture. Unsupported rich/media, clipped, transitioning, protected, TTL/spoiler, secret, scheduled/paid/slow-mode cases retain existing native paths; do not claim universal conversion.
- Bounded idle-releasing worker compresses and validates WebP off-main; preview stays local. Explicit Send uses the existing SendMessagesHelper uploaded document with real sticker attributes, account/peer/thread/quote arguments. No photo/generic fallback.
- Success requires its own local outgoing ID and a matching account/peer server notification with an actual server sticker document. Local metadata, wrong events and generic server documents do not count. Pending transactions retain no UI and release observers on success/error/timeout. A possibly queued native upload keeps its file for the native retry lifecycle; menu close must not delete an active upload. No account/server test is run in CI.
- Save uses Android ACTION_CREATE_DOCUMENT and a bounded off-main content-URI write. It saves a WebP file, not an unconfirmed favourites entry. Closing a menu cancels obsolete conversion, releases UI references and unsubmitted files. Published bitmaps are cleared, not recycled under HWUI.

## Performance and preservation

Smart Preview line positions move from two getPrimaryHorizontal calls on every draw to two calls during the existing layout build. Only primitive relative coordinates are retained; current messageLeft/RTL/clipping/alpha still apply on draw. Rebind/layout construction refreshes them. Native Android pixel comparisons against the actual PR122 renderer cover translation, new layout, RTL/font scales and icons. This is structural work reduction, not a measured phone FPS/latency claim.

Native first-touch hit testing reuses one Rect/coordinate scratch pair per search, limits traversal to128 views and retains the original native dispatch/curves. The conservative fallback remains for an unsupported tree. No new animation, global clock, scroll polling, unbounded cache or per-frame preference I/O.

Header4, blur kernel/cache/workers, Matte, original message cells, native sending services, auth/JNI/composer/player and their native animation code are preserved. Only the Context Panel host, its direct settings route, native hit-test helper and Smart Preview draw metrics change. Historical reviews are immutable; a separate exact Alpha1283 review rejects unknown source mutations.

## Acceptance limits / integration

Run host/Android isolated suites, resource link and the full ARM64 build. Protocol/account/cell hosts are explicit doubles in isolated sticker tests. Full ChatActivity compilation is proved only by Gradle, and an authentic server send/second-client reception only by owner-controlled physical testing. No real accounts, messages or private screenshots in CI or repo artifacts.

Install the final signed version1283 over1282 without uninstalling. Validate text bubble conversion/restriction rejection, send and receipt as sticker on a second client, local Save, menu cancellation/recycled rows, native reactions/actions, cold/warm blur, Portrait theme/font/RTL, repeated Back→other-chat, folders/music/background. FrameTimeline/gfxinfo p50/p95/p99/jank and high-refresh latency remain physical acceptance; do not infer them from video playback or host timings.

Use the unchanged Work1 private-draft delivery machinery with the exact reviewed candidate SHA. No public APK upload, new signature, account migration or automatic merge. Revert this candidate's source/tests/review together; version1283 was chosen above the last verified private1282.
