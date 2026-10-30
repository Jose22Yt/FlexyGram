"""Current Bottom Bar product wiring; no physical/FPS claim."""
from pathlib import Path
root=Path(__file__).resolve().parents[3];java=root/'TMessagesProj/src/main/java'
bar=(java/'org/telegram/ui/MainTabsLayout.java').read_text();host=(java/'org/telegram/ui/MainTabsActivity.java').read_text()
profile=(java/'app/flexygram/navigation/LiquidNavigationConfig.java').read_text()
for removed in ['LiquidLensRenderer','setLiquidGlassEffectAllowed','clipPath','flexyExpansion']:assert removed not in bar
for token in ['slotWidth=inner/Math.max(1,count)','inner%Math.max(1,count)','selection.cancel()']:assert token in bar
for retired in ['LiquidNavigationPreviewView','LiquidNavigationSettingsActivity','LiquidNavigationTabsActivity']:
    assert not (java/'app/flexygram/navigation'/str(retired+'.java')).exists()
for screen in ['OpenExteraAppearanceActivity','OpenExteraAppNavigationActivity']:
    assert 'LiquidNavigationSettingsActivity' not in (java/'app/exteraless/settings'/str(screen+'.java')).read_text()
assert 'return LiquidNavigationDestinations.defaults()' in profile
assert 'return 60' in profile and 'edit.remove(key)' in profile and '.clear()' not in profile
for read in ['p.getInt(', 'p.getString(']:assert read not in profile
assert 'DIALOGS_TYPE_GROUPS_ONLY' in host and 'DIALOGS_TYPE_CHANNELS_ONLY' in host
assert 'target.setCurrentAccount(currentAccount)' in host
assert 'bringToFront()' in host
print('PASS Bottom Bar fixed profile/equal layout/native routes; physical acceptance separate')
