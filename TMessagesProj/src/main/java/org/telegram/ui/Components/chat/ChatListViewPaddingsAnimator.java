package org.telegram.ui.Components.chat;

import android.view.View;

import androidx.recyclerview.widget.RecyclerView;

import org.telegram.messenger.FileLog;

public class ChatListViewPaddingsAnimator {
    private final RecyclerView recyclerView;
    private int pendingTopOffset;

    private final View.OnLayoutChangeListener applyTopOffset = (view, left, top, right, bottom,
            oldLeft, oldTop, oldRight, oldBottom) -> applyPendingOffset();

    public ChatListViewPaddingsAnimator(RecyclerView recyclerView) {
        this.recyclerView = recyclerView;
    }

    public void setPaddings(int paddingTop, float paddingBottomAnimated, boolean allowScrollCompensation) {
        final int paddingBottom = Math.round(paddingBottomAnimated);
        final int dy = recyclerView.getPaddingTop() - paddingTop;
        if (!allowScrollCompensation && pendingTopOffset != 0) {
            pendingTopOffset = 0;
            recyclerView.removeOnLayoutChangeListener(applyTopOffset);
        }
        if (dy == 0 && recyclerView.getPaddingBottom() == paddingBottom) return;

        if (allowScrollCompensation && dy != 0
                && recyclerView.canScrollVertically(dy < 0 ? 1 : -1)) {
            if (pendingTopOffset == 0) recyclerView.addOnLayoutChangeListener(applyTopOffset);
            pendingTopOffset += dy;
            if (pendingTopOffset == 0) recyclerView.removeOnLayoutChangeListener(applyTopOffset);
        }
        recyclerView.setPadding(recyclerView.getPaddingLeft(), paddingTop, recyclerView.getPaddingRight(), paddingBottom);
    }

    private void applyPendingOffset() {
        recyclerView.removeOnLayoutChangeListener(applyTopOffset);
        final int dy = pendingTopOffset;
        pendingTopOffset = 0;
        if (dy == 0) return;
        try {
            recyclerView.scrollBy(0, dy);
        } catch (RuntimeException error) {
            FileLog.e(error);
        }
    }

    public int getCurrentAdditionalHeight() {
        return 0;
    }
}
