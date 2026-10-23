# Offline installation helper for the first Connected Alpha delivery

This separate Android application reads the owner's selected `.tar.age` file and
original X25519 identity through Android's local document picker. It uses
`filippo.io/age v1.3.2` unchanged through a small Go/C/JNI bridge. The identity is
read into bounded memory, never written to disk, never displayed or logged, and
never uploaded. No Internet or storage permission is declared. The identity URI
is not persisted. The source identity and recovery ZIP are never modified.

Only this delivery is accepted:

- Alpha source: `c4210911a048d4fde080c03c31aa98741336db2f` (PR #59).
- APK SHA-256: `579f70e6e90f4445b2fedfe747ad433392bc8a7f9beebebf98752e4b284194fb`.
- Cipher SHA-256: `33cd33d4e0d7da4733af0c02eb1b34288e8659886dc4df8c3d49d2f4e863147c`.
- Original recipient: `age1dc36uuvdg4ut52crhgux297zfjc5u0p0rucgnjss8svmgdl2eylseanqqe`.

The Go gate requires authenticated age EOF, exactly two regular tar entries,
bounded lengths, the pinned APK hash, source commit, report status and 96 unique
ELF inventory entries. It stages output privately and rejects path traversal,
links, duplicates, extra files, incorrect identities and authentication failures.
Android independently rechecks APK SHA-256, package identity and the archive
signer's certificate against the encrypted report, including before installation
and when the installer's read-only URI is opened. No APK content or signature is
changed. The system installer always requires the owner's personal confirmation.

The only permission is `REQUEST_INSTALL_PACKAGES`. Verified output is in Android's
no-backup directory, readable only through a provider granting the exact APK URI.
The user can clear temporary output or uninstall this helper after installing
Alpha. This does not remove or change Telegram, Exteraless or FlexyGram data.

The helper has its own ephemeral CI signing identity, unrelated to Alpha's
existing certificate. Its build reads **no repository secrets**. No helper key,
test instrumentation APK, test identities, or decrypted Alpha APK are uploaded.
The uploaded artifact contains only the helper, its public build report and the
emulator smoke result. Upstream dependency license notices are bundled.

## Validation

`go test -race -count=1 ./internal/delivery` and `go vet ./internal/delivery` cover
authenticated extraction, corrupt/truncated final AEAD chunks, incorrect hashes,
reports, identities and unsafe archives using disposable TEST identities.
`build.py` compiles the independent helper against API 37, verifies its signer,
exact permission set, non-debuggable identity and 16 KB native segment alignment.
`android_smoke.sh` runs only the helper in an API 35 x86_64 emulator: UI startup,
disabled installation before verification, native invalid-identity rejection,
provider path/write rejection and corrupt APK rejection. The helper also contains
ARM64 binaries for the owner's phone.

These checks are NOT a physical test of Android 17, the Poco, FlexyGram startup,
login or Telegram networking. Full successful decryption of the real delivery
requires the original identity on the owner's phone and remains pending there.

## Phone flow (no terminal)

1. Install the helper APK; download the original `.tar.age` delivery to the phone.
2. Open the protected recovery ZIP locally and make the original identity file
   available to the Android picker (or open it through a local archive provider).
   Do not select `delivery-public-recipient.txt`, and never send the private file.
3. In the helper, select the encrypted delivery and the original identity file.
4. Tap **Descifrar y comprobar**. Installation stays blocked on any failure.
5. Tap **Instalar**, grant Android's source permission if requested, return and
   tap **Instalar** again. Confirm in the Android system installer.
6. Open **FlexyGram Alpha** from its separate icon. Test startup and native login
   privately, then conversations and media. Existing Telegram clients stay intact.
7. Clear helper temporary output and remove any temporary extracted copy of the
   identity, retaining the protected recovery ZIP. The helper can be uninstalled.
