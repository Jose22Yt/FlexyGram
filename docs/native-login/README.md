# Native LoginActivity integration preparation

Source base: PR #36 `b09b79301db93e19471bd0c21aecba0bb9e64063`.
Work 2 / PR #34 was independently rechecked at
`36e27309bee4e6c27e3850321fa0c6c44e2acf42`. Neither branch was modified.
This draft stacks on #36. FlexyGram's responsible author remains @Lukhou23;
Telegram/Exteraless code authorship, GPL licensing and attribution remain intact.

## Implemented integration

The new `telegram-native-login` source module connects typed TL responses to the
existing controller, owner, view relay and operation journal using local ports.
The owner now accepts `LocalSessionStore`; the previous concrete constructor remains
available. The controller gains only a revisioned UI refresh hook, without state,
generation, request or policy changes. No client, Gradle, manifest or shared JNI file
is changed; the module is deliberately not registered in the Android build.

| Original LoginActivity reference at PR #34 | Local adapter behavior |
|---|---|
| sendCode 3248–3322 | Sent-code delivery metadata; early authorization/signup handled without another code request |
| signIn 4996–5066 | Original authorization object retained only after callback selection; code errors allow explicit retry |
| getPassword / checkPassword 5690–5757 | Supported SRP algorithm metadata validated; proof is synthetic, no new crypto; SRP refresh needs explicit action |
| signUp 8379–8405 | Consent and required terms checked; `SIGN_UP` origin preserved for later `afterSignup` handling |
| export/importLoginToken 8572–8652 | QR token/success/migration states; explicit poll/migration, no native datacenter switch or timer |
| onAuthSuccess 1710–1747 | Same TL authorization passed to an original-format **local fake** writer; journal/receipts distinguish outcomes |
| native view recreation | Existing LoginActivityAdapter + AuthUiRelay detach old observers; owner persists, process death restores only a restart marker |

These line references describe existing source, not executed Android flows. Errors map
to bounded enums; raw error text, QR/phone hashes, SRP parameters and authorization tokens
are not exposed by snapshots or exception messages. Request-owned char arrays are wiped.
Clearing references to original TL objects is not guaranteed JVM heap zeroization.

An added regression reproduced a defect in this new adapter: a second raw authorization
callback could stage an object even when the transport rejected that callback. Deferred
staging now occurs only after selecting the first response and validating the returned
cancellation handle. Losing, late, callback-then-throw and missing-handle responses are
discarded. Concurrent and same-object duplicate cases are covered. This was a host
adapter defect, not a demonstrated original Telegram or Android defect.

## Original persistence contract

`NativePersistenceFence` captures USER_CONFIG, NATIVE_CONFIG, NATIVE_BACKUP and
MESSAGE_DATABASE metadata before beginning the existing OperationJournal. A private
operation lease and chained before/after receipts establish current-flow writes. No
MTProto key format is replaced. Existing native session files or an activated account
block this rehearsal, without deleting anything. An existing database is classified
as preexisting even when a scoped local write succeeds.

COMPLETED requires matching account metadata and receipts for user/native config and
database. A proven unchanged failed write becomes FAILED; partial, foreign, missing,
throwing or uncertain writes become UNCERTAIN (or remain WRITING if journal persistence
also fails). There is no rollback, restoration, revocation, logout or automatic retry.
Receipts are trusted-port evidence, not proof that an arbitrary writer preserved data.

## Selective security patch review

The four inherited patch files remain unchanged and **unapplied**. Their SHA-256 values
and the five original target blob IDs are pinned in
`TMessagesProj_Modules/telegram-native-login/integration/security-series.json`.

| Patch | Scope verified on temporary copies | Remaining integration condition |
|---|---|---|
| 0001 | Reject null UserConfig user before partial mutation; reproduce old/fixed Java methods | Integrate selectivity after P1/P2; does not make all onAuthSuccess writes transactional |
| 0002 | Remove debug-only CONNECTION_NOT_INITED cleanup(true)/implicit retry | DEBUG_PRIVATE_VERSION is currently false; preserve error delivery, test future real transport separately |
| 0003 | Closed realAlpha returns 0/empty; private approved pair selected together, legacy preference overrides rejected | Does not authorize credentials or open transport; other variants retain existing behavior |
| 0004 | Replace original login token/billing and native integrity token log sinks with operation-only messages | Three sinks only; review remaining error.text, Throwable and original SDK/native logging before login |

Nine existing integration tests actually apply these patches to **temporary copies**,
compile extracted Java/C++ methods and exercise synthetic values. No shared original
file was patched. The pin test rejects changed patch/target bytes. This establishes
compatibility with the fixed PR #34 source above, not with arbitrary later commits.
The earlier session incident is not attributed to any code path by this work.

## Executed validation and limits

See [results.json](evidence/results.json), per-suite logs, commands and source hashes.
The final runs contain **44 new + 33 selected existing = 77 distinct tests**, each
executed normally and with Python `-O`: **154 passing executions, zero failures/skips**.
Preliminary logs retain the resolved compile ambiguity and duplicate-callback failure;
they are excluded from the final totals.

Tests run actual adapter/core Java with JDK 21, Java 8 bytecode and an SDK24 symbol
compile. The TL fixture projects **32 exact selected class declarations/fields** from
the fixed original TLRPC/TL_account sources; it does not compile their serializers.
Framework/controllers/storage/RPC are doubles. Selected #36 tests compile/run its
read-only JNI on this Linux host. No Android runtime, D8, full APK, native Telegram
transport, wire protocol, session database or SRP cryptography was exercised.
SDK24 symbols plus JDK release 8 are not Android minSdk/runtime certification.

## Exact handoff to Work 2 after P1/P2

1. Review this stacked diff after #35/#36; retain original LoginActivity pages and
   transitions. The source module's `main` and `telegram` directories need explicit
   Android build integration later. Do not change Diagnostic/BetaDevelopment/Production
   or their policies to include or enable it automatically.
2. Use `TelegramAuthorizationStore.localTransport` and the existing LoginFlowOwner /
   LoginActivityAdapter wiring shown in the module README. Render transport metadata
   through the existing relay, routing intermediate actions explicitly on a serial
   worker; restore only the existing non-sensitive restart marker after process death.
3. Prepare a separately reviewed original writer around UserConfig/MessagesStorage
   and native config, with scoped transaction/CAS and read-only generation evidence.
   Preserve original key formats, unrelated database rows and `afterSignup`. The current
   original onAuthSuccess does separate mutations and cleanup; this seam does not make
   those mutations atomic or safe to invoke unchanged.
4. Prepare a separate native request-context adapter for original TLRPC requests,
   phone-code hash/QR expiry/SRPHelper state, cancellation and flags. Current local
   receipts (`L`) are coordination markers, never Telegram codes, keys or session data.
   Do not pass them to real requests or persistence.
5. Explicitly review unsupported email, setup-email, Firebase, payment, Fragment-SMS,
   password-setup/recovery and unknown algorithm branches. They currently fail closed
   without silently switching delivery route/provider. No automatic QR retry or DC
   change is implemented.
6. Apply each reviewed safety patch selectively only after validating new source
   context, then audit remaining original logging/Bundle retention. Obtain project-owned
   API credentials privately in the later approved stage; do not request or commit them
   here. Independently authorize transport/authentication before any real RPC/account test.
7. Compile a full integrated realAlpha APK and run lifecycle/storage/native tests on
   authorized Android before claiming runtime or session safety. Preserve closed policy
   agreement between Java/JNI until a separate transport review permits otherwise.

No APK was built, signed, installed or distributed in this mission. There were no real
credentials, Telegram requests, Internet permission changes, workflow runs or merges.
