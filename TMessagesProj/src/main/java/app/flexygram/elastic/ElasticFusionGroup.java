package app.flexygram.elastic;

import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;
import android.view.View;
import android.view.ViewGroup;
import java.lang.ref.WeakReference;
import java.util.WeakHashMap;
import org.telegram.ui.ActionBar.Theme;

/** Local contour bridges for deliberately registered neighboring controls, never a screen overlay.
 * Only the gap is painted; native content/actions remain separate. No blur, capture or idle ticker.
 */
public final class ElasticFusionGroup extends Drawable implements View.OnAttachStateChangeListener {
    private static final WeakHashMap<ViewGroup,ElasticFusionGroup> groups=new WeakHashMap<>();
    private final WeakReference<ViewGroup> owner;
    private final WeakReference<View>[] members;
    private final RectF[] bounds;
    private final WeakReference<Drawable>[] surfaces;
    private final Rect scratch=new Rect();
    private final Path path=new Path();
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    @SuppressWarnings("unchecked") private ElasticFusionGroup(ViewGroup host,View[] views,Drawable[] backgrounds){
        owner=new WeakReference<>(host);int n=Math.min(views.length,4);
        members=new WeakReference[n];bounds=new RectF[n];surfaces=new WeakReference[n];
        for(int i=0;i<n;i++){members[i]=new WeakReference<>(views[i]);bounds[i]=new RectF();surfaces[i]=new WeakReference<>(backgrounds==null?null:backgrounds[i]);}
        host.addOnAttachStateChangeListener(this);
        host.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->setBounds(0,0,r-l,b-t));
        setBounds(0,0,host.getWidth(),host.getHeight());host.getOverlay().add(this);
    }
    public static void bind(ViewGroup owner,View... views){
        if(groups.containsKey(owner))return;
        groups.put(owner,new ElasticFusionGroup(owner,views,null));
    }
    public static void bindSurfaces(ViewGroup owner,View[] views,Drawable[] backgrounds){
        if(groups.containsKey(owner))return;
        groups.put(owner,new ElasticFusionGroup(owner,views,backgrounds));
    }
    static void invalidateFor(View view){
        View current=view;
        for(int depth=0;depth<40&&current!=null;depth++){
            if(current instanceof ViewGroup){ElasticFusionGroup group=groups.get(current);if(group!=null){group.invalidateSelf();return;}}
            current=current.getParent() instanceof View?(View)current.getParent():null;
        }
    }
    @Override public void draw(Canvas canvas){
        ViewGroup host=owner.get();if(host==null||!ElasticConfig.enabled())return;
        boolean hasMotion=false;
        for(WeakReference<View> member:members){View view=member.get();if(view!=null&&view.getAnimation() instanceof ElasticTransform){hasMotion=true;break;}}
        if(!hasMotion||!ElasticConfig.allowed())return;
        boolean active=false;
        for(int i=0;i<members.length;i++){
            View view=members[i].get();RectF rect=bounds[i];rect.setEmpty();
            if(view==null||view.getVisibility()!=View.VISIBLE||view.getAlpha()<.5f)continue;
            View ancestor=view;
            while(ancestor!=null&&ancestor!=host)ancestor=ancestor.getParent() instanceof View?(View)ancestor.getParent():null;
            if(ancestor!=host)continue;
            view.getDrawingRect(scratch);host.offsetDescendantRectToMyCoords(view,scratch);rect.set(scratch);
            float cx=rect.centerX(),cy=rect.centerY();
            Drawable surface=surfaces[i].get();
            if(surface!=null){rect.set(surface.getBounds());if(surface.getPadding(scratch)){
                rect.left+=scratch.left;rect.top+=scratch.top;rect.right-=scratch.right;rect.bottom-=scratch.bottom;
            }}
            if(view.getAnimation() instanceof ElasticTransform){
                ElasticTransform motion=(ElasticTransform)view.getAnimation();
                rect.set(cx+(rect.left-cx)*motion.x.value,cy+(rect.top-cy)*motion.y.value,
                         cx+(rect.right-cx)*motion.x.value,cy+(rect.bottom-cy)*motion.y.value);
                rect.offset(motion.offsetX(),motion.offsetY());active|=Math.abs(motion.x.value-1)>.002f;
            }
        }
        if(!active)return;
        paint.setColor(Theme.getColor(Theme.key_windowBackgroundWhite));
        float limit=18*host.getResources().getDisplayMetrics().density;
        for(int i=0;i<bounds.length;i++)for(int j=i+1;j<bounds.length;j++){
            RectF a=bounds[i],b=bounds[j];if(a.isEmpty()||b.isEmpty())continue;
            if(a.centerX()>b.centerX()){RectF swap=a;a=b;b=swap;}
            float gap=b.left-a.right;
            float span=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
            if(gap<=0||gap>=limit||span<=0)continue;
            // The connector occupies the background gap, with a liquid waist that grows on approach.
            float half=span*.38f*(1-gap/limit),cy=(Math.max(a.top,b.top)+Math.min(a.bottom,b.bottom))/2;
            if(half<.5f)continue;
            float overlap=2*host.getResources().getDisplayMetrics().density;
            float l=a.right-overlap,r=b.left+overlap,m=(l+r)/2;
            path.rewind();path.moveTo(l,cy-half);
            path.cubicTo(m,cy-half,m,cy-half*.22f,r,cy-half);
            path.lineTo(r,cy+half);
            path.cubicTo(m,cy+half*.22f,m,cy+half,l,cy+half);
            path.close();canvas.drawPath(path,paint);
        }
    }
    @Override public void setAlpha(int alpha){paint.setAlpha(alpha);}
    @Override public void setColorFilter(ColorFilter filter){paint.setColorFilter(filter);}
    @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    @Override public void onViewAttachedToWindow(View view){((ViewGroup)view).getOverlay().add(this);}
    @Override public void onViewDetachedFromWindow(View view){((ViewGroup)view).getOverlay().remove(this);}
}
