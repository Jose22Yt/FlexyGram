# Validation — explicit limits

## Executed on the candidate

| Check | Result | Meaning |
| --- | --- | --- |
| General pytest suite including 12 new Settings3 tests | 156 passed, 31 optional skips | Source/ownership/callback/provenance regressions; missing optional corpus/R8 files are documented by pytest |
| `python3 tools/settings2/checks.py` | 12 passed | Existing ownership/security checks retained; scope updated for authorized controller presentation changes, with original click/backend preservation covered separately |
| Settings3 Android probe | 10 passed | Real API37 resource link/Java compilation of root/cell/registry/policy/adapter; Robolectric API35 Android graphics and actual AndroidX RecyclerView 1.4 adapter. Telegram hosts, list plumbing and legacy controllers are explicit doubles |
| Original resource checker | PASS_RESOURCES_AND_ISOLATED_LINK_ONLY | Main AAPT2 compile (inherited formatting warnings), strict ConnectedAlpha overlay and isolated link; not the full app merged manifest |
| Java21 syntax parser | 28 production files parsed | JavaParser 3.26.4 language level21, no semantic/type/module compilation claim |
| Gradle wrapper | BLOCKED | Pinned Gradle 9.7.1 download fails with `java.net.SocketException: Network is unreachable`, including a proxy-configured retry |
| Physical Android17/Poco, jank, latency, memory | NOT_TESTED | No account, private conversation or physical device used; no invented numbers |

The initial general test failures were due to an unmaterialized pinned media submodule and Kotlin sparse paths. After restoring those exact sources the suite passed; no tests were disabled to bypass them. Android fixture errors were corrected in the explicit host doubles. The actual resource checks were repeated after materializing the original flavor overlays.

## Reproduce

- `python3 -m pytest tests/ -q -rs`
- `python3 tools/settings2/checks.py`
- `python3 tools/settings3/android/run.py --sdk-root /path/to/android-sdk --output-dir build/settings3-native`
- `python3 tools/connected_alpha/check_resources.py --sdk-root /path/to/android-sdk --output-dir build/settings3-resource-check`

The probe reuses the existing native graphics runner. Its inherited banner mentions music; `Settings3AndroidTest` and the final Settings3 banner identify the actual suite. API35 runtime tests are not Android17 emulation. No x86 emulator or production APK is used. Install Maven and a Java17 compiler on PATH; provide actual API37/build-tools36. The old Settings2 visual entry point now delegates to the superseding Settings3 probe rather than asserting obsolete colored/eight-category screenshots.

For syntax parsing, compile `tools/settings3/JavaSyntaxProbe.java` with JavaParser3.26.4 on the host classpath and pass actual changed production files. This is optional host tooling, not an application dependency.

## Required before marking complete

1. Compile the full official Beta modules with their existing approved source/signing gates. Do not weaken frozen scopes, use fake private inputs, change versions/certificates or generate a parallel APK.
2. Launch each category and every original conditional group. Confirm Header/Bubbles/Composer appear once, in order, in one scroll surface; compare actual app screenshots against both supplied references.
3. Test each toggle/slider/dialog, native setter side effects and update notification. Verify representative **and remaining** preference values before/after update, restart, Back and configuration recreation. No completeness claim is made from representative isolated preference tests.
4. Exercise long-press row sharing, legacy aliases, global/root search and confirmed value import; ensure no old hub or duplicate editor appears.
5. Check conditional count changes, sticker reset, preview enablement, hidden passcode, ghost mode, sensitive content, drawer rebuild, icon changes and deferred settings. Verify deep-link position mapping with expanded/collapsed groups.
6. Repeatedly open/close/rotate/background with dialogs, file selectors, permission results, keyboard, active music and previews. Confirm pending requests/observers/dialogs cannot target destroyed views.
7. Check narrow screens, RTL, font scales, TalkBack and live theme changes. In particular verify embedded sliders/previews recolor correctly and each controller cleans up when the host view is recreated.
8. Audit global duplicate preferences including mode-specific old navigation vs Signature dock controls and specialized managers. Source ownership checks are not exhaustive runtime proof.
9. Check original Telegram screens, accounts, connection, chats, multimedia, notifications, plugins, files and existing preview P0 behavior.
10. Measure the same navigation/scroll workload on Poco X8 Pro (effective refresh rate, same conditions), comparing the base and candidate with the existing performance lab. Do not claim greater smoothness from source inspection.

The full category controllers and modified base classes are **not yet integration-compiled** in this environment. Their lifecycle composition is the principal integration risk; maintain draft status until verified.

## GitHub CI and baseline comparison

[Run 41350301078](https://github.com/Jose22Yt/FlexyGram/actions/runs/41350301078) passed the real Gradle task-graph validation for **both Alpha and Beta**, using `assembleConnectedAlpha --dry-run` and `assembleBeta --dry-run`. It did not compile the application. Source checks stopped at the frozen Beta scope gate. The later artifact-upload error reports missing screenshots because rendering was never reached.

[Blur run 41350301097](https://github.com/Jose22Yt/FlexyGram/actions/runs/41350301097) was reproduced on a separate, unmodified worktree at the exact base: both base and candidate have **4 passing tests, 1 failed historical ActionBar comparison and 1 scope error**. The candidate ActionBar.java is byte-identical to the base. The scope error is already present on the base and also correctly identifies the feature's new unreviewed paths. This is **not** a claim that the full CI passes, nor permission to bypass source review.

See `ci-baseline-comparison.json`. Reproduce by creating a detached worktree at the base, materializing its original source/workflow/config/documentation paths, and running `python3 -m unittest discover -s tools/connected_alpha -p test_reconstruction1285.py -v` in both worktrees. Do not update historical hashes merely to make this feature green.
