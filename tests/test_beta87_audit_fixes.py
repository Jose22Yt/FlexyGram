"""Targeted regressions for Beta 87 security, crash, and performance audit fixes."""
import importlib.util
import io
import os
import stat
import sys
import types
import zipfile

import pytest

from test_composer_layout import method
from test_render_work_reuse import JAVA, ROOT, probe


def _load_py_module(rel_path: str, name: str):
    path = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_studio_client_catalog_rejects_secrets_and_pii_from_portable_export(tmp_path):
    source = (JAVA / 'app/flexygram/studio/StudioClientCatalog.java').read_text()
    portable = method(source, 'private static boolean portable(String key)')
    probe(tmp_path, {
        'Probe.java': '''import java.util.Locale;
public class Probe {
    PORTABLE
    static void check(boolean ok, String msg) { if (!ok) throw new AssertionError(msg); }
    public static void main(String[] args) {
        String[] blocked = {
            "openAiKey", "geminiKey", "claudeKey", "deepseekKey", "grokKey",
            "openRouterKey", "groqKey", "cerebrasKey", "nvidiaKey", "workersAiKey",
            "GoogleCloudTransKey", "DeepLTranslateKey", "workersAiAccountId",
            "weatherLat", "weatherLon", "weatherAddress", "customDoH", "lastFmNick",
            "botToken", "clientSecret", "userPassword", "authCookie", "proxy_list"
        };
        for (String key : blocked) {
            check(!portable(key), "must block sensitive key: " + key);
        }
        String[] allowed = {
            "squareAvatar", "hidePhoneNumber", "actionBarDecoration", "tabIcons", "disableNumberRounding"
        };
        for (String key : allowed) {
            check(portable(key), "should allow UI key: " + key);
        }
    }
}'''.replace('PORTABLE', portable)
    })


def test_dev_server_token_permissions_loopback_debugger_and_line_cap(tmp_path, monkeypatch):
    dev_server = _load_py_module('TMessagesProj/src/main/python/dev_server.py', 'flexy_dev_server_audit')
    logged = []
    monkeypatch.setattr(dev_server, '_log', logged.append)
    fake_file_utils = types.SimpleNamespace(get_plugins_dir=lambda: str(tmp_path))
    monkeypatch.setitem(sys.modules, 'file_utils', fake_file_utils)
    monkeypatch.setattr(dev_server, '_token', None)

    token = dev_server._ensure_token()
    dev_server._publish_token(token)
    assert len(token) >= 32
    assert all(token not in entry for entry in logged), 'token must never be logged'
    token_file = tmp_path / dev_server.TOKEN_FILE
    assert token_file.read_text(encoding='utf-8') == token
    mode = stat.S_IMODE(os.stat(token_file).st_mode)
    assert mode == 0o600, f'expected 0o600, got {oct(mode)}'

    for bad_host in ('192.168.1.5', '0.0.0.0', 'evil.example'):
        res = dev_server._cmd_start_debugger({'host': bad_host, 'port': 5678})
        assert res['ok'] is False and 'loopback' in res['error'].lower()
    for bad_port in (80, 1023, 65536, 'abc'):
        res = dev_server._cmd_start_debugger({'host': '127.0.0.1', 'port': bad_port})
        assert res['ok'] is False

    responses = []

    class FakeSocket:
        def __init__(self):
            self.timeout = None

        def settimeout(self, t):
            self.timeout = t

    handler = object.__new__(dev_server._Handler)
    handler.request = FakeSocket()
    handler.rfile = io.BytesIO(b'x' * (dev_server._MAX_LINE_BYTES + 10) + b'\n')
    handler._respond = responses.append
    handler.handle()
    assert handler.request.timeout == dev_server._SOCKET_TIMEOUT_SECONDS
    assert responses and responses[0]['ok'] is False and 'maximum size' in responses[0]['error']


def _zip_bytes(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for item in entries:
            if isinstance(item[0], zipfile.ZipInfo):
                zf.writestr(item[0], item[1])
            else:
                zf.writestr(item[0], item[1])
    return buf.getvalue()


def test_pip_controller_safe_extract_and_fail_closed_digest(tmp_path):
    pip_ctrl = _load_py_module('TMessagesProj/src/main/python/pip_controller.py', 'flexy_pip_ctrl_audit')

    with pytest.raises(RuntimeError, match='missing sha256'):
        pip_ctrl._verify_digest('demo', '1.0.0', {}, b'payload')

    bad_zip = _zip_bytes([('../escape.py', 'print(1)')])
    with pytest.raises(RuntimeError, match='unsafe'):
        pip_ctrl._safe_extract(bad_zip, str(tmp_path / 'out1'))

    info = zipfile.ZipInfo('link.py')
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    sym_zip = _zip_bytes([(info, '/etc/passwd')])
    with pytest.raises(RuntimeError, match='symlink'):
        pip_ctrl._safe_extract(sym_zip, str(tmp_path / 'out2'))

    bomb_zip = _zip_bytes([('big.bin', b'A' * 4096)])
    old_cap = pip_ctrl._MAX_UNCOMPRESSED_BYTES
    try:
        pip_ctrl._MAX_UNCOMPRESSED_BYTES = 1024
        with pytest.raises(RuntimeError, match='exceeds'):
            pip_ctrl._safe_extract(bomb_zip, str(tmp_path / 'out3'))
    finally:
        pip_ctrl._MAX_UNCOMPRESSED_BYTES = old_cap


def test_vosk_transcriber_defers_model_close_while_recognizer_is_in_flight(tmp_path):
    source = (JAVA / 'app/exteraless/speech/VoskTranscriber.java').read_text()
    methods = '\n'.join(method(source, sig) for sig in [
        'public static void trimMemory(int level)',
        'public static void releaseModel()',
        'private static void closeQuietly(Model model)',
        'private static Model acquireModel(String code) throws IOException',
        'private static void releaseModelUse(Model model)',
    ]).replace('VoskTranscriber.class', 'Probe.class')
    probe(tmp_path, {
        'android/content/ComponentCallbacks2.java': 'package android.content;public interface ComponentCallbacks2{int TRIM_MEMORY_RUNNING_LOW=10,TRIM_MEMORY_UI_HIDDEN=20;}',
        'Probe.java': '''import java.io.File;import java.io.IOException;
public class Probe {
    static class Model { volatile boolean closed; Model(String p) throws IOException {} void close(){ closed = true; } }
    static class FileLog { static void e(Throwable t){} }
    static class LogLevel { static final int WARNINGS = 0; }
    static class LibVosk { static void setLogLevel(int lvl){} }
    static class VoskManager { static File getModelDir(String code){ return new File("/tmp") { @Override public boolean exists(){ return true; } }; } }
    private static Model cachedModel;
    private static String cachedCode;
    private static int cachedModelUses;
    private static boolean logLevelSet;
    METHODS
    static void check(boolean ok, String m) { if (!ok) throw new AssertionError(m); }
    public static void main(String[] args) throws Exception {
        Model m = acquireModel("en");
        check(m != null && !m.closed, "model should be open");
        // Release while active recognizer holds refcount -> must NOT close native Model yet!
        releaseModel();
        check(!m.closed, "model closed while still in use (native UAF!)");
        // Now recognizer finishes -> deferred close runs immediately.
        releaseModelUse(m);
        check(m.closed, "model should close once last active user exits");
        // trimMemory below RUNNING_LOW (10) or UI_HIDDEN (20) keeps idle cached model; >=10 releases it.
        Model m2 = acquireModel("en");
        releaseModelUse(m2);
        trimMemory(5); check(!m2.closed, "low trim must keep model");
        trimMemory(20); check(!m2.closed, "UI_HIDDEN must keep model");
        trimMemory(10); check(m2.closed, "RUNNING_LOW must close idle model");
    }
}'''.replace('METHODS', methods)
    })


def test_files_work_rapid_submits_never_throw_rejected_execution(tmp_path):
    probe(tmp_path, {
        'app/flexygram/files/Helper.java': '''package app.flexygram.files;
import java.util.concurrent.*;import java.util.concurrent.atomic.*;
public class Helper {
    public static void run() throws Exception {
        try (FilesWork work = new FilesWork()) {
            CountDownLatch blocker = new CountDownLatch(1);
            CountDownLatch finalDone = new CountDownLatch(1);
            AtomicInteger lastRan = new AtomicInteger(-1);
            work.submit(() -> { try { blocker.await(2, TimeUnit.SECONDS); } catch (InterruptedException ignored) {} });
            for (int i = 0; i < 50; i++) {
                final int id = i;
                work.submit(() -> {
                    lastRan.set(id);
                    if (id == 49) finalDone.countDown();
                });
            }
            blocker.countDown();
            if (!finalDone.await(5, TimeUnit.SECONDS)) throw new AssertionError("latest work did not complete");
            if (lastRan.get() != 49) throw new AssertionError("expected 49, got " + lastRan.get());
        }
    }
}''',
        'Probe.java': 'public class Probe { public static void main(String[] args) throws Exception { app.flexygram.files.Helper.run(); } }'
    }, [JAVA / 'app/flexygram/files/FilesWork.java'])


def test_inline_scanner_number_parses_regional_formats_without_dynamic_regex(tmp_path):
    scanner_src = (JAVA / 'app/flexygram/inlineconverter/InlineConversionScanner.java').read_text()
    number_body = method(scanner_src, 'public static BigDecimal number(String raw,Locale locale)')
    assert 'Pattern.quote' not in number_body and '.split(' not in number_body and '.matches(' not in number_body
    probe(tmp_path, {
        'Probe.java': '''import app.flexygram.inlineconverter.InlineConversionScanner;
import java.math.BigDecimal;import java.util.Locale;
public class Probe {
    static void check(boolean ok, String m) { if (!ok) throw new AssertionError(m); }
    static void bad(String raw, Locale loc) {
        try { InlineConversionScanner.number(raw, loc); throw new AssertionError("should fail: " + raw); }
        catch (IllegalArgumentException expected) {}
    }
    public static void main(String[] args) {
        check(new BigDecimal("1234.56").compareTo(InlineConversionScanner.number("1,234.56", Locale.US)) == 0, "US");
        check(new BigDecimal("-9876543.25").compareTo(InlineConversionScanner.number("−9,876,543.25", Locale.US)) == 0, "US neg");
        check(new BigDecimal("1234.56").compareTo(InlineConversionScanner.number("1.234,56", Locale.GERMANY)) == 0, "DE");
        bad("1,23.45", Locale.US);
        bad("1.2.3", Locale.US);
        bad("12a", Locale.US);
        bad("", Locale.US);
    }
}'''
    }, [JAVA / 'app/flexygram/inlineconverter/InlineConversionMatch.java',
        JAVA / 'app/flexygram/inlineconverter/InlineConversionScanner.java'])


def test_network_and_update_hot_paths_use_static_plugin_hook_gates():
    cm = (JAVA / 'org/telegram/tgnet/ConnectionsManager.java').read_text()
    mc = (JAVA / 'org/telegram/messenger/MessagesController.java').read_text()
    smh = (JAVA / 'org/telegram/messenger/SendMessagesHelper.java').read_text()
    assert 'PluginsController.hasActiveRequestHooks()' in cm
    assert 'PluginsController.getInstance().hasAnyRequestHooks()' not in cm
    assert 'PluginsController.hasActiveUpdatesContainerHooks()' in mc
    assert 'PluginsController.hasActiveUpdateHooks()' in mc
    assert 'PluginsController.hasActiveSendMessageHooks()' in smh


def test_ghost_mode_toggle_sends_correct_status_and_applies_presets(tmp_path):
    src = (JAVA / 'tw/nekomimi/nekogram/NekoConfig.java').read_text()
    methods = '\n'.join(method(src, sig) for sig in [
        'public static boolean isGhostModeActive()',
        'public static void setGhostMode(boolean enabled)',
        'public static void toggleGhostMode()',
        'public static void applyGhostPreset(int preset)',
    ])
    probe(tmp_path, {
        'Probe.java': '''import java.util.*;
public class Probe {
    static class Pair<A, B> { final A first; final B second; Pair(A a, B b) { first = a; second = b; } }
    static class ConfigItem {
        boolean b; int i;
        ConfigItem(boolean v) { b = v; }
        ConfigItem(int v) { i = v; }
        boolean Bool() { return b; }
        int Int() { return i; }
        void setConfigBool(boolean v) { b = v; }
        void setConfigInt(int v) { i = v; }
    }
    static final List<Boolean> statusCalls = new ArrayList<>();
    static class AyuGhostUtils {
        static void performStatusRequest(Boolean offline) { statusCalls.add(offline); }
    }
    public static ConfigItem sendReadMessagePackets = new ConfigItem(true);
    public static ConfigItem sendReadStoriesPackets = new ConfigItem(true);
    public static ConfigItem sendOnlinePackets = new ConfigItem(true);
    public static ConfigItem sendUploadProgress = new ConfigItem(true);
    public static ConfigItem sendOfflinePacketAfterOnline = new ConfigItem(false);
    public static ConfigItem ghostBlockReactionOnline = new ConfigItem(false);
    public static ConfigItem ghostBlockMentionsRead = new ConfigItem(false);
    public static ConfigItem markReadAfterSend = new ConfigItem(false);
    static ConfigItem unlocked = new ConfigItem(false);
    private static final List<Pair<ConfigItem, ConfigItem>> ghostToggleItems = Arrays.asList(
        new Pair<>(sendReadMessagePackets, unlocked),
        new Pair<>(sendReadStoriesPackets, unlocked),
        new Pair<>(sendOnlinePackets, unlocked),
        new Pair<>(sendUploadProgress, unlocked),
        new Pair<>(sendOfflinePacketAfterOnline, unlocked)
    );
    METHODS
    static void check(boolean ok, String msg) { if (!ok) throw new AssertionError(msg); }
    public static void main(String[] args) {
        check(!isGhostModeActive(), "starts inactive");
        toggleGhostMode();
        check(isGhostModeActive(), "now active");
        check(statusCalls.size() == 1 && Boolean.TRUE.equals(statusCalls.get(0)),
              "enabling ghost mode must send offline=true, got " + statusCalls);
        toggleGhostMode();
        check(!isGhostModeActive(), "now inactive again");
        check(statusCalls.size() == 2 && Boolean.FALSE.equals(statusCalls.get(1)),
              "disabling ghost mode must send offline=false, got " + statusCalls);
        applyGhostPreset(0);
        check(isGhostModeActive() && ghostBlockReactionOnline.Bool() && ghostBlockMentionsRead.Bool() && !markReadAfterSend.Bool(), "preset 0");
        applyGhostPreset(1);
        check(isGhostModeActive() && markReadAfterSend.Bool() && ghostBlockReactionOnline.Bool(), "preset 1");
        applyGhostPreset(2);
        check(!sendReadStoriesPackets.Bool() && sendReadMessagePackets.Bool() && sendOnlinePackets.Bool(), "preset 2");
    }
}'''.replace('METHODS', methods)
    })


def test_preferred_refresh_rate_selects_matching_mode_and_skips_redundant_updates(tmp_path):
    src = (JAVA / 'org/telegram/messenger/AndroidUtilities.java').read_text()
    methods = '\n'.join(method(src, sig) for sig in [
        'private static int findPreferredDisplayModeId(Window window, float targetRate)',
        'public static void setPreferredMaxRefreshRate(Window window, float rate)',
    ])
    probe(tmp_path, {
        'Probe.java': '''public class Probe {
    static class Build { static class VERSION { static int SDK_INT = 35; } static class VERSION_CODES { static final int M = 23, R = 30; } }
    static class FileLog { static void e(Throwable t) { throw new RuntimeException(t); } }
    static class Display {
        static class Mode {
            final int id, w, h; final float rr;
            Mode(int id, int w, int h, float rr) { this.id = id; this.w = w; this.h = h; this.rr = rr; }
            int getModeId() { return id; }
            int getPhysicalWidth() { return w; }
            int getPhysicalHeight() { return h; }
            float getRefreshRate() { return rr; }
        }
        Mode current; Mode[] modes;
        Mode getMode() { return current; }
        Mode[] getSupportedModes() { return modes; }
    }
    static class WindowManager {
        static class LayoutParams { float preferredRefreshRate; int preferredDisplayModeId; }
        Display d;
        Display getDefaultDisplay() { return d; }
    }
    static class Context {
        Display d;
        Display getDisplay() { return d; }
    }
    static class Window {
        Context ctx = new Context();
        WindowManager wm = new WindowManager();
        WindowManager.LayoutParams lp = new WindowManager.LayoutParams();
        int setCalls;
        Context getContext() { return ctx; }
        WindowManager getWindowManager() { return wm; }
        WindowManager.LayoutParams getAttributes() { return lp; }
        void setAttributes(WindowManager.LayoutParams p) { lp = p; setCalls++; }
    }
    METHODS
    static void check(boolean ok, String msg) { if (!ok) throw new AssertionError(msg); }
    public static void main(String[] args) {
        Window w = new Window();
        Display d = new Display();
        Display.Mode m60 = new Display.Mode(1, 1080, 2400, 60f);
        Display.Mode m120 = new Display.Mode(2, 1080, 2400, 120f);
        Display.Mode m120LowRes = new Display.Mode(3, 720, 1600, 120f);
        d.current = m60;
        d.modes = new Display.Mode[]{m60, m120LowRes, m120};
        w.ctx.d = d;
        w.wm.d = d;

        setPreferredMaxRefreshRate(w, 120f);
        check(w.setCalls == 1 && w.lp.preferredRefreshRate == 120f && w.lp.preferredDisplayModeId == 2,
              "should select 1080x2400@120Hz mode id=2");
        setPreferredMaxRefreshRate(w, 120f);
        check(w.setCalls == 1, "repeated call must be a no-op");
        setPreferredMaxRefreshRate(w, Float.NaN);
        setPreferredMaxRefreshRate(w, 0f);
        check(w.setCalls == 1 && w.lp.preferredDisplayModeId == 2, "invalid rates ignored");
    }
}'''.replace('METHODS', methods)
    })


def test_120hz_and_ghost_and_player_wiring():
    launch = (JAVA / 'org/telegram/ui/LaunchActivity.java').read_text()
    assert 'AndroidUtilities.setPreferredMaxRefreshRate(getWindow());' in method(launch, 'protected void onCreate(Bundle savedInstanceState)')
    assert 'AndroidUtilities.setPreferredMaxRefreshRate(getWindow());' in method(launch, 'protected void onResume()')
    assert 'AndroidUtilities.setPreferredMaxRefreshRate(getWindow());' in method(launch, 'public void onWindowFocusChanged(boolean hasFocus)')

    ghost_ui = (JAVA / 'tw/nekomimi/nekogram/settings/GhostModeActivity.java').read_text()
    assert '((CheckBoxCell) view).setChecked(!NekoConfig.sendReadMessagePackets.Bool(), true);' in ghost_ui
    assert '((CheckBoxCell) view).setChecked(!NekoConfig.sendOnlinePackets.Bool(), true);' in ghost_ui
    assert '((CheckBoxCell) view).setChecked(!NekoConfig.sendReadStoriesPackets.Bool(), true);' in ghost_ui
    assert '((CheckBoxCell) view).setChecked(!NekoConfig.sendUploadProgress.Bool(), true);' in ghost_ui

    player = (JAVA / 'app/exteraless/player/baseline/PlayerSheet.java').read_text()
    assert 'Utilities.globalQueue.postRunnable' in player
    assert 'AndroidUtilities.setPreferredMaxRefreshRate(getWindow())' in player
    assert 'tempCopy.recycle()' in player


def test_hidden_bottlenecks_and_canvas_or_db_leaks_fixed():
    cell = (JAVA / 'org/telegram/ui/Cells/ChatMessageCell.java').read_text()
    assert 'canvas.saveLayerAlpha(null, (int) (255 * 0.75f)' not in cell
    assert 'final int translucentRestore = (shouldTranslucentDeleted() && ayuDeleted' in cell
    assert 'Theme.chat_msgTextPaint.setAlpha(prevDeletedCaptionAlpha);' in cell

    ayu_data = (JAVA / 'com/radolyn/ayugram/database/AyuData.java').read_text()
    assert 'JournalMode.WRITE_AHEAD_LOGGING' in ayu_data
    assert 'PRAGMA synchronous = NORMAL' in ayu_data

    ayu_ctrl = (JAVA / 'com/radolyn/ayugram/messages/AyuMessagesController.java').read_text()
    assert 'deletedMessageDao.getExistingMessageIds(userId, dialogId, java.util.Collections.singletonList(messageId))' in ayu_ctrl
    assert 'Utilities.globalQueue.postRunnable(() -> {' in method(ayu_ctrl, 'public void deleteCurrent(')

    drawer_picker = (JAVA / 'app/exteraless/drawer/DrawerAccountPickerView.java').read_text()
    assert 'if (topAlpha <= 0.0f && bottomAlpha <= 0.0f)' in drawer_picker

    member_lens = (JAVA / 'app/flexygram/memberlens/MemberLensConfig.java').read_text()
    assert 'private static volatile Boolean cached;' in member_lens

    fade = (JAVA / 'org/telegram/ui/Components/blur3/BlurredBackgroundWithFadeDrawable.java').read_text()
    assert 'matrixTmp.setScale(1f, height);' in method(fade, 'private void drawOverrideFade(')

    cam = (JAVA / 'app/exteraless/camera/CameraZoomSliderView.java').read_text()
    assert 'if (edgeFadeShader == null' in cam
    assert 'paint.getFontMetricsInt(tmpFontMetrics);' in cam

    persian = (JAVA / 'tw/nekomimi/nekogram/shamsicalendar/PersianDate.java').read_text()
    assert 'Calendar.getInstance()' in method(persian, 'private void changeTime()')
    assert 'new SimpleDateFormat' not in method(persian, 'private void changeTime()')

    typeface = (JAVA / 'tw/nekomimi/nekogram/helpers/TypefaceHelper.java').read_text()
    assert 'synchronized (PAINT)' in method(typeface, 'private static boolean testTypeface(')


def test_adaptive_scroll_throttle_120hz_behavior(tmp_path):
    probe(tmp_path, {
        'Probe.java': '''import app.flexygram.performance.AdaptiveScrollThrottle;
public class Probe {
    static void check(boolean ok, String m) { if (!ok) throw new AssertionError(m); }
    public static void main(String[] args) {
        AdaptiveScrollThrottle t = new AdaptiveScrollThrottle();
        // 60 Hz never skips blur or pauses heavy ops.
        for (int i = 0; i < 10; i++) {
            check(t.shouldInvalidateBlur(AdaptiveScrollThrottle.SCROLL_STATE_SETTLING, 300, 60f, 3f), "60hz blur");
            check(t.updateFastFlingHeavyOps(AdaptiveScrollThrottle.SCROLL_STATE_SETTLING, 300, 60f, 3f) == AdaptiveScrollThrottle.HEAVY_OP_NOOP, "60hz heavy");
        }
        // 120 Hz dragging never skips blur.
        for (int i = 0; i < 10; i++) {
            check(t.shouldInvalidateBlur(AdaptiveScrollThrottle.SCROLL_STATE_DRAGGING, 300, 120f, 3f), "120hz drag");
        }
        // 120 Hz high-velocity settling alternates blur (skip, draw, skip, draw) and marks deferred on skip.
        check(!t.shouldInvalidateBlur(AdaptiveScrollThrottle.SCROLL_STATE_SETTLING, 200, 120f, 3f), "fling skip 1");
        check(t.shouldInvalidateBlur(AdaptiveScrollThrottle.SCROLL_STATE_SETTLING, 200, 120f, 3f), "fling draw 2");
        check(!t.shouldInvalidateBlur(AdaptiveScrollThrottle.SCROLL_STATE_SETTLING, -200, 120f, 3f), "fling skip 3");
        check(t.consumeDeferredBlur(), "deferred flush on idle");
        check(!t.consumeDeferredBlur(), "second flush must be false");

        // 120 Hz fast-fling heavy op pause and smooth deceleration resume.
        check(t.updateFastFlingHeavyOps(AdaptiveScrollThrottle.SCROLL_STATE_SETTLING, 220, 120f, 3f) == AdaptiveScrollThrottle.HEAVY_OP_PAUSE, "pause on fast fling");
        check(t.isHeavyOpsPaused(), "paused flag");
        check(t.updateFastFlingHeavyOps(AdaptiveScrollThrottle.SCROLL_STATE_SETTLING, 220, 120f, 3f) == AdaptiveScrollThrottle.HEAVY_OP_NOOP, "already paused");
        check(t.updateFastFlingHeavyOps(AdaptiveScrollThrottle.SCROLL_STATE_SETTLING, 30, 120f, 3f) == AdaptiveScrollThrottle.HEAVY_OP_RESUME, "resume on slow fling");
        check(!t.isHeavyOpsPaused(), "resumed flag");

        // Lifecycle release always clears paused state cleanly.
        check(t.updateFastFlingHeavyOps(AdaptiveScrollThrottle.SCROLL_STATE_SETTLING, 250, 120f, 3f) == AdaptiveScrollThrottle.HEAVY_OP_PAUSE, "pause again");
        check(t.releaseHeavyOps(), "release must signal resume");
        check(!t.releaseHeavyOps(), "second release is noop");
    }
}'''
    }, [JAVA / 'app/flexygram/performance/AdaptiveScrollThrottle.java'])


def test_pass7_startup_gpu_and_memory_optimizations():
    app = (JAVA / 'org/telegram/messenger/ApplicationLoader.java').read_text()
    create = method(app, 'public void onCreate()')
    assert 'if (BuildConfig.NATIVE_BASELINE_TEST) preloadStartupPreferences()' not in create
    assert 'preloadStartupPreferences();' in create
    assert 'DialogCell.trimMemory(level)' in method(app, 'public void onTrimMemory(int level)')
    assert 'DialogCell.trimMemory(' in method(app, 'public void onLowMemory()')

    tve = (JAVA / 'tw/nekomimi/nekogram/TextViewEffects.java').read_text()
    tve_draw = method(tve, 'protected void onDraw(Canvas canvas)')
    assert 'if (spoilers.isEmpty()) {' in tve_draw
    assert 'canvas.saveLayer(unionL, unionT, unionR, unionB + padY, null);' in tve_draw

    dialog_cell = (JAVA / 'org/telegram/ui/Cells/DialogCell.java').read_text()
    assert 'private static Paint getSharedFadePaint(boolean left)' in dialog_cell
    assert 'public static void trimMemory(int level)' in dialog_cell
    assert 'canvas.saveLayerAlpha(nameLeft, fadeTop, nameLeft + nameWidth, fadeBottom' in dialog_cell
    assert 'thumbBackgroundPaint' not in dialog_cell

    chat = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    assert 'chatPool.setMaxRecycledViews(1, 14);' in chat
    assert 'chatScrollThrottle.updateFastFlingHeavyOps(' in chat
    assert 'releaseFastFlingHeavyOps();' in method(chat, 'public void onPause()')
    assert 'releaseFastFlingHeavyOps();' in method(chat, 'public void onFragmentDestroy()')

    dialogs = (JAVA / 'org/telegram/ui/DialogsActivity.java').read_text()
    assert 'dialogsScrollThrottle.shouldInvalidateBlur(' in dialogs
    assert 'dialogsScrollThrottle.consumeDeferredBlur()' in dialogs

    img = (JAVA / 'org/telegram/messenger/ImageLoader.java').read_text()
    assert 'memoryClass >= 512 ? 112 : 80' in img

    cfg = (JAVA / 'tw/nekomimi/nekogram/config/ConfigItem.java').read_text()
    assert 'public volatile Object value;' in cfg

    emoji = (JAVA / 'org/telegram/ui/Components/EmojiView.java').read_text()
    assert 'emojiPool.setMaxRecycledViews(0, 32);' in emoji
    assert 'stickersPool.setMaxRecycledViews(0, 25);' in emoji

    media = (JAVA / 'org/telegram/ui/Components/SharedMediaLayout.java').read_text()
    assert 'mediaPool.setMaxRecycledViews(0, 24);' in media
    assert 'layoutManager.setInitialPrefetchItemCount(12);' in media

    profile = (JAVA / 'org/telegram/ui/ProfileActivity.java').read_text()
    assert 'layoutManager.setInitialPrefetchItemCount(8);' in profile
    assert 'listView.setItemViewCacheSize(10);' in profile

    action = (JAVA / 'org/telegram/ui/Cells/ChatActionCell.java').read_text()
    assert 'reactionsLayoutInBubble.x + reactionsLayoutInBubble.width + pad' in action

    regex_act = (JAVA / 'tw/nekomimi/nekogram/filters/RegexFiltersSettingActivity.java').read_text()
    assert 'private static final Gson GSON = new Gson();' in regex_act
    assert 'new Gson().' not in regex_act

    sheet = (JAVA / 'org/telegram/ui/ActionBar/BottomSheet.java').read_text()
    assert 'AndroidUtilities.setPreferredMaxRefreshRate(window);' in sheet
    assert 'private void setSheetTransitionActive(boolean active)' in sheet
    assert 'setSheetTransitionActive(false);' in method(sheet, 'public void dismissInternal()')

    alert = (JAVA / 'org/telegram/ui/ActionBar/AlertDialog.java').read_text()
    assert 'AndroidUtilities.setPreferredMaxRefreshRate(window);' in alert

    photo = (JAVA / 'org/telegram/ui/PhotoViewer.java').read_text()
    assert 'windowLayoutParams.preferredRefreshRate = AndroidUtilities.screenMaxRefreshRate;' in photo

    popup = (JAVA / 'org/telegram/ui/ActionBar/ActionBarPopupWindow.java').read_text()
    assert 'setPopupAnimationFrameRate(finalViewGroup, true);' in popup
    assert 'finalViewGroup.setLayerType(View.LAYER_TYPE_HARDWARE, null);' in popup

    pager = (JAVA / 'org/telegram/ui/Components/ViewPagerFixed.java').read_text()
    assert 'private void beginTabTransition()' in pager
    assert 'private void endTabTransition()' in pager
    assert 'endTabTransition();' in method(pager, 'protected void onDetachedFromWindow()')

    dialogs = (JAVA / 'org/telegram/ui/DialogsActivity.java').read_text()
    assert 'public void beginFolderTabTransition()' in dialogs
    assert 'public void endFolderTabTransition()' in dialogs
    assert 'contentView.beginFolderTabTransition();' in dialogs
    assert 'contentView.endFolderTabTransition();' in dialogs


def test_dialogs_restore_scroll_anchor_stays_at_newest_chats_with_hidden_archive(tmp_path):
    source = (JAVA / 'org/telegram/ui/DialogsActivity.java').read_text()
    restore = method(source, 'private void restoreScrollAnchor(')
    probe(tmp_path, {'Probe.java': '''import java.util.function.IntUnaryOperator;
public class Probe {
    static class RecyclerView { static final int NO_POSITION = -1, SCROLL_STATE_IDLE = 0; }
    static class View {
        final int position, top, bottom;
        View(int p, int t, int b) { position = p; top = t; bottom = b; }
        int getTop() { return top; }
        int getBottom() { return bottom; }
    }
    static class ListView {
        View[] rows;
        int paddingTop = 200, paddingBottom = 100, height = 2000, state = 0;
        int getScrollState() { return state; }
        int getChildCount() { return rows.length; }
        View getChildAt(int i) { return rows[i]; }
        int getPaddingTop() { return paddingTop; }
        int getPaddingBottom() { return paddingBottom; }
        int getHeight() { return height; }
        int getChildAdapterPosition(View v) { return v.position; }
    }
    static class Manager {
        int position = -1, offset = 0, calls = 0;
        boolean hasPendingScrollPosition() { return false; }
        void scrollToPositionWithOffset(int p, int o) { position = p; offset = o; calls++; }
    }
    static final int DIALOGS_TYPE_DEFAULT = 0, ARCHIVE_ITEM_STATE_HIDDEN = 0;
    final ListView listView = new ListView();
    final Manager layoutManager = new Manager();
    int dialogsType = 0, archivePullViewState = 0;
    boolean hasStories = false, hiddenArchiveFlag = true;
    float scrollYOffset = 0f;
    boolean hasHiddenArchive() { return hiddenArchiveFlag; }
    RESTORE
    static void check(boolean ok, String m) { if (!ok) throw new AssertionError(m); }
    public static void main(String[] args) {
        Probe p = new Probe();
        // Case 1: Hidden archive off top, position 1 at top (offset 0), 15 new chats sync (1 -> 16) -> MUST stay at 1!
        p.listView.rows = new View[]{ new View(0, 20, 200), new View(1, 200, 380), new View(2, 380, 560) };
        p.restoreScrollAnchor(pos -> pos == 1 ? 16 : pos + 15, false);
        check(p.layoutManager.position == 1 && p.layoutManager.offset == 0, "hidden archive top jumped to " + p.layoutManager.position);

        // Case 2: Hidden archive + collapsed stories (negative scrollYOffset), position 1 at top -> MUST stay at 1!
        p.hasStories = true;
        p.scrollYOffset = -150f;
        p.listView.rows = new View[]{ new View(1, 50, 230), new View(2, 230, 410) };
        p.restoreScrollAnchor(pos -> pos == 1 ? 12 : pos + 11, false);
        check(p.layoutManager.position == 1 && p.layoutManager.offset == -150, "stories collapsed top jumped to " + p.layoutManager.position);

        // Case 3: Hidden archive peeking (skipArchive), 10 new chats sync -> MUST snap to 1!
        p.hasStories = false;
        p.scrollYOffset = 0f;
        p.listView.rows = new View[]{ new View(0, 120, 260), new View(1, 260, 440) };
        p.restoreScrollAnchor(pos -> pos == 1 ? 11 : pos + 10, false);
        check(p.layoutManager.position == 1 && p.layoutManager.offset == 0, "skipArchive jumped to " + p.layoutManager.position);

        // Case 4: User actually scrolled down to position 8 -> MUST preserve reading position (8 -> 18)!
        p.listView.rows = new View[]{ new View(8, 200, 380), new View(9, 380, 560) };
        p.restoreScrollAnchor(pos -> pos + 10, false);
        check(p.layoutManager.position == 18 && p.layoutManager.offset == 0, "scrolled reading lost: " + p.layoutManager.position);

        // Case 5: Returning from a chat at position 1 -> follows anchor cleanly.
        p.listView.rows = new View[]{ new View(1, 200, 380), new View(2, 380, 560) };
        p.restoreScrollAnchor(pos -> pos == 1 ? 5 : pos + 4, true);
        check(p.layoutManager.position == 5, "returning from chat anchor: " + p.layoutManager.position);
    }
}'''.replace('RESTORE', restore)})




