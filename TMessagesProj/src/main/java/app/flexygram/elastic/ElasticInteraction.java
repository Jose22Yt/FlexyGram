package app.flexygram.elastic;

import android.graphics.Rect;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewConfiguration;
import android.widget.EditText;
import android.widget.SeekBar;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.WeakHashMap;

/** Non-consuming observer shared by native activities, sheets, menus and viewers.
 * Native code receives the original event exactly once; only the active visual surface animates.
 */
public final class ElasticInteraction {
    private static final WeakHashMap<View, Session> sessions = new WeakHashMap<>();
    private ElasticInteraction() {}
    public static void observe(View source, MotionEvent event) {
        if(source==null)return;
        View root=source.getRootView();
        Session session=sessions.get(root);
        if(!ElasticConfig.allowed()) { if(session!=null)session.cancel(); return; }
        if(session==null){session=new Session(root);sessions.put(root,session);}
        session.observe(event);
    }
    public static void drawSurface(android.graphics.Canvas canvas, View target, android.graphics.drawable.Drawable surface) {
        if(!canvas.isHardwareAccelerated() || target==null || !(target.getAnimation() instanceof ElasticTransform)){surface.draw(canvas);return;}
        ElasticTransform motion=(ElasticTransform)target.getAnimation();
        motion.getTransformation(target.getDrawingTime(),motion.surfaceTransformation);
        int save=canvas.save();canvas.translate(motion.offsetX(),motion.offsetY());
        canvas.scale(motion.x.value,motion.y.value,target.getX()+target.getWidth()/2f,target.getY()+target.getHeight()/2f);
        surface.draw(canvas);canvas.restoreToCount(save);
    }
    public static void drawInputSurface(android.graphics.Canvas canvas, View scope, android.graphics.drawable.Drawable surface) {
        // Shared rails are stationary. Individual controls own their own backgrounds.
        surface.draw(canvas);
    }
    public static void cancelAll() { for(Session s:new ArrayList<>(sessions.values()))s.cancel(); }
    private static final class Session implements View.OnAttachStateChangeListener {
        final WeakReference<View> root;
        final Rect hit=new Rect();
        WeakReference<View> target=new WeakReference<>(null);
        ElasticTransform transform;
        final ArrayList<WeakReference<ElasticTransform>> motions=new ArrayList<>(3);
        float downX,downY; int slop;
        long lastTime=-1,downTime=-1;int lastAction=-1;float lastX,lastY;
        boolean dragging,blocked;
        int candidateBudget;
        Session(View root){this.root=new WeakReference<>(root);slop=ViewConfiguration.get(root.getContext()).getScaledTouchSlop();root.addOnAttachStateChangeListener(this);}
        void observe(MotionEvent event){
            int action=event.getActionMasked();float x=event.getRawX(),y=event.getRawY();
            if(lastTime==event.getEventTime()&&downTime==event.getDownTime()&&lastAction==action&&lastX==x&&lastY==y)return;
            lastTime=event.getEventTime();downTime=event.getDownTime();lastAction=action;lastX=x;lastY=y;
            if(action==MotionEvent.ACTION_DOWN){
                if(transform!=null)transform.release();transform=null;target.clear();
                View owner=root.get();if(owner==null)return;
                blocked=false;View view=find(owner,x,y,0);if(view==null)return;
                view=surfaceTarget(view);
                if(view.getAnimation()!=null && !(view.getAnimation() instanceof ElasticTransform))return; // Native transition has priority.
                downX=x;downY=y;dragging=view instanceof SeekBar || (!insideScroll(view)
                        && !(view instanceof EditText) && !Boolean.TRUE.equals(view.getTag(org.telegram.messenger.R.id.flexy_elastic_input_scope)));
                target=new WeakReference<>(view);
                float dp=view.getWidth()/view.getResources().getDisplayMetrics().density;
                float strength=dp>180?.15f:dp>110?.24f:.51f;
                if(view instanceof EditText || Boolean.TRUE.equals(view.getTag(org.telegram.messenger.R.id.flexy_elastic_input_scope)))strength=.108f;
                if(view.getAnimation() instanceof ElasticTransform){
                    transform=(ElasticTransform)view.getAnimation();transform.press();
                }else{
                    for(int i=motions.size()-1;i>=0;i--){ElasticTransform old=motions.get(i).get();if(old==null||old.hasEnded())motions.remove(i);}
                    if(motions.size()>=3){ElasticTransform old=motions.remove(0).get();if(old!=null)old.finish();}
                    transform=new ElasticTransform(view,strength);motions.add(new WeakReference<>(transform));view.startAnimation(transform);
                }
            }else if(action==MotionEvent.ACTION_MOVE&&transform!=null){
                float dx=x-downX,dy=y-downY;
                if(!dragging&&(dx*dx+dy*dy)>slop*slop){transform.release();transform=null;}
                else transform.drag(dx,dy);
            }else if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_CANCEL||action==MotionEvent.ACTION_POINTER_DOWN){
                if(transform!=null){transform.release();transform=null;}
            }
        }
        View surfaceTarget(View view){
            // An actionable child is a boundary: never climb to a bar/panel that owns
            // other actions. Explicit tags may identify only this control itself.
            if(view.getTag(org.telegram.messenger.R.id.flexy_elastic_surface)==view)return view;
            if(view instanceof EditText)return view;
            View ancestor=view.getParent() instanceof View?(View)view.getParent():null;
            float density=view.getResources().getDisplayMetrics().density;
            for(int depth=0;depth<2&&ancestor instanceof ViewGroup;depth++){
                ViewGroup group=(ViewGroup)ancestor;
                if(isList(group)||group instanceof android.widget.ScrollView||group.getChildCount()!=1||group.isClickable()||group.isLongClickable())break;
                if(group.getWidth()>360*density||group.getHeight()>160*density)break;
                if(group.getBackground()!=null)return group;
                ancestor=group.getParent() instanceof View?(View)group.getParent():null;
            }
            return view;
        }
        View find(View view,float x,float y,int depth){
            if(depth>40||view.getVisibility()!=View.VISIBLE||!view.isEnabled()||view.getAlpha()<.05f
                    ||!view.getGlobalVisibleRect(hit)||!hit.contains((int)x,(int)y))return null;
            if(view instanceof app.flexygram.kyant.KyantDockView && ((app.flexygram.kyant.KyantDockView)view).isRendering()){blocked=true;return null;}
            if(view instanceof android.webkit.WebView || view instanceof android.view.SurfaceView || view instanceof android.view.TextureView){blocked=true;return null;}
            if(view instanceof ViewGroup){ViewGroup group=(ViewGroup)view;
                for(int i=group.getChildCount()-1;i>=0;i--){View child=find(group.getChildAt(i),x,y,depth+1);if(child!=null)return child;if(blocked)return null;}}
            String name=view.getClass().getName();
            // These Canvas cells contain separate links/media/reaction actions. They
            // cannot be treated as one control by a generic View observer.
            if(name.endsWith("ChatMessageCell"))return null;
            if(view instanceof ViewGroup && (view.isClickable()||view.isLongClickable()||view.getTag(org.telegram.messenger.R.id.flexy_elastic_surface)==view||view.getParent() instanceof View&&isList((View)view.getParent()))) {
                candidateBudget=64;
                if(hasIndependentChildAction((ViewGroup)view,0))return null;
            }
            if(view.getParent() instanceof ViewGroup && isList((View)view.getParent())
                    && !name.contains("Header") && !name.contains("Info") && view.getHeight()<160*view.getResources().getDisplayMetrics().density)return view;
            if(isList(view)||view instanceof android.widget.ScrollView)return null;
            boolean semantic=name.endsWith("DialogCell")||name.contains("SeekBar");
            return view.isClickable()||view.isLongClickable()||view instanceof EditText||semantic||view.getTag(org.telegram.messenger.R.id.flexy_elastic_surface)==view?view:null;
        }
        boolean hasIndependentChildAction(ViewGroup group,int depth){
            if(depth>=8)return true; // Unclassified deep panels never become one animated control.
            for(int i=0;i<group.getChildCount();i++){
                if(--candidateBudget<0)return true;
                View child=group.getChildAt(i);
                if(child.getVisibility()!=View.VISIBLE||!child.isEnabled()||child.getAlpha()<.05f)continue;
                if(child.isClickable()||child.isLongClickable()||child instanceof EditText)return true;
                if(child instanceof ViewGroup&&hasIndependentChildAction((ViewGroup)child,depth+1))return true;
            }
            return false;
        }
        boolean insideScroll(View view){
            View parent=view.getParent() instanceof View?(View)view.getParent():null;
            for(int depth=0;depth<40&&parent!=null;depth++){
                if(isList(parent)||parent instanceof android.widget.ScrollView)return true;
                parent=parent.getParent() instanceof View?(View)parent.getParent():null;
            }
            return false;
        }
        boolean isList(View view){return view instanceof androidx.recyclerview.widget.RecyclerView||view instanceof android.widget.AbsListView;}
        void cancel(){
            for(WeakReference<ElasticTransform> ref:motions){ElasticTransform motion=ref.get();if(motion!=null)motion.finish();}
            motions.clear();transform=null;target.clear();
        }
        @Override public void onViewAttachedToWindow(View view){}
        @Override public void onViewDetachedFromWindow(View view){cancel();}
    }
}
