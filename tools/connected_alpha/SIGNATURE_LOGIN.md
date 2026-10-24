# Signature Login — integration candidate

Base: PR84 / a261ccc3cf2fe1c4af46cb858bb3318b2310aeb8, Alpha1270. No version bump, APK build, new credentials, account operations or installer changes.

## Production implementation

- IntroActivity chooses a static native SignatureWelcomeView only for CONNECTED_ALPHA, before TextureView/EGLThread/ViewPager/flicker creation. The legacy path/resources remain available to other variants. Native DC settings/remote languages initialization stays in place. Native fragment navigation has no new animator or artificial delay. Resume resets a failed/interrupted navigation gate; theme/configuration updates reuse the same views.
- LoginActivity keeps all20 native stages, transport constructors/flags/request calls, timers, callbacks, country/prefix/paste/formatting/IME/error/state/permission logic. Color calls delegate to a login-scoped palette; global themes/preferences are never written. Native outlines get a Matte fill and16dp opt-in corners, retaining the original focus/error/attached-edit-text implementation. The original done/progress/visibility/click state machine remains in FragmentFloatingButton. PhoneView is top aligned with a24sp heading; its keyboard/scroll measurements are unchanged.
- OutlineTextContainerView adds one opt-in radius setter. Its default follows the original8dp density calculation.
- ConnectedAlpha's inherited NagramX resource key displays FlexyGram. No package, applicationId, preference/database/path/service/provider/component identifiers are renamed. Original legal attribution files are byte-identical.
- UpdaterSheet uses the shared identity and explains encrypted Alpha delivery. Evidence: background check was already gated but fetch/download were not. Both direct entry points are now gated before upstream network/disk work, preserving legacy behavior and preferences for other variants. No updater repository, protocol or new service is substituted.

## Shared Work1 airplane and protected work

Production resolves mipmap/ic_flexy_blue provided by PR85 at runtime. Integrate PR85's official launcher resources before visual acceptance; this candidate does not copy or edit any production launcher asset or alias. On the isolated1270 base only, the existing native msg_send glyph is a blue fallback. The graphics probe uses exact copies of Work1's bd3bc666 resources solely as test fixtures; never install them as a second production icon.

Bubble/MessageDrawable, Home2, composer, sliders, Chats/General/Appearance, launcher selector, global navigation, preview transitions, account/transport/JNI/Chaquopy and version/signing/delivery files are frozen against1270. No cause of the global long-press preview freeze was established in this scope.

Read-only git merge-tree against Work1 PR85 HEAD0e359f0e7841a99d61c79f996dd162b7c836a9bf found no production-class conflicts. Two tooling conflicts need manual integration: .github/workflows/pr.yml must retain both Work1 branch/version exclusions and the feat/signature-native-login exclusion; test_bubbles1270.py must retain Work1's1271 presentation restoration and add login_contract.PATHS to its allowed candidate scope. Other historical scope tests auto-merged. No branch was merged or altered by this probe.

Merge/cherry-pick this branch after the desired Work1 integration. Reconcile CI exclusions and historical test scope allow-lists by preserving both changes. Keep the new Login reversal audit in check_source.py; update future release-version assertions with the integrator's version. The explicit native presentation patch must reverse to the exact original authentication source. Do not automatically merge stable branches.

## Validation boundaries

Locally:124 ConnectedAlpha tests PASS;144 project tests PASS,31 optional external corpus/R8 cases skipped. Six API35 Robolectric native-graphics tests PASS, compiling real production Welcome/Palette/Identity/Outline/Button-subclass plus the real native OutlineTextContainerView and SpringAnimation1.0.0. Cases cover ES/EN/RU,240/320/600dp,100–300% fonts, light/dark, portrait/landscape-sized layouts, same-view refresh/click response, button accessibility/normal/pressed/disabled styling, native focus/error/attachment and legacy palette fallback. API37 compiles/links login resources. Dependency doubles for Theme/LocaleController/BuildConfig/math and the original FAB shell are explicitly in login_visual/stubs.py. They do not simulate Telegram authentication or prove the native FAB state machine.

The PNG is isolated production components with Work1 artwork, not a full app screenshot. A genuine before/after full-screen comparison is unavailable without a complete runnable baseline; no reconstructed old screenshot is presented as evidence.

Pending: full integrated Java/Kotlin build, first/existing install, real guest phone/country/IME/back/transitions, every live code/2FA/email/recovery/register/error/retry method, dialogs/popup theme updates, actual PhoneView large-font/landscape layout, edge-to-edge/navigation insets, owner PocoAndroid17/HyperOS4, ANR and physical performance. No real owner account or credentials are used in CI. Native logic parity is not end-to-end authentication acceptance.

## Performance

Source evidence: old IntroActivity creates TextureView/EGLThread, reschedules drawRunnable at the display refresh interval and invalidates its flicker button in onDraw. The ConnectedAlpha Signature branch allocates none of those and owns no repeated render/animation callbacks. Existing native authentication animations remain. This establishes removal of that specific processing, not measured startup/FPS/energy gains.

measure_login.py captures cold start TotalTime and gfxinfo framestats from a manually prepared TEST device. It requires explicit test-device confirmation, state, package/component and frame budget. It never clears data, logs UI/logcat, captures screenshots, sends numbers/codes, or reads sessions. Reports include environment/animation/font/density settings, sample count, median, nearest-rank p95 and over-budget frame counts. The same device/prepared guest state/settings and at least20 runs per scenario are required for comparing reference and candidate. For phone/country/keyboard/back, capture manual guest interactions with --manual-seconds. Device state is explicitly not verified by the harness. No valid reference/candidate device pair was available here; superiority is NOT_ESTABLISHED.
