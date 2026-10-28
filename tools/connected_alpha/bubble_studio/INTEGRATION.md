# FlexyGram Bubble Interaction 2.0 — integration workbench

Base: Alpha1281 PR116 / `a4d66fc84695f59a17a1d30ac888cd18ebcb1bba`.
This is an **incremental code branch**, NOT a claim of a finished APK or Telegram sticker delivery.

## Already written

- BubbleTapMotion: shared FlexyFrameMotion spring, scaling the bubble drawing only, no cell transforms; DOWN/UP/cancel/dispose API.
- BubbleTouchPolicy: conservative admission for native interactive children, protected/TTL/spoiler/unsupported messages.
- BubbleTapGestureState: one bounded DOWN/MOVE/UP sequence, no panel on scroll, long press or native veto.
- BubbleStickerEncoder: native bubble painter contract, exact original-pixel capture, 512px WebP encode, bounded size, private cache file.
- NativeStickerMetadata: Telegram MIME, image dimensions and TL_documentAttributeSticker + TL_inputStickerSetEmpty.
- BubbleActionPanelView: theme-aware Signature Matte, tabs Acciones / Sticker / Seleccionar, delegated actions and confirm-to-send CTA.
- BubbleInteractionSettingsActivity accessible from Chats -> Burbujas via BubbleSettingsActivity.
- Isolated pure Java tests run by workflow.

CI: `Bubble Studio isolated contracts` passed on the draft PR at checkpoint `4c046fe`; later commits must revalidate. This is **not** an Android APK, message render, or sticker send check.

## Native integration required for a user-visible feature

**The repository connector does not return the full body of giant ChatMessageCell.java / ChatActivity.java files.**
Do not edit them by guess or replace them with truncated versions.

1. In ChatMessageCell's *existing* hit-test path, call BubbleTouchPolicy.mayAnimate only for a valid bubble interior and not for links, buttons, embedded controls, gestures or action mode. On eligible original DOWN initialize BubbleTapGestureState.down() and call BubbleTapMotion.down(); on MOVE crossing native touchSlop cancel; on long press call gesture.longPress(); on actual UP/CANCEL call BubbleTapMotion.up()/cancel(). Only an accepted native single-tap may open the optional Signature panel. Never fabricate events. Host MUST call reset and dispose when cell is rebound/detached; do not retain MessageObject.
2. Apply BubbleTapMotion.saveBubble(canvas, actualBubbleRect) and restoreBubble(canvas,saved) surrounding ONLY the native message background/content draw operations, not the whole RecyclerView cell or click targets. If native draw order makes this impossible, use a safe transform at the smallest paint boundary. Test baseline and extreme multitap on hardware.
3. In native message context menu, render BubbleActionPanelView only after the existing permission checks and opt-in. Bind each Action to the actual Telegram handler, preserving reply/edit/copy/forward/pin/delete/select behavior and original restrictions. Native long press must still work. Single tap may animate without opening a menu; no forced long-press side effects.
4. After selecting the Sticker tab, use BubbleTouchPolicy.mayConvertToSticker with **actual** message permission/TTL/hidden flags and peer sending restrictions. The NativeBubblePainter must render only the already visible original message bubble (including original style/tail/text and permitted media, not the wallpaper or surrounding content). Never decode protected/hidden media.
5. Capture bitmap on UI only; encode on a worker, then return to UI for preview. Enforce a small queue, generation tokens, cancel stale results, delete failed/unused cache files. Sticker byte size must be <=512 KiB. Reject unreadably long multi-line bubbles rather than silently clipping original message.
6. On explicit **Enviar aquí** click, hand the `.webp` to the **real native sticker-upload/send path**. A file path or a TL_document built in memory is NOT YET a server-side sticker. Preserve selected dialog/thread/reply and actual account. After upload, confirm the returned document has image/webp + documentAttributeSticker and Telegram renders it in the sticker UI (no photo/document wrapper). Reject if transport treats it as document/photo. Clean up temporary file after native upload/cancel.
7. On a second real Telegram client verify native sticker semantics, forward and save-to-stickers when server supports it. Test content protected, spoiler, TTL, bot/channel read-only, media-only, custom emoji and accessibility cases. Do not claim completion without this test.
8. Localize Spanish UI labels with resource strings and accessibility descriptions. Existing temporary labels match the approved layout but are NOT the localization finish.
9. Run Gradle source verification, compile ARM64 privately with existing certificate, performance traces, and tests on API37 as well as lower-end hardware.

Do not merge Work2 PR114 or change Flexy Motion Engine/global Android animation scales while completing this independent feature. Keep unverified options off by default.

## Critical acceptance bar

- Single tap on eligible message: compression begins on the same input, then returns to 1x with spring (Flash instant).
- No scrolling, link, voice-playback, selection, clipboard, menu, preview or native long-press regression.
- Contextual panel appears only if enabled; never opens destructive actions by default.
- Conversion preserves source bubble silhouette and content; no screenshot of entire chat.
- **Transport and receiving client recognize actual Telegram STICKER**, not a JPEG, PNG, standalone WebP document or photo.
- No crashes, duplicate sends, ghost touch, leaks or FPS regression.
