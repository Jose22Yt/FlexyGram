"""Source-only check. Full Android compilation and physical input tests remain necessary."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
base=ROOT/'TMessagesProj/src/main/java'
nav=(base/'org/telegram/ui/ActionBar/ActionBarLayout.java').read_text()
policy=(base/'app/flexygram/navigation/NativeInstantTouchPolicy.java').read_text()
hit=(base/'app/flexygram/navigation/NativeInstantTouchTarget.java').read_text()
assert 'nativeInstantTouchDown' in nav
assert 'NativeInstantTouchPolicy.canFinishNativeCloseForDown' in nav
assert 'NativeInstantTouchTarget.isVisibleDialogRow' in nav
assert nav.index('nativeInstantTouchDown(ev);') < nav.index('return super.dispatchTouchEvent(ev);', nav.index('private boolean tabsEvents;'))
assert 'onAnimationEndCheck(true)' in nav
assert 'import app.flexygram.motion.' not in nav+policy+hit
assert 'SharedPreferences' not in nav+policy+hit
assert 'MotionEvent.obtain' not in nav+policy+hit
assert 'ValueAnimator' not in policy+hit
print('Native Instant Touch source wiring passed')
