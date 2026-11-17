package app.flexygram.kyant;

import android.graphics.Canvas;
import android.graphics.RecordingCanvas;
import android.graphics.RenderNode;
import android.view.View;
import androidx.annotation.RequiresApi;

/** The two Kyant layers reuse one native icon recording, including labels and badges. */
@RequiresApi(33)
public final class KyantIconSnapshot {
    private final View view;
    private final RenderNode node = new RenderNode("KyantDockIcon");
    private long revision = Long.MIN_VALUE;
    private int width, height;
    public KyantIconSnapshot(View view) { this.view = view; }
    public void draw(Canvas canvas, long revision) {
        if (!canvas.isHardwareAccelerated()) { view.draw(canvas); return; }
        int w = view.getWidth(), h = view.getHeight();
        if (w <= 0 || h <= 0) return;
        if (!node.hasDisplayList() || this.revision != revision || width != w || height != h) {
            node.setPosition(0, 0, w, h);
            RecordingCanvas target = node.beginRecording();
            boolean success = false;
            try { view.draw(target); success = true; }
            finally { node.endRecording(); if (!success) node.discardDisplayList(); }
            width = w; height = h; this.revision = revision;
        }
        canvas.drawRenderNode(node);
    }
    public void release() { node.discardDisplayList(); revision = Long.MIN_VALUE; }
}
