"""Static routing invariants only: a real Android compile/touch device remains required."""
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[3]
j=root/"TMessagesProj/src/main/java"
tab=(j/"org/telegram/ui/MainTabsLayout.java").read_text()
activity=(j/"org/telegram/ui/MainTabsActivity.java").read_text()
appearance=(j/"app/exteraless/settings/OpenExteraAppearanceActivity.java").read_text()
page=(j/"app/flexygram/navigation/LiquidNavigationSettingsActivity.java").read_text()
preview=(j/"app/flexygram/navigation/LiquidNavigationPreviewView.java").read_text()
config=(j/"app/flexygram/navigation/LiquidNavigationConfig.java").read_text()
assert "private void flexyBeginDrag(float x)" in tab
assert "private void flexyMoveDrag(float x)" in tab
assert "private void flexyFinishDrag(boolean cancelled)" in tab
assert "onInterceptTouchEvent(MotionEvent ev)" in tab
assert "Math.abs(dx) > flexyTouchSlop" in tab
assert "target.performClick()" in tab
assert "flexyDragging" in tab and "LiquidNavigationMath.width(rawWidth, flexyStretch)" in tab
assert "selectedTabPositionX.animateToFinalPosition(center)" in tab
assert "MainTabsUiHelper.isIosNavigationBar()" in tab
assert "return super.dispatchTouchEvent(ev);" in tab
assert 'addRow("flexyLiquidNavigation")' in appearance
assert "new app.flexygram.navigation.LiquidNavigationSettingsActivity()" in appearance
assert "LiquidNavigationPreviewView" in page
assert "LiquidNavigationConfig.opacity(value)" in page
assert "LiquidNavigationConfig.elasticity(value)" in page
assert "getMainTabsHideContacts()" in page and "getMainTabsHideProfile()" in page
assert "setShowCallsTab" in page and "feedTabVisibleToggled" in page
assert "current = Math.min(current, count - 1);" in preview
assert "if (AppearanceConfig.showFeedTab())" in preview
assert "private static final String NAME" in config
assert "TABS_COUNT = 4" in activity, "Do not invent fragment pages in this iteration"
for locale in ("values","values-es","values-ru"):
    xml=root/f"TMessagesProj/src/main/res/{locale}/flexy_liquid_navigation.xml"
    names={x.attrib.get("name") for x in ET.parse(xml).getroot()}
    assert {"FlexyLiquidNavTitle","FlexyLiquidNavEnabled","FlexyLiquidNavElasticity",
        "FlexyLiquidNavOpacity","FlexyLiquidNavPreview","FlexyLiquidNavContacts","FlexyLiquidNavProfile"} <= names
print("Liquid Navigation source wiring verified (not a device test)")
