"""Regression checks for frame ownership and duplicate message redraw requests."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_navigation_counts_one_open_and_owns_the_correct_swipe_pointer(tmp_path):
    source = (JAVA / 'org/telegram/ui/ActionBar/ActionBarLayout.java').read_text()
    methods = '\n'.join(method(source, signature) for signature in (
        'private static Runnable openingTransitionStart(', 'private static boolean isSwipeRelease(',
    ))
    touch = method(source, 'public boolean onTouchEvent(MotionEvent ev)')
    assert 'final boolean backAnimation = cancelled ||' in touch
    assert 'ev.findPointerIndex(startedTrackingPointerId)' in touch
    assert 'getXVelocity(startedTrackingPointerId)' in touch
    present = method(source, 'public boolean presentFragment(NavigationParams params)')
    assert present.count('!fragment.needDelayOpenAnimation()') == 1
    assert 'onOpenAnimationEndRunnable = () -> {\n                    dispatchOpenStart.run();' in present
    probe(tmp_path, {'Probe.java': '''
public class Probe {
    record MotionEvent(int actionIndex, int... ids) {
        static final int ACTION_CANCEL=3, ACTION_UP=1, ACTION_POINTER_UP=6;
        int getActionIndex() { return actionIndex; }
        int getPointerId(int i) { return ids[i]; }
    }
    static class BaseFragment {
        int starts; boolean open; Runnable reenter;
        void onTransitionAnimationStart(boolean opening, boolean backward) {
            starts++; open=opening; if (reenter!=null) reenter.run();
        }
    }
    METHODS
    static void check(boolean valid) { if (!valid) throw new AssertionError(); }
    public static void main(String[] args) {
        BaseFragment previous=new BaseFragment(), opening=new BaseFragment();
        Runnable start=openingTransitionStart(previous,opening);
        previous.reenter=start;
        start.run(); start.run(); check(previous.starts==1 && !previous.open && opening.starts==1 && opening.open);
        check(isSwipeRelease(new MotionEvent(0),MotionEvent.ACTION_CANCEL,12));
        check(!isSwipeRelease(new MotionEvent(0,7,12),MotionEvent.ACTION_POINTER_UP,12));
        check(isSwipeRelease(new MotionEvent(1,7,12),MotionEvent.ACTION_POINTER_UP,12));
        check(isSwipeRelease(new MotionEvent(0,12),MotionEvent.ACTION_UP,12));
    }
}'''.replace('METHODS', methods)})


def test_dialog_preview_blur_publishes_only_while_preview_is_current(tmp_path):
    source = (JAVA / 'org/telegram/ui/DialogsActivity.java').read_text()
    methods = '\n'.join(method(source, signature) for signature in (
        'private void clearPreviewBlur()', 'private void prepareBlurBitmap()',
    )).replace('app.flexygram.performance.AsyncBitmapBlur', 'AsyncBitmapBlur').replace('<DialogsActivity>', '<Probe>').replace('final DialogsActivity current', 'final Probe current')
    assert 'if (isOpen) clearPreviewBlur();' in method(source, 'public void onTransitionAnimationEnd(')
    probe(tmp_path, {'Probe.java': '''import java.util.*;
import java.util.function.Consumer;
public class Probe {
    static class Bitmap {
        static int allocations; boolean recycled;
        enum Config { ARGB_8888 }
        static Bitmap createBitmap(int w,int h,Config config) { allocations++; return new Bitmap(); }
        void eraseColor(int color) {} void recycle() { recycled=true; }
    }
    static class Canvas { Canvas(Bitmap b) {} void scale(float x,float y) {} }
    record BitmapDrawable(Object resources,Bitmap bitmap) {}
    static class View {
        static final int VISIBLE=0,GONE=8;
        int visibility=GONE,width=720,height=1440; float alpha; Object background;
        int getVisibility() { return visibility; } void setVisibility(int value) { visibility=value; }
        int getMeasuredWidth() { return width; } int getMeasuredHeight() { return height; }
        void setBackground(Object value) { background=value; } void setAlpha(float value) { alpha=value; }
        Object getResources() { return this; } void draw(Canvas canvas) {}
    }
    static class Theme { static final int key_windowBackgroundWhite=1; }
    static class SharedConfig { static boolean enabled=true; static boolean chatBlurEnabled() { return enabled; } }
    static class Parent { boolean preview=true; boolean isInPreviewMode() { return preview; } }
    static class AsyncBitmapBlur {
        static boolean accepted=true; static Bitmap last; static final Deque<Runnable> work=new ArrayDeque<>();
        static boolean submit(Bitmap image,int radius,String section,Consumer<Bitmap> done) {
            last=image; if (!accepted) return false; work.add(() -> done.accept(image)); return true;
        }
    }
    View fragmentView=new View(), blurredView=new View(); Parent parentLayout=new Parent();
    int previewBlurGeneration; boolean previewBlurPending; float previewBlurAlpha;
    int getThemedColor(int color) { return color; } void checkUi_mainTabsVisible() {}
    METHODS
    static void check(boolean valid) { if (!valid) throw new AssertionError(); }
    public static void main(String[] args) {
        Probe p=new Probe(); SharedConfig.enabled=false; p.prepareBlurBitmap(); check(Bitmap.allocations==0);
        SharedConfig.enabled=true; p.fragmentView.width=0; p.prepareBlurBitmap(); check(Bitmap.allocations==0);
        p.fragmentView.width=720; p.prepareBlurBitmap(); Bitmap stale=AsyncBitmapBlur.last;
        p.clearPreviewBlur(); AsyncBitmapBlur.work.remove().run(); check(stale.recycled && p.blurredView.background==null);
        p.prepareBlurBitmap(); p.previewBlurAlpha=.5f; AsyncBitmapBlur.work.remove().run();
        check(p.blurredView.visibility==View.VISIBLE && p.blurredView.alpha==.5f && !p.previewBlurPending);
        p.prepareBlurBitmap(); p.parentLayout.preview=false; AsyncBitmapBlur.work.remove().run();
        check(AsyncBitmapBlur.last.recycled && p.blurredView.background==null);
        AsyncBitmapBlur.accepted=false; p.prepareBlurBitmap(); check(AsyncBitmapBlur.last.recycled && !p.previewBlurPending);
    }
}'''.replace('METHODS', methods)})


def test_emoji_effects_share_a_frame_index_and_fade_by_elapsed_time(tmp_path):
    source = (JAVA / 'org/telegram/ui/EmojiAnimationsOverlay.java').read_text()
    methods = '\n'.join(method(source, signature) for signature in (
        'private static MessageObject effectAnchorMessage(', 'private void indexEffectAnchors(',
        'private View findEffectAnchor(', 'public void draw(Canvas canvas)',
        'private void updateRemovalProgress(',
    ))
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
    record MessageObject(int id) { int getId() { return id; } }
    static class View {}
    static class ChatMessageCell extends View {
        MessageObject message;
        ChatMessageCell(Integer id) { message=id==null ? null : new MessageObject(id); }
        MessageObject getMessageObject() { return message; }
    }
    static class ChatActionCell extends View {
        MessageObject getMessageObject() { return new MessageObject(21); }
    }
    static class Canvas {}
    static class SparseArray<T> {
        Map<Integer,T> data=new HashMap<>();
        int indexOfKey(int key) { return data.containsKey(key) ? 0 : -1; }
        void put(int key,T value) { data.put(key,value); }
        T get(int key) { return data.get(key); }
        void clear() { data.clear(); }
    }
    static class ListView {
        final List<View> rows=new ArrayList<>(); int visits;
        int getChildCount() { return rows.size(); }
        View getChildAt(int i) { visits++; return rows.get(i); }
    }
    final ListView listView=new ListView();
    final List<Integer> drawingObjects=new ArrayList<>();
    final Object chatActivity=new Object();
    SparseArray<View> effectAnchors;
    long removeStartTime=-1;
    float removeProgress;
    final List<View> matches=new ArrayList<>();
    void drawEffects(Canvas canvas, SparseArray<View> anchors) {
        matches.clear();
        for (int id:drawingObjects) matches.add(anchors==null ? findEffectAnchor(id) : anchors.get(id));
    }
    METHODS
    static void check(boolean valid) { if (!valid) throw new AssertionError(); }
    public static void main(String[] args) {
        Probe p=new Probe();
        View first=new ChatMessageCell(10), action=new ChatActionCell();
        p.listView.rows.addAll(List.of(first,new ChatMessageCell(10),new ChatMessageCell(null),new View(),action));
        p.drawingObjects.addAll(List.of(21,10,10,99,21,99,21,10));
        p.draw(new Canvas());
        check(p.listView.visits==5 && p.matches.get(0)==action && p.matches.get(1)==first && p.matches.get(3)==null);
        check(p.effectAnchors.data.isEmpty());
        p.listView.rows.set(0,new ChatMessageCell(30));
        p.draw(new Canvas());
        check(p.matches.get(1)==p.listView.rows.get(1) && p.effectAnchors.data.isEmpty());
        p.drawingObjects.clear(); p.drawingObjects.add(30); p.listView.visits=0;
        p.draw(new Canvas());
        check(p.listView.visits==1 && p.matches.get(0)==p.listView.rows.get(0));
        Probe sixty=new Probe(), oneTwenty=new Probe();
        for (int i=0;i<=4;i++) sixty.updateRemovalProgress(1000+16*i);
        for (int i=0;i<=8;i++) oneTwenty.updateRemovalProgress(1000+8*i);
        check(sixty.removeProgress==oneTwenty.removeProgress && sixty.removeProgress<1f);
        sixty.updateRemovalProgress(1150); oneTwenty.updateRemovalProgress(1190);
        check(sixty.removeProgress==1f && oneTwenty.removeProgress==1f);
    }
}'''.replace('METHODS', methods)})
    chat = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    end_callback = method(chat, 'public void onAllEffectsEnd()')
    assert 'invalidateMessagesVisiblePart()' in end_callback
    assert 'updateMessagesVisiblePart(' not in end_callback


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
