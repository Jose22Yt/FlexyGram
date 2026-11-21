package org.telegram.ui.Components.chat;

import android.graphics.PointF;
import android.graphics.RectF;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewParent;
import android.view.ViewTreeObserver;

import androidx.annotation.NonNull;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import java.lang.ref.WeakReference;

/**
 * Tracks position changes of multiple Views relative to a specified ancestor ViewGroup.
 * Coordinates are computed manually by summing getX()/getY() up the hierarchy.
 *
 * Works through a single ViewTreeObserver.OnPreDrawListener attached to the given anchorView.
 */
public final class ViewPositionWatcher implements
        ViewTreeObserver.OnPreDrawListener,
        View.OnAttachStateChangeListener {

    /** Per-view callback invoked when a view's position relative to its parent changes. */
    public interface OnChangedListener {
        void onPositionChanged(@NonNull View view, @NonNull RectF rectInParent);
    }

    public interface OnOffsetChangedListener<T> {
        void onOffsetChanged(T owner, float x, float y);
    }

    private final View anchorView;
    private ViewTreeObserver vto;
    private boolean listening;
    private boolean closed;

    /** Per-view tracking state. */
    private static final class Tracked {
        final ViewGroup parent;
        final OnChangedListener listener;
        final WeakReference<?> lifetime;
        final RectF last = new RectF();
        final boolean multiwindow;
        boolean hasLast;

        Tracked(ViewGroup parent, OnChangedListener listener, boolean multiwindow, WeakReference<?> lifetime) {
            this.parent = parent;
            this.listener = listener;
            this.multiwindow = multiwindow;
            this.lifetime = lifetime;
        }
    }

    private final WeakHashMap<View, List<Tracked>> tracked = new WeakHashMap<>();
    private final WeakHashMap<View, ViewOnPreDraw> multiwindowObservers = new WeakHashMap<>();
    private final RectF tmpRect = new RectF(); // reused for all calculations
    private static final int[] tmpCords = new int[2];

    public ViewPositionWatcher(@NonNull View anchorView) {
        this.anchorView = anchorView;
        anchorView.addOnAttachStateChangeListener(this);
    }

    public void subscribe(@NonNull View view,
                          @NonNull ViewGroup parentView,
                          @NonNull OnChangedListener listener) {
        subscribe(view, parentView, listener, false);
    }

    /** Subscribe a view for tracking relative to the given parent (must be an ancestor). */
    public void subscribe(@NonNull View view,
                          @NonNull ViewGroup parentView,
                          @NonNull OnChangedListener listener,
                          boolean multiwindow) {
        subscribe(view, new Tracked(parentView, listener, multiwindow, null));
    }

    /** Offset observers keep their owner weak and share one invalidation per view. */
    public <T> void subscribeOffsets(@NonNull View view, @NonNull ViewGroup parentView, @NonNull T owner,
            @NonNull OnOffsetChangedListener<T> listener, boolean multiwindow) {
        final WeakReference<T> lifetime = new WeakReference<>(owner);
        subscribe(view, new Tracked(parentView, (v, rect) -> {
            final T liveOwner = lifetime.get();
            if (liveOwner != null) listener.onOffsetChanged(liveOwner, rect.left, rect.top);
        }, multiwindow, lifetime));
    }

    private void subscribe(View view, Tracked t) {
        if (closed) return;
        List<Tracked> tList = tracked.get(view);
        if (tList == null) {
            tList = new ArrayList<>(1);
            tracked.put(view, tList);
        }
        tList.add(t);

        ensureListening();

        if (t.multiwindow && !multiwindowObservers.containsKey(view)) {
            multiwindowObservers.put(view, new ViewOnPreDraw(view, anchorView, this));
        }
    }

    /** Unsubscribe a specific view. */
    public void unsubscribe(@NonNull View view) {
        tracked.remove(view);
        ViewOnPreDraw observer = multiwindowObservers.remove(view);
        if (observer != null) observer.destroy();
        if (tracked.isEmpty()) detachIfListening();
    }

    /** Clear all subscriptions. */
    public void clear() {
        for (ViewOnPreDraw observer : multiwindowObservers.values()) observer.destroy();
        multiwindowObservers.clear();
        tracked.clear();
        detachIfListening();
    }

    /** Stop watching entirely. */
    public void shutdown() {
        closed = true;
        anchorView.removeOnAttachStateChangeListener(this);
        clear();
    }

    // ─────────────── ViewTreeObserver lifecycle ───────────────

    private void attachIfPossible() {
        if (tracked.isEmpty() || !anchorView.isAttachedToWindow()) return;
        ViewTreeObserver newVto = anchorView.getViewTreeObserver();
        if (newVto != null && newVto.isAlive()) {
            vto = newVto;
            if (!listening) {
                vto.addOnPreDrawListener(this);
                listening = true;
            }
        }
    }

    private void ensureListening() {
        if (!listening) attachIfPossible();
    }

    private void detachIfListening() {
        if (listening && vto != null && vto.isAlive()) {
            vto.removeOnPreDrawListener(this);
        }
        listening = false;
        vto = null;
    }

    @Override
    public void onViewAttachedToWindow(@NonNull View v) {
        attachIfPossible();
    }

    @Override
    public void onViewDetachedFromWindow(@NonNull View v) {
        if (v == anchorView) {
            detachIfListening();
        }
    }

    // ─────────────── OnPreDraw ───────────────

    @Override
    public boolean onPreDraw() {
        // Reattach if VTO changed
        ViewTreeObserver current = anchorView.getViewTreeObserver();
        if (current != vto) {
            detachIfListening();
            attachIfPossible();
        }

        final Iterator<Map.Entry<View, List<Tracked>>> entries = tracked.entrySet().iterator();
        while (entries.hasNext()) {
            final Map.Entry<View, List<Tracked>> e = entries.next();
            View view = e.getKey();
            List<Tracked> tList = e.getValue();
            if (view == null || tList == null) continue;

            ViewGroup previousParent = null;
            boolean previousMultiwindow = false, rectValid = false, hasMultiwindow = false, invalidateOffsets = false;
            for (int i = 0; i < tList.size(); i++) {
                final Tracked t = tList.get(i);
                if (t.lifetime != null && t.lifetime.get() == null) {
                    tList.remove(i--);
                    continue;
                }
                hasMultiwindow |= t.multiwindow;
                if (previousParent != t.parent || previousMultiwindow != t.multiwindow) {
                    previousParent = t.parent;
                    previousMultiwindow = t.multiwindow;
                    if (t.multiwindow) {
                        view.getLocationOnScreen(tmpCords);
                        tmpRect.set(tmpCords[0], tmpCords[1], tmpCords[0] + view.getWidth(), tmpCords[1] + view.getHeight());
                        t.parent.getLocationOnScreen(tmpCords);
                        tmpRect.offset(-tmpCords[0], -tmpCords[1]);
                        rectValid = true;
                    } else {
                        rectValid = computeRectInParent(view, t.parent, tmpRect);
                    }
                }
                if (!rectValid) continue;

                final boolean changed = t.lifetime != null
                        ? tmpRect.left != t.last.left || tmpRect.top != t.last.top : !tmpRect.equals(t.last);
                if (!t.hasLast || changed) {
                    t.last.set(tmpRect);
                    t.hasLast = true;
                    try {
                        t.listener.onPositionChanged(view, t.lifetime != null ? tmpRect : new RectF(tmpRect));
                        invalidateOffsets |= t.lifetime != null;
                    } catch (Throwable ignored) {
                        // Do not crash UI if callback throws
                    }
                }
            }
            if (invalidateOffsets) view.invalidate();
            if (tList.isEmpty()) entries.remove();
            if (!hasMultiwindow) {
                final ViewOnPreDraw observer = multiwindowObservers.remove(view);
                if (observer != null) observer.destroy();
            }
        }
        if (tracked.isEmpty()) detachIfListening();
        return true;
    }

    // ─────────────── Coordinate calculation ───────────────

    public static float computeYCoordinateInParent(@NonNull View view, @NonNull ViewGroup parentView) {
        computeRectInParent(view, parentView, tmpRectF2);
        return tmpRectF2.top;
    }

    public static float computeXCoordinateInParent(@NonNull View view, @NonNull ViewGroup parentView) {
        computeRectInParent(view, parentView, tmpRectF2);
        return tmpRectF2.left;
    }

    private static RectF tmpRectF2 = new RectF();
    public static boolean computeCoordinatesInParent(@NonNull View view,
                                                   @NonNull ViewGroup parentView, PointF out) {
        final boolean result = computeRectInParent(view, parentView, tmpRectF2);
        if (result) {
            out.x = tmpRectF2.left;
            out.y = tmpRectF2.top;
        }

        return result;
    }

    /**
     * Compute the view's rect in parentView coordinates
     * by summing getX()/getY() up the hierarchy until reaching parentView.
     *
     * @return false if parentView is not an ancestor of view.
     */

    public static boolean computeRectInParent(@NonNull View view,
                                               @NonNull View parentView,
                                               @NonNull RectF out) {
        float left = 0f;
        float top = 0f;

        View current = view;
        while (current != null && current != parentView) {
            left += current.getX();
            top  += current.getY();

            ViewParent vp = current.getParent();
            if (!(vp instanceof View)) {
                return false; // parentView not found in hierarchy
            }
            View parent = (View) vp;
            left -= parent.getScrollX();
            top  -= parent.getScrollY();

            current = parent;
        }

        if (current != parentView) {
            // parentView not found in ancestor chain
            return false;
        }

        final float l = left;
        final float t = top;
        final float r = l + view.getWidth();
        final float b = t + view.getHeight();
        out.set(l, t, r, b);
        return true;
    }







    private static class ViewOnPreDraw {

        private final WeakReference<View> viewReference;
        private final WeakReference<View> anchorReference;
        private final ViewTreeObserver.OnPreDrawListener listener;

        private ViewTreeObserver viewTreeObserver;

        public ViewOnPreDraw(
                @NonNull View view,
                @NonNull View anchor,
                @NonNull ViewTreeObserver.OnPreDrawListener listener
        ) {
            this.viewReference = new WeakReference<>(view);
            this.anchorReference = new WeakReference<>(anchor);
            this.listener = listener;

            view.addOnAttachStateChangeListener(attachStateChangeListener);

            if (view.isAttachedToWindow()) {
                attach();
            }
        }

        private final View.OnAttachStateChangeListener attachStateChangeListener =
                new View.OnAttachStateChangeListener() {
                    @Override
                    public void onViewAttachedToWindow(@NonNull View v) {
                        attach();
                    }

                    @Override
                    public void onViewDetachedFromWindow(@NonNull View v) {
                        detach();
                    }
                };

        private void attach() {
            View view = viewReference.get();
            if (view == null) return;
            ViewTreeObserver observer = view.getViewTreeObserver();
            View anchor = anchorReference.get();
            if (anchor != null && observer == anchor.getViewTreeObserver()) {
                detach();
                return;
            }
            if (viewTreeObserver == observer) {
                return;
            }

            detach();

            viewTreeObserver = observer;
            if (observer.isAlive()) {
                observer.addOnPreDrawListener(listener);
            }
        }

        private void detach() {
            if (viewTreeObserver == null) {
                return;
            }

            if (viewTreeObserver.isAlive()) {
                viewTreeObserver.removeOnPreDrawListener(listener);
            }
            viewTreeObserver = null;
        }

        public void destroy() {
            detach();
            View view = viewReference.get();
            if (view != null) view.removeOnAttachStateChangeListener(attachStateChangeListener);
        }
    }
}
