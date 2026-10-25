# Alpha1272 corrective integration

Base: PR89 / `997ac40a65be00c672dc8009b61f55825537d498`. Preserve native authentication, sessions, playback engine, Home2 and composer. Version1272 updates1271 using the same authorized Alpha package/certificate. Never publish the APK, signing inputs or owner screenshots in this public repository.

## Navigation P0 evidence

Original SignatureMusicBubble.release() removes a sibling from the fragment root while FragmentContextView/PlayerMiniView.onDetachedFromWindow is called during ViewGroup's child iteration. The isolated API35 native Android probe reproduces the reported exception: `NullPointerException` in `ViewGroup.dispatchDetachedFromWindow`, `children[i]` is null. The original production bubble is taken from the pinned integrated base, not a reconstructed old screenshot or simulated Telegram account.

Window-detach now unregisters observers, clears art/message state, stops play/gesture work and hides the root-owned child without removing it from the array Android is traversing. A subsequent attach reuses this inert child; repeated detach/attach does not grow the tree. Explicit detach outside that traversal still removes the child. Spring callbacks invalidate their ownership before completion; cancellation rolls back the gesture and stale callbacks cannot close another fragment. Native animation engines remain.

Run music_visual/run.py, then music_visual/reproduce_detach.py. The first tests corrected production components and 100 repeated tree detach/attach cycles. The second requires the original bubble to reproduce the exact framework NPE. This is isolated Android evidence, not a physical Poco acceptance result.

## Other corrective changes

ContextView now supplies an EXACT height MeasureSpec so oversized children cannot paint into the following translator allocation. Existing native panel stacking, transitions and Music2 design remain. The test extracts the real measurement method and exercises native Android layout/space recovery with explicit header/translator View doubles; full real-chat touch acceptance remains pending.

Signature Login opts into one fill and one rounded contour, clipped only beneath the intersecting floating label. Legacy fields keep their original renderer and all authentication stages remain byte-identical. Launcher migration keeps historical aliases and explicit choices, atomically enables the selected modern alias and disables the old primary. Modern blue uses a fresh component identity to avoid reusing the stale primary launcher cache. HyperOS shortcut/cache behavior needs physical verification; no app data or launcher data is cleared.

Chats uses three grouped Matte sections, native line artwork, chevrons and wrapped native titles. Bubble border range is0.5–2.0dp in0.1dp steps, default1.1dp, with a new bounded preference; legacy preferences are retained. A doubled stroke is clipped inside the unchanged native silhouette, avoiding contour intrusion into adjacent native cells. No message layout, grouping or cell height changes. The preview contains synthetic native drawables and cached labels, with no account or permanent animation loop.

## Optional cached blur limitation

Cached wallpaper blur is NOT implemented or certified in this corrective build. No active control falsely claims to enable it. The settings explain that Matte is used. Complete a full ARM64 build and physical navigation/memory/scroll validation of the P0 fixes before adding a shared asynchronous wallpaper cache. Do not restore the old live Glass callback or claim that this fallback is a measured blur optimization.

## Acceptance still required

On the owner's Poco: update without uninstalling; verify accounts/preferences/icon across reboot; previews with immediate release, canceled/predictive gestures, repeated taps and subsequent chat/settings/folder navigation; actual music plus translator with keyboard, focus/background/system controls; all login stages using a test account; ES/EN/RU, RTL, font scales, light/dark, media/replies/reactions/grouping and border extremes. Source parity and native graphics doubles do not prove these real account/device flows.

No physical paired gfxinfo/median/p95/jank/memory measurements are available here. Superiority over Exteraless remains NOT_ESTABLISHED. Keep the PR draft and stable branches unmerged.
