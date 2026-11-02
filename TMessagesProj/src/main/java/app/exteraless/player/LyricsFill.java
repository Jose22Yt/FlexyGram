package app.exteraless.player;

import android.graphics.LinearGradient;
import android.graphics.Shader;

/** One shader per visible/recycled lyric line. Geometry stays in the caller's matrix. */
final class LyricsFill {
    private LinearGradient shader;
    private int filled;
    private int unfilled;

    LinearGradient get(int filledColor, int unfilledColor) {
        if (shader == null || filled != filledColor || unfilled != unfilledColor) {
            filled = filledColor;
            unfilled = unfilledColor;
            shader = new LinearGradient(0, 0, 0, 1, filled, unfilled, Shader.TileMode.CLAMP);
        }
        return shader;
    }

    void clear() {
        shader = null;
    }
}
