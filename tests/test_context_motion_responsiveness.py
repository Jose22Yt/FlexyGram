"""Motion cleanup and input-release regressions; simulated clocks are not device FPS."""
from pathlib import Path
import shutil
import pytest
from tools.connected_alpha import test_native_context135 as native_physics

ROOT = Path(__file__).resolve().parents[1]
CHAT = ROOT / 'TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java'


def test_real_springs_close_quickly_and_new_input_finishes_owner_once():
    if not shutil.which('java'):
        pytest.skip('JDK required')
    native_physics.NativeContextPhysics().test_actual_springs_preserve_velocity_on_handoff_and_interrupted_close()


def test_return_releases_scroll_and_does_not_block_next_touch():
    source = CHAT.read_text()
    from test_composer_layout import method
    close = method(source, 'public void dismiss(boolean animated)')
    assert 'boolean springClose = compactContext && animated && selectedBubbleMotion.hasOwner()' in close
    assert close.index('setFocusable(false)') < close.index('update();') < close.index('selectedBubbleMotion.close(')
    assert close.count('update();') == 1
    assert close.index('setCanScrollVertically(true)') < close.index('selectedBubbleMotion.close(')
    assert 'setFocusable(false)' in close and 'setTouchable(false)' in close
    assert 'updateMessageListAccessibilityVisibility()' in close
    touch_end = source.index('lastTouchY = ev.getY()')
    touch_start = source.rfind('public boolean dispatchTouchEvent(MotionEvent ev)', 0, touch_end)
    touch = source[touch_start:touch_end]
    assert touch.index('finishBubbleReturnForInput()') < touch.index('scrimView != null')
    assert 'MotionEvent.ACTION_DOWN) finishBubbleReturnForInput()' in touch
    helper = source[source.index('private void finishBubbleReturnForInput()'):source.index('    private View scrimView;')]
    assert helper.index('scrimPopupWindow.dismiss(false)') < helper.index('scrimAnimatorSet.end()')
    assert 'if (invoked && selectedBubbleMotion.isClosing()) finishBubbleReturnForInput();' in source
    assert 'else if (scrimPopupWindow != null && !selectedBubbleMotion.isClosing())' in source
    assert 'if (waitForLangDetection.get() && !compactContext)' in source
    assert 'if (!compactContext && glassMenu && scrimBlur3SourceBitmap.getBitmap() == null)' in source
