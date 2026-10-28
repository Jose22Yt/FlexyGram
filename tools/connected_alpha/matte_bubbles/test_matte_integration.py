"""Static wiring checks; intentionally not an Android render/Gradle build."""
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[3]
java = root / "TMessagesProj/src/main/java"
config = (java / "app/flexygram/bubbles/BubbleConfig.java").read_text()
settings = (java / "app/flexygram/bubbles/BubbleSettingsActivity.java").read_text()
renderer = (java / "org/telegram/ui/ActionBar/MessageDrawable.java").read_text()
preview = (java / "app/flexygram/bubbles/BubblePreviewView.java").read_text()

assert 'signature_matte_enabled' in config
assert 'signature_matte_strength' in config
assert 'BubbleConfig.matteEnabled()' in settings
assert 'BubbleConfig.setMatteStrength(value)' in settings
assert 'BubbleConfig.setMatteEnabled(' in settings
assert 'position == matteStrengthRow' in settings
assert 'SignatureMatteFinish.color(' in renderer
assert 'flexyFillPaint.setShader(p.getShader())' in renderer
assert 'matteGradientFilter(app.flexygram.bubbles.BubbleConfig.matteStrength()) : null' in renderer
assert 'if (flexyMatteStrength != strength)' in renderer
assert 'BubbleConfig.backgroundBlur()' in renderer  # independent mode
assert 'bubbles[i].drawCached(canvas, caches[i])' in preview  # same painter as actual chat
for locale in ('values','values-es','values-ru'):
    file = root / f"TMessagesProj/src/main/res/{locale}/flexy_bubble_matte.xml"
    fields = {item.attrib.get('name') for item in ET.parse(file).getroot()}
    assert {'FlexyBubbleMatteEnabled','FlexyBubbleMatteStrength'} <= fields
print("Signature Matte source wiring checks passed")
