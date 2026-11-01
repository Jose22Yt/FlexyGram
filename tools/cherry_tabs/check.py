#!/usr/bin/env python3
"""Focused source integration checks (not a substitute for Android compilation)."""
from pathlib import Path

root = Path(__file__).resolve().parents[2] / "TMessagesProj/src/main/java"
settings = (root / "app/flexygram/navigation/BottomTabsSettingsActivity.java").read_text()
config = (root / "app/flexygram/navigation/LiquidNavigationConfig.java").read_text()
host = (root / "org/telegram/ui/MainTabsActivity.java").read_text()
glass = (root / "org/telegram/ui/Components/glass/GlassTabView.java").read_text()

checks = {
    "real native tab views in editor": "LiquidNavigationTabs.createPreview(getContext(), id)" in settings,
    "six slots in editor": "i < currentDestinations.size(); i++) {\n                    addEditableTab" in settings,
    "draggable editor": "MotionEvent.ACTION_MOVE" in settings and "Math.round(delta /" in settings,
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
