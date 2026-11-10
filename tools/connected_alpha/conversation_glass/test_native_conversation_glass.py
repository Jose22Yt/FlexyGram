"""Scoped source contracts; not an Android compile, GPU test, or FPS measurement."""
from pathlib import Path

root = Path(__file__).resolve().parents[3]
java = root / 'TMessagesProj/src/main/java'


def method(source, anchor):
    start = source.index(anchor)
    pos = source.index('{', start)+1
    depth = 1
    while depth:
        depth += (source[pos] == '{')-(source[pos] == '}')
        pos += 1
    return source[start:pos]


lite = (java/'org/telegram/messenger/LiteMode.java').read_text()
header = (java/'org/telegram/ui/ActionBar/ActionBar.java').read_text()
adapter = (java/'app/flexygram/header/SignatureChatHeader.java').read_text()
composer = (java/'org/telegram/ui/Components/ChatActivityEnterView.java').read_text()
parent = (java/'org/telegram/ui/Components/chat/ChatInputViewsContainer.java').read_text()
host = (java/'org/telegram/ui/ChatActivity.java').read_text()
renderer = (java/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawableRenderNode.java').read_text()

assert 'FLAG_LIQUID_GLASS = 1 << 18' in lite
assert 'LiteMode.FLAG_LIQUID_GLASS' in method(host, 'private void refreshSignatureNativeGlassPolicy()')
assert 'actionBar.updateSignatureNativeGlassPolicy(liquidPolicy)' in host
assert 'chatInputViewsContainer.updateNativeLiquidGlassPolicy(liquidPolicy)' in host
assert 'LiteMode.addOnPowerSaverAppliedListener(signatureGlassPowerListener)' in host
assert 'LiteMode.removeOnPowerSaverAppliedListener(signatureGlassPowerListener)' in host
assert 'actionBar.setupGlass(\n            glassBackgroundDrawableFactory,' in host
assert 'chatInputViewsContainer.setCompactGlassFactory(glassBackgroundDrawableFactory, blurredBackgroundColorProvider)' in host

native_header = method(header, 'public boolean drawSignatureNativeGlass(')
for role in ['glassDrawableBack','glassDrawable','glassDrawableMenu','signatureGlassCall']:
    assert role+'.draw(canvas)' in native_header
assert 'nativeGlassDrawn = bar.drawSignatureNativeGlass(canvas, this)' in adapter
assert 'if (!fusionActive() || nativeGlassDrawn) return;' in adapter
assert 'renderNodeFill.setRenderEffect(null)' in renderer
assert 'allowed == (liquidGlassEffect != null)' in renderer

islands = method(parent, 'private void drawFlexyNativeGlassIslands(')
assert islands.count('drawCompactGlass(canvas,') == 4
assert 'drawFlexyComposerTint' not in parent
assert 'canvas.drawRoundRect' not in islands
assert 'flexyNativeGlassDrawn = true' in islands
assert 'flexyLastPill.setEmpty()' in islands
compact = method(parent, 'private void drawFlexyCompactBackground(')
assert 'canvas.isHardwareAccelerated()' in compact
assert 'flexyComposer.flexyNativeGlassIslandsAvailable()' in compact
assert compact.index('drawFlexyNativeGlassIslands(') < compact.index('if (flexyPearlGlass')
assert 'ComposerStyle.surface(' in compact
assert 'if (compactGlassRadius[index] != radius)' in parent

policy = method(parent, 'public void updateNativeLiquidGlassPolicy(')
assert 'for (BlurredBackgroundDrawable drawable : compactGlass)' in policy
assert 'flexyComposer.invalidateNativeGlassColors()' in policy
handoff = method(parent[parent.index('/* Render */'):], 'protected void dispatchDraw(')
assert handoff.index('setFlexyNativeGlassBackdropDrawn(flexyNativeGlassDrawn)') < handoff.index('super.dispatchDraw(canvas)')
assert 'setFlexyNativeGlassBackdropDrawn(previousNative)' in handoff
assert 'if (withComposeShadowDrawable && !flexyIslands)' in composer
assert 'if (!flexyVoiceBackdropDrawn) canvas.drawRoundRect' in composer
assert 'if (isNewDesignSendButton && !compactBackdropDrawn)' in composer
assert 'FlexyComposerConfig.glass()' in composer
assert 'new Bitmap(' not in islands
print('Native conversation glass source contracts passed (no GPU/FPS assertion).')
