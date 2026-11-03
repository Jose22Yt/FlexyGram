package org.telegram.ui.Components.blur3;

import android.graphics.Canvas;
import android.graphics.RecordingCanvas;
import android.graphics.RenderNode;
import android.os.Build;

import androidx.annotation.RequiresApi;

import org.telegram.ui.Components.blur3.capture.IBlur3Hash;

@RequiresApi(api = Build.VERSION_CODES.Q)
public class RenderNodeWithHash {
    public static final long HASH_UNSUPPORTED = -1;

    public final RenderNode renderNode;
    private final Renderer renderer;
    private final Blur3HashImpl hashBuilder = new Blur3HashImpl();

    private long lastHash = 0;
    private long invalidationVersion;
    private long recordedVersion = -1;
    private int lastWidth, lastHeight;

    public RenderNodeWithHash(RenderNode renderNode, Renderer renderer) {
        this.renderNode = renderNode;
        this.renderer = renderer;
    }

    public RenderNodeWithHash(String name, Renderer renderer) {
        this.renderNode = new RenderNode(name);
        this.renderer = renderer;
    }

    public interface Renderer {
        void renderNodeUpdateDisplayList(Canvas canvas);
        default void renderNodeCalculateHash(IBlur3Hash hash) { hash.unsupported(); }
    }

    public void updateDisplayListIfNeeded() {
        final int width = renderNode.getWidth();
        final int height = renderNode.getHeight();

        hashBuilder.start();
        renderer.renderNodeCalculateHash(hashBuilder);

        final long hash = hashBuilder.get();
        final long version = invalidationVersion;
        boolean needUpdateDisplayList = recordedVersion != version || !renderNode.hasDisplayList()
            || width != lastWidth
            || height != lastHeight
            || hash != lastHash
            || hash == HASH_UNSUPPORTED;

        if (needUpdateDisplayList) {
            RecordingCanvas canvas = renderNode.beginRecording();
            try {
                renderer.renderNodeUpdateDisplayList(canvas);
            } catch (RuntimeException | Error failure) {
                invalidationVersion++;
                throw failure;
            } finally {
                renderNode.endRecording();
            }
            lastWidth = width;
            lastHeight = height;
            lastHash = hash;
            // Keep invalidations raised by the renderer pending for the next pass.
            recordedVersion = version;
        }
    }

    public void invalidate() {
        invalidationVersion++;
    }
}
