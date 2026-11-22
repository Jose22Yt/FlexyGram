"""Targeted host tests for camera placement, gesture thresholds and opt-in state."""

from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_camera_geometry_and_reversible_drag(tmp_path):
    source = (JAVA / "app/flexygram/notifications/InAppBannerView.java").read_text()
    methods = "\n".join(method(source, signature) for signature in (
        "private static boolean isCameraCutout(",
        "private static float dragProgress(",
        "private static boolean shouldDismiss(",
    ))
    probe(tmp_path, {"Probe.java": """
public class Probe {
    static int dp(float value) { return Math.round(value); }
    record Rect(int width, int height) {}
    METHODS
    static void check(boolean value) { if (!value) throw new AssertionError(); }
    public static void main(String[] args) {
        check(isCameraCutout(new Rect(16, 17), 180, 18, 360, 48));
        check(isCameraCutout(new Rect(16, 17), 38, 18, 360, 48));
        check(!isCameraCutout(new Rect(80, 17), 180, 18, 360, 48));
        check(!isCameraCutout(new Rect(12, 12), 358, 140, 360, 48));
        check(!isCameraCutout(new Rect(10, 0), 180, 18, 360, 48));
        check(dragProgress(1, -12, 60) == 0.8f);
        check(dragProgress(1, 0, 60) == 1);
        check(dragProgress(1, -85, 60) == 0);
        check(!shouldDismiss(0.8f, -250));
        check(shouldDismiss(0.8f, -750));
        check(shouldDismiss(0.5f, 0));
    }
}
""".replace("METHODS", methods)})


def test_alert_selection_count_tracks_enable_and_inheritance(tmp_path):
    source = (JAVA / "app/flexygram/notifications/InAppAlerts.java").read_text()
    methods = "\n".join(method(source, signature) for signature in (
        "public static boolean hasSelections(",
        "private static void saveOptions(",
        "private static String key(",
        "private static String topicCountKey(",
    ))
    probe(tmp_path, {"Probe.java": """
import java.util.HashMap;
import java.util.Map;
public class Probe {
    static final int ENABLED = 1;
    static final String ACTIVE_COUNT = "count";
    static class SharedPreferences {
        final Map<String, Integer> values = new HashMap<>();
        int getInt(String key, int fallback) { return values.getOrDefault(key, fallback); }
        Editor edit() { return new Editor(); }
        class Editor {
            Editor remove(String key) { values.remove(key); return this; }
            Editor putInt(String key, int value) { values.put(key, value); return this; }
            void apply() {}
        }
    }
    METHODS
    static void check(boolean value) { if (!value) throw new AssertionError(); }
    public static void main(String[] args) {
        SharedPreferences settings = new SharedPreferences();
        check(!hasSelections(settings));
        saveOptions(settings, -5, 0, 1);
        saveOptions(settings, -5, 1, 32);
        check(hasSelections(settings) && settings.getInt(ACTIVE_COUNT, 0) == 1);
        saveOptions(settings, -5, 1, 5);
        saveOptions(settings, -5, 1, 17);
        check(settings.getInt(ACTIVE_COUNT, 0) == 2);
        saveOptions(settings, -5, 0, 0);
        check(hasSelections(settings) && settings.getInt(topicCountKey(-5), 0) == 1);
        saveOptions(settings, -5, 1, 0);
        check(!hasSelections(settings) && !settings.values.containsKey(key(-5, 1)));
        check(!settings.values.containsKey(topicCountKey(-5)));
    }
}
""".replace("METHODS", methods)})


def test_normal_message_delivery_offers_alert_before_dispatching_ui_observers():
    source = (JAVA / "org/telegram/messenger/MessagesController.java").read_text()
    update = method(source, "public boolean updateInterfaceWithMessages(")
    dispatch = "postNotificationName(NotificationCenter.didReceiveNewMessages, dialogId, messages, scheduled, mode)"
    assert update.index("isBlockedOrFiltered(message)") < update.index("launch.onFlexyIncomingMessages(")
    assert update.index("launch.onFlexyIncomingMessages(") < update.index(dispatch)
    assert "mode == ChatActivity.MODE_DEFAULT && hasNotOutMessage && launch != null" in update
