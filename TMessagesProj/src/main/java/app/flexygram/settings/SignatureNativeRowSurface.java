package app.flexygram.settings;

import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Outline;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;
import android.view.View;
import android.view.ViewOutlineProvider;
import org.telegram.messenger.AndroidUtilities;

/** Static grouped native row surface; geometry is rebuilt only on bind/bounds changes. */
public final class SignatureNativeRowSurface extends Drawable {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path path = new Path();
    private final RectF rect = new RectF();
    private final float[] radii = new float[8];
    private boolean top, bottom;
    private int color;
    public static void bind(View view, int color, boolean top, boolean bottom) {
        SignatureNativeRowSurface surface;
        if (view.getBackground() instanceof SignatureNativeRowSurface) surface = (SignatureNativeRowSurface) view.getBackground();
        else { surface = new SignatureNativeRowSurface(); view.setBackground(surface); }
        if (surface.top != top || surface.bottom != bottom || surface.color != color) {
            surface.top = top; surface.bottom = bottom; surface.color = color;
            surface.paint.setColor(color); surface.geometry(); surface.invalidateSelf();
        }
        view.setOutlineProvider(ViewOutlineProvider.BACKGROUND);
        view.setClipToOutline(true);
    }
    private void geometry() {
        rect.set(getBounds());
        for (int i = 0; i < 4; i++) radii[i] = top ? AndroidUtilities.dp(18) : 0;
        for (int i = 4; i < 8; i++) radii[i] = bottom ? AndroidUtilities.dp(18) : 0;
        path.rewind(); path.addRoundRect(rect, radii, Path.Direction.CW);
    }
    @Override protected void onBoundsChange(Rect bounds) { geometry(); }
    @Override public void draw(Canvas canvas) { canvas.drawPath(path, paint); }
    @Override public void getOutline(Outline outline) { if (!path.isEmpty()) outline.setConvexPath(path); }
    @Override public void setAlpha(int alpha) { paint.setAlpha(alpha); invalidateSelf(); }
    @Override public void setColorFilter(ColorFilter filter) { paint.setColorFilter(filter); invalidateSelf(); }
    @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
}
