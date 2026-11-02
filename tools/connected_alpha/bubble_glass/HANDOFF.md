# FlexyGram — Bubble-only Glass (Work 1 integration handoff)

## Decision / source checkpoint
- Owner decision: **retire the Matte effect from chat bubbles**. Matte surfaces elsewhere (header, contextual cards, settings) stay intact.
- This independent review branch starts from **PR #123** (`e00b33e806921017ad74ff50eb5ec88607131d9c`). It is **not merged, not compiled, and no APK is claimed**.
- PR #124 (compact message context menu) is a separate sibling of the same base; do not blindly overwrite or duplicate its work. Merge or rebase only after conflict review.

## Implemented changes
- `BubbleConfig`: saved legacy `signature_matte_enabled` and `signature_matte_strength` are no longer read; `matteEnabled()` always returns false for renderer compatibility. No color desaturation can run, even for users who saved Matte=ON. Matte preference API is inert for old callers; do not delete it without updating the renderer.
- **Chats → Burbujas**: remove Matte switch/slider. Replace old wallpaper-blur toggle label with **Glass en las burbujas**, plus a new **Intensidad del Glass** slider (0–100%, default70, persisted in `signature_glass_intensity`). Existing tint transparency, per-theme colors, outlines, contour/tail controls and live preview remain. OFF by default for existing blur-OFF installs.
- `BubbleGlassPolicy`: pure, bounded alpha policy. `SignatureWallpaperBlur.Owner.draw()` uses that intensity to blend the **previously cached blurred wallpaper** within the actual native bubble path. No new per-message bitmap/capture, no per-frame blur kernel, no glass overlay over the header or whole chat. Alpha from the native transition is retained. This is **intensity/opacity of blurred backing**, **not** a variable blur radius.
- Reuse the existing shared 2-entry 384px cache, wallpaper snapshots for native/static/gradient/frozen motion sources, and safe fallback for unsupported animated/video sources. Preserve native `MessageDrawable` shape/tail/gradient/reaction/text and original theme bubble colors.
- ES/EN/RU resource strings and updated isolated alpha/source contracts in the existing historical CI job (renamed display name to Bubble Glass).

## Important constraints / pending Work 1 engineering
1. **Do not claim an exact iOS 27 pixel match** without screenshot comparisons. The current Glass is the already-existing local wallpaper blur rendered inside the bubble silhouette, now user-controllable via strength. It does not sample messages or arbitrary view content behind the bubble and does not blur the entire chat compositing stack; that is intentional for privacy, battery and performance.
2. **Native renderer cleanup remains**: the `MessageDrawable` file was too large for the connector's line fetch. The old Matte conditional is left compiled but unreachable because `BubbleConfig.matteEnabled()` is always false. Work 1 should remove that dead color/gradient-filter block **only after** a full source fetch and exact integration audit; never change native gradient opacity or break existing popups. Do not bring back `SignatureMatteFinish` into active bubble rendering. Old Matte locale XML/test class are legacy inert files; remove them in an auditable cleanup if all references are checked.
3. Verify whether users with previous blur ON retain the intended Glass ON state (same `signature_cached_blur` key) and ensure no disabled settings rows are left stale on first visit.
4. If Glass is not visible when color tint transparency is low, explain the existing transparency slider relationship rather than secretly recoloring the theme or overriding user alpha.
5. On theme/wallpaper changes and per-chat backgrounds, verify mapping, gradients, tiled images, parallax and owner invalidation. Animated wallpapers may use a cached frozen frame; video may fall back to the native translucent bubble. No screenshot/grab of message contents.
6. Verify theme light/dark, RTL, outgoing/incoming, message grouping, BubbleStickerEncoder conversion, 90% transparency, border 0.5–2dp, and accessibility/contrast.
7. Run Gradle ARM64 full CI and real Poco X8 Pro/Android17 hardware tests with frame stats/scroll 60–144Hz, multi-tap and 20–50-screen chat scroll. The source-only math/contract tests do not prove device performance.
8. Keep PR #123 / #124 sticker and native action permissions, app signature, credentials, native animations and login unchanged.

## Acceptance cases
- OFF: exactly native translucent/tinted bubbles, with Glass/Matte off; no painter changes outside bubbles.
- ON: one cached wallpaper source, blur appears inside the **actual bubble silhouette and tail**; original bubble colors, text, checks, reactions and outline intact. Intensity 0/50/70/100 changes blur backing blend without new kernel render.
- Matte previously ON + Glass OFF: Matte never reappears, even across process restart.
- Wallpapers: default, solid, native gradients, tiled, chat-specific static, motion frozen fallback; contrast and theme changes preserve all interactions.
- Settings preview matches on-device bubble output for opacity, native geometry and caching.
- Work 1 may optimize/change implementation, but it must preserve the user-approved design and explain any changed behavior before APK acceptance.
