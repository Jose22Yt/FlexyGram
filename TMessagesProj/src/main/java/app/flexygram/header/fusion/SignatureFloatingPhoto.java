package app.flexygram.header.fusion;

import android.graphics.Canvas;
import org.telegram.messenger.ImageReceiver;

/** Fits the native portrait over a fading continuation of the same picture.
 * No second image request, bitmap ownership, blur capture or animation loop.
 * The host applies the full-panel alpha mask after this local composition.
 */
public final class SignatureFloatingPhoto {
    private final SignatureFusionAvatarMask join = new SignatureFusionAvatarMask();

    public static float fittedWidth(float width, float height, int imageWidth, int imageHeight) {
        if (width <= 0 || height <= 0) return 0;
        if (imageWidth <= 0 || imageHeight <= 0) return Math.min(width, height);
        return Math.min(width, height * ((float) imageWidth / imageHeight));
    }

    public void draw(Canvas canvas, ImageReceiver receiver, float width, float height, boolean rtl) {
        if (width <= 0 || height <= 0) return;
        boolean aspectFit = receiver.isAspectFit();
        float x = receiver.getImageX(), y = receiver.getImageY();
        float w = receiver.getImageWidth(), h = receiver.getImageHeight();
        int outer = canvas.save();
        try {
            // A continuation behind the text; the fitted foreground preserves
            // the complete original composition instead of zooming into a face.
            receiver.setAspectFit(false);
            receiver.setImageCoords(0, 0, width, height);
            receiver.draw(canvas);
            float fitted = fittedWidth(width, height, receiver.getBitmapWidth(), receiver.getBitmapHeight());
            float left = rtl ? width - fitted : 0;
            canvas.translate(left, 0);
            int layer = join.begin(canvas, 0, 0, fitted, height);
            receiver.setAspectFit(true);
            receiver.setImageCoords(0, 0, fitted, height);
            receiver.draw(canvas);
            // Only the inner edge blends into the continuation, in both directions.
            join.finish(canvas, layer, fitted, height,
                    rtl ? 0 : fitted * .8f, rtl ? fitted * .2f : fitted, .86f, rtl);
        } finally {
            canvas.restoreToCount(outer);
            receiver.setAspectFit(aspectFit);
            receiver.setImageCoords(x, y, w, h);
        }
    }
}
