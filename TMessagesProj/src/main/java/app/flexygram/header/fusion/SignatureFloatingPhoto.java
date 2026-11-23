package app.flexygram.header.fusion;

import android.graphics.Canvas;
import android.graphics.Path;
import org.telegram.messenger.ImageReceiver;

/** Draws the native portrait once and fades its inward edge into the header. */
public final class SignatureFloatingPhoto {
    private final SignatureFusionAvatarMask mask = new SignatureFusionAvatarMask();

    private final Path placeholderClip = new Path();
    private float clipDiameter;

    public static float fittedWidth(float width, float height, int imageWidth, int imageHeight) {
        if (width <= 0 || height <= 0) return 0;
        if (imageWidth <= 0 || imageHeight <= 0) return Math.min(width, height);
        return Math.min(width, height * ((float) imageWidth / imageHeight));
    }

    public void draw(Canvas canvas, ImageReceiver receiver, float width, float height, boolean rtl) {
        draw(canvas, receiver, width, height, rtl, 0);
    }

    public void draw(Canvas canvas, ImageReceiver receiver, float width, float height, boolean rtl,
                     float placeholderDiameter) {
        if (width <= 0 || height <= 0 || receiver == null) return;
        float h = placeholderDiameter > 0 ? Math.min(Math.min(width, height), placeholderDiameter) : height;
        float w = placeholderDiameter > 0 ? h :
                fittedWidth(width, h, receiver.getBitmapWidth(), receiver.getBitmapHeight());
        boolean aspectFit = receiver.isAspectFit();
        float x = receiver.getImageX(), y = receiver.getImageY();
        float oldWidth = receiver.getImageWidth(), oldHeight = receiver.getImageHeight();
        int save = canvas.save();
        try {
            canvas.translate(rtl ? width - w : 0, (height - h) * .5f);
            if (placeholderDiameter > 0) {
                if (clipDiameter != h) {
                    placeholderClip.rewind();
                    placeholderClip.addCircle(h * .5f, h * .5f, h * .5f, Path.Direction.CW);
                    clipDiameter = h;
                }
                canvas.clipPath(placeholderClip);
            }
            int layer = mask.begin(canvas, 0, 0, w, h);
            receiver.setAspectFit(true);
            receiver.setImageCoords(0, 0, w, h);
            receiver.draw(canvas);
            mask.finishFloating(canvas, layer, w, h, rtl);
        } finally {
            canvas.restoreToCount(save);
            receiver.setAspectFit(aspectFit);
            receiver.setImageCoords(x, y, oldWidth, oldHeight);
        }
    }
}
