# FlexyGram Connected Alpha — Exteraless baseline

Owner/creator: @Lukhou23. Upstream code and credits remain under their existing licenses.

Branch: `alpha/connected-exteraless-baseline`.
Parent: `1ad6a60a6834ffca722b1a22f4fba27ecb29a061` (original Exteraless).
This branch does not depend on Diagnostic, beta-offline or realAlpha code. It is a baseline review, not ready to merge into develop's isolated profiles.

## Behavior and scope

Uses the original LoginActivity (PhoneView, LoginActivitySmsView, LoginActivityPasswordView), ConnectionsManager, C++ MTProto, LaunchActivity, DialogsActivity, ChatActivity, messages/media controllers, themes, notification handling and Python plugin engine. The source gate checks 15 critical files byte-for-byte against the pinned upstream commit, and records their SHA-256 hashes in source-evidence.json. This proves source preservation, not Android functionality or performance.

Only `connectedAlpha` is enabled. The application ID is `io.github.jose22yt.flexygram.alpha`; Java/Kotlin namespaces stay original. All localized launcher/app labels are overridden. AccountManager identity, contacts MIME types and shortcut targets use the Alpha package; provider authorities already derive from applicationId. Android private files, databases and plugins remain in the independent app sandbox. BackupAgent is removed, backup/restore and all extraction domains are disabled. Legacy Android media directories and saved Ayu attachments are separated to avoid using upstream shared paths. No session migration or automatic login is added.

INTERNET and the upstream network/authentication implementation remain present. There is no LOCAL_LOGIN_UNAVAILABLE interception. No Crystal Pearl, animation engine, glass, navigation redesign or custom player was imported. Upstream APK updater is disabled for this Alpha. Diagnostic payload/network logging and Crashlytics collection are disabled to avoid recording account credentials. Passkeys are disabled following upstream's warning that they only work for official app IDs; manual phone/code/password authentication remains native. API selection uses only authorized build-time Alpha credentials. No inherited Telegram, Maps, Google OAuth or Firebase configuration is used as a fallback.

## Private inputs required

Never paste keys, passwords, phone codes, session files or local.properties into an issue or PR.

1. Obtain YOUR `api_id` and `api_hash` through https://my.telegram.org → API development tools. Official instructions: https://core.telegram.org/api/obtaining_api_id . They identify this client application; they are not a user's login code. Configure `TELEGRAM_APP_ID` and `TELEGRAM_APP_HASH` in ignored root `local.properties` or environment variables. The gate rejects empty/malformed values and known inherited/sample IDs 4, 6 and 2040. It cannot prove ownership: the operator must supply authorized credentials.
2. Register YOUR Firebase Android application with package `io.github.jose22yt.flexygram.alpha` and its Alpha certificate, then download its `google-services.json` to `TMessagesProj/src/connectedAlpha/google-services.json` (ignored). Firebase remains required because upstream initializes it directly and uses its native push integration. The inherited JSON was removed.
3. Use an authorized test key dedicated to this Alpha at ignored `config/connected-alpha-test.keystore`. Set `ALPHA_STORE_PASSWORD`, `ALPHA_KEY_ALIAS`, `ALPHA_KEY_PASSWORD` privately. There is no fallback to upstream release keys or the machine's default debug key. Keep a durable private backup; updates must use the same key. Example interactive creation, with passwords entered at keytool prompts:

   ```sh
   mkdir -p config
   keytool -genkeypair -keystore config/connected-alpha-test.keystore -alias flexygram-alpha -keyalg RSA -keysize 3072 -validity 3650
   ```

4. Optional: your restricted `MAPS_API_KEY`; your `ALPHA_GOOGLE_AUTH_CLIENT_ID` for Google login integrations. Native phone/code login does not require Google OAuth. These features need separate testing; no borrowed keys are included.

`config/connected-alpha.local.properties.example` lists the exact property names. Root `local.properties`, `LOCAL_PROPERTIES` (base64 properties) and environment inputs are supported; local values take precedence. No private input has been configured in this delivery.

## Build and verify

Actual upstream requirements: JDK 21, Gradle 9.7.1, AGP 9.3.1, Python 3.11 / Chaquopy 17.0.0, compile SDK 37 (installed package android-37.0), target SDK 36, min SDK 24, build-tools 36.0.0, NDK 27.2.12479018, CMake 3.31.6. Submodule commit pins are unchanged.

Use sufficient free disk (the current host had only about 580 MB free, insufficient for a full native rebuild). Initialize submodules and configure sdk.dir / CHAQUOPY_BUILD_PYTHON privately. Do not use NATIVE_TARGET=SKIP or reuse JNI from another profile.

```sh
git submodule update --init --recursive
python3 tools/connected_alpha/check_source.py
python3 -m unittest discover -s tools/connected_alpha -p 'test_*.py' -v
NATIVE_TARGET=arm64-v8a ./gradlew :TMessagesProj:assembleConnectedAlpha
```

APK destination after a successful build: `TMessagesProj/build/outputs/apk/connectedAlpha/`. Do not distribute an APK merely because the path exists. Get the authorized certificate SHA-256 fingerprint from your key and then verify the actual APK:

```sh
keytool -list -v -keystore config/connected-alpha-test.keystore -alias flexygram-alpha
python3 tools/connected_alpha/verify_apk.py PATH_TO_APK --build-tools PATH_TO_SDK/build-tools/36.0.0 --certificate-sha256 EXPECTED_AUTHORIZED_CERTIFICATE_SHA256
```

The verifier checks ZIP CRC/duplicates, v2 signature and exact certificate, zipalign, compiled package/label/launcher/INTERNET, backup restrictions and provider identities, ARM64 JNI presence and ELF PT_LOAD compatibility with both 4 KB and 16 KB pages, including nested Chaquopy runtime archives. Its JSON includes APK SHA-256 and per-ELF hashes. It has NOT been run on an Alpha APK because none was produced. The original native/Python binaries may reveal further compatibility issues when this gate can run; no 96/96 claim is made for this branch.

## Results on 2026-10-22

- PASS: 15 critical upstream source components are byte-identical; source Android identity checks pass.
- PASS: 8 verifier unit tests (ARM64/16 KB/64 KB acceptance, x86/4 KB-only/misaligned/truncated/missing-load rejection, nested Chaquopy inspection). These are tests of the verifier, not of Android or Telegram.
- PASS: AAPT2 compiled all Alpha branding overlays and the new extraction-rules XML.
- PASS: actual `:TMessagesProj:tasks --all` with Gradle 9.7.1 / JDK 21 offline: BUILD SUCCESSFUL, 18 seconds. Only assembleConnectedAlpha is enabled.
- BLOCKED: actual `:TMessagesProj:assembleConnectedAlpha` offline: BUILD FAILED, 16 seconds, at validateConnectedAlphaConfiguration because authorized Telegram credentials are absent. No Java/Kotlin application or JNI compilation success is claimed. buildSrc compiled/reused cache, not the application.
- BLOCKED: standalone manifest task without private configuration cannot run the Google Services task because YOUR JSON is absent. An attempt excluding that task is also blocked by its generated-resource provider. No merged/binary manifest success is claimed. Those exclusions are not part of the build instructions or committed configuration.
- NOT AVAILABLE: signed Alpha APK, APK SHA-256, verified certificate, downloadable GitHub APK artifact.
- NOT RUN: Android installation/launch/login/performance. ADB reports no devices; no /dev/kvm or usable emulator is available.

The PR CI job for this branch runs only source checks and verifier unit tests. A green static job does not mean an APK compiled. The inherited debug build job is skipped for this branch because it would request the disabled assembleDebug variant and inherited secrets.

## Physical acceptance — all pending

Use the Poco X8 Pro (Android 17 / HyperOS 4) only after a signed APK passes the artifact verifier. You perform all account login actions manually. Do not share phone/code/password or session data in evidence.

| Scenario | Automatic evidence now | Physical acceptance |
|---|---|---|
| 1 Independent installation | Source package/account/provider separation | Pending: install alongside Exteraless and previous FlexyGram; both remain installed |
| 2 Opens without crash | Not established | Pending: cold start, relaunch, rotation, background/foreground |
| 3 Native authentication | LoginActivity identical to upstream | Pending: original phone screen appears, no LOCAL_LOGIN_UNAVAILABLE |
| 4 Authorized account login | No credentials/account used | Pending: manually enter number, code and 2FA if requested |
| 5 Real conversations | Original controllers retained | Pending: real dialog list loads |
| 6 Chat open/close | Original navigation retained | Pending: repeated open/back, fast taps and predictive back |
| 7 Send/receive | Original send/network sources retained | Pending: exchange a harmless test message with a consenting test account |
| 8 Multimedia | Original media/player retained | Pending: photo, video, file, voice playback/download/upload |
| 9 No critical errors | Not established | Pending: sustained use, push receipt, screen off, lifecycle, crash/ANR review |
| 10 Original navigation speed | Original navigation code retained | Pending: same-device comparison with Exteraless, identical settings and refresh rate |

After successful compilation and verification, upload only the signed APK and sanitized verifier JSON to a GitHub Actions artifact or an explicitly requested test release; record its immutable commit, URL, SHA-256 and certificate fingerprint in the PR. Never upload signing material, google-services.json, local.properties or user/session data. No artifact URL exists yet.
