# Connected Alpha — native cloud build (support PR)

This support workflow is based on PR #55, commit `4b0bf291284ff64c3cac89ccdf2b76bb00041e39`. It does not alter Telegram authentication, networking, Gradle variants, Firebase initialization, or source Java/C++ files.

## Purpose
The Work 1 host has only ~580 MB of free disk and therefore cannot rebuild JNI/Chaquopy. The additional workflow attempts native ARM64 on a GitHub-hosted Ubuntu runner **only when the required private inputs exist**. It builds `:TMessagesProj:assembleConnectedAlpha` with the original submodules and then verifies the result using Work 1's `verify_apk.py`.

## Configuration in GitHub
In the repository's **Settings → Secrets and variables → Actions → Secrets**, the repository owner must configure the following secret names privately (do not put values in code, comments, issues, or chat):

- `TELEGRAM_APP_ID` — your own authorized Telegram API ID.
- `TELEGRAM_APP_HASH` — your own authorized Telegram API hash.
- `ALPHA_STORE_PASSWORD` — password for the independent test keystore.
- `ALPHA_KEY_ALIAS` — alias in that keystore.
- `ALPHA_KEY_PASSWORD` — private key password.
- `ALPHA_FIREBASE_JSON_B64` — base64 of the Firebase JSON for `io.github.jose22yt.flexygram.alpha`.
- `ALPHA_KEYSTORE_B64` — base64 of `config/connected-alpha-test.keystore`.

The two base64 values are **still private**. Base64 encoding is not encryption. Do not share them.

The workflow decodes the files on the temporary runner and deletes them after running. It validates the Firebase package identifier before invoking Gradle. The signing key is not substituted with a default or generated automatically.

## Trigger and result
The workflow listens for pushes to `alpha/connected-exteraless-baseline` or `support/connected-alpha-ci-20261022` changing listed sources. The support branch is enough to test the cloud build; you do **not** need to merge into main. If secrets are missing, only a small presence-check job runs. To try again after configuring them, rerun the workflow in the GitHub Actions interface or push a non-secret source change.

**By default no APK is published or uploaded.** If a full build succeeds, the job prints its APK SHA-256 and verified ELF count. This proves only an artifact build, not on-device login or performance.

If and only if the repository owner explicitly agrees to publishing the APK to a GitHub Actions artifact in a **public repository**, they can create a repository Actions **variable** named `ALPHA_PUBLIC_APK_ARTIFACT` with value `enabled`. The upload then includes the signed APK and sanitized verification report with 1-day retention. This is not a private distribution channel. Do not enable it if the Alpha must remain private.

## Constraints
- Never add `local.properties`, keystores, or `google-services.json` to commits, PRs, or build artifacts.
- Do not run `NATIVE_TARGET=SKIP` or claim a successful Gradle task listing is a completed app build.
- GitHub runner disk availability varies; the workflow checks that at least 8 GiB remains before compiling. It can still run out of disk or fail due to upstream dependencies.
- GitHub-hosted runners do not conduct physical Android login testing.
- This has not yet produced an APK. A green static/source job alone must not be represented as success.
- Keep PR #55 and this PR as drafts until signed build and independent acceptance checks are reviewed.
