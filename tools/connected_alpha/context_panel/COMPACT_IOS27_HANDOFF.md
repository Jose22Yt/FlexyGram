# FlexyGram — Compact iOS 27 context panel, Work 1 handoff

## Baseline and non-goals
- This **review-only** change starts from **PR #123** commit `e00b33e806921017ad74ff50eb5ec88607131d9c` (Alpha 1283). It is **not** merged and is **not** a compiled APK.
- Do not reset PR #123's real native WebP/static-sticker path, uploads, account/peer binding, save-to-document route, native menu admission, or safe fallback.
- Do not restore cancelled Flexy Motion Engine, BubbleTapMotion, PR #117's rejected UI, or change the app's package/signature.

## Approved reference — visible layout
Native Telegram reaction strip is **not** recreated. The host maintains the selected message, reaction permissions, wallpaper dim/blur and native popup positioning. Only the existing `BubbleActionPanelView` is made compact.

1. Top: up to three permitted quick-action tiles (Reply, Copy, Forward) plus always-visible MORE for **all other native actions**, each 64 dp high and accessible.
2. Bottom: **Pin** (if native status admits it), **Convert to sticker** (eligible + user enabled, highlighted Matte row) and **Delete** (if native status admits it, danger color). EDIT/SELECT/other actions remain in native MORE; never delete functionality.
3. Sticker row enters the existing preview state and invokes **BUILD_STICKER** once. Preview offers explicit **Send here** and **Save**. Nothing sends automatically on long press or conversion.
4. Panel: theme-sourced Matte surface, 24 dp corners and modest non-shader shadow; NO expensive live blur or per-frame image allocations. Colors adapt to current theme.
5. Android/Telegram's native reaction bar and original menu remain available on unsupported messages and when the signature panel is disabled.

## New settings in Chats -> Message interactions
- **Flexy context panel**: pre-existing opt-in, default OFF (preserves existing installs).
- **iOS-style menu spring**: default ON; uses bounded 270 ms local AnimatorSet scale/translation keyframes, cancelled and reset on detach; no global clock, navigation or list animation changes.
- **Convert bubbles to stickers**: default ON, but only effective when context panel is active and native eligibility is true. Enforced by the panel's sticker entry point.
- Preference reads are cached; no disk read inside each animation frame. Locale strings ES/EN/RU.

## Sticker correctness — reused from PR #123, NOT newly verified on device
- Capture only the fully visible text bubble (shape/tail/theme/text); a transparent ARGB_8888 bitmap is created, and cleared to transparent, encoded to bounded WebP 512px max side, <=512 KiB.
- Sticker metadata must include `image/webp` plus static-sticker and dimensions attributes. Native SendMessagesHelper transport; only server-confirmed matching account, peer and sticker counts as success.
- Respect noforwards/protected, secret/scheduled/paid, slow mode, ephemeral, spoiler, clipped/transitioning, media or non-writable cases. Keep the native fallback. Never capture chat wallpaper/sensitive background as an opaque rectangle.
- User-controlled Save writes local WebP through Android SAF, not an unconfirmed Telegram stickers/favourites entry.
- Pixel-alpha edges, actual Telegram-side sticker recognition, second-client receipt, and retained transparency remain **physical acceptance** tasks.

## Work 1 MUST finish before calling this feature complete
- The 270 ms elastic entrance in this branch currently animates the **context panel**, **not the selected ChatMessageCell itself**. To match the reference video fully, wire a short localized selected-bubble press/spring visual effect at the native long-press gesture's approved popup-display boundary. Use the already-owned selected bubble/overlay; **do not scale or retain a recycled list cell** or mutate its permanent bound geometry. Cancel on preview dismiss, back, view detach, gesture interruption and chat transition. Verify outgoing/incoming, groups, RTL, full-sized messages and 120 Hz/144 Hz without touches delayed or double-dispatched.
- Verify compact labels/icons, accessibility hit areas (ideally >=44 dp), visual positioning with Android 17 gesture nav, dynamic fonts and long localizations. Native MORE must contain editing, selecting, copying links, reporting etc. where Telegram permits.
- Add real host/UI regression tests for quick-action permission matrix, actions exactly once, conversion admission, dismiss/cleanup, and sticker send.
- Run the full Android ARM64 build and test harness; do not infer compile or FPS from code inspection. Update Alpha review/manifest/checkpoint policy in a separate auditable step instead of pretending the PR #123 exact-HEAD hash suite covers this new source. Keep APK private and signature unchanged unless user approves a new delivery process.
- No release/beta promotion without owner physical acceptance.

## Regression / acceptance checklist
Long press message -> selected bubble receives local soft compression and bounce -> reactions retain their native position -> compact menu appears below without clipping or covering selected text -> Reply/Copy/Forward work once -> MORE exposes less common native actions -> sticker preview preserves alpha and bubble tail -> explicit Send arrives as an actual static sticker on second client -> Save remains transparent -> Back/dismiss releases preview and restores the original chat UI. Repeat with themes, gradients, wallpaper, custom bubbles, messages near screen edge and fast multitap.