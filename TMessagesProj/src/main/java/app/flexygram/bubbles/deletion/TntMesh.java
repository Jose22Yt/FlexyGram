/* Adapted from Bubble Fracture v1.0 by @larrat23, supplied with this change.
 * Original attribution retained; see CREDITS.md. */

package app.flexygram.bubbles.deletion;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/** Rectangular tiles keep the original bubble visible in a block-style explosion. */
public final class TntMesh {
    private TntMesh() {}

    public static List<FractureMesh.Piece> make(float width, float height, int count, long seed) {
        if (width <= 0f || height <= 0f) throw new IllegalArgumentException("Empty bubble");
        count = Math.max(12, Math.min(64, count));
        int rows = Math.max(1, Math.min(count, Math.round((float) Math.sqrt(count * height / width))));
        Random random = new Random(seed);
        List<FractureMesh.Piece> tiles = new ArrayList<FractureMesh.Piece>(count);
        for (int row = 0; row < rows; row++) {
            int columns = count / rows + (row < count % rows ? 1 : 0);
            float top = height * row / rows;
            float bottom = height * (row + 1) / rows;
            for (int column = 0; column < columns; column++) {
                float left = width * column / columns;
                float right = width * (column + 1) / columns;
                float x = (left + right) * .5f;
                float y = (top + bottom) * .5f;
                float dx = (x / width - .5f) * 2f + (random.nextFloat() - .5f) * .35f;
                float dy = (y / height - .5f) * 2f + (random.nextFloat() - .5f) * .35f;
                float length = Math.max(.15f, (float) Math.sqrt(dx * dx + dy * dy));
                float impulse = .55f + random.nextFloat() * .55f;
                tiles.add(new FractureMesh.Piece(
                    new float[] {left, top, right, top, right, bottom, left, bottom},
                    x, y, 0f, dx / length * impulse, dy / length * impulse,
                    (random.nextFloat() - .5f) * 150f
                ));
            }
        }
        return tiles;
    }
}
