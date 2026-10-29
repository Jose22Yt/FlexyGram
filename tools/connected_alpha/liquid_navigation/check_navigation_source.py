"""Product routing/source controls, not a device rendering or FPS claim."""
from pathlib import Path
root=Path(__file__).resolve().parents[3];java=root/'TMessagesProj/src/main/java'
bar=(java/'org/telegram/ui/MainTabsLayout.java').read_text()
host=(java/'org/telegram/ui/MainTabsActivity.java').read_text()
preview=(java/'app/flexygram/navigation/LiquidNavigationPreviewView.java').read_text()
settings=(java/'app/flexygram/navigation/LiquidNavigationSettingsActivity.java').read_text()
config=(java/'app/flexygram/navigation/LiquidNavigationConfig.java').read_text()
for token in ['private void flexyBeginDrag(', 'private void flexyMoveDrag(', 'private void flexyFinishDrag(', 'target.performClick()', 'onDetachedFromWindow()', 'flexyDeformation.cancel()', 'flexyPointerId', 'MotionEvent.ACTION_CANCEL']:
 assert token in bar,token
assert 'new MainTabsLayout(' in preview and 'LiquidNavigationTabs.create(' in preview
assert 'onTouchEvent(' not in preview
for key in ['OPACITY','ELASTICITY','DEFORMATION','SPEED','DAMPING','REBOUND','FOLLOW','SETTLE','HEIGHT','COMPACT','SPACING','ICON','WIDTH']:
 assert key in config and key in settings,key
assert 'LiquidNavigationConfig.value(parameter,v)' in settings
assert 'LiquidNavigationTabsActivity' in settings
assert 'DIALOGS_TYPE_GROUPS_ONLY' in host and 'DIALOGS_TYPE_CHANNELS_ONLY' in host
assert 'TABS_COUNT = 4' in host
assert 'target.setCurrentAccount(currentAccount)' in host
assert 'bringToFront()' in host
assert 'AndroidUtilities.runOnUIThread(restoreDrawSelector, 370)' not in bar
print('PASS real destination routing and shared native-bar source contracts; physical acceptance separate')
