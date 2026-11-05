package org.telegram.ui.Components.blur3;

import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.Matrix;
import android.os.Build;
import android.os.SystemClock;
import androidx.core.graphics.ColorUtils;
import org.telegram.ui.Components.blur3.source.*;

/** Bounded samples of an already available CPU bitmap. Never captures or reads GPU pixels. */
public final class GlassBackdropColor {
    private final Matrix inverse = new Matrix();
    private final float[] point = new float[2];
    private long sampledAt = Long.MIN_VALUE;
    private int cached;
    public void reset() { sampledAt=Long.MIN_VALUE; }
    public int resolve(BlurredBackgroundSource source, float x, float y, int fallback) {
        long now=SystemClock.uptimeMillis();
        if(sampledAt!=Long.MIN_VALUE && now-sampledAt<180) return cached;
        sampledAt=now;cached=fallback;
        // Wrapped factories and GPU sources may expose the existing wallpaper source.
        for(int depth=0;source!=null && depth<8;depth++) {
            if(source instanceof BlurredBackgroundSourceWrapped) source=((BlurredBackgroundSourceWrapped)source).getSource();
            else if(Build.VERSION.SDK_INT>=29 && source instanceof BlurredBackgroundSourceRenderNode)
                source=((BlurredBackgroundSourceRenderNode)source).underSource;
            else break;
        }
        if(source instanceof BlurredBackgroundSourceColor) {
            cached=ColorUtils.compositeColors(((BlurredBackgroundSourceColor)source).getColor(),fallback);
        } else if(source instanceof BlurredBackgroundSourceBitmap) {
            BlurredBackgroundSourceBitmap image=(BlurredBackgroundSourceBitmap)source;
            Bitmap bitmap=image.getBitmap();
            if(bitmap==null || bitmap.isRecycled() || (Build.VERSION.SDK_INT>=26 && bitmap.getConfig()==Bitmap.Config.HARDWARE)
                    || !image.getMatrix().invert(inverse)) return cached;
            point[0]=x;point[1]=y;inverse.mapPoints(point);
            int cx=Math.max(0,Math.min(bitmap.getWidth()-1,Math.round(point[0])));
            int cy=Math.max(0,Math.min(bitmap.getHeight()-1,Math.round(point[1])));
            int red=0,green=0,blue=0;
            try {
            for(int dy=-1;dy<=1;dy++) for(int dx=-1;dx<=1;dx++) {
                int pixel=bitmap.getPixel(Math.max(0,Math.min(bitmap.getWidth()-1,cx+dx)),
                        Math.max(0,Math.min(bitmap.getHeight()-1,cy+dy)));
                pixel=ColorUtils.compositeColors(pixel,fallback);
                red+=Color.red(pixel);green+=Color.green(pixel);blue+=Color.blue(pixel);
            }
            cached=Color.rgb(red/9,green/9,blue/9);
            } catch (IllegalStateException | IllegalArgumentException unavailable) { cached=fallback; }
        }
        return cached;
    }
}
