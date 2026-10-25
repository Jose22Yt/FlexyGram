# Performance Engineering1.0 — executable lab

Integration note: the original PR90 lab below is preserved for reproducibility. PR92 selectively incorporates its two Lyrics commits on top of the newer P0/settings/bubble fixes; it does not restore PR90’s older Work1 files. Reserved-source assertions now reverse the separately reviewed Work1 patches before comparing with the original1271 baseline. Native performance probes run alongside all existing probes. Original runtime/build availability statements below describe PR90, not a current APK or physical-device result.

Run from repository root. This lab reuses `measure_login.frame_times`, `measure_music.stats`, existing preview-navigation fixtures and the existing Android music-probe pipeline. It neither launches owner accounts nor reads screens, logs, chats, phone numbers or sessions. No Android setting is written. No APK/signing/version/distribution change is included.

## Reproduce local/CI evidence

```sh
python3 -m unittest discover -s tools/connected_alpha -p test_performance.py -v
python3 tools/connected_alpha/run_checks.py
python3 tools/connected_alpha/check_resources.py --sdk-root "$ANDROID_HOME"
python3 tools/connected_alpha/performance/native/run.py --sdk-root "$ANDROID_HOME"
python3 -m tools.connected_alpha.performance.audit --out build/performance/source-audit.json
```

Native probe requires Maven/JDK17+ and the original API37/build-tools36 resources; CI uses JDK21. It compiles the unchanged actual native `LineView` source from original integrated1271 alongside the current inner source and the actual `LyricsFill` class. A FrameLayout shell supplies explicit test metadata/controller/typeface/list dependencies. Instrumented TextPaint observes shader identities; actual Canvas pixels are compared over1000draws and color/alpha changes. Outer detach method is copied from production into the shell; stopScroll rescheduling is a deliberate test double. This does not compile the whole LyricsView/RecyclerListView/app module or run Telegram/ART/Poco. Existing music graphics keep their default runner behavior; the extension hook only avoids duplicating its AAPT2/Maven infrastructure.

Generated `performance-native-result.json` is isolated native-graphics evidence, never a device report. Frame timings, ART allocation bytes and GPU results remain null. `reference_matrix.json` explicitly leaves all physical metrics pending. No synthetic fixture qualifies as physical acceptance. Stable shader count1000→1 describes this specific draw path, not a speedup percentage or app-wide allocation count.

## Collect real repetitions only on a prepared test device

ADB and an independently prepared test account/corpus are required; none is connected here. Never point the collector at the owner's real authenticated client. Do not clear app data or create/login accounts through CI. The operator controls interactions manually; startup force-stop is an explicit extra opt-in and applies only to the chosen test package.

```sh
python3 -m tools.connected_alpha.performance.capture \
  --serial TEST_SERIAL --package io.github.jose22yt.flexygram.alpha \
  --source-commit FULL_VERIFIED_SOURCE_SHA --label candidate \
  --scenario music_navigation --iterations 20 --confirm-test-device \
  --theme dark --cache-state warm --conversation-fixture synthetic-long-chat-v1 \
  --workload-id music-open-chat-back-v1 --music-state local-track-v1-playing \
  --refresh-profile operator-confirmed-fixed120Hz \
  --installation-state existing-test-install --test-session-state prepared-test-only \
  --charging unplugged --output build/performance/candidate.json
```

The SHA placeholder must be replaced with the actual40hex commit. Use the actual declared state, not the example values by default. `--verified-hz 120` is only an explicitly verified fallback when Android omits FrameInterval. When available, each recorded FrameInterval wins, including refresh changes; there is no implicit60Hz budget. Unknown/flagged/incomplete/max-timestamp records are counted/rejected. Identical records in separate window sections remain separate app-window records. Gfxinfo duration is IntendedVsync→FrameCompleted, not touch→visible latency, SurfaceFlinger jank, GPU utilization or displayed FPS. Deadline misses are separate when FrameDeadline exists.

The collector reads only selected package gfxinfo/meminfo plus display/font/animation/build/battery/thermal configuration. It saves numerical summaries/records, a hash of the serial and declared workload metadata; raw dumps, UI and serial are not saved. Meminfo is outside the frame window. PSS/RSS are snapshots, not allocated-byte counts. CPU/GPU/GC/allocation and input latency are explicitly unavailable in this collector. Temperature/battery/thermal conditions must be available and within declared thresholds before and after every repetition; otherwise collection stops. Checkpoints with fewer than20repetitions are rejected for acceptance comparison.

For `cold_start`, also pass the real `--component PACKAGE/org.telegram.ui.LaunchActivity` and `--allow-test-force-stop`. No `pm clear`; am TotalTime is reported separately and reused/failed activity launches are rejected. A static cold welcome may expose no eligible gfxinfo frames: a valid am TotalTime remains a startup-only sample and frame metrics stay null, rather than inventing frames. All warm/background/chat scenarios are operator-driven; their interaction latency is NOT inferred from gfxinfo.

Run each identical scenario for Exteraless, integrated1271 and candidate on the same device/build/theme/font/display/animations/cache/music/corpus/install/test-session state. Alternate/rebalance order across repeated blocks, allow natural cooling without changing device settings, and retain the same charging policy.20repetitions per scenario are preferred/required by the acceptance comparator; fewer are exploratory only. Inspect heat drift and variance, not just median. High-refresh modes need the actual interval profile, not a screen advertising120Hz.

```sh
python3 -m tools.connected_alpha.performance.compare \
  build/performance/exteraless.json build/performance/alpha1271.json \
  build/performance/candidate.json --out build/performance/comparison.json
```

Comparison refuses mismatched/unknown conditions, incomplete samples, synthetic reports, nonfinite values and unmatched observed refresh profiles/proportions. Conditions such as account/cache/theme/corpus are operator attestations, not inspected by the tool; reports are not tamper-proof signed evidence. A qualifying table still says superiority is not automatically established. Median of repetition p95 values is explicitly not pooled p95. Review paired distributions, confidence/order/thermal confounding and behavioral regressions before accepting any faster-client claim.

## Perfetto plans for the same prepared test device

```sh
python3 -m tools.connected_alpha.performance.perfetto \
  --package io.github.jose22yt.flexygram.alpha --seconds 20 \
  --out-dir build/performance/trace-plan
```

The command only generates a bounded32MiB/20second configuration and SQL; it neither starts capture nor downloads tools. On the prepared test device, use the official local Perfetto recording procedure with that config, keep the trace private/offline, then run its SQL in an installed official trace_processor. `frame_timeline.sql` scopes app surface-frame records and separates classified/unclassified jank. `scheduled_cpu.sql` groups scheduled CPU time into main/RenderThread/other; it is not GPU time. `startup.sql` uses official startup/TTID/TTFD modules for cold/warm/hot classification; missing fully-drawn evidence remains null. Input-to-present flow, heapprofd/GC and supported vendor GPU counters require separate actual instrumentation; this branch never fabricates them. Queries are tested against synthetic schema fixtures, not a real captured trace here. FrameTimeline has platform/source limitations (including SurfaceView coverage); read official documentation before interpreting media frames.

Official primary references:
- https://perfetto.dev/docs/data-sources/frametimeline
- https://perfetto.dev/docs/analysis/stdlib-docs#android-startup-startups
- https://perfetto.dev/docs/cookbook/recording-traces
- https://developer.android.com/reference/android/view/FrameMetrics

Raw traces/heap dumps under this module are ignored; normal output goes to ignored build/performance. CI uploads only source inventory, native numerical evidence and test XML, never APKs/accounts/traces.

## Integration and rollback

Base: approved PR89 /997ac40a65be00c672dc8009b61f55825537d498. Production delta is only LyricsView.java and new LyricsFill.java. Work1 reserved files, launcher, bubbles, Chats, login, navigation and distribution/build metadata are byte-identical to that base. No new animator, timing constant, renderer, preference or animation style. Preserve this small production commit as an isolated revert unit. Revert it if integration/device acceptance shows a regression; no data migration is involved. Tooling commit is separate; keep the exact scope and reverse-patch checks when rebasing onto a later integrated Work1 head. Do not overwrite its corrective branch or restore old1271 UI from historical commits. CI `pr.yml` needs both existing branch exclusions and the performance branch exclusion; no APK job is added.

Real module compile attempt: `:TMessagesProj:compileConnectedAlphaJavaWithJavac --no-daemon --console=plain --max-workers=2`, NATIVE_TARGET arm64-v8a, original build settings. The wrapper failed fetching Gradle9.7.1 with `Network is unreachable` before configuration/Java compilation. Only JDK17/API37/build-tools are present; JDK21/NDK/CMake/Python build inputs and private credentials are not available here. No fake API/Firebase/signature values or skipped validation used. Full module compilation is a blocking integration check for Work1, not a pass claimed from native probes.
