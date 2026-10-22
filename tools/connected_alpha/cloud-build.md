# Connected Alpha ARM64 — cloud build and private delivery

Continues PR #56 on `support/connected-alpha-ci-20261022`, based on PR #55 HEAD `4b0bf291284ff64c3cac89ccdf2b76bb00041e39`. Neither main nor develop needs to be merged or changed. PRs remain drafts. No login, MTProto, chats, navigation, themes, player or plugin implementation is changed.

## Corrections in this revision

- The verifier now requires `lib/arm64-v8a/libtmessages.49.so`, matching both the original NativeLoader version 49 and `set(NATIVE_LIB "tmessages.49")` in CMake. The old unversioned name would reject the real output.
- The ephemeral CI checkout uses daemon criteria `toolchainVersion=21` and `toolchainVendor=ADOPTIUM`, matching setup-java's Temurin. Upstream requests JetBrains, which overrides JAVA_HOME and otherwise causes an additional JDK download. The committed upstream daemon configuration is preserved.
- `CMAKE` points explicitly to SDK CMake 3.31.6 for the original Chaquopy runtime script, which otherwise selects the runner's system CMake. Native submodules must match their pinned commits.
- Source tests run even when credentials are unavailable. Missing secrets cause an explicit blocked/failing credential check, not a green claim of an APK build. The inherited PR job no longer attempts disabled assembleDebug on the support branch.
- Signing verification compares against an independently configured certificate fingerprint; deriving the expected fingerprint from the same supplied keystore is no longer treated as proof of authorization. Keystore alias, store password and private-key access are checked before assembling.
- No plaintext APK can be uploaded by this workflow. The former public upload opt-in is removed. Optional delivery encrypts the verified APK/report to the owner's age public key before uploading only ciphertext. Gradle caching is disabled because generated BuildConfig/resources contain private application configuration; private files and generated plaintext are removed in an always step.

## Exact project toolchain

These values were checked against build.gradle, TMessagesProj/build.gradle and the wrapper:

| Component | Required value |
|---|---|
| JDK | 21; CI Temurin/Adoptium |
| Gradle Wrapper | 9.7.1 |
| Android Gradle Plugin | 9.3.1 |
| Python / Chaquopy | 3.11 / 17.0.0 |
| compile SDK | 37; sdkmanager package `platforms;android-37.0` |
| target / minimum SDK | 36 / 24 (unchanged) |
| build-tools | 36.0.0 |
| NDK | 27.2.12479018 |
| CMake | 3.31.6 |
| ABI | arm64-v8a |

The command remains `./gradlew :TMessagesProj:assembleConnectedAlpha --no-daemon --console=plain --max-workers=2`, with `NATIVE_TARGET=arm64-v8a`. No JNI skip, excluded validation, fake credentials or reused offline-profile binaries are permitted. The runner installs nasm/ninja and uses recursive pinned submodules. The 8 GiB disk preflight is a minimum gate, not a promise that a full native build will fit.

## Configure private GitHub inputs

Open repository Settings → Secrets and variables → Actions → Secrets. Configure all eight **repository secrets** privately:

| Secret | Value supplied by the owner |
|---|---|
| `TELEGRAM_APP_ID` | Your own authorized Telegram application API ID |
| `TELEGRAM_APP_HASH` | Your application's API hash |
| `ALPHA_STORE_PASSWORD` | Password of the independent Alpha test keystore |
| `ALPHA_KEY_ALIAS` | Private-key alias in that keystore |
| `ALPHA_KEY_PASSWORD` | Password of that private key |
| `ALPHA_FIREBASE_JSON_B64` | Base64 of your complete Firebase Android JSON for `io.github.jose22yt.flexygram.alpha` |
| `ALPHA_KEYSTORE_B64` | Base64 of your authorized Alpha-only keystore |
| `ALPHA_CERTIFICATE_SHA256` | SHA-256 of the authorized signing certificate, recorded independently before uploading the keystore |

Base64 is not encryption. Never put any of these values in code, issues, PR text, screenshots or chat. The connector cannot inspect or configure GitHub Secrets. Secret presence is established only by an actual Actions credential-check job, not inferred from an empty run list. Tests use local fixtures solely to exercise validators, never to compile or connect a Telegram client.

Get your application ID/hash through https://my.telegram.org → API development tools. See https://core.telegram.org/api/obtaining_api_id . Do not use inherited/sample IDs. Register your own Firebase Android application with the Alpha package; its JSON must include project, client and API key fields. The original Firebase initialization and push implementation remain intact.

Record the certificate fingerprint on your trusted machine (keytool prompts for the keystore password):

```sh
keytool -exportcert -keystore config/connected-alpha-test.keystore -alias YOUR_ALPHA_ALIAS | sha256sum
```

The result is the certificate DER SHA-256, not the keystore file SHA-256. A colon-separated fingerprint from keytool -list -v is also accepted. Use the same authorized key for subsequent Alpha updates. Keep a durable private backup. The workflow neither generates a replacement key nor falls back to another installation's key.

## Optional delivery encrypted to you

Before the build, generate an age identity on a trusted machine, outside this repository:

```sh
age-keygen -o flexygram-delivery.agekey
age-keygen -y flexygram-delivery.agekey
```

Keep `flexygram-delivery.agekey` private and backed up **outside GitHub**. Copy only the public `age1...` recipient into an Actions repository **variable**, `ALPHA_AGE_RECIPIENT`.

Only after a successful full build and APK verification will the workflow encrypt a tar containing exactly the APK and sanitized verification JSON, and upload `FlexyGram-ConnectedAlpha-ARM64-encrypted` with one-day retention. Anyone who can access the public repository artifact may obtain the ciphertext, but decryption requires your private age identity. This does not make the GitHub repository or artifact listing private. No plaintext APK, keystore, Firebase JSON or local.properties is uploaded. If you prefer a different private delivery channel, leave the variable unset and agree on that channel before building; without a recipient, no artifact is retained for download after the runner ends.

Download/extract the GitHub artifact ZIP, then on your trusted machine:

```sh
age --decrypt -i flexygram-delivery.agekey -o FlexyGram-Alpha-arm64.tar FlexyGram-Alpha-arm64.tar.age
tar -xf FlexyGram-Alpha-arm64.tar
sha256sum FlexyGram-Alpha-arm64.apk
```

Compare with verification.json and the Actions summary. Encryption delivery is opt-in through the public-recipient variable; no private decryption key is sent to the runner. No release publishing is performed.

## Trigger without merging into main/develop

The push event includes this support branch and alpha/connected-exteraless-baseline, and watches the workflow, Gradle, buildSrc, native/Android and connected-alpha tooling paths.

1. In the repository's Actions tab, check that Actions/workflows are enabled. Forks may need the owner's initial enablement. This has not been established merely from the API returning zero runs.
2. Configure the eight secrets (and optional public delivery recipient).
3. If an existing run is listed, rerun that run. Otherwise make a small non-secret edit to this document **on support/connected-alpha-ci-20261022** and commit it to produce a matching push event. Do not use an empty commit: path filters may ignore it.
4. Check the source-checks, credentials-present and build-arm64 jobs separately. A full build must finish `assembleConnectedAlpha` and then pass APK verification before its output is accepted.

`workflow_dispatch` is declared for future/manual use, but GitHub's default-branch registration rules mean a Run workflow button is not guaranteed for a workflow that exists only on this support branch. Do not merge into main just to obtain that button. References: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow and https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow .

The connected GitHub tools can read runs and rerun existing jobs; they cannot enable Actions, set secrets, or dispatch a first workflow. No browser or account-settings changes are made automatically.

## Verified and pending in this revision

- PASS: source parity gate, 15 upstream critical components unchanged.
- PASS: 22 Python tests, including the original eight ELF tests plus 14 cloud-build/verifier/input regressions.
- PASS: age 1.2.1 encryption/decryption round trip with a temporary unit identity and non-APK fixture; no project key or private input used.
- PASS: actionlint 1.7.7 on both touched workflows; bash syntax for their 18 run steps; embedded Python AST; Python compilation and git diff whitespace checks.
- No new application Java/Kotlin/JNI build has completed; no Alpha APK, APK SHA-256, authorized final certificate, or Android acceptance is claimed.
- GitHub Actions run status is recorded in the PR after the commit is saved. A returned empty run list is not a successful build, nor proof that a particular secret is missing.
- Earlier host storage of ~580 MB was historical. A refreshed local host now reports ~29 GiB free, but the old build directory/SDK/JDK caches were removed. No stale disk block is used as the current explanation for a missing APK.

After a real build, the artifact verifier checks the compiled package/name/launcher/INTERNET, v2 signature against the authorized fingerprint, zipalign, ZIP integrity, actual versioned Telegram JNI, and all packaged ELF PT_LOAD segments including nested Chaquopy archives for 4/16 KiB compatibility. Existing upstream Python/native dependencies may still reveal errors in that real run; such failures must be fixed, not waived.

Physical installation, original phone/code/2FA login, real dialogs/messages/media, notifications/lifecycle, Android 17 predictive back and same-device navigation speed on the Poco X8 Pro remain pending. The owner performs login manually. A signed, verified artifact alone does not prove those ten acceptance scenarios.
