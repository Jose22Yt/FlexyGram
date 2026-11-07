# Conversation controls

## Changes

- `ChatActivity`: preserve the custom header's full touch width when resuming,
  applying Studio settings and entering preview mode. The previous 52dp right
  margin put controls outside their parent's touch bounds.
- `ConversationControlIcons`, composer controls and header previews: decode the
  packaged vectors directly so optional icon packs cannot substitute a call
  glyph for the overflow menu. Retain decoded composer drawables between updates.
- `FlexyComposerConfig`: restore the reference clip/sticker/microphone selection
  once. Later explicit selections and imported settings remain respected.
- `HeaderConfig` and `SignatureChatHeader`: restore the integrated back counter
  once and retain its pill at zero unread chats. Cache unchanged counter text,
  including the capped `99+` display.
- Message action panels: use the shared selection blur and its translucent scrim
  tint, independently of the persistent chat-surface blur preference. Device blur
  capability restrictions remain in effect.

## Verification

- Maintained Python/JVM suite: 349 passed, 33 skipped.
- Regression coverage includes resumed/imported header touch bounds at several
  widths, densities and layout directions, one-time setting repairs, imported
  choices, vector decoding and stable counter layout reuse.
- Decoder compiled against Android SDK 37; main resources compiled with AAPT2.
- Java syntax parsing and `git diff --check` passed.
- No APK was assembled or signed for this change. Device interaction, contrast
  with different wallpapers and visual blur quality still require verification.

## Device checks

1. Open a chat, leave it and reopen it. Back, call and overflow must each activate
   their own action. Repeat after applying Studio header settings.
2. Check zero, one and more than 99 unread chats. The integrated back pill must
   remain visible; explicit later counter settings must be preserved.
3. Select the compact composer and check clip, sticker and microphone with each
   optional global icon pack, light/dark themes and an imported configuration.
4. Open and dismiss message action panels with supported blur enabled, then with
   reduced-capability settings. Confirm text contrast and selection cleanup.
