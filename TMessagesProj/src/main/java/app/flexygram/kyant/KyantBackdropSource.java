package app.flexygram.kyant;

import android.graphics.Canvas;
import android.graphics.Matrix;
import java.util.Arrays;
import android.graphics.RecordingCanvas;
import android.graphics.RenderNode;
import android.view.View;
import androidx.annotation.RequiresApi;

/** Raw, cropped View scene for Kyant. No Telegram glass shader, Bitmap capture or CPU readback. */
@RequiresApi(33)
public final class KyantBackdropSource {
    private final View scene;
    private final View anchor;
    private final RenderNode node = new RenderNode("KyantRawDockBackdrop");
    private final Matrix sceneToAnchor = new Matrix();
    private final float[] matrixValues = new float[9], recordedMatrix = new float[9];
    private float recordedInset = Float.NaN;
    private int width, height;
    private long recordedRevision = Long.MIN_VALUE;
    private boolean recording;

    public KyantBackdropSource(View scene, View anchor) { this.scene = scene; this.anchor = anchor; }

    public boolean isRecording() { return recording; }

    public boolean contains(View view) {
        while (view != null) {
            if (view == scene) return true;
            android.view.ViewParent parent = view.getParent();
            view = parent instanceof View ? (View) parent : null;
        }
        return false;
    }

    public void draw(Canvas canvas, int width, int height, long revision, float verticalInset) {
        if (!canvas.isHardwareAccelerated() || width <= 0 || height <= 0 || recording || !scene.isAttachedToWindow()) return;
        sceneToAnchor.reset();
        scene.transformMatrixToGlobal(sceneToAnchor);
        anchor.transformMatrixToLocal(sceneToAnchor);
        sceneToAnchor.getValues(matrixValues);
        if (!node.hasDisplayList() || this.width != width || this.height != height
                || !Arrays.equals(matrixValues, recordedMatrix) || recordedInset != verticalInset || recordedRevision != revision) {
            recording = true;
            // Restrict the offscreen surface to the bar plus the optical sampling margin.
            int margin = Math.round(32 * anchor.getResources().getDisplayMetrics().density);
            node.setPosition(0, 0, width + margin * 2, height + margin * 2);
            RecordingCanvas target = node.beginRecording();
            try {
                target.clipRect(0, 0, node.getWidth(), node.getHeight());
                target.translate(margin, margin - verticalInset);
                target.concat(sceneToAnchor);
                scene.draw(target);
            } finally {
                node.endRecording();
                recording = false;
            }
            this.width = width; this.height = height; recordedInset = verticalInset;
            System.arraycopy(matrixValues, 0, recordedMatrix, 0, 9); recordedRevision = revision;
        }
        int save = canvas.save();
        int margin = Math.round(32 * anchor.getResources().getDisplayMetrics().density);
        canvas.translate(-margin, -margin);
        canvas.drawRenderNode(node);
        canvas.restoreToCount(save);
    }

    public void release() { node.discardDisplayList(); recordedRevision = Long.MIN_VALUE; }
}
