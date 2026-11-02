# FlexyGram Performance Engineering1.0

## Base, scope and evidence

Public source checked: PR89 HEAD997ac40a65be00c672dc8009b61f55825537d498, already integrating Work1 UI/1271, Login87 and Music88. Published Work1 PR85 remained0e359f0e7841a99d61c79f996dd162b7c836a9bf at initial inspection; no later integrated/corrective public branch was present. This does not reveal unpublished/interrupted Work1 workspace edits. No Work1 source is overwritten. Full source inventory/provenance is reproducible via `audit.py` and the exact scope contract. Original Exteraless reference is1ad6a60a6834ffca722b1a22f4fba27ecb29a061.

Only two production files change: LyricsView.java and new package-local LyricsFill.java. No identity/version/certificate/native library/session/protocol/preference/distribution change. No visual redesign/new effect/animation/timing constant. All nine explicitly reserved filenames plus bubble production and protected core files are tested byte-for-byte against integrated1271. Dialogs/ActionBarLayout/MessageDrawable/ChatMessageCell/Login/FragmentContextView/PlayerBarView/launcher/Chats remain untouched. Work1 still owns the physical preview crash, player/translator interaction, login/icon/Chats/bubble correction and final compile/APK.

`findings.json` provides component/method/scenario/current behavior/cause/evidence/proposal or change/validation/result/priority/risk/status/rollback per finding. Confirmed source behavior is distinguished from isolated native measurement and from unmeasured device hypotheses. Source complexity, grep hits and several JNI entry calls are not evidence of slowness.

## Confirmed changes

| Finding | Before: integrated1271 | Candidate | Evidence and acceptance limit |
| --- | --- | --- | --- |
| P1 active lyric shader | New LinearGradient every active text draw; also present in original Exteraless | One-entry cache keyed by both ARGB endpoints; progress still updates the same local Matrix | Actual inner LineView, API35 native Canvas:1000distinct shaders→1 over1000stable-color draws;0changed pixels across24million comparisons; color/alpha changes preserved. No ART-byte/CPU/GPU/frame-time percentage inferred. |
| P2 pending lyric work after close | Anonymous child-list scroll posts and750ms follow Runnable, no explicit container cancellation | One coalesced container-owned scroll Runnable; stop own list scrolling before removing follow/scroll callbacks; clear line shader on detach | Actual new detach body in an Android fixture: baseline pending follow/scroll executions1/1→0/0 after detach. StopScroll-rescheduling test enforces cleanup order. Not a demonstrated unbounded leak or physical ANR. |

P1 changes only resource reuse. Alpha's color, opacity springs, text layout, shadow/glow, wave/seek, matrix and native playback stay unchanged. A line stores at most one shader; there is no static/global/growing cache. Different colors replace it, detach clears it. Extra retained memory is one shader+two color fields per existing line instance, bounded per view rather than a new global cache. Actual ART/native byte totals require device profiling.

P2 preserves the750ms interaction delay and current-line calculation. Duplicate size/lyrics alignment requests coalesce to the latest existing state. Container ownership matters: a child can detach before its parent, so parent cleanup cannot rely on the child's old Handler. The first experiment exposed that limitation; the final regression includes it. Reattach/navigation/country/media state are not silently reconstructed. Full RecyclerListView/real playback acceptance remains pending.

Production changes are isolated commits so each can be reverted. If integration/device acceptance regresses, revert the responsible production commit and update the reviewed performance reversal contract to the resulting accepted source; retain the original security/parity tests. No preferences or migration must be undone.

## Architecture audit: what was preserved and why

- Startup/ApplicationLoader/LaunchActivity: NativeLoader's synchronized+volatile loaded guard prevents repeated JNI loading despite multiple entry calls. Its ordering protects Telegram startup; no deferral justified. Config/preference/module setup contains synchronous work, but no trace establishes duration or blocking. Signature Welcome already avoids legacy EGL/TextureView construction for Alpha. No process-wide lazy-start rewrite.
- Plugins/Chaquopy: PluginsController checks engine enablement; Python.start runs in its existing single-thread executor. Preferences/plugin directory initialization is synchronous; impact is unmeasured. Disabling plugins or changing callback/security order would hide cost by removing functionality. Keep original engine and service paths.
- Chat creation/destruction/navigation: source-level createView is large, but size does not identify first-frame cost. Existing account/global observer removals are present. Extended existing actual-method preview model from200to2000cycles with explicit fragment/view doubles; no ActionBarLayout edit and no claim about the owner's onSlideAnimationEnd exception. Physical P0 remains Work1's blocking prerequisite.
- Dialogs/rows/folders: native recycling, lazy Paint/Path, color-keyed archive/reorder shaders and existing Home per-tab tints are retained. Guarded allocations are not incorrectly reported as per-frame churn. No duplicate-observer defect or scroll regression demonstrated. Long test-list/album/avatar/folder workload traces are needed before touching reserved DialogsActivity.
- Message drawing/images/reactions:1271 native path memoization/grouping/selection, ImageLoader/ImageReceiver/dispatch queues remain. Bubble thickness/spacing/blur and cell work belong to Work1. No GPU/overdraw/upload/lock contention diagnosed without actual traces. Separate shader churn in lyrics does not prove message rendering is slow.
- Music: Alpha fixed palettes already bypass old cover color extraction; original PlayerArt has64cached color entries and background quantization. Existing CoverImage/ImageReceiver artwork caches are reused. Mini/compact hosts add some hierarchy/notification/bounds work versus original Exteraless, but no measured whole-player regression exists. Existing30Hz wave scheduling is not changed to make comparison look faster; real120Hz navigation still needs paired traces.
- NotificationCenter/core/services: duplicate-membership guard, broadcast mutation queues, specialized hot observer lists and background dispatch are already present. No account/event reduction or service disabling. MediaController/MusicPlayerService/auth/MTProto/JNI/session storage remain exact.

This is an inspected source audit across the named architecture and a narrow measured drawing/lifecycle experiment, not an exhaustive hardware profile of every path. Main-thread/RenderThread blocking, GPU saturation, GC, leaks, long-session memory, input latency, cold/warm process timings and battery behavior remain unmeasured unless explicitly listed otherwise.

## Reference comparison

| Metric | Original Exteraless | Integrated Alpha1271 | Performance candidate |
| --- | --- | --- | --- |
| Source reference |1ad6a60…|997ac40…|Final performance PR HEAD|
| Active-line shader construction | Unconditional allocation confirmed in source |1000objects/1000stable draws in isolated native probe|1object/1000stable draws in same probe|
| Pixels in that probe | No full original-app capture | Baseline |0different pixels; changed ARGB endpoints also equivalent|
| Cold/warm startup, median/p95, high-refresh frames, jank |Pending|Pending|Pending|
| ART allocations, CPU/GPU, PSS/RSS, GC, prolonged use |Pending|Pending|Pending|
| Overall superiority |Not established|Not established|Not established|

`reference_matrix.json` keeps all physical metric values null. No run with simulated dependencies is substituted for a full app/device run. The lab reuses existing parsers and native probe machinery. Tests cover120Hz budgets, variable intervals, invalid/flagged frames, separate windows, missing data, nearest-rank p95, invalid comparisons, thermal/battery gates, read-only capture and scoped Perfetto SQL with synthetic schemas. Only numerical TEST-device reports with enough repetitions and equivalent conditions can qualify for comparison; qualification still does not automatically prove superiority.

## Validation and build boundary

See CI and test XML for final counts; original run_checks/security/upstream/native-tree/host/project suites remain mandatory. The original six native graphics probes are retained plus four performance-native cases. API37 AAPT2 is real resource validation; API35 native graphics use explicit test shells/dependency doubles and do not emulate Android17/Poco.

The original real module compile was attempted without task exclusions: `NATIVE_TARGET=arm64-v8a :TMessagesProj:compileConnectedAlphaJavaWithJavac`. Gradle wrapper download9.7.1 failed with Network is unreachable before configuration/Java compilation. JDK21/NDK/CMake/full build Python/private inputs also are not provisioned in this environment. No credentials were requested/read/generated, no fake Firebase/API/signing configuration supplied, no build guard disabled. Full affected app-module compilation remains BLOCKED/PENDING for Work1 integration; source AST+isolated native compilation are not reported as that build.

## Work1 integration and physical acceptance

Cherry-pick the small production commits onto the latest approved corrective integration; keep Work1 fixes, version1271 or later, identity and signing. Reconcile only explicit test-scope/CI hooks when later tooling changed; never replace reserved production files with old base bytes. The exact reviewed performance patch and original parity checks must continue passing. This branch generates no APK and does not alter the current private direct-delivery process.

On the Poco, after Work1 supplies the correctly signed integrated update without data removal:
1. Verify the P0 separately first: long-press preview, release/back/interruption and repeated close; report an exception as a blocker. This branch does not claim to fix it.
2. In a nonprivate test account/corpus, repeat chat open/back, folders, list/message scroll, keyboard, settings, synthetic send/reactions and background resume; include rapid taps/configuration changes.
3. Play the same licensed test track; repeat player/lyrics/queue/miniplayer/compact drag/expand while browsing. Pause/resume, switch track/voice, receive a test interruption/call and return from background. No double bar or lost controls is acceptable.
4. For the changed path, open synced lyrics, let active text progress, scroll manually, close before750ms, reopen repeatedly; change light/dark/font/orientation. Text fill/follow behavior must match the prior accepted design.
5. Have the lab operator collect20repetitions per comparable scenario for the three pinned builds under the same real refresh/thermal/cache/battery/test-session conditions. High-refresh changes get their own scenario; do not alter Android settings through this tooling. Stop when hot or unstable. Input-to-present, GPU/GC/allocations require actual additional instrumentation and remain null otherwise.

Signature Motion is not implemented. Before any later animation work, establish stable P0-free traces, preserve native cancelable transitions, identify actual main/RenderThread deadline misses, bound cache ownership and measure high-refresh workloads. No extra renderer/blur/spring/navigation engine is justified by this audit.
