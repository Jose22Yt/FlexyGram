/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.exteraless.player;

import android.graphics.Bitmap;
import android.graphics.Rect;
import android.os.SystemClock;
import android.view.View;
import android.view.ViewTreeObserver;
import java.util.ArrayList;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LiteMode;

/** One bounded backdrop traversal for all visible surfaces in a player. UI-owned. */
final class MusicBlurCapture implements ViewTreeObserver.OnPreDrawListener,
        ViewTreeObserver.OnScrollChangedListener, ViewTreeObserver.OnGlobalLayoutListener {
    private final View root;
    private final ArrayList<MusicBlurSurface> owners = new ArrayList<>();
    private final Rect region = new Rect();
    private ViewTreeObserver observer;
    private boolean pending, dirty = true, trailingPosted;
    private int generation, revision;
    private long lastCapture = -160;
    private final Runnable trailing;
    MusicBlurCapture(View root) {
        this.root = root;
        trailing = () -> {
            trailingPosted = false;
            if (!owners.isEmpty() && !MusicBlurSurface.isFrozen()) root.invalidate();
        };
    }

    void add(MusicBlurSurface owner) {
        if (owners.contains(owner)) return;
        owners.add(owner);
        if (observer == null) {
            observer = root.getViewTreeObserver();
            observer.addOnPreDrawListener(this);
            observer.addOnScrollChangedListener(this);
            observer.addOnGlobalLayoutListener(this);
        }
        markDirty();
    }
    void remove(MusicBlurSurface owner) {
        owners.remove(owner);
        markDirty();
        if (!owners.isEmpty()) return;
        generation++; pending = false; lastCapture = -160;
        root.removeCallbacks(trailing); trailingPosted = false;
        if (observer != null && observer.isAlive()) {
            observer.removeOnPreDrawListener(this);
            observer.removeOnScrollChangedListener(this);
            observer.removeOnGlobalLayoutListener(this);
        }
        observer = null;
    }
    void markDirty() { dirty = true; revision++; if (!owners.isEmpty()) root.invalidate(); }
    @Override public void onScrollChanged() { markDirty(); }
    @Override public void onGlobalLayout() { markDirty(); }

    @Override public boolean onPreDraw() {
        if (owners.isEmpty() || MusicBlurSurface.isFrozen() || MusicBlurSurface.isCapturing()) return true;
        if (!LiteMode.isEnabled(LiteMode.FLAG_CHAT_BLUR)) {
            for (MusicBlurSurface owner : owners) owner.clearCapture();
            dirty = true; return true;
        }
        region.setEmpty();
        for (MusicBlurSurface owner : owners) {
            if (owner.updateGeometry()) { dirty = true; revision++; }
            if (owner.captureVisible) region.union(owner.screenBounds);
        }
        if (!dirty || pending || region.isEmpty()) return true;
        long delay = 160 - (SystemClock.uptimeMillis() - lastCapture);
        if (delay > 0) {
            // Single trailing invalidation after a change; never a periodic frame clock.
            if (!trailingPosted) { trailingPosted = true; root.postDelayed(trailing, delay); }
            return true;
        }
        root.removeCallbacks(trailing); trailingPosted = false;
        final Rect capturedRegion = new Rect(region);
        final int ticket = generation, capturedRevision = revision;
        float downscale = Math.max(8f, Math.max(region.width(), region.height()) / 384f);
        pending = true; dirty = false; lastCapture = SystemClock.uptimeMillis();
        MusicBlurSurface.capturing = true;
        try {
            AndroidUtilities.makeGlobalBlurBitmap(result -> AndroidUtilities.runOnUIThread(() -> {
                if (ticket != generation) { if (result != null) result.recycle(); return; }
                pending = false;
                if (capturedRevision != revision || !LiteMode.isEnabled(LiteMode.FLAG_CHAT_BLUR)) {
                    if (result != null) result.recycle();
                    dirty = true; if (!owners.isEmpty()) root.invalidate(); return;
                }
                for (MusicBlurSurface owner : owners) {
                    if (owner.captureVisible) owner.acceptCapture(result, capturedRegion);
                }
                if (result == null) dirty = true;
            }), downscale, 4, root, null, true, capturedRegion);
        } catch (RuntimeException failed) { pending = false; dirty = true; }
        finally { MusicBlurSurface.capturing = false; }
        return true;
    }
}
