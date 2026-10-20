package org.telegram.ui.beta;

import android.view.View;
import android.view.ViewTreeObserver;
import java.util.function.BooleanSupplier;
import java.util.function.Consumer;

/** beta_idle_predraw_frame_v1: idle scene pre-draw followed by frame callback, NOT physical presentation. */
final class SceneFrameObserver {
    private final View view;
    private final BooleanSupplier currentAndIdle;
    private final Consumer<Boolean> completion;
    private ViewTreeObserver tree;
    private boolean finished;
    private final Runnable timeout = () -> complete(false);
    private final Runnable frame = this::afterFrame;
    private final ViewTreeObserver.OnPreDrawListener draw = this::beforeDraw;

    SceneFrameObserver(View view, BooleanSupplier currentAndIdle, Consumer<Boolean> completion) {
        this.view = view; this.currentAndIdle = currentAndIdle; this.completion = completion;
    }
    void start() {
        tree = view.getViewTreeObserver();
        if (!tree.isAlive()) { complete(null); return; }
        tree.addOnPreDrawListener(draw);
        view.postDelayed(timeout, 5000); // observer timeout only; never alters the animation
        view.invalidate();
    }
    private boolean visible() { return view.isAttachedToWindow() && view.isShown() && view.hasWindowFocus()
            && view.getWidth() > 0 && view.getHeight() > 0; }
    private boolean beforeDraw() {
        if (!finished && currentAndIdle.getAsBoolean() && visible()) {
            removeDraw(); view.postOnAnimation(frame);
        }
        return true; // the observer must never veto drawing
    }
    private void afterFrame() { if (!finished) complete(currentAndIdle.getAsBoolean() && visible() ? Boolean.TRUE : null); }
    private void removeDraw() { if (tree != null && tree.isAlive()) tree.removeOnPreDrawListener(draw); }
    private void complete(Boolean result) {
        if (finished) return;
        cancel(); completion.accept(result);
    }
    void cancel() { finished = true; removeDraw(); view.removeCallbacks(timeout); view.removeCallbacks(frame); }
}
