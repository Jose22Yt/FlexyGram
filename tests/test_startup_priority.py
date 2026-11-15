"""Startup scheduling and warm-resume layout regressions; no device timing claim."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_local_dialog_request_precedes_plugin_start_and_no_new_frame_gate():
    source = (JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text()
    init = method(source, 'public static void postInitApplication(boolean prepareDialogs)')
    assert init.index('initializeStartupAccount(a, prepareDialogs && a == startupAccount, uiStartup)') < init.index('PluginsController.getInstance().init(applicationContext)')
    core = method(source, 'private static void initializeStartupAccount(int a, boolean prepareDialogs, boolean uiStartup)')
    assert core.index('prepareSelectedDialogs();') < core.index('scheduleStartupUnsentMessages(a, uiStartup)')
    assert 'postFrameCallback' not in core and 'Thread.sleep' not in core
    sender = method(source, 'private static void checkStartupUnsentMessages(int account)')
    assert sender.index('getCurrentUser() != null') < sender.index('checkUnsentMessages()')


def test_trial_bottom_bar_uses_native_layout_without_custom_reconfiguration():
    source=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    assert 'applyFlexyTabs' not in source and 'flexyTabConfigListener' not in source
    assert 'new MainTabsLayout(context, resourceProvider)' in source
