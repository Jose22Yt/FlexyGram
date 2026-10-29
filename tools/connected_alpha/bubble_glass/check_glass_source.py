"""Glass-only bubble source contracts; static checks, NOT an Android pixel/Gradle test."""
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[3]
java = root / "TMessagesProj/src/main/java"
config = (java / "app/flexygram/bubbles/BubbleConfig.java").read_text()
settings = (java / "app/flexygram/bubbles/BubbleSettingsActivity.java").read_text()
blur = (java / "app/flexygram/bubbles/SignatureWallpaperBlur.java").read_text()
renderer = (java / "org/telegram/ui/ActionBar/MessageDrawable.java").read_text()
preview = (java / "app/flexygram/bubbles/BubblePreviewView.java").read_text()

# Retired matte preferences may stay on disk; never read/activate or expose to UI.
assert '@Deprecated public static boolean matteEnabled() { return false; }' in config
assert "signature_matte_enabled" not in config
assert "setMatteEnabled" not in settings
assert "matteRow" not in settings
assert "FlexyBubbleMatteStrength" not in settings
assert "matteStrengthRow" not in settings

# The native message geometry/tails and original Telegram theme color remain authoritative.
assert "BubbleConfig.backgroundBlur(isOut)" in renderer
assert "flexyGlassSource.draw(canvas, path, alpha)" in renderer
assert "flexyFillPaint.setShader(p.getShader())" in renderer
assert "bubbles[i].drawCached(canvas, caches[i])" in preview
assert "bubble.setFlexyGlassSource(cachedWallpaper)" in preview

# Actual prior wallpaper blur snapshot/cache/kernel is reused; only alpha blend changes.
assert "private static final int MAX_ENTRIES = 2, MAX_EDGE = 384" in blur
assert "canvas.drawPath(shape, paint)" in blur
assert "BubbleGlassPolicy.opacity(alpha, BubbleConfig.glassIntensity())" in blur
assert "public static boolean bubbleGlassEnabled()" in config
assert 'signature_glass_intensity' in config
assert 'signature_cached_blur' in config
assert "glassStrengthRow" in settings
assert "BubbleConfig.setGlassIntensity(value)" in settings
assert "BubbleConfig.setBubbleGlassEnabled" in settings

# Only new user-visible bubble controls, not Matte, in all locales.
for locale in ("values", "values-es", "values-ru"):
    file = root / f"TMessagesProj/src/main/res/{locale}/flexy_bubble_glass.xml"
    fields = {item.attrib.get("name") for item in ET.parse(file).getroot()}
    assert {"FlexyBubbleGlassEnabled", "FlexyBubbleGlassStrength"} <= fields

print("Bubble-only Glass source wiring checks passed")
