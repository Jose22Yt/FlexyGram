"""Scoped source contracts; not a Gradle compile, visual pixel test, or FPS measurement."""
from pathlib import Path

root = Path(__file__).resolve().parents[3]
java = root / "TMessagesProj/src/main/java"
lite = (java / "org/telegram/messenger/LiteMode.java").read_text()
header = (java / "org/telegram/ui/ActionBar/ActionBar.java").read_text()
adapter = (java / "app/flexygram/header/SignatureChatHeader.java").read_text()
composer = (java / "org/telegram/ui/Components/ChatActivityEnterView.java").read_text()
style = (java / "app/flexygram/composer/ComposerStyle.java").read_text()

assert "FLAG_LIQUID_GLASS = 1 << 18" in lite
assert "public boolean drawSignatureNativeGlass(Canvas canvas" in header
assert "LiteMode.FLAG_LIQUID_GLASS" in header, "Native top glass must obey Telegram LiteMode"
assert "glassMode" in header and "glassDrawable.draw(canvas)" in header
assert "glassDrawableBack.draw(canvas)" in header
assert "glassDrawableMenu.draw(canvas)" in header
assert "if (bar.drawSignatureNativeGlass(canvas, this)) return;" in adapter
assert "surface.draw(canvas, geometry" in adapter, "OFF must retain existing header rendering"
assert "fusion.surface.drawBackdrop" in adapter, "OFF must retain portrait/fusion rendering"
assert "void drawFlexyNativeGlassIslands(Canvas canvas)" in composer
assert "LiteMode.FLAG_LIQUID_GLASS" in composer, "Bottom glass must obey same native flag"
assert "SharedConfig.chatBlurEnabled()" in composer
assert "sizeNotifierLayout.drawBlurRect(canvas, getTop(), flexyNativeGlassBounds" in composer
assert "drawFlexyNativeGlassIsland(canvas, flexyNativeGlassShape)" in composer
assert "getFlexyAttachmentBounds(flexyNativeGlassShape)" in composer
assert "getFlexyTextPillBounds(flexyNativeGlassShape)" in composer
assert "getFlexyVoiceBounds(flexyNativeGlassShape)" in composer
assert "getFlexySendBounds(flexyNativeGlassShape)" in composer
assert "if (flexyIslands) {" in composer
assert "drawFlexyNativeGlassIslands(canvas);\n            return;" in composer, "The opaque native full-width bar must be skipped when islands are active"
assert "if (withComposeShadowDrawable && !flexyIslands)" in composer, "No solid shadow band behind islands"
assert "isFlexyCompactPresentation()" in composer, "Native special states must bypass new UI"
assert "setFlexyVoiceBackdropDrawn(false)" in composer, "Native fallback must restore voice"
assert "flexyNativeGlassClip.rewind();" in composer
assert "private final Path flexyNativeGlassClip = new Path();" in composer
assert "nativeGlassTint" in style and "nativeGlassButton" in style
assert "getThemedColor(Theme.key_chat_messagePanelBackground)" in composer
assert "FlexyComposerConfig.glass()" in composer, "Do not remove prior independent settings"
assert "new Bitmap(" not in composer, "Do not allocate extra bitmap in the composer"
print("Native conversation Liquid Glass scoped source contracts passed")
