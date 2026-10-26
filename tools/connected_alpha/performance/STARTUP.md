# Startup checkpoint over PR100

Base application: `175b299e0d4faeb246eca8e1be16a362a3a62213`.
Its existing full ARM64 private delivery passed in Actions run 40370898772.
That is baseline build evidence, not baseline Android startup timing.

## Evidence and small production change

`LaunchActivity.updateCurrentConnectionState()` maps Updating to Telegram's
`ConnectionsManager.ConnectionStateUpdating`. The latter is returned only while
connected and `isUpdating` is true; Telegram's difference synchronization controls
that flag. This title overlay neither empties nor gates `DialogsAdapter`'s rows.
The indicator and connection errors remain unchanged.

The first local `loadDialogs(0,0,100,true)` was requested by DialogsActivity after
`ApplicationLoader.postInitApplication()` had initialized ten account controllers,
connections, unsent-message work, contact/download controllers and billing.
The native read/merge/notification path itself already permits cached rows while
network synchronization continues; it is not replaced.

The launch-only entry now requests that same native cache load as soon as the
selected activated account has its current user installed. Account zero remains
first because it owns global preferences; the selected account follows it,
followed by all remaining accounts in their original relative order. None is
removed. SQLite remains on MessagesStorage's queue. The native loading and reset
guards remain authoritative. Background service initialization keeps its original
no-prefetch behavior. DialogsActivity avoids repeating a completed nonempty read.
No cross-account or independently persisted dialog cache is introduced; login,
passcode and network state are not bypassed.

## Tests, limits and risk

`test_startup.py` executes production account ordering and the actual extracted
launch gate with isolated API doubles. It checks every account exactly once,
account-zero precedence, selected-account identity, inactive/missing-user rejection,
UI ownership, and retention of native duplicate-load guards. This does not exercise
SQLite/JNI or prove a latency gain. Historical source contracts retain exact
snapshots and reject unreviewed mutations through startup_review.json.

Perfetto can record `Flexy.startup.post_init` and
`Flexy.startup.request_local_dialogs` sections, plus `Flexy.dialogs.read_local`
on the existing SQLite queue. These measure initialization, enqueue work and local
read/decode work, respectively. They do not measure visible rows or useful
interaction. There is no polling, permanent frame callback, timer, account ID or
message data in instrumentation. Trace sections have no enabled data capture
outside an operator-started system trace.

No ADB/device is available in this workspace. Cold/warm/hot startup, useful-row
latency, Updating duration, p95/p99, GC and device comparisons remain NOT_MEASURED.
Existing performance capture/Perfetto tools must be run on equivalent test fixtures
with real Android, including locked/unlocked sessions, offline/slow network,
account changes, process death and multitap. Do not call the physical P0 fixed.

Risk: earlier native cache work may overlap other startup I/O. Physical traces must
check contention and memory before accepting the candidate. All account/service
initialization and synchronization remain present; this is scheduling, not a claim
that initialization itself is now free. Revert this startup commit to restore the
previous scheduling without touching user data or PR100 features.
