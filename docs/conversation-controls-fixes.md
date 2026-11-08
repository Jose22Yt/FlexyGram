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
- While the custom header owns the action buttons, exclude the overlapping native
  menu from drawing, touch dispatch and accessibility. Native search/action modes
  retain their controls, and custom buttons still invoke the original actions.
- Anchor overflow popups to the actual custom button, without adding coordinates
  from the hidden native menu. Mirror popup alignment for right-to-left layouts.
- Dismiss message selection from its preview placeholder, unhandled viewport
  touches and outside events. Consume the dismissal gesture; retain normal menu
  button and scrolling gestures and the existing single-owner return animation.
- Both smile/sticker entry states use the selected circular curved-fold glyph
  with reference icons enabled; keyboard and recording states keep their meaning.
- Restore the original clip, microphone and curved-fold resource files from
  `6342e1d46`, instead of the subsequently substituted smiley artwork. Load the
  packaged native handset and overflow bitmaps without global icon substitution;
  restore the original back-chevron stroke and keep previews consistent.
- Keep active header controls visible through measurement. Temporarily hiding
  them before every measure cancelled pending Android clicks, including the
  overflow popup and call action. Only the inactive branch now hides them.

## Verification

- Maintained Python/JVM suite: 355 passed, 33 skipped.
- Regression coverage includes resumed/imported header touch bounds at several
  widths, densities and layout directions, one-time setting repairs, imported
  choices, vector decoding and stable counter layout reuse.
- Touch regression tests execute native-menu exclusion, external anchor alignment
  in both layout directions and preview dismissal without consuming menu gestures.
- `MessageMenuViewport` also compiles against the real Android SDK 37.
- Android touch regression: the old measure entry failed both popup/call tests;
  the corrected entry passes all three native tests. The probe uses real Android
  views and PopupWindow, with explicit geometry/navigation fixtures, rather than
  counting synthetic callback invocations alone. Maven is a CI test tool; no
  application dependency was added.
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
5. Tap beside the selected bubble and in empty preview areas. The menu must close
   without activating a message or control underneath. Repeat during entry and
   return animations; action buttons and scrolling inside the menu must still work.
