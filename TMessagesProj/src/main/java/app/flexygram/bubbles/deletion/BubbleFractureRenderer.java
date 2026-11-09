/* Animation rendering adapted from Bubble Fracture v1.0 by @larrat23.
 * Equations, defaults and meshes retain their original behavior. See CREDITS.md. */
package app.flexygram.bubbles.deletion;
import android.graphics.*;
import java.util.*;

/** Snapshot renderer only. No plugin loader, reflective hooks or deletion authority. */
final class BubbleFractureRenderer {
    private static final class Options {
        final int style,spread,spin,cracks,drift,turns,squeeze;
        final int fuse,power,tiles,flash,smoke,lift;
        Options(int style,int spread,int spin,int cracks,int drift,int turns,int squeeze,int fuse,int power,int tiles,int flash,int smoke,int lift) {
            this.style=Math.max(0,Math.min(3,style));
            this.spread=Math.max(0,Math.min(220,spread));
            this.spin=Math.max(0,Math.min(200,spin));
            this.cracks=Math.max(0,Math.min(150,cracks));
            this.drift=Math.max(-100,Math.min(100,drift));
            this.turns=Math.max(30,Math.min(300,turns));
            this.squeeze=Math.max(70,Math.min(240,squeeze));
            this.fuse=Math.max(250,Math.min(1600,fuse));
            this.power=Math.max(30,Math.min(200,power));
            this.tiles=Math.max(12,Math.min(64,tiles));
            this.flash=Math.max(0,Math.min(150,flash));
            this.smoke=Math.max(0,Math.min(150,smoke));
            this.lift=Math.max(0,Math.min(200,lift));
        }
    }
    private final Bitmap image;
    private final float width,height,density,gravity;
    private final int duration,force=100;
    private final Options settings;
    private final List<FractureMesh.Piece> pieces;
    private final ArrayList<Path> paths = new ArrayList<>();
    private final Paint paint = new Paint(3), piecePaint = new Paint(3), edge = new Paint(3), flashPaint = new Paint(3), blastPaint = new Paint(3), smokePaint = new Paint(3);
    private final int[] pos = {0,0};
    private final Rect src;
    private final RectF dst;
    private float fallDistance;

    BubbleFractureRenderer(Bitmap image,float width,float height,float density,int style,int duration,long seed) {
        this.image=image;this.width=width;this.height=height;this.density=density;this.duration=duration;
        settings=new Options(style-1,100,100,100,15,100,100,650,100,32,100,90,100);
        gravity=160*density;
        pieces=settings.style==0?FractureMesh.make(width,height,20,seed):settings.style==3?TntMesh.make(width,height,32,seed):Collections.emptyList();
        for(FractureMesh.Piece p:pieces){
            Path path=new Path();path.moveTo(p.xy[0],p.xy[1]);
            for(int i=2;i<p.xy.length;i+=2)path.lineTo(p.xy[i],p.xy[i+1]);path.close();paths.add(path);
        }
        src=new Rect(0,0,image.getWidth(),image.getHeight());dst=new RectF(0,0,width,height);
        BitmapShader shader = new BitmapShader(image, Shader.TileMode.CLAMP, Shader.TileMode.CLAMP);
        if (image.getWidth() != (int) width || image.getHeight() != (int) height) {
            Matrix matrix = new Matrix();
            matrix.setScale(width / (float) image.getWidth(), height / (float) image.getHeight());
            shader.setLocalMatrix(matrix);
        }
        piecePaint.setShader(shader);
        edge.setStyle(Paint.Style.STROKE);edge.setStrokeWidth(.55f*density);edge.setColor(0x44ffffff);
        flashPaint.setColorFilter(new PorterDuffColorFilter(0xffffffff,PorterDuff.Mode.SRC_ATOP));
        blastPaint.setStyle(Paint.Style.STROKE);
    }
        void draw(Canvas c, float progress, float fallDistance) {
            this.fallDistance = fallDistance;
            progress=FractureMotionMath.unit(progress);
            float total=duration/1000f;
            int viewportSave=c.save();
            if(settings.style==3) {
                drawTnt(c,progress);
                c.restoreToCount(viewportSave);
                return;
            }
            if(settings.style==1) {
                float eased=FractureMotionMath.falling(progress,force);
                float x=settings.drift*.01f*width*eased,y=fallDistance*eased;
                int saved=c.save();
                c.translate(pos[0]+x,pos[1]+y);
                c.rotate(settings.spin*.18f*eased,width*.5f,height*.5f);
                paint.setAlpha(255);
                c.drawBitmap(image,src,dst,paint);
                c.restoreToCount(saved);
                c.restoreToCount(viewportSave);
                return;
            }
            if(settings.style==2) {
                float eased=FractureMotionMath.smooth(progress),size=FractureMotionMath.spiralScale(progress,settings.squeeze);
                int saved=c.save();
                c.translate(pos[0]+width*.5f,pos[1]+height*.5f);
                c.rotate(270f*settings.turns*.01f*eased,0,0);
                c.scale(size,size);
                c.translate(-width*.5f,-height*.5f);
                paint.setAlpha((int)(255*FractureMotionMath.spiralAlpha(progress)));
                c.drawBitmap(image,src,dst,paint);
                c.restoreToCount(saved);
                c.restoreToCount(viewportSave);
                return;
            }
            piecePaint.setAlpha((int)(255*FractureMesh.fade(progress)));
            for(int i=0;i<pieces.size();i++) {
                FractureMesh.Piece p=pieces.get(i);
                float phase=FractureMesh.phase(progress,p.delay);
                float seconds=phase*total;
                float x=p.vx*density*seconds*.38f*settings.spread*.01f,y=p.vy*density*seconds*.28f+gravity*seconds*seconds*.5f,rotation=p.spin*phase*phase*settings.spin*.01f;
                int save=c.save();
                c.translate(pos[0]+x,pos[1]+y);
                c.rotate(rotation,p.cx,p.cy);
                c.drawPath(paths.get(i),piecePaint);
                c.restoreToCount(save);
            }
            // Hairline cracks emerge only before their pieces detach, never a solid overlay.
            if(settings.cracks>0&&progress>.04f&&progress<.50f) {
                int save=c.save();
                c.translate(pos[0],pos[1]);
                edge.setAlpha((int)(70*settings.cracks*.01f*Math.sin(Math.min(1,progress/.50f)*Math.PI)));
                for(int i=0;i<paths.size();i++)if(progress<pieces.get(i).delay)c.drawPath(paths.get(i),edge);
                c.restoreToCount(save);
            }
            c.restoreToCount(viewportSave);
        }
        private void drawTnt(Canvas canvas,float progress) {
            float fuse=TntMotion.fuseDuration(settings.fuse,duration)/(float)duration;
            float centerX=width*.5f,centerY=height*.5f;
            if(progress<fuse) {
                float flash=TntMotion.flash(progress/fuse);
                float size=1f+.035f*flash;
                int saved=canvas.save();
                canvas.translate(pos[0],pos[1]);
                canvas.scale(size,size,centerX,centerY);
                paint.setAlpha(255);
                canvas.drawBitmap(image,src,dst,paint);
                flashPaint.setAlpha(Math.min(255,(int)(220f*settings.flash*.01f*flash)));
                if(flashPaint.getAlpha()>0)canvas.drawBitmap(image,src,dst,flashPaint);
                canvas.restoreToCount(saved);
                return;
            }
            float burst=FractureMotionMath.unit((progress-fuse)/(1f-fuse));
            float travel=TntMotion.travel(burst);
            float radius=Math.max(width,height)*.62f*settings.power*.01f;
            piecePaint.setAlpha((int)(255*TntMotion.fade(burst)));
            for(int i=0;i<pieces.size();i++) {
                FractureMesh.Piece tile=pieces.get(i);
                float x=tile.vx*radius*travel;
                float y=tile.vy*radius*travel-radius*.24f*settings.lift*.01f*burst+gravity*.35f*burst*burst;
                int saved=canvas.save();
                canvas.translate(pos[0]+x,pos[1]+y);
                canvas.rotate(tile.spin*travel*settings.spin*.01f,tile.cx,tile.cy);
                float shrink=1f-.55f*FractureMotionMath.smooth(burst);
                canvas.scale(shrink,shrink,tile.cx,tile.cy);
                canvas.drawPath(paths.get(i),piecePaint);
                canvas.restoreToCount(saved);
            }
            int saved=canvas.save();
            canvas.translate(pos[0]+centerX,pos[1]+centerY);
            // A short shock ring and square smoke motes remain inside the chat clip.
            float ringAlpha=(1f-FractureMotionMath.smooth(burst/.35f))*settings.flash*.01f;
            if(ringAlpha>0f) {
                blastPaint.setColor(0xffffcf78);
                blastPaint.setStrokeWidth(Math.max(density,4f*density*(1f-burst)));
                blastPaint.setAlpha(Math.min(255,(int)(170f*ringAlpha)));
                canvas.drawCircle(0f,0f,Math.max(2f*density,radius*.72f*travel),blastPaint);
            }
            if(settings.smoke>0&&burst>0f) {
                int count=Math.min(20,pieces.size());
                for(int i=0;i<count;i++) {
                    FractureMesh.Piece tile=pieces.get(i);
                    float smokeProgress=FractureMotionMath.unit(burst/.85f);
                    float size=density*(3f+(i%4)*1.8f)*(1f+smokeProgress*1.6f);
                    float x=tile.vx*radius*.8f*travel;
                    float y=tile.vy*radius*.65f*travel-radius*.35f*smokeProgress;
                    smokePaint.setColor(i%3==0?0xffffbe64:i%3==1?0xffe7dfd4:0xff77716e);
                    float smokeAlpha=FractureMotionMath.smooth(burst/.12f)*(1f-FractureMotionMath.smooth((burst-.2f)/.8f));
                    smokePaint.setAlpha(Math.min(255,(int)(130f*settings.smoke*.01f*smokeAlpha)));
                    canvas.drawRect(x-size,y-size,x+size,y+size,smokePaint);
                }
            }
            canvas.restoreToCount(saved);
        }
}
