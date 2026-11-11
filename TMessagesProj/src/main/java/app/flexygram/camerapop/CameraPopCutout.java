/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.camerapop;
import android.graphics.*;import android.os.Build;import android.view.*;import android.widget.FrameLayout;
import org.telegram.messenger.AndroidUtilities;import org.telegram.messenger.NotchInfoUtils;
/** Reuses the tested Telegram/official cutout strategy for both island states. */
final class CameraPopCutout {
 static final class Anchor {final RectF bounds=new RectF();int left,top,right,bottom;}
 static Anchor read(FrameLayout root) {
 int[] location=new int[2];
        int width=root.getWidth(), height=root.getHeight();
        if(width<=0 || height<=0) return new Anchor();
        int left=0,top=AndroidUtilities.statusBarHeight,right=0,bottom=0;
        RectF notch=new RectF();
        WindowInsets insets=root.getRootWindowInsets();
        if(insets!=null) {
            if(Build.VERSION.SDK_INT>=30) {
                android.graphics.Insets safe=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());
                left=safe.left;top=safe.top;right=safe.right;bottom=safe.bottom;
            } else {
                left=insets.getSystemWindowInsetLeft();top=insets.getSystemWindowInsetTop();
                right=insets.getSystemWindowInsetRight();bottom=insets.getSystemWindowInsetBottom();
            }
            if(Build.VERSION.SDK_INT>=28) {
                DisplayCutout cutout=insets.getDisplayCutout();
                if(cutout!=null) {
                    root.getLocationInWindow(location);
                    // WindowInsets cutout rectangles have already been inset to this window.
                    for(Rect rect:cutout.getBoundingRects()) {
                        RectF candidate=new RectF(rect); candidate.offset(-location[0],-location[1]);
                        if(candidate.top<height/2f && (notch.isEmpty() || candidate.top<notch.top)) notch.set(candidate);
                    }
                    if(Build.VERSION.SDK_INT>=31) {
                        Path path=cutout.getCutoutPath();
                        if(path!=null) {
                            // Use the actual contour when available, rather than its padded safe bounds.
                            // Unlike the bounds above, this path is in display coordinates.
                            Path local=new Path(path);root.getLocationOnScreen(location);
                            local.offset(-location[0],-location[1]);
                            if(!notch.isEmpty()) {
                                Path region=new Path();region.addRect(notch,Path.Direction.CW);
                                if(!local.op(region,Path.Op.INTERSECT))local.reset();
                            }
                            RectF precise=new RectF();local.computeBounds(precise,true);
                            if(!precise.isEmpty())notch.set(precise);
                        }
                    }
                }
            }
        }
        if(notch.isEmpty() && width>=height) {
            // Do not interpret portrait firmware paths in landscape.
            notch.setEmpty();
        } else if(notch.isEmpty()) {
            // Existing Telegram detector: best-effort only; never a dependency.
            try {
                NotchInfoUtils.NotchInfo info=NotchInfoUtils.getInfo(root.getContext());
                if(info!=null) {
                    notch.set(info.bounds); root.getLocationOnScreen(location);
                    notch.offset(-location[0],-location[1]);
                }
            } catch(RuntimeException ignored) { /* Some OEMs do not expose this resource. */ }
        }

 Anchor result=new Anchor();result.bounds.set(notch);result.left=left;result.top=top;result.right=right;result.bottom=bottom;return result;
 }
}
