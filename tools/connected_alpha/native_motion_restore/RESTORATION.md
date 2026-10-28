# Native animation restoration — Alpha1281

Owner decision: Flexy Motion Engine / Instant Navigation are cancelled. Do not integrate PR107/108/114 or restart that engine. PR107, PR108 and PR114 are closed as cancelled.

## References and implementation

Application base: PR116 `a4d66fc84695f59a17a1d30ac888cd18ebcb1bba` (Alpha1281). No newer integrated application PR was found at this review. PR117 is an independent Bubble Studio draft and is not integrated.

Native reference: pre-engine Work1 Alpha1278 `14e586b4ddb7a686f39cda3cb175920c49cecf11`. This preserves independent P0/stability fixes and native transitions with the current Signature UI, instead of resetting the entire app to historical Exteraless. The exclusive engine diff is reversed from reviewed PR108 `c3dd04ec43a8ec7ff53a4d9df7dae1a9bd2600ed`. Eighteen complete classes match the pre-engine reference byte-for-byte. ChatActivity and FilterTabsView additionally retain post-engine blur/folder fixes. Re-applying only the original engine diff reconstructs all 20 Alpha1281 components exactly; an automated test verifies this.

Native SpringAnimation, AnimatorSet/ObjectAnimator, original ButtonBounce/ScaleStateListAnimator, tab and reaction owners, popup dismissal and player timelines are restored, not rebuilt. All 14 exclusive Java engine classes and ES/EN/RU engine resources are removed, including settings entry/profile controls. The unused local preference file is left inert rather than deleting arbitrary user preferences. No account/data/key/schema migration.

## Features preserved

Signature UI/Home/composer, current music layout/playback, themes, Smart Previews 2.0, cached/Instant Blur, FlexyStudio/FlexyFiles, identity/version/signing/private delivery, authentication and original services remain. The only ChatActivity delta removes popup engine opt-in. Blur worker/cache/prefetch/LRU logic is byte-preserved; its one cold owner-level 120ms reveal now uses native ValueAnimator, with listener removal/cancellation on release and weak owner/visibility checks. Warm reuse remains ready from the first draw. No permanent loop or global clock is introduced.

## Work1 / PR117 integration

Do not merge PR114; it was never part of PR116. Do not integrate PR117 automatically. Its `bubbles/interaction/BubbleTapMotion.java` imports `FlexyFrameMotion` and `FlexyMotionSettings`; discard that optional tap effect or adapt only its local draw transform to original native ButtonBounce/ValueAnimator with lifecycle cancellation. Remove engine profile/physics assumptions and associated controls. Preserve BubbleStickerEncoder, BubbleStickerSpec, BubbleStickerWorkflow, NativeStickerMetadata, conversion metadata and real send logic independently. No PR117 production file is changed here.

## Validation and delivery limits

Host/source restoration checks and selected native API37 compilation/API35 Robolectric tests are separate from integrated APK/physical behavior. Historical exact reviews/manifests remain frozen. A new exact-byte overlay handles deleted code solely for historical source audits, never for runtime loading; unknown mutations fail closed. Exclusive engine tests are retired and replaced by native-control, restoration and preservation checks.

Required device checks: repeated chat open/close and immediate Back; swipe/predictive Back cancellation; preview release/Back without freeze; folders/reordering; reactions/context menus; music with navigation/background; cold/warm blur with theme changes and memory pressure; multi-account, pause/resume, detach and rotation. No device/session automation or physical acceptance is claimed.

Integration: review and merge this restoration branch onto the exact PR116 base before further feature integration. Retain the complete restoration source/test/contract overlay. Do not cherry-pick historical engine commits afterwards. No versionCode/applicationId/certificate or distribution changes are required. Full signed ARM64 build and private round-trip delivery must use the existing authorized workflow, with this exact candidate SHA after review; no public APK or signing material is added.

Rollback: revert the restoration commit as a whole only if explicitly requested; do not selectively restore engine consumers without their removed definitions. This cancellation has no account/session migration.

## Executed checks (host / isolated, not phone)

- Native restoration source/preservation: 8 tests passed.
- Native restored controls: 6 API35 Robolectric tests passed, API37 compilation.
- Bubble/blur raster: 34 passed, including warm-cache lifecycle reuse and native cold-fade sampling.
- Header/reactions/channel controls: 24 passed with original native animator owners.
- Player visuals: 15 passed; playback services remain explicit doubles.
- Matte cells/accessibility: 7 passed.
- AAPT2 main/Connected Alpha compile and isolated link: passed; full merged APK manifest is not validated by this probe.
- Full Connected Alpha/general suites and integrated signed build are tracked in the PR; no device/FPS/jank superiority claim.

The initial sparse checkout omitted some unchanged compatibility fixtures. They are materialized before rerunning the original tests; no checks are excluded for that reason. Native animator progress is sampled explicitly in the isolated cold-fade test, not presented as elapsed display-frame timing.
