"""Current Bottom Bar product wiring; no physical/FPS claim."""
from pathlib import Path
root=Path(__file__).resolve().parents[3];java=root/'TMessagesProj/src/main/java'
bar=(java/'org/telegram/ui/MainTabsLayout.java').read_text();host=(java/'org/telegram/ui/MainTabsActivity.java').read_text()
preview=(java/'app/flexygram/navigation/LiquidNavigationPreviewView.java').read_text();settings=(java/'app/flexygram/navigation/LiquidNavigationSettingsActivity.java').read_text()
for removed in ['LiquidLensRenderer','setLiquidGlassEffectAllowed','clipPath','flexyExpansion']:assert removed not in bar
for token in ['slotWidth=inner/Math.max(1,count)','inner%Math.max(1,count)','selection.cancel()']:assert token in bar
assert 'new MainTabsLayout(' in preview and 'LiquidNavigationTabs.createPreview(' in preview
assert 'onTouchEvent(' not in preview
assert 'LiquidNavigationConfig.value(parameter,v)' in settings
assert 'LiquidNavigationTabsActivity' in settings
assert 'DIALOGS_TYPE_GROUPS_ONLY' in host and 'DIALOGS_TYPE_CHANNELS_ONLY' in host
assert 'target.setCurrentAccount(currentAccount)' in host
assert 'bringToFront()' in host
print('PASS Bottom Bar equal layout/shared preview/native routes; physical acceptance separate')
