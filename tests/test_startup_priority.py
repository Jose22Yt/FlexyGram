"""Startup scheduling and warm-resume layout regressions; no device timing claim."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_local_dialog_request_precedes_plugin_start_and_no_new_frame_gate():
    source = (JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text()
    init = method(source, 'public static void postInitApplication(boolean prepareDialogs)')
    assert init.index('initializeStartupAccount(a, prepareDialogs && a == startupAccount, uiStartup)') < init.index('initializeStartupIntegrations()')
    integrations = method(source, 'private static void initializeStartupIntegrations()')
    assert integrations.index('PluginsController.getInstance().init(applicationContext)') < integrations.index('reconcilePushRegistration()')
    core = method(source, 'private static void initializeStartupAccount(int a, boolean prepareDialogs, boolean uiStartup)')
    assert core.index('prepareSelectedDialogs();') < core.index('scheduleStartupUnsentMessages(a, uiStartup)')
    assert 'postFrameCallback' not in core and 'Thread.sleep' not in core
    sender = method(source, 'private static void checkStartupUnsentMessages(int account)')
    assert sender.index('getCurrentUser() != null') < sender.index('checkUnsentMessages()')


def test_push_can_process_secondary_account_before_the_next_frame(tmp_path):
    app = (JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text()
    push = (JAVA/'org/telegram/messenger/PushListenerController.java').read_text()
    handler = method(push, 'public static void processRemoteMessage(')
    assert handler.index('AndroidUtilities.runOnUIThread(') < handler.index('postInitApplicationForPush()') < handler.index('Utilities.stageQueue.postRunnable(')
    push_init = method(app, 'static void postInitApplicationForPush()')
    deferred = method(app, 'private static void initializeDeferredStartupAccount(')
    drain = method(app, 'private static void initializePendingStartupAccounts()')
    probe(tmp_path, {'Probe.java': '''
public class Probe {
    static final boolean[] deferredStartupAccounts = new boolean[3];
    static final boolean[] ready = new boolean[3];
    static final class UserConfig {
        static final int MAX_ACCOUNT_COUNT = 3;
        static UserConfig getInstance(int account) { return new UserConfig(); }
        boolean isClientActivated() { return true; }
    }
    static int deferredStartupAccountCount, preparedCount;
    static void postInitApplication() {
        if (deferredStartupAccountCount != 0) throw new AssertionError("push could race a queued drain");
        if (!ready[0]) initializeStartupAccount(0, false); // cold process
    }
    static void initializeStartupAccount(int account, boolean dialogs) {
        if (dialogs || ready[account]) throw new AssertionError();
        ready[account] = true;
        preparedCount++;
    }
    PUSH_INIT
    DEFERRED
    DRAIN
    public static void main(String[] args) {
        postInitApplicationForPush();
        if (!ready[0]) throw new AssertionError();
        deferredStartupAccounts[1] = deferredStartupAccounts[2] = true;
        deferredStartupAccountCount = 2;
        postInitApplicationForPush();
        if (!ready[1] || !ready[2] || deferredStartupAccountCount != 0) throw new AssertionError();
        initializePendingStartupAccounts(); // UI frame already in flight
        postInitApplicationForPush();
        if (preparedCount != 3) throw new AssertionError();
    }
}'''.replace('PUSH_INIT', push_init).replace('DEFERRED', deferred).replace('DRAIN', drain)})


def test_incoming_push_only_persists_its_timestamp_and_keeps_payloads_out_of_error_logs():
    app = (JAVA/'org/telegram/messenger/SharedConfig.java').read_text()
    push = (JAVA/'org/telegram/messenger/PushListenerController.java').read_text()
    stamp = method(app, 'static void recordPushReceived()')
    assert 'synchronized (sync)' in stamp
    assert stamp.count('.edit()') == 1 and stamp.count('.putLong(') == 1
    assert '.putLong("pushLastReceivedTime", pushLastReceivedTime).apply()' in stamp
    handler = method(push, 'public static void processRemoteMessage(')
    assert 'SharedConfig.recordPushReceived();' in handler
    assert 'SharedConfig.saveConfig()' not in handler
    assert 'bytesToHex(SharedConfig.pushAuthKey)' not in handler
    assert 'jsonString' not in handler and 'FileLog.e(e)' not in handler


def test_trial_bottom_bar_uses_native_layout_without_custom_reconfiguration():
    source=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    assert 'applyFlexyTabs' not in source and 'flexyTabConfigListener' not in source
    assert 'new MainTabsLayout(context, resourceProvider)' in source
