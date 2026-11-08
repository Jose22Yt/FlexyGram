package app.exteraless.player;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.os.Build;
import android.view.View;
import androidx.annotation.RequiresApi;
import org.telegram.ui.Components.blur3.BlurredBackgroundDrawableViewFactory;
import org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable;
import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundColorProvider;
import org.telegram.ui.Components.blur3.source.BlurredBackgroundSourceColor;
import org.telegram.ui.Components.blur3.source.BlurredBackgroundSourceRenderNode;

/** Adapter to the same retained native glass renderer used by chat headers; API 33+ only. */
@RequiresApi(api=Build.VERSION_CODES.TIRAMISU)
final class MusicGlassRenderer {
    private final BlurredBackgroundSourceRenderNode source=new BlurredBackgroundSourceRenderNode(new BlurredBackgroundSourceColor());
    private final BlurredBackgroundDrawable drawable;
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);
    private Bitmap recorded;
    private int width,height,surface,outline;
    MusicGlassRenderer(View target,float radius){
        BlurredBackgroundDrawableViewFactory factory=new BlurredBackgroundDrawableViewFactory(source);factory.setLiquidGlassEffectAllowed(true);
        drawable=factory.create(target,new BlurredBackgroundColorProvider(){
            public int getShadowColor(){return 0;}
            public int getBackgroundColor(){return (surface&0xffffff)|0x99000000;}
            public int getStrokeColorTop(){return outline;}
            public int getStrokeColorBottom(){return outline;}
        }).setRadius(radius).setPadding(0);
    }
    void draw(Canvas canvas,Bitmap bitmap,Rect bounds,int color,int stroke){
        if(recorded!=bitmap||width!=bounds.width()||height!=bounds.height()){
            width=bounds.width();height=bounds.height();Canvas capture=source.beginRecording(width,height);
            try{capture.drawBitmap(bitmap,null,bounds,paint);}finally{source.endRecording();}recorded=bitmap;
        }
        if(surface!=color||outline!=stroke){surface=color;outline=stroke;drawable.updateColors();}
        drawable.setBounds(bounds);drawable.draw(canvas);
    }
    void clear(){recorded=null;source.beginRecording(1,1);source.endRecording();}
}
