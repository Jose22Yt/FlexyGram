# FlexyGram Beta 1 integration candidate

Integration on PR136 / `cd2af16c8271e52738f0c4e726cf59862c637087`:

| Source | Exact input | Included |
| --- | --- | --- |
| PR131–136 | ancestor chain of PR136 | official Beta identity, Work2 P0, fixed Home, native Signature |
| PR137 | `7ab986a2adf60976189f697439aeea9344d40c43` | four snapshot deletion effects |
| PR138 | `30da55efe088a2084a09aa69d755f074053b8fef` | native inline smart pill layout/classification |
| PR139 | `d5099523f1f97720ac6b2180466ae18673f2c8fb` | per-cell border cache, touch prefilter, tabs/slider work reduction |

No original branch/main is merged or rewritten. The integration PR is a draft.

## Production changes after integration

- Signature row-side context uses the same approved panel as bubble context. Native event arbitration, actions, links and media controls remain authoritative. Visible name: **FlexyGram Signature**.
- The existing phase spring controls scrim opacity as well as bubble/card/reactions. Cancelling the independent scrim animator prevents a second return phase; a settled dismissal cleans up without another 320 ms fade. Division by zero in a zero-opacity scrim is prevented.
- Placement uses the visible window, list bounds and system insets. The action card remains scrollable. Long selected messages keep at least 72% size and scroll inside a temporary accessible preview; source chat content is unchanged. Existing grouped-message native fallback is retained.
- Delete effects connect to `ChatListItemAnimator.animateRemoveImpl`, after native row removal is accepted, before the detached row is released. Native confirmations, RPC, permissions, Ayu retention, undo and move animations are unchanged. A successful snapshot finishes only that holder's removal; the overlay owns visual rendering. Capture failures use the native effect. Native group removal remains the fallback for albums. Up to four simultaneous snapshots, each at most 900,000 pixels; host detach and failures release callbacks/bitmaps. Backgrounds normally drawn by the parent are included in capture.
- Settings route: FlexyGram → Animations → Message animations → Animation on delete. Five styles and a local preview. English/Spanish resources; current-theme sample colors.
- Smart Pills has **Multicolor / Automatic / Off** only. Stored legacy Matte (2) maps to Automatic (1); Off retains stored ID 3. No per-category controls. One primary content pill and, where space permits, one reliable secondary status. Roles come from already loaded participant/admin caches; deleted status uses `isAyuDeleted()` materialized metadata. No I/O/downloads or participant requests in row binding. Filenames keep their suffix even before ellipsizing. Unknown archive formats are not mislabeled 7Z.
- Beta stays `com.flexygram.messenger`, `1.0.0-beta.1`, versionCode **1290**, official certificate pin and Gradle build type `beta`. No signing gate is weakened and no key is generated.

## Reproduction

```sh
python3 -m pip install -r tools/connected_alpha/requirements-ci.txt
git submodule update --init --depth 1 TMessagesProj_Modules/media
python3 tools/connected_alpha/run_checks.py
python3 tools/beta_integration/run_host.py
python3 tools/identity/check_identity.py
python3 tools/signing/check_verifier.py
python3 tools/connected_alpha/check_resources.py --sdk-root "$ANDROID_HOME"
python3 tools/beta_integration/compile_api37.py --sdk-root "$ANDROID_HOME"
python3 tools/beta_integration/android/run.py --sdk-root "$ANDROID_HOME"
```

The exact integration audit projects only reviewed hashes to the previous audit layer and rejects unknown bytes/scope. Historical manifests stay unchanged. The retained smart-preview tests now exercise current metadata kinds and reserved-width spans, with expanded participant/deleted/long-filename cases. No test is removed. The historical login freeze compares unchanged JNI/Chaquopy tracked bytes with Git directly, avoiding repeated Python copies of large native archives while retaining the mandatory native/submodule equality check.

## Verified local results

- Retained source/host suite: **373 PASS**, no failures/errors (227.161 s).
- General suite: **144 PASS / 31 optional skips**.
- Real production math: **3241 placement assertions**, **10001 deletion samples**, **152 classifier/contrast assertions**.
- API37 compilation of new production views with explicit Telegram/Recycler doubles: PASS.
- AAPT2 main/Alpha/Beta resources and public identity: PASS; no full APK manifest/DEX/JNI assertion.
- Android native graphics in isolation (API35): **4 PASS**, zero failures/errors/skips.
- Official public certificate and **8 rejection/non-disclosure cases**: PASS. Private-key correspondence was not checked because the original private inputs are unavailable.

Machine-readable results: [verification.json](verification.json). GitHub Actions repeats the source/resource/isolated validation; it never signs an alternative APK.

## Delivery gates and known limits

**Not an accepted/released Beta.** No full app Gradle/JNI/DEX build, signed APK, installation, update test, device FPS, jank or Poco acceptance is claimed by host/isolated checks. API37 compilation uses real Android APIs with explicitly stubbed Telegram/Recycler hosts; native graphics tests run isolated API35, not Android17.

The authorized runtime currently has no official PKCS12/passwords or Telegram application credentials. Only the public official certificate is available. A Beta APK must not be replaced by Alpha/debug signing. No private material is requested in chat, stored in Git, loaded into Actions or included in test artifacts. The Actions workflow in this PR runs source/resource/isolated validation only.

Still required before release: authorized complete Beta build using the original key and registered services, certificate/payload verification, real installation/login/network/push/media, same-signature higher-versionCode update, physical reference comparison and sustained scroll/multitap/preview/theme/blur testing on Poco X8 Pro. Check extreme keyboard/landscape layouts, preview clipping/scroll accessibility, album fallback, deleting >4 visible messages, photo/video snapshots and interaction interruptions. An accessible viewport and geometry tests do not prove every native popup placement on a phone.
