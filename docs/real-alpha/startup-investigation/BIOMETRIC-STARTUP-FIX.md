# Offline realAlpha: omit biometric key preparation

Base: PR #41, cce67ce7023e8231cd1c244c60f0305c455c160c.
Physical report, recorded in issuecomment-6324642457: API37, exit reason 4,
OTHER_RUNTIME -> SECURITY@LAUNCH:737@REAL_ALPHA:46, DIALOGS_VIEW_RETURN but no LAUNCH_RETURN.
No complete private Android report or device data is required for this patch.

## Located failure path

The old diagnostic overlay inserts two lines before original LaunchActivity.java:735;
the instrumented line 737 calls FingerprintController.checkKeyReady(). Its boolean
overload evaluates BiometricManager.canAuthenticate(BIOMETRIC_STRONG) before entering
the queued key generation handler. That call is not covered by the generator's catch.
The realAlpha merged manifest deliberately omits USE_BIOMETRIC and USE_FINGERPRINT.
Android's framework API requires USE_BIOMETRIC:
https://developer.android.com/reference/android/hardware/biometrics/BiometricManager#canAuthenticate(int)

This confirms the source/permission conflict and the line mapping. Whether this
patch is sufficient for the physical phone remains pending a new authorized test.

## Minimal change and limits

The existing SDK guard now excludes only the immutable realAlpha build profile when
ISOLATED_DIAGNOSTIC is true and authentication/Telegram transport capabilities are
false. It applies to realAlphaDebug and its startupDiagnostic derivative. No new
permission, account, restored session, key, navigation engine or biometrics fallback
is introduced. FingerprintController itself and all manifests remain byte-identical.
Diagnostic, BetaDevelopment, Production and unknown variants retain the original call.
Non-isolated or open-policy combinations do not gain a bypass based on variant name.

Only the LaunchActivity overlay's baseline/output hashes change; its two diagnostic
insertions and the other six overlays remain intact. The common realAlpha DEX verifier
now rejects an unguarded biometric startup call. It accepts removal by the compiler or
the forward branch that skips the call after comparing the compiled realAlpha literal
with itself. Existing Back/factory, identity, permission and native gates are retained.

## Other biometric paths inspected

LaunchActivity contains a single direct FingerprintController call, in onCreate.
ApplicationLoader/post-init and DialogsActivity have no direct biometric readiness call.
onResume delegates to onPasscodeResume: AndroidUtilities.needShowPasscode requires a
non-empty app passcode hash. Startup Probe has a separate package, restoration disabled,
and the test does not configure an app passcode. PasscodeView.checkFingerprint and
hasFingerprint contain their own exception handlers; deleteInvalidKey can re-enter the
controller only through the app-lock path. These paths were reviewed and left unchanged;
this is not a general biometric feature removal or a claim about every future UI flow.

## Regression and physical follow-up

The host regression extracts the actual LaunchActivity condition and the actual two
checkKeyReady overloads. A permission-enforcing BiometricManager double reproduces the
baseline SecurityException and verifies that corrected isolated realAlpha performs no
biometric query or key access. SDK24/32/37 values, other variants, permission present,
open-policy combinations and the original pre23 guard are exercised. The new regression
fails on the old source and passes with this patch. This host double is not Android.
The source fault line, exact two-line mapping and unchanged manifests/controller are
also asserted. A separate DEX gate regression rejects unsafe branch mutations.

Build both realAlphaDebug and realAlphaStartupDiagnostic with real ARM64 JNI/Chaquopy;
check actual merged/binary manifests, DEX, resources, native policy, all 96 ARM64 ELF,
4/16KB alignment and absence of signing. Save each unsigned and a full recovery archive
to private Library and recover them independently before requesting new signing approval.

Keep both failed signed APKs and their backups. No signing key is retained and no new
signature, delivery or installation is authorized by this patch. Do not merge PRs.
After separately approving the new Startup Probe hash/certificate, execute one native
launch on the phone and preserve the sanitized report. Required observations:
no old biometric SecurityException, LAUNCH_RETURN, FIRST_DRAW, and visually confirmed
native empty dialogs. A different failure remains diagnostic evidence, not a success.
