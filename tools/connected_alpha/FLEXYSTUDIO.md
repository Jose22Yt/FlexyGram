# FlexyStudio 1.0 — native configuration exchange

Base: PR92 `751c926d91acd536d96b427af5f34f2fe6bedbc4`. No production release metadata, signature, application identity, plugin engine, playback engine or navigation transitions changed. Integration is additive: nine reviewed hooks (including CI) reverse exactly to the base using `studio_contract.py`. The old compositor freeze test now reverses only this recorded delta before comparing its original bytes; unrelated mutations remain rejected.

## Implemented

Settings → FlexyGram → FlexyStudio has exactly Export, Import and Share. SAF creates/opens documents; sharing grants temporary read access to a dedicated non-exported provider restricted to `cache/flexystudio/share/`. The native download observer intercepts exact `.flexyGram` files in chat and shared documents before generic/plugin opening, respects the message account, cancels repeat download taps, and opens the validated native sheet on completion. Other extensions keep their original route.

Schema1 is deterministic UTF8 JSON with format, schema, minApp1273, name, sorted sections, typed values and SHA256 of the canonical payload. SHA256 detects corruption, **not author identity**. The parser limits size to64KiB, nesting to6, nodes to256, strings to256 and settings to32. Duplicate fields, invalid UTF8/surrogates, unsupported schemas/keys, invalid enums/ranges and mismatched checksums are rejected. Future settings reject the whole file, naming the unsupported identifier; no unconfirmed partial imports.

The first audited whitelist contains17 keys in four sections: chat bubbles (glass, border, edges, transparency, border thickness, cached blur); conversation header (style, compactness, counter, opacity); composer (style, glass, position, density, icons, gap); launcher icon. Defaults match the current native configurations. Exports include only changed keys; if no exportable changes exist, a native checkbox dialog allows explicitly including supported categories with current values. The sheet lists exactly validated sections, actual document name and actual byte count.

**Scope limit:** themes/wallpaper files, general appearance, animation settings and music preferences are not registered in this first whitelist. They are neither exported nor silently applied. Adding them requires a reviewed migration and targeted refresh contract. No account, privacy, authentication, contacts, sessions, messages or plugin data are read for export.

External provider reads use a lazy bounded single worker, queue1, idle expiry1second; existing Telegram globalQueue handles only trusted local preference transactions. No background file polling, permanent observer or playback work is added. A provider that ignores cancellation can occupy the isolated worker; subsequent imports report busy without blocking Telegram queues.

Apply journals only previous affected visual values in a private AtomicFile, commits once per preference file off UI, then reloads only affected native config snapshots. Composer preference notifications coalesce to one refresh per view. Visible bubble cells invalidate, header refreshes, native launcher controller handles icon changes. No activity recreation/list reload/scroll reset is requested. Failure rolls back grouped preferences; failed recovery retains the journal and blocks further imports until it can restore. Startup performs one existence check and queues recovery only when needed. Undo refuses to overwrite settings changed since import.

Cross-file SharedPreferences + PackageManager are not a single Android atomic transaction. The bounded journal provides recovery; an OS crash or disk failure can delay restoration until next startup. Launcher icon appearance is controlled by Android and can be delayed. Cached blur retains its existing asynchronous/fallback implementation. Cache expiry is one-shot JobScheduler + bounded next-share cleanup (max8 files); force-stop/OS scheduling can delay deletion. No long-term URI permission is taken. Source detach, fragment pause/destruction, timeout and cancellation release importer work/observers. A pending external intent is discarded if its Activity is destroyed; reopen the file after such recreation. A generated export awaiting SAF has bounded saved-state restoration.

## Validation and integration

```
python3 tools/connected_alpha/run_checks.py
python3 tools/connected_alpha/check_resources.py --sdk-root "$ANDROID_HOME"
python3 tools/connected_alpha/studio_native/run.py --sdk-root "$ANDROID_HOME"
```

The JVM core test executes actual codec/transaction code with5073 checks, including5000 hostile mutations. Sixteen isolated API35 Robolectric tests compile all new Studio production classes against real Android widgets/preferences/AtomicFile/graphics; Telegram services, resource IDs, theme and navigation are explicit doubles. They cover dynamic1–4section sheets, actual preference apply/undo/recovery, coalesced listeners, native-download adapter completion/cancellation, account selection, icon-only changes, routing, provider metadata/content-stream rejection, the native sensitive-content reveal gate and detach. Four light/dark single/multiple-section images use large text; **they are isolated illustrations, not screenshots of a running full client**. New vectors and ES/EN/RU strings separately link with real AAPT2/API37. The shared runner prints its legacy music label before the Studio-specific scope statement.

Host benchmark (`StudioCodecBenchmark.java`) measures synthetic decode/validation only. One local run (532-byte full supported preset,1000 warmup,2000 samples) gave median34.161µs and p95 72.209µs on the host JVM; these are environment-specific microbenchmark observations, not device results. It cannot establish Android latency, smoothness, jank, inactive overhead or superiority to Exteraless. No private account or physical device is used.

Full Gradle module compile was attempted and stopped before configuration: wrapper Gradle9.7.1 download failed with `Network is unreachable`. No fake credentials, skipped security/JNI/Chaquopy tasks or successful APK claim. Full merged manifest and whole-client Java/Kotlin/JNI compilation remain pending Work1 integration. Do not merge based solely on isolated tests.

Integrate this branch onto exactly its PR92 base or review/cherry-pick the feature commit onto Work1's next base, resolving only the recorded additive chat/composer/intent/settings hooks. Keep Work1's newer production changes. Run all tests and a genuine integrated build before distributing a single coordinated Alpha. Do not apply `flexystudio_native.patch` separately: it is a review/reversal record of hooks already included in the commit.

On the Poco use synthetic test conversations/files: export bubble-only, export several categories, no-change explicit selection, SAF save/import and share; receive downloaded/undownloaded files in private/group/channel/forward/shared documents; test repeated taps, cancel, corrupt/oversize/incompatible files; apply/undo with keyboard and music active; confirm scroll/session/account unchanged, launcher behavior, cached-blur fallback, theme/RTL/font/rotation/Back and existing plugin types. Run the performance lab with matched effective refresh rate and repeated baseline/candidate trials for card opening, Apply-to-visible-update, framestats, memory and idle cost. Android17 physical acceptance and performance results remain pending.

## Recorded local results

- `run_checks.py`:213 Connected Alpha host tests passed;144 general tests passed,31 optional skips (external plugin corpus / R8 report absent). Source parity and JNI boundary checks passed.
- Studio actual codec/transaction:5073 assertions including5000 hostile mutations passed.
- Final isolated native run:16 API35 tests,0failures/errors/skips. Actual new Studio classes compiled; dependencies explicitly doubled as described above.
- AAPT2 API37:main resources compile with existing legacy formatting warnings, Alpha overlay strict compile and isolated linking pass. Full merged manifest remains unverified.
- Full Gradle module:blocked before project configuration by wrapper download network failure. Android17 device interaction/performance/ANR/update acceptance remains pending.

The feature consists of12 new Java classes under `app/flexygram/studio/` (schema, codec, transaction, store, IO, file/provider/cache cleanup, import helper, activity, sheet, labels), five original GPL line vectors, a narrow provider-path XML, and matching ES/EN/RU strings. Existing production changes are restricted to the eight app hooks recorded in `flexystudio_native.patch`; production component implementations owned by Work1 are retained. CI excludes this feature branch from the unrelated APK build job and runs read-only host/resource/isolated-native checks. No distribution workflow, certificate or credential changed.
