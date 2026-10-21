# Native login integration seam — LOCAL ONLY

This unregistered source module extends the PR #35/#36 rehearsal components. It is not
included in `settings.gradle` or an APK. No network, real session writer, SRP implementation,
credentials, timers, replacement login UI or capability-enabling switch is provided.
Original Telegram/Exteraless source, copyright and GPL notices remain unchanged.

`TlAuthResponses` consumes actual TL class names/fields. `NativeLoginTransport` relates
their typed metadata to the existing `AuthenticationController` and `AuthUiRelay`.
`TelegramAuthorizationStore` passes the same authorization object to a local-only
`OriginalFormatPort`; it does not serialize MTProto keys or invent a session format.
`NativePersistenceFence` joins that port to the existing `OperationJournal`.

Local wiring (see executable `tests/native_login/NativeLoginHarness.java`):

```java
TelegramAuthorizationStore store = new TelegramAuthorizationStore(runtime, journal, localDisk);
NativeLoginTransport transport = store.localTransport(runtime, localRpc, localClock);
LoginFlowOwner owner = new LoginFlowOwner(runtime, transport, store, serialWorker);
transport.bindLocalStateSignal(owner::signalLocalAdapterState);
// Existing LoginActivityAdapter attaches/detaches the original native fragment's view.
// localRpc submits ONLY synthetic inputs and returns typed local responses through:
// TlAuthResponses.mapAndStageLocal(request, store, originalSyntheticResponse, syntheticError).
```

`runtime` must attest closed realAlpha; both ports must declare `LOCAL_SIMULATION`
and match the account scope. These are adapter contracts, not a sandbox against malicious
implementations. No remote port or original Android writer is implemented here.

After initialization, use the existing owner start/verify/cancel/commit operations.
Intermediate 2FA, signup, QR migration, refresh and retry actions are explicit calls on
the transport; `Snapshot` supplies non-sensitive metadata to the native renderer.
Bind the signal before initialization and retain the owner, never a view, across recreation.
Worker serialization and main-thread rendering remain the integrator's responsibility.

Storage generations are opaque metadata, not key/content digests. Absent→present alone
does not establish ownership. Receipts bind each change to the same lease and before/after
chain. An existing message database remains preexisting; a receipt permits a scoped fake
transaction, but a future real writer must prove preservation of unrelated rows. Previous
user/native config or backup blocks initialization. Unknown outcomes block recovery and
do not cause rollback, deletion or automatic retry.

See [integration handoff](../../docs/native-login/README.md) for native page mapping,
unsupported branches, patch review, exact test evidence and remaining Android work.
