# Performance Engineering 2.0 — navigation, scrolling and input

Integration note: Work1 incorporates exactly the reviewed ImageReceiver candidate on top of the newer Music3/header commits. Its current UI delta is pinned separately in work1_after340.patch and reversed byte-for-byte for the original reserved-source assertions; unreviewed changes still fail. Source inventory reports real current hashes and labels normalized reservation counts explicitly. The original four-cohort C baseline remains340cd323; it is not silently replaced. Original standalone-branch claims below describe PR93. No physical performance result or final APK is implied.

Base verified: PR92 `340cd323f5f5809abc746507b2e252da71298720`, branch `integration/connected-alpha-1273-signature`. PR91/Alpha1272: `8619ba40fbd8fd9d9d898ff307fb0c0716661254`. Original Exteraless: `1ad6a60a6834ffca722b1a22f4fba27ecb29a061`. No PR90 cherry-pick: its integrated lyric changes are preserved byte-for-byte.

## Implemented production change

**R1 — ImageReceiver.applyRoundRadiusInternal, inherited from original Exteraless.** Custom avatar radius recalculation created an `int[4]` in both proportional and uniform modes, including repeated requests with identical radii. Calls occur in DialogCell avatar preparation/update and ChatMessageCell image/thumbnail radius updates; BackupImageView also forwards radius animation values. This establishes reachability, not how frequently a physical workload executes the branch.

The candidate calculates each scalar radius in the existing comparison/copy loop. It preserves the original requested array, integer multiplication and float/ceil order, width clamp, uniform maximum, isRoundRect test, changed flag and ordered drawable notifications. It adds no retained array, cache, thread, listener, invalidation, preference or work queue. Default avatars and already-applied corners keep their original path. All public overloads and their virtual delegation are byte-identical.

**Evidence:** exact baseline/candidate methods compiled in explicit preference/drawable doubles; 30,000 deterministic mixed state transitions compare effective/requested radii, isRoundRect and notification order/digest. Includes short/empty/long arrays, scalar/four-corner setters, subclass array overrides, avatar flags, widths including exceptional floats, resize, configuration changes, default/custom/uniform modes. The complete production Java source also parses with the JDK AST parser; that is not semantic module compilation.

**Host allocation experiment:** JDK17 HotSpot, escape analysis disabled and tier capped explicitly; 20,000 recalculations per mode, supplied array preallocated to isolate this change. Baseline proportional: 640,000 temporary bytes; candidate: 0. Baseline uniform: 640,000; candidate: 0. Counters are host ThreadMXBean, **not ART allocated bytes, Android GC reduction, frame timing or FPS**. CI reruns rather than hardcoding those numbers. Existing scalar-setter arrays deliberately remain.

**Android evidence:** five isolated API35 native tests, comprising the four existing lyric tests and one new actual-radius-method clipping comparison over 20 mode combinations. Canvas/Path are Android implementations; preference/drawable dependencies and the ImageReceiver shell are explicit doubles. No full image decoder, RecyclerView, real chat, GPU or Android17 device is exercised.

**Risk:** scalar computation is interleaved with the radius copy instead of preceding it in a temporary array. The method makes no callbacks until after that loop; tests verify callback snapshots and order. No concurrency contract changes; the old receiver state was already mutable. Changes in appearance settings during one invocation are not a supported atomic snapshot in either version. Expected benefit is limited to custom avatar radius calls. Allocation saved does not prove a perceptible chat-opening improvement.

**Rollback:** revert the first production-only commit (ImageReceiver) independently. No persisted state to migrate. Update the explicitly reviewed `radius.patch` and its differential allocation acceptance if intentionally reverting; retain parity, privacy and Work1 checks. Do not remove guards merely to make tests green.

## Audited paths and finding disposition

| ID / component / scenario | Evidence and cause | Decision / result / status |
|---|---|---|
| R1 ImageReceiver.applyRoundRadiusInternal; custom avatar bind/resize | Original and PR92 methods identical; two temporary scaled-array sites; differential and allocation evidence above | Implemented; isolated reduction demonstrated; physical effect pending. Low scope, no retained-memory cost. |
| R2 ImageReceiver.setRoundRadius; rapid bind and radius animation | Scalar overload delegates to virtual array overload. ChatMessageCell's photoImage override also updates poll radii | Direct scalar fast path **discarded**: could bypass poll behavior. Public methods unchanged. |
| N1 DialogsActivity.onItemClick → ActionBarLayout.presentFragment → ChatActivity.onFragmentCreate/createView; chat open | Original native preparation, arguments, adapter/view construction and asynchronous message/storage loads remain. Work1 owns these methods | No measured wall-time attribution. Preserve guards and loading order. Trace main CPU/runnable plus FrameTimeline first; no speculative deferral patch. Pending physical evidence. |
| N2 ChatActivity.onFragmentDestroy; immediate Back / repeated open-close | Existing observersGroup.removeAllObservers, explicit unread/close/plugin removals, classGuid cancellation and metadata/input/attachment teardown present | No proven observer leak. Preserve ownership/order. Lifecycle regression probes inherited; real close latency pending. |
| N3 DispatchQueue.postRunnable/cancelRunnable/sendMessage; first-use queue | syncLatch.await waits for Handler readiness; Looper initialization is off-thread. These methods are byte-identical to original | Blocking is possible by design; no measured long wait. Do not replace with racy null-handler shortcuts. CPU/runnable query separates scheduled work from scheduling delay; lock attribution still requires local trace inspection. Pending. |
| S1 DialogsAdapter.onBindViewHolder / updateList; folder/list churn | Existing recycled cells and special view types; list rebuild allocates ItemInternal objects. Native notification/full refresh paths are not all per-frame | No measured redundant bind/layout count. Preserve updates; no cache or skipped notifications added. Pending trace and allocation profile. |
| S2 DialogCell, AvatarDrawable.draw, AnimatedEmojiDrawable; list/message scroll | DialogCell/AvatarDrawable/AnimatedEmojiDrawable/RecyclerListView byte-identical to original in source inventory. AvatarDrawable gradient is already keyed by size/colors; ImageReceiver uses existing matrices/paths | Keep existing resource reuse. Shader complexity alone is not a GPU bottleneck. R1 is the narrowly isolated exception; no Recycler replacement. |
| I1 ImageLoader decode queues/cache; image-heavy scroll | Existing imageLoadQueue/cacheOutQueue, key dedup/cancellation. Original→PR92 ImageLoader delta only selects the independent external directory name | No evidence Alpha introduced synchronous decode in this path. Keep native image lifecycle/cache. No new bitmap cache, prefetch, session or path change. |
| T1 ActionBarLayout preview/input and DialogsActivity recovery; rapid taps | PR92 has Work1's corrected input ownership. Existing 2,000-cycle model and Android MotionEvent/ViewGroup probes retained | Reserved and byte-identical. P0 physical acceptance **NOT_ESTABLISHED**. No protection removal, artificial synthetic responsiveness or speed changes. |
| F1 ApplicationLoader / LaunchActivity / modules | LaunchActivity identical to original; ApplicationLoader has reviewed Alpha identity/config integration. JNI/Python/service startup was audited in Performance1; no new init added here | No repeated init or measurable startup regression demonstrated. Preserve startup/auth/queues/JNI. Physical cold/warm measurements pending. |
| M1 Music active during navigation | All player production files and Work1 music hosts/bubble unchanged; baseline callbacks/caches retained including integrated lyric fixes | Separate music-off/on workloads required. No Music3 or animation modification; physical overhead pending. |

`navigation_audit.py` emits SHA-256 lineage for 18 sources across A/B/C/D and checks **51 reserved production files byte-for-byte**, including every production/resource file changed in PR92 and all current player, Home and composer sources. Hash differences indicate lineage, never runtime cost. All Work1 code remains untouched.

No proven optimization in a reserved class has been found that warrants an unapplied production patch. The table identifies exact trace/instrumentation points for Work1; an optimization patch will require a reproducible cost and regression test first. The P0 is not mixed into this delta.

## Lab 2.0 extensions

Reuses `capture.py`, `compare.py`, `metrics.py`, `perfetto.py`, existing scenarios and native graphics pipeline; no parallel lab or app instrumentation engine.

- `capture` accepts Alpha1272 and PR92 labels and explicit build mode. Manual interactions only; effective frame budgets come from each FrameInterval. Existing fallback requires explicit verified Hz. No device setting is written.
- `compare --cohort navigation2` requires exactly A=Exteraless, B=Alpha1272, C=PR92, D=candidate; pins A/B/C revisions, rejects candidate reusing one of them, requires equal verified build mode and original environment/refresh/thermal/battery guards and at least20 repetitions. Legacy three-way mode remains covered. Adds numerical PSS snapshot summaries, rejects malformed/nonfinite/negative memory values. Memory snapshots are not peak RSS/heap allocation measurements.
- `navigation.py` reads an existing local prepared-test trace with a supplied native trace_processor binary; no download wrapper, server, upload, capture, touch synthesis or UI inspection. It executes numeric-only queries over an explicit trace-clock window ≤60s. CPU/runnable intervals are clipped at boundaries. Frames and GC must be complete within the window. No channel names, IDs, message text, phone numbers or source trace paths are exported.
- Input query uses official android.input exact non-speculative frame association. ACK duration stays separate. Missing association, speculative frame or presentation past the window yields null. This is InputReader-read→associated-frame-present, **not touchscreen hardware latency, useful chat readiness or time until the next interaction is accepted**. Those two semantic app metrics remain null until valid instrumentation exists. No nearest-frame timing guess.
- FrameTimeline query distinguishes classified and unknown records; surface records are not display refresh counts. GC uses android.garbage_collection when present; empty/unavailable data does not establish zero GC. Main/RenderThread scheduled CPU is not GPU time. No GPU utilization invented.
- Existing bounded Perfetto config adds atrace input category. Raw traces may still contain sensitive system metadata: use prepared test sessions exclusively, keep raw files local and never attach them to public PRs. No logcat/keyboard text datasource enabled by these tools.

SQL/CSV logic has deterministic synthetic schema tests. All five queries also executed on native **Perfetto v58.2** against an explicitly synthetic Chrome trace: schema/shell smoke only, no Android perf measurement. The tool detects v58 default-CSV versus newer explicit-format CLI support. Unsupported queries are reported unavailable; stderr is not copied to reports.

Official schema/semantics: [Perfetto standard library](https://perfetto.dev/docs/analysis/stdlib-docs), [CLI](https://perfetto.dev/docs/reference/trace-processor-cli), [FrameTimeline](https://perfetto.dev/docs/data-sources/frametimeline). Vendor trace coverage must be checked on the Poco.

## Reproduce locally

```sh
python3 tools/connected_alpha/run_checks.py
python3 tools/connected_alpha/check_resources.py --sdk-root "$ANDROID_HOME"
python3 tools/connected_alpha/performance/radius_probe.py
python3 tools/connected_alpha/performance/native/run.py --sdk-root "$ANDROID_HOME"
python3 -m tools.connected_alpha.performance.navigation_audit --out build/performance2/source-audit.json
python3 -m tools.connected_alpha.performance.capture --help
python3 -m tools.connected_alpha.performance.compare --help
python3 -m tools.connected_alpha.performance.navigation --help
```

Maven must be on PATH (or supply existing `--maven` option). API37/build-tools36 are required for resources. Native graphics uses Robolectric API35; it is not an Android17 emulator. The workflow runs all existing native renderers, music detach reproduction and preview input probes with no credentials or APK task.

Actual module command attempted: `NATIVE_TARGET=arm64-v8a ./gradlew :TMessagesProj:compileConnectedAlphaJavaWithJavac --no-daemon --console=plain --max-workers=2`. Wrapper failed downloading Gradle9.7.1 with `java.net.SocketException: Network is unreachable`, **before configuration/compilation**. This environment has Java17 and SDK resources, not Work1's private full build setup. Full Android module compilation remains **BLOCKED**, not passed. No credentials fabricated, guards disabled, tasks excluded, signed build or APK generated. Work1 must run the real module/build before integration acceptance.

## Poco physical comparison protocol

1. Work1 provides equivalent build-mode reference/candidate applications in a prepared test environment. Never downgrade, wipe or automate the owner's live installation/session. B/C/D share the app ID, so cannot coexist in one Android profile: stage equivalent test installations under an agreed test-only protocol. Do not reuse the owner's account. This branch does not build or distribute APKs.
2. Prepare a fixed synthetic corpus with private test chat, group, channel and bot; text/long text/replies/groups of photos/stickers/emoji/reactions; licensed local music; same folders/archives and initial viewport. Fix corpus/workload identifiers without exporting contents. Set cache state deliberately; do not mix cold and warm samples.
3. Keep actual refresh profile, display/font scale, animations, theme, compile mode, battery/thermal limits, charging and workload identical. Observe per-frame effective FrameInterval. Do not force frequency/system settings through the lab. Alternate A/B/C/D order in five blocks (Latin-square/rotating order), cool between blocks, collect ≥20 samples per scenario. Tool comparison cannot establish equal conditions by itself: theme/corpus/cache/build mode are operator attestations.
4. Start with chat_open/chat_close/chat_repeat, dialogs_scroll/messages_scroll/folders, then keyboard/settings, music_navigation and background_resume. Use identical manual gesture/repetition pattern, including rapid/interrupted Back and scroll interruption. Stop upon crash, nonresponsive input or health-limit breach; record pass/fail numerically without private logs. Do not count failed interactions as successful fast samples.
5. Example capture (replace placeholders with real test inputs; repeat for all four labels/revisions):

```sh
python3 -m tools.connected_alpha.performance.capture \
 --serial TEST_SERIAL --package TEST_PACKAGE --source-commit FULL_SOURCE_SHA \
 --label candidate --scenario chat_open --iterations 20 --confirm-test-device \
 --build-mode release-profileable --theme dark --cache-state warm \
 --conversation-fixture synthetic-v1 --workload-id chat-open-v1 --music-state off \
 --refresh-profile observed-adaptive --installation-state equivalent-test \
 --test-session-state synthetic-only --charging unplugged \
 --output build/performance2/D-chat-open.json
python3 -m tools.connected_alpha.performance.compare --cohort navigation2 \
 build/performance2/A-chat-open.json build/performance2/B-chat-open.json \
 build/performance2/C-chat-open.json build/performance2/D-chat-open.json \
 --out build/performance2/chat-open-comparison.json
```

6. Generate the existing bounded plan with `python3 -m tools.connected_alpha.performance.perfetto --package TEST_PACKAGE --out-dir build/performance2/trace-plan`. Capture locally using Android System Tracing/ADB in the prepared test environment. Keep the trace on the computer; do not upload it. Select the same workload-only interval using trace-clock nanoseconds. Execute:

```sh
python3 -m tools.connected_alpha.performance.navigation \
 --trace-processor /absolute/path/to/native/trace_processor \
 --trace /absolute/path/to/local-test.pftrace --package TEST_PACKAGE \
 --start-ns TRACE_START --end-ns TRACE_END --confirm-test-trace \
 --out build/performance2/local-trace-numbers.json
```

Use a current local native binary (tested v58.2); no script/downloader. Query availability does not imply captured data availability. Confirm no dropped trace packets/coverage gaps in local Perfetto inspection before interpreting numbers; this tool does not certify trace completeness. Exact presentation association may be unavailable on vendor builds. Do not replace unknown input latency with frame duration.
7. Review medians/p95 distributions, missed effective budgets, FrameTimeline classifications, CPU/runnable, PSS and GC separately. Record music-on and off as separate workloads. Also manually check rotate/theme/font-scale, memory pressure, interruption by background/audio, camera/voice, and all original chat actions. Physical P0 preview release/Back/input recovery requires Work1 acceptance. Report real ANR/crash failures; do not conceal them by shortening animations.

## Integration and next steps

Production-only first commit can be cherry-picked onto Work1's current branch after confirming ImageReceiver has not changed. It is independent of UI, P0, certificates, versionCode and distribution. The lab/CI commit is optional for the APK and includes exact allow-list/reversal extensions, not historical resets. If PR92 advances, rebase in this independent branch and re-run byte-exact reserved checks; do not overwrite Work1 files to force success. PR stays draft; never merge main/develop automatically.

Signature Motion recommendations only: measure existing folder/ripple/message/player transitions under interruption, minimize region invalidation, preserve native cancellation/ownership, require physical p95/jank before adding effects. No new animation, altered durations or global navigation engine is implemented.

**Physical comparison / touch responsiveness / GC / memory benefit / superior-to-Exteraless: NOT_ESTABLISHED.** `reference_navigation2.json` intentionally leaves the four-device comparison blank until real measurements exist.
