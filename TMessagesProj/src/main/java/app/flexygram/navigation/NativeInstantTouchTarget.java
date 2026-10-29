/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;

import android.graphics.Rect;
import android.view.View;
import android.view.ViewGroup;
import org.telegram.ui.Cells.DialogCell;

/**
 * Non-destructive hit test for a *visible* native dialog row. The actual
 * RecyclerListView and its original click listener remain the only input owner.
 * No reconstructed row, synthetic MotionEvent, or cached dialog ID.
 */
public final class NativeInstantTouchTarget {
    private NativeInstantTouchTarget() {}

    /** Native ACTION_DOWN raw coordinates, on the original UI thread. */
    public static boolean isVisibleDialogRow(View root, float rawX, float rawY) {
        if (root == null || !Float.isFinite(rawX) || !Float.isFinite(rawY)) return false;
        return find(root, rawX, rawY, 0, new Search());
    }

    private static final class Search {
        final Rect visible = new Rect();
        final int[] screen = new int[2];
        int remaining = 128;
    }
    private static boolean find(View view, float x, float y, int depth, Search search) {
        if (view == null || --search.remaining < 0 || depth > 16 || view.getVisibility() != View.VISIBLE
                || view.getAlpha() <= .01f || !view.isShown()) return false;
        if (view instanceof DialogCell) {
            return view.isEnabled() && containsVisiblePoint(view, x, y, search.visible, search.screen);
        }
        if (!(view instanceof ViewGroup) || !containsVisiblePoint(view, x, y, search.visible, search.screen)) return false;
        ViewGroup group = (ViewGroup) view;
        for (int i = group.getChildCount() - 1; i >= 0 && search.remaining > 0; i--) {
            if (find(group.getChildAt(i), x, y, depth + 1, search)) return true;
        }
        return false;
    }

    /** Clipped bounds in screen coordinates; Android native view transforms used. */
    public static boolean containsVisiblePoint(View view, float rawX, float rawY) {
        if (view == null || view.getWidth() <= 0 || view.getHeight() <= 0
                || !view.isShown() || view.getAlpha() <= .01f) return false;
        return containsVisiblePoint(view, rawX, rawY, new Rect(), new int[2]);
    }
    private static boolean containsVisiblePoint(View view, float rawX, float rawY, Rect visible, int[] screen) {
        if(view==null || view.getWidth()<=0 || view.getHeight()<=0 || !view.isShown() || view.getAlpha()<=.01f)return false;
        if (!view.getLocalVisibleRect(visible) || visible.isEmpty()) return false;
        view.getLocationOnScreen(screen);
        return rawX >= screen[0] + visible.left && rawX < screen[0] + visible.right
                && rawY >= screen[1] + visible.top && rawY < screen[1] + visible.bottom;
    }
}
