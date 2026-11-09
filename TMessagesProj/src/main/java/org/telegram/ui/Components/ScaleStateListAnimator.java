package org.telegram.ui.Components;

import android.animation.AnimatorSet;
import android.animation.ObjectAnimator;
import android.animation.StateListAnimator;
import android.view.View;
import android.view.animation.OvershootInterpolator;

public class ScaleStateListAnimator {

    public static void apply(View view) {
        apply(view, .1f, 1.5f);
    }

    public static void apply(View view, float scale, float tension) {
        if (view == null) {
            return;
        }
        view.setStateListAnimator(null);
    }

    public static void reset(View view) {
        if (view != null) {
            view.setStateListAnimator(null);
        }
    }

}
