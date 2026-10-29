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
parent = (java / "org/telegram/ui/Components/chat/ChatInputViewsContainer.java").read_text()
host = (java / "org/telegram/ui/ChatActivity.java").read_text()
assert "actionBar.setupGlass(" in host
assert "glassBackgroundDrawableFactory," in host
assert "chatActivityEnterView.shouldDrawBackground = false" in host
assert "LiteMode.FLAG_LIQUID_GLASS" in composer
assert "SharedConfig.chatBlurEnabled()" in composer
assert "setFlexyNativeGlassBackdropDrawn(false)" in parent
assert "flexyComposer.flexyNativeGlassIslandsAvailable()" in parent
start = parent.index("private void drawFlexyNativeGlassIslands(")
end = parent.index("private void drawFlexyCompactBackground(", start)
compositor = parent[start:end]
assert compositor.count("blurredBackgroundDrawable.draw(canvas)") == 1
assert compositor.count("addRoundRect(") == 4
assert "canvas.clipPath(flexyMask)" in compositor
assert "setFlexyNativeGlassBackdropDrawn(true)" in compositor
for bound in ["getFlexyTextPillBounds", "getFlexyAttachmentBounds", "getFlexyVoiceBounds", "getFlexySendBounds"]:
    assert bound in parent
assert "sizeNotifierLayout.drawBlurRect(canvas, getTop(), flexyNativeGlassBounds" not in composer
assert "final boolean flexyIslands = flexyNativeGlassBackdropDrawn" in composer
assert "if (withComposeShadowDrawable && !flexyIslands)" in composer
assert "if (nativeGlass)" in parent
assert "flexyLastPill.setEmpty()" in compositor
assert "nativeGlassTint" in style and "nativeGlassButton" in style
assert "getThemedColor(Theme.key_chat_messagePanelBackground)" in composer
assert "FlexyComposerConfig.glass()" in composer, "Do not remove prior independent settings"
assert "new Bitmap(" not in composer, "Do not allocate extra bitmap in the composer"
print("Native conversation Liquid Glass scoped source contracts passed")

assert "updateSignatureNativeGlassPolicy(allowed)" in host
assert "updateNativeLiquidGlassPolicy(allowed)" in host
assert "LiteMode.addOnPowerSaverAppliedListener(signatureGlassPowerListener)" in host
assert "LiteMode.removeOnPowerSaverAppliedListener(signatureGlassPowerListener)" in host
assert "glassBackgroundSourceRenderNode!=null" in host
renderer=(java/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawableRenderNode.java').read_text()
assert "setLiquidGlassEffectAllowed(boolean allowed)" in renderer
assert "renderNodeFill.setRenderEffect(null)" in renderer
assert "allowed == (liquidGlassEffect != null)" in renderer

assert "signatureGlassFactory.create(this)" in header
assert "signatureGlassCall.draw(canvas)" in header
assert "bar.prepareSignatureNativeGlass(g.mattePortrait && g.callAvailable)" in adapter
assert "updateSignatureNativeGlassDrawable(signatureGlassCall,allowed)" in header

start=header.index("public boolean drawSignatureNativeGlass(")
end=header.index("private int centeredTitleAvailableWidth(",start)
assert ".setRadius(" not in header[start:end], "Do not rebuild native radius/stroke paths on every frame"
assert "if(signatureGlassRadius==radius)return" in header
assert "int padding=signature ? 0 : dp(6)" in header
assert "configureSignatureGlassGeometry(signature)" in header
