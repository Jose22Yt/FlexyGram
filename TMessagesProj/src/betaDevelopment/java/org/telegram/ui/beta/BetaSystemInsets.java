package org.telegram.ui.beta;

import android.content.Context;
import android.view.View;
import android.widget.FrameLayout;

import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

/** Own system-bar/cutout padding once; leave remaining IME insets to ActionBarLayout. */
final class BetaSystemInsets {
    private BetaSystemInsets() {}

    static FrameLayout wrap(Context context, View content) {
        FrameLayout root = new FrameLayout(context);
        root.addView(content, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));
        ViewCompat.setOnApplyWindowInsetsListener(root, (view, insets) -> {
            Insets bars = insets.getInsets(WindowInsetsCompat.Type.systemBars()
                    | WindowInsetsCompat.Type.displayCutout());
            // Absolute padding: repeated dispatch must not accumulate space.
            view.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            return insets.inset(bars.left, bars.top, bars.right, bars.bottom);
        });
        return root;
    }
}
