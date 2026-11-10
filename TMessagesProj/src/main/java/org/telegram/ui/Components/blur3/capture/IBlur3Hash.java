package org.telegram.ui.Components.blur3.capture;

import android.graphics.ColorMatrix;
import android.os.Build;
import android.view.View;

public interface IBlur3Hash {

    void add(long value);

    void unsupported();

    default void add(View v) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            add(v.getUniqueDrawingId());
            // A view ID identifies the owner, not its current pixels or composition.
            // Keep scrolling/transitions live and never reuse dirty child content.
            if (v.isDirty() || v.isLayoutRequested()) unsupported();
            addF(v.getX());
            addF(v.getY());
            addF(v.getAlpha());
            addF(v.getScaleX());
            addF(v.getScaleY());
            addF(v.getRotation());
            addF(v.getRotationX());
            addF(v.getRotationY());
            addF(v.getPivotX());
            addF(v.getPivotY());
            add(v.getWidth());
            add(v.getHeight());
            add(v.getScrollX());
            add(v.getScrollY());
            add(v.getVisibility());
        } else {
            unsupported();
        }
    }

    default void addF(float value) {
        add(Float.floatToIntBits(value));
    }

    default void add(boolean value) {
        add(value ? 1 : 0);
    }

    default void add(ColorMatrix colorMatrix) {
        add(colorMatrix.getArray());
    }

    default void add(float[] arr) {
        for (float f : arr) {
            addF(f);
        }
    }
}
