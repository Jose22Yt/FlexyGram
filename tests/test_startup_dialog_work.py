"""Check draft selection and scroll phase updates using actual production methods."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_top_level_drafts_snapshot_excludes_topic_only_entries(tmp_path):
    source = (JAVA / 'org/telegram/messenger/MessagesStorage.java').read_text()
    implementation = method(source, 'private long[] getTopLevelDraftDialogIds()')
    probe(tmp_path, {'Probe.java': '''import java.util.*;
class TLRPC { static class DraftMessage {} }
class LongSparseArray<T> {
    final List<Long> keys = new ArrayList<>();
    final List<T> values = new ArrayList<>();
    void put(long key, T value) { keys.add(key); values.add(value); }
    int size() { return keys.size(); }
    long keyAt(int i) { return keys.get(i); }
    T valueAt(int i) { return values.get(i); }
    T get(long key) { int i = keys.indexOf(key); return i < 0 ? null : values.get(i); }
}
public class Probe {
    final LongSparseArray<LongSparseArray<TLRPC.DraftMessage>> drafts = new LongSparseArray<>();
    Probe getMediaDataController() { return this; }
    LongSparseArray<LongSparseArray<TLRPC.DraftMessage>> getDrafts() { return drafts; }
    IMPLEMENTATION
    public static void main(String[] args) {
        Probe p = new Probe();
        if (p.getTopLevelDraftDialogIds() != null) throw new AssertionError("empty");
        var draft = new TLRPC.DraftMessage();
        var topic = new LongSparseArray<TLRPC.DraftMessage>();
        topic.put(12, draft);
        p.drafts.put(-200, topic);
        if (p.getTopLevelDraftDialogIds() != null) throw new AssertionError("topic only");
        var normal = new LongSparseArray<TLRPC.DraftMessage>();
        normal.put(0, draft);
        p.drafts.put(-45, normal);
        p.drafts.put(31, normal);
        if (!Arrays.equals(p.getTopLevelDraftDialogIds(), new long[]{-45, 31}))
            throw new AssertionError("only top-level peers belong to the first page");
    }
}'''.replace('IMPLEMENTATION', implementation)})


def test_scroll_updates_only_changed_blur_render_node_axes(tmp_path):
    source = (JAVA / 'org/telegram/ui/Components/blur3/DownscaleScrollableNoiseSuppressor.java').read_text()
    implementation = method(source, 'public void onScrolled(float dx, float dy)')
    probe(tmp_path, {'Probe.java': '''class RenderNode {
    int writesX, writesY;
    float x, y;
    void setTranslationX(float x) { this.x = x; writesX++; }
    void setTranslationY(float y) { this.y = y; writesY++; }
}
public class Probe {
    boolean allowNoiseSuppress = true;
    int scaleX = 4, scaleY = 8;
    float scrollX, scrollY;
    RenderNode renderNodeOriginalWithOffset = new RenderNode();
    RenderNode[] renderNodeRestored = { new RenderNode(), new RenderNode() };
    IMPLEMENTATION
    public static void main(String[] args) {
        Probe p = new Probe();
        p.onScrolled(0, 5);
        p.onScrolled(0, 8);
        p.onScrolled(1, 0);
        RenderNode original = p.renderNodeOriginalWithOffset;
        if (original.writesX != 1 || original.writesY != 1 || original.x != 1 || original.y != 5)
            throw new AssertionError("unchanged phase was written or changed phase was lost");
        for (RenderNode node : p.renderNodeRestored)
            if (node.x != -1 || node.y != -5 || node.writesX != 1 || node.writesY != 1)
                throw new AssertionError("wrong restore phase");
        p.allowNoiseSuppress = false;
        p.onScrolled(2, 2);
        if (original.writesX != 1 || original.writesY != 1) throw new AssertionError("disabled");
    }
}'''.replace('IMPLEMENTATION', implementation)})


def test_scheduled_read_waits_for_a_usable_chat_including_empty_history(tmp_path):
    source = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    implementation = method(source, 'private boolean canLoadInitialScheduledMessages()')
    probe(tmp_path, {'Probe.java': '''public class Probe {
    boolean isFinished, paused, firstLoading = true;
    View contentView;
    static class View {
        boolean attached = true, shown = true, layout;
        boolean isAttachedToWindow() { return attached; }
        boolean isShown() { return shown; }
        boolean isLayoutRequested() { return layout; }
    }
    IMPLEMENTATION
    public static void main(String[] args) {
        Probe p = new Probe();
        p.contentView = new View();
        if (p.canLoadInitialScheduledMessages()) throw new AssertionError("still loading");
        p.firstLoading = false;
        if (!p.canLoadInitialScheduledMessages()) throw new AssertionError("empty chat can use its composer");
        p.paused = true;
        if (p.canLoadInitialScheduledMessages()) throw new AssertionError("paused");
        p.paused = false;
        p.contentView.attached = false;
        if (p.canLoadInitialScheduledMessages()) throw new AssertionError("detached");
        p.contentView.attached = true;
        p.isFinished = true;
        if (p.canLoadInitialScheduledMessages()) throw new AssertionError("closed");
    }
}'''.replace('IMPLEMENTATION', implementation)})
