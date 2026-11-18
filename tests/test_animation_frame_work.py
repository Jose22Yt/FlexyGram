"""Regression checks for frame ownership and duplicate message redraw requests."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_classic_navigation_reuses_one_vsync_callback_and_handles_stalls(tmp_path):
    source = (JAVA / 'org/telegram/ui/ActionBar/ActionBarLayout.java').read_text()
    start = source.index('        final Choreographer choreographer', source.index('private void startLayoutAnimation('))
    end = source.index('\n    }', start)
    frame = source[start:end]
    # Stub rendering only. Keep the real clock, ownership, scheduling and finish paths.
    render_start = frame.index('                if (newFragment != null)')
    render_end = frame.index('                if (layoutAnimationFrame != this) return;', render_start)
    frame = frame[:render_start] + '                drawn.add(animationProgress);\n' + frame[render_end:]
    probe(tmp_path, {'Probe.java': '''import java.util.*;
class Choreographer {
    interface FrameCallback { void doFrame(long time); }
    static final Choreographer INSTANCE = new Choreographer();
    final ArrayDeque<FrameCallback> next = new ArrayDeque<>();
    static Choreographer getInstance() { return INSTANCE; }
    void postFrameCallback(FrameCallback callback) { next.add(callback); }
    void draw(long timestamp) { next.remove().doFrame(timestamp); }
}
public class Probe {
    Choreographer.FrameCallback layoutAnimationFrame;
    long transitionAnimationStartTime;
    float animationProgress;
    int completions;
    final List<Float> drawn = new ArrayList<>();
    void onAnimationEndCheck(boolean byCheck) { completions++; }
    void start(boolean open, boolean preview) { CALLBACK }
    public static void main(String[] args) {
        Probe p = new Probe();
        Choreographer clock = Choreographer.getInstance();
        p.start(true, false);
        var same = clock.next.peek();
        clock.draw(1_000_000L);
        if (clock.next.size() != 1 || clock.next.peek() != same || p.animationProgress != 0f)
            throw new AssertionError("callback was replaced or queued more than once");
        clock.draw(76_000_000L);
        if (p.animationProgress != .5f || clock.next.peek() != same) throw new AssertionError("elapsed time");
        clock.draw(210_000_000L);
        if (p.animationProgress != 1f || p.completions != 1 || !clock.next.isEmpty())
            throw new AssertionError("stalled frame prolonged the animation");
        p.start(true, true);
        clock.draw(220_000_000L);
        p.layoutAnimationFrame = null;
        clock.draw(230_000_000L);
        if (p.drawn.size() != 4 || p.completions != 1 || !clock.next.isEmpty())
            throw new AssertionError("cancelled frame applied changes");
    }
}'''.replace('CALLBACK', frame)})
    completion = method(source, 'private void onAnimationEndCheck(boolean byCheck)')
    assert 'removeFrameCallback(layoutAnimationFrame)' in completion


def test_message_batches_share_one_redraw_animator_and_cancel_on_end(tmp_path):
    source = (JAVA / 'org/telegram/ui/recyclerview/ChatListItemAnimator.java').read_text()
    implementation = method(source, 'private void startListRedraw()')
    probe(tmp_path, {'Probe.java': '''class ValueAnimator {
    interface Listener { void update(ValueAnimator a); }
    static int allocations;
    Listener listener;
    boolean started;
    long duration, playTime;
    static ValueAnimator ofFloat(float a, float b) { allocations++; return new ValueAnimator(); }
    boolean isStarted() { return started; }
    long getCurrentPlayTime() { return playTime; }
    long getDuration() { return duration; }
    void cancel() { started = false; }
    void addUpdateListener(Listener listener) { this.listener = listener; }
    void setDuration(long duration) { this.duration = duration; }
    void start() { started = true; playTime = 0; }
}
public class Probe {
    static class ListView { int redraws; void invalidate() { redraws++; } }
    static class Activity { int redraws; void onListItemAnimatorTick() { redraws++; } }
    final ListView recyclerListView = new ListView();
    final Activity activity = new Activity();
    ValueAnimator listRedrawAnimator;
    long moveDuration = 150;
    long getMoveDuration() { return moveDuration; }
    long getRemoveDuration() { return 100; }
    IMPLEMENTATION
    public static void main(String[] args) {
        Probe p = new Probe();
        p.startListRedraw();
        var animator = p.listRedrawAnimator;
        animator.playTime = 30;
        p.moveDuration = 50;
        p.startListRedraw();
        if (animator.playTime != 30 || animator.duration != 250) throw new AssertionError("shortened live batch");
        p.moveDuration = 180;
        p.startListRedraw();
        if (animator.playTime != 0 || animator.duration != 280 || p.listRedrawAnimator != animator
                || ValueAnimator.allocations != 1) throw new AssertionError("duplicated ticker");
        animator.listener.update(animator);
        if (p.activity.redraws != 1 || p.recyclerListView.redraws != 0) throw new AssertionError("wrong redraw");
    }
}'''.replace('IMPLEMENTATION', implementation)})
    assert 'listRedrawAnimator.cancel()' in method(source, 'public void endAnimations()')
