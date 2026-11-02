#!/usr/bin/env python3
"""Focused source integration checks (not a substitute for Android compilation)."""
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[2] / "TMessagesProj/src/main/java"
settings = (root / "app/flexygram/navigation/BottomTabsSettingsActivity.java").read_text()
config = (root / "app/flexygram/navigation/LiquidNavigationConfig.java").read_text()
host = (root / "org/telegram/ui/MainTabsActivity.java").read_text()
glass = (root / "org/telegram/ui/Components/glass/GlassTabView.java").read_text()

checks = {
    "real native tab views in editor": "LiquidNavigationTabs.createPreview(getContext(), id)" in settings,
    "six slots in editor": "i < currentDestinations.size(); i++) {\n                    addEditableTab" in settings,
    "draggable editor": "MotionEvent.ACTION_MOVE" in settings and "Math.round(" in settings and "LocaleController.isRTL" in settings,
    "hide internal overflow": "LiquidNavigationDestinations.isSelectable(id)" in settings,
    "reset available": "setOrder(LiquidNavigationDestinations.defaults())" in settings,
    "live order change": 'putString("tab_order", sb.toString()).apply();\n        notifyChanged();' in config,
    "live show change": 'putBoolean("show_tabs", value).apply();\n        notifyChanged();' in config,
    "registered lifecycle": "addChangeListener(flexyTabConfigListener)" in host and "removeChangeListener(flexyTabConfigListener)" in host,
    "overflow only enabled tabs": "contains(flexyConfiguredDestinations,destination)" in host,
    "search behavior": "LiquidNavigationConfig.alwaysSearchChats()" in host,
    "native search glyph": "NAV_SEARCH(TabAnimationType.STATIC" in glass,
}
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + " " + name)
assert all(checks.values())


resources = Path(__file__).resolve().parents[2] / "TMessagesProj/src/main/res"
needed = {
    "FlexyTabsPreviewHint", "FlexyTabsAvailable", "FlexyTabsOff", "FlexyTabsLimit",
    "FlexyTabsRestore", "FlexyTabsRestoreSub", "FlexyTabsConfigure",
    "FlexyTabsMovePrevious", "FlexyTabsMoveNext", "FlexyTabsRemove",
    "FlexyTabsAdd", "FlexyTabsAddTitle", "FlexyTabsAddPrefix",
}
for locale in ("values", "values-es", "values-ru"):
    tree = ET.parse(resources / locale / "flexygram_navigation.xml")
    strings = [v.attrib["name"] for v in tree.getroot() if v.tag == "string"]
    assert len(strings) == len(set(strings)), locale + ": duplicated resource names"
    assert needed <= set(strings), locale + ": missing translated resource keys"
    print("PASS " + locale + " resource coverage")
