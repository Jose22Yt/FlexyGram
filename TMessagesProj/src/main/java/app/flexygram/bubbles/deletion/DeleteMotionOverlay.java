/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.deletion;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.view.Choreographer;
import android.view.View;
import android.view.ViewGroup;

import java.util.ArrayList;
import java.util.List;

/**
 * Snapshot-only visual deletion, independently created for FlexyGram.
 * The native, confirmed Telegram deletion remains the single source of truth.
 * Capture BEFORE native list removal; animate AFTER native deletion starts.
 * No source View is retained after capture and no touch event is intercepted.
 */
public final class DeleteMotionOverlay extends View implements Choreographer.FrameCallback {
    private static final int MAX_ACTIVE = 4;
    private static final int MAX_PIXELS = 900_000;
    private static int active;
    private final ViewGroup host;
    private final Bitmap image;
    private final float left, top, contentWidth, contentHeight;
    private final int style;
    private final long durationMs;
    private final List<Piece> pieces = new ArrayList<>();
    private final Paint bitmapPaint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
    private final Paint flashPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private long firstFrame = -1L;
    private boolean stopped;
    private boolean counted;
    private float progress;

    public static final class Target {
        public final View cell;
        public final RectF localBubbleBounds;
        public Target(View cell, RectF localBubbleBounds) {
            this.cell = cell;
            this.localBubbleBounds = new RectF(localBubbleBounds);
        }
    }

    /**
     * Call from the successful, user-confirmed deletion path, on the UI thread.
     * The callback MUST contain the original native Telegram deletion code and
     * is invoked exactly once, immediately after snapshots are captured.
     * For multi-select delete, pass all selected cells and one native callback.
     * Returns only the number of visual overlays, not deletion success.
     */
    public static int runNativeDelete(ViewGroup host, List<Target> targets,
                                      int style, Runnable nativeDelete) {
        if (nativeDelete == null) throw new IllegalArgumentException("nativeDelete required");
        final ArrayList<DeleteMotionOverlay> started = new ArrayList<>();
        int chosen = DeleteMotionSettings.sanitize(style);
        if (host != null && chosen != DeleteMotionSettings.DEFAULT
                && DeleteMotionSettings.effectsAllowed() && host.isAttachedToWindow()
                && targets != null) {
            for (Target t : targets) {
                if (active >= MAX_ACTIVE) break;
                DeleteMotionOverlay overlay = capture(host, t, chosen);
                if (overlay == null) continue;
                try {
                    overlay.layout(0, 0, host.getWidth(), host.getHeight());
                    host.getOverlay().add(overlay);
                    active++;
                    overlay.counted = true;
                    started.add(overlay);
                    overlay.start();
                } catch (RuntimeException e) {
                    // Never prevent a legitimate deletion due to visual effects.
                    overlay.stop();
                }
            }
        }
        try {
            nativeDelete.run();
        } catch (RuntimeException | Error e) {
            for (DeleteMotionOverlay overlay : started) overlay.stop();
            throw e;
        }
        return started.size();
    }

    private static DeleteMotionOverlay capture(ViewGroup root, Target target, int style) {
        if (target == null || target.cell == null || !target.cell.isAttachedToWindow()) return null;
        RectF r = target.localBubbleBounds;
        if (r.width() < 2f || r.height() < 2f || root.getWidth() <= 0 || root.getHeight() <= 0)
            return null;
        int[] cellAt = new int[2], hostAt = new int[2];
        target.cell.getLocationInWindow(cellAt);
        root.getLocationInWindow(hostAt);
        float x = cellAt[0] - hostAt[0] + r.left;
        float y = cellAt[1] - hostAt[1] + r.top;
        if (x + r.width() < 0 || y + r.height() < 0
                || x > root.getWidth() || y > root.getHeight()) return null;
        float downsample = Math.min(1f, (float)Math.sqrt(MAX_PIXELS/(r.width()*r.height())));
        int w = Math.max(2, Math.round(r.width()*downsample));
        int h = Math.max(2, Math.round(r.height()*downsample));
        Bitmap image = null;
        try {
            image = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
            Canvas c = new Canvas(image);
            c.scale(w/r.width(), h/r.height());
            c.translate(-r.left, -r.top);
            target.cell.draw(c);
        } catch (OutOfMemoryError | RuntimeException e) {
            // OOM or transient recycled cell: fall back to Telegram's native removal.
            if (image != null && !image.isRecycled()) image.recycle();
            return null;
        }
        return new DeleteMotionOverlay(root, image, x, y, r.width(), r.height(), style);
    }

    private DeleteMotionOverlay(ViewGroup host, Bitmap image, float left, float top,
                                float width, float height, int style) {
        super(host.getContext());
        this.host = host;
        this.image = image;
        this.left = left; this.top = top;
        this.contentWidth = width; this.contentHeight = height;
        this.style = style;
        durationMs = style == DeleteMotionSettings.LIQUID_FALL ? 430L
                : style == DeleteMotionSettings.LIQUID_VORTEX ? 480L
                : style == DeleteMotionSettings.TNT_DISPERSION ? 470L : 510L;
        setWillNotDraw(false);
        // Avoid allocating a full-screen hardware layer for a small message bitmap.
        if (style == DeleteMotionSettings.CRYSTAL_FRACTURE) makeCrystalPieces();
        if (style == DeleteMotionSettings.LIQUID_VORTEX) makeVortexPieces();
        if (style == DeleteMotionSettings.TNT_DISPERSION) makeTntPieces();
    }

    private static final class Piece {
        final Path clip = new Path();
        float x,y,dx,dy,angle,spin,weight;
    }

    /** Voronoi-style irregular polygons, computed once and never allocated per frame. */
    private void makeCrystalPieces() {
        final int columns = 5, rows = 5, n = columns*rows;
        float[] sx = new float[n], sy = new float[n];
        for (int i=0;i<n;i++) {
            int col=i%columns, row=i/columns;
            sx[i]=image.getWidth()*(col+.25f+.5f*DeleteMotionMath.hash(i*19+2))/columns;
            sy[i]=image.getHeight()*(row+.25f+.5f*DeleteMotionMath.hash(i*23+4))/rows;
        }
        for (int i=0;i<n;i++) {
            List<float[]> poly = rectangle(image.getWidth(),image.getHeight());
            for (int j=0;j<n && !poly.isEmpty();j++) {
                if (i==j) continue;
                float a=2f*(sx[j]-sx[i]), b=2f*(sy[j]-sy[i]);
                float c=sx[j]*sx[j]+sy[j]*sy[j]-sx[i]*sx[i]-sy[i]*sy[i];
                poly=clipHalfPlane(poly,a,b,c);
            }
            if (poly.size() < 3) continue;
            Piece p = new Piece();
            p.clip.moveTo(poly.get(0)[0],poly.get(0)[1]);
            for (int j=1;j<poly.size();j++) p.clip.lineTo(poly.get(j)[0],poly.get(j)[1]);
            p.clip.close();
            p.x=sx[i];p.y=sy[i];
            float vx=(p.x-image.getWidth()*.5f)/Math.max(1f,image.getWidth());
            float vy=(p.y-image.getHeight()*.5f)/Math.max(1f,image.getHeight());
            p.dx=(vx*.55f+(DeleteMotionMath.hash(i*31+3)-.5f)*.30f)*image.getWidth();
            p.dy=(vy*.32f-.27f-DeleteMotionMath.hash(i*13+9)*.2f)*image.getHeight();
            p.spin=(DeleteMotionMath.hash(i*7+17)-.5f)*52f;
            p.weight=.8f+DeleteMotionMath.hash(i*17+13)*.5f;
            pieces.add(p);
        }
    }

    private static List<float[]> rectangle(int w, int h) {
        ArrayList<float[]> p = new ArrayList<>(4);
        p.add(new float[]{0,0});p.add(new float[]{w,0});
        p.add(new float[]{w,h});p.add(new float[]{0,h});return p;
    }
    private static List<float[]> clipHalfPlane(List<float[]> poly,float a,float b,float c) {
        ArrayList<float[]> result=new ArrayList<>(poly.size()+1);
        float[] prev=poly.get(poly.size()-1);
        float prevDist=a*prev[0]+b*prev[1]-c;
        for(float[] cur:poly) {
            float d=a*cur[0]+b*cur[1]-c;
            boolean wasInside=prevDist<=0, isInside=d<=0;
            if(wasInside!=isInside) {
                float denom=prevDist-d;
                float t=Math.abs(denom)<1e-6f?0f:prevDist/denom;
                result.add(new float[]{prev[0]+t*(cur[0]-prev[0]),prev[1]+t*(cur[1]-prev[1])});
            }
            if(isInside)result.add(cur);
            prev=cur;prevDist=d;
        }
        return result;
    }
    private void makeVortexPieces() {
        final int n=16; float cx=image.getWidth()*.5f,cy=image.getHeight()*.5f;
        float radius=(float)Math.hypot(image.getWidth(),image.getHeight());
        for(int i=0;i<n;i++) {
            float a=(float)(2*Math.PI*i/n),b=(float)(2*Math.PI*(i+1)/n);
            Piece p=new Piece();p.clip.moveTo(cx,cy);
            p.clip.lineTo(cx+(float)Math.cos(a)*radius,cy+(float)Math.sin(a)*radius);
            p.clip.lineTo(cx+(float)Math.cos(b)*radius,cy+(float)Math.sin(b)*radius);
            p.clip.close();p.x=cx;p.y=cy;p.angle=i*360f/n;
            p.weight=.85f+.3f*DeleteMotionMath.hash(i*61+4);
            pieces.add(p);
        }
    }
    private void makeTntPieces() {
        final int cols=6,rows=6;
        float iw=image.getWidth(), ih=image.getHeight();
        for(int row=0;row<rows;row++) for(int col=0;col<cols;col++) {
            int i=row*cols+col;Piece p=new Piece();
            float l=col*iw/cols, t=row*ih/rows, r=(col+1)*iw/cols, b=(row+1)*ih/rows;
            p.clip.addRect(l,t,r,b,Path.Direction.CW);
            p.x=(l+r)*.5f;p.y=(t+b)*.5f;
            float theta=(float)(Math.PI*2*DeleteMotionMath.hash(i*29+7));
            float force=.3f+.5f*DeleteMotionMath.hash(i*37+17);
            p.dx=(float)Math.cos(theta)*iw*force;
            p.dy=(float)Math.sin(theta)*Math.max(ih*.4f,iw*.3f)*force-ih*.12f;
            p.spin=(DeleteMotionMath.hash(i*19+21)-.5f)*190f;
            p.weight=.8f+.4f*DeleteMotionMath.hash(i*23+6);
            pieces.add(p);
        }
    }

    private void start() { Choreographer.getInstance().postFrameCallback(this); invalidate(); }
    @Override public void doFrame(long frameTimeNanos) {
        if (stopped) return;
        if (firstFrame < 0L) firstFrame=frameTimeNanos;
        progress=DeleteMotionMath.clamp((frameTimeNanos-firstFrame)/(durationMs*1_000_000f));
        invalidate();
        if(progress>=1f) stop();
        else Choreographer.getInstance().postFrameCallback(this);
    }

    @Override protected void onDraw(Canvas canvas) {
        if (stopped || image.isRecycled()) return;
        int save=canvas.save();
        canvas.translate(left,top);
        canvas.scale(contentWidth/image.getWidth(),contentHeight/image.getHeight());
        switch(style) {
            case DeleteMotionSettings.CRYSTAL_FRACTURE: drawCrystal(canvas);break;
            case DeleteMotionSettings.LIQUID_FALL: drawFall(canvas);break;
            case DeleteMotionSettings.LIQUID_VORTEX: drawVortex(canvas);break;
            case DeleteMotionSettings.TNT_DISPERSION: drawTnt(canvas);break;
            default: canvas.drawBitmap(image,0,0,bitmapPaint);
        }
        canvas.restoreToCount(save);
    }
    private void drawCrystal(Canvas c) {
        float t=progress;
        if(t<.13f) { drawWhole(c,DeleteMotionMath.preCompression(t),1f,0f,0f,255);return; }
        float scatter=DeleteMotionMath.scatter(t);
        for(Piece p:pieces) {
            int checkpoint=c.save();
            c.translate(p.dx*scatter*p.weight,p.dy*scatter*p.weight + image.getHeight()*.18f*scatter*scatter);
            c.rotate(p.spin*scatter,p.x,p.y);
            c.clipPath(p.clip);
            bitmapPaint.setAlpha(Math.round(255f*DeleteMotionMath.fade(t,.60f)));
            c.drawBitmap(image,0,0,bitmapPaint);
            c.restoreToCount(checkpoint);
        }
        bitmapPaint.setAlpha(255);
    }
    private void drawFall(Canvas c) {
        float t=progress, fall=DeleteMotionMath.smooth(t);
        float dy=(host.getHeight()-top+contentHeight*.3f)*fall;
        float rx=1f+.022f*(float)Math.sin(t*Math.PI*2f)* (1f-t);
        float ry=1f+.055f*(float)Math.sin(t*Math.PI)* (1f-t);
        int save=c.save();
        c.translate(0,dy);
        c.rotate(-9f*fall,image.getWidth()*.5f,image.getHeight()*.45f);
        c.scale(rx,ry,image.getWidth()*.5f,image.getHeight()*.5f);
        bitmapPaint.setAlpha(Math.round(255f*DeleteMotionMath.fade(t,.69f)));
        c.drawBitmap(image,0,0,bitmapPaint);
        bitmapPaint.setAlpha(255);
        c.restoreToCount(save);
    }
    private void drawVortex(Canvas c) {
        float t=progress, orbit=DeleteMotionMath.smooth(t);
        float cx=image.getWidth()*.5f,cy=image.getHeight()*.5f;
        int saved=c.save();
        c.translate(cx,cy);c.rotate(250f*orbit);c.scale(1f-.94f*orbit,1f-.94f*orbit);
        c.translate(-cx,-cy);
        for(Piece p:pieces) {
            int save=c.save();
            c.rotate(12f*orbit*p.weight,cx,cy);
            c.clipPath(p.clip);
            bitmapPaint.setAlpha(Math.round(255f*DeleteMotionMath.fade(t,.74f)));
            c.drawBitmap(image,0,0,bitmapPaint);
            c.restoreToCount(save);
        }
        bitmapPaint.setAlpha(255);
        c.restoreToCount(saved);
    }
    private void drawTnt(Canvas c) {
        float t=progress;
        if(t<.085f) { drawWhole(c,1f-.015f*(t/.085f),1f-.015f*(t/.085f),0,0,255);return; }
        float s=DeleteMotionMath.smooth((t-.085f)/.915f);
        if(t<.21f) {
            flashPaint.setColor(Color.WHITE);
            flashPaint.setAlpha(Math.round(44f*(1f-DeleteMotionMath.smooth((t-.085f)/.125f))));
            c.drawRoundRect(0,0,image.getWidth(),image.getHeight(),image.getWidth()*.025f,
                    image.getWidth()*.025f,flashPaint);
        }
        for(Piece p:pieces) {
            int save=c.save();
            c.translate(p.dx*s*p.weight,p.dy*s*p.weight+image.getHeight()*.36f*s*s);
            c.rotate(p.spin*s,p.x,p.y);
            c.scale(1f-.32f*s,1f-.32f*s,p.x,p.y);
            c.clipPath(p.clip);
            bitmapPaint.setAlpha(Math.round(255f*DeleteMotionMath.fade(t,.63f)));
            c.drawBitmap(image,0,0,bitmapPaint);
            c.restoreToCount(save);
        }
        bitmapPaint.setAlpha(255);
    }
    private void drawWhole(Canvas c,float sx,float sy,float dx,float dy,int alpha) {
        int save=c.save();
        c.translate(dx,dy);
        c.scale(sx,sy,image.getWidth()*.5f,image.getHeight()*.5f);
        bitmapPaint.setAlpha(alpha);
        c.drawBitmap(image,0,0,bitmapPaint);
        bitmapPaint.setAlpha(255);
        c.restoreToCount(save);
    }
    private void stop() {
        if (stopped) return;
        stopped=true;
        Choreographer.getInstance().removeFrameCallback(this);
        if (counted) {
            counted = false;
            active = Math.max(0, active - 1);
            try { host.getOverlay().remove(this); } catch (RuntimeException ignored) {}
        }
        if (!image.isRecycled()) image.recycle();
    }
    @Override protected void onDetachedFromWindow() {
        // Stop if the chat is destroyed mid-animation (back/navigation).
        stop();
        super.onDetachedFromWindow();
    }
}
