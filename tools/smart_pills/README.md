# FlexyGram Smart Mini Pills v2 — Work 1 handoff

This branch **extends** SignatureSmartPreviews; it does not add a parallel chat-list renderer.

## Already implemented
- Pure local filename/MIME classifier for PDF, TXT, ZIP, RAR, 7Z, APK, PNG, JPG, WEBP, GIF, MP3/FLAC, videos, DOCX, XLSX, PPTX and generic files.
- Service messages: joined, left, pinned; native media: image, video, audio, voice, sticker, poll, contact, location; standalone URL, channel post and edited text when reliably indicated.
- Existing four theme modes remain: Adaptive / Theme / Matte / Off.
- An **inline ReplacementSpan** draws exactly the pixels reserved for the colored capsule. The filename or preview text is outside this colored rect and ellipsizes independently; dialog row geometry, clocks and click areas remain untouched.
- Guard margin in SignatureSmartPillLayout, one-line content sanitization, spoiler/TTL/restriction checks and fallback to native on narrow rows.
- EN/ES captions. No file reads, downloads, network requests or per-frame bitmap work.

## Deliberate limitations — Work 1 must verify before acceptance
- The current renderer prioritizes **one pill per chat row**. Two pills (e.g. ADMIN + PDF) require verified participant roles, priority policy and real width testing, not guesses.
- Never label a sender ADMIN/OWNER from a channel post alone. The role hook in SignatureMiniPillClassifier accepts only locally confirmed rights; integrate it only where a reliable cached participant record exists.
- A filename ending in .jpg or .png does not prove WALLPAPER intent. Leave it PNG/JPG unless Telegram has explicit wallpaper media metadata.
- Deleted-message badges require explicit AyuGram deletion metadata in the compatible Full variant. Never claim deleted based on absent messages or reveal content not stored.
- Existing native multi-message albums, special rows, protected/spoiler content, highlighted searches, drafts and typing events keep native fallback.
- Run the Android ARM64 compile, ES/EN tests, sent/received media + sender-prefix + thumbnail + RTL + large text + narrow screen + recycled row + theme-switch + scroll tests on actual Android.

## Host checks
From repo root:
```sh
mkdir -p /tmp/flexy-pills-test
javac -d /tmp/flexy-pills-test \
 TMessagesProj/src/main/java/app/flexygram/home/SignatureSmartPreviewPalette.java \
 TMessagesProj/src/main/java/app/flexygram/home/SignatureMiniPillClassifier.java \
 TMessagesProj/src/main/java/app/flexygram/home/SignatureSmartPillLayout.java \
 tools/smart_pills/SmartPillHostTest.java
java -cp /tmp/flexy-pills-test SmartPillHostTest
```

**No APK, phone validation or completed admin/deleted integration is claimed.** Draft only.
