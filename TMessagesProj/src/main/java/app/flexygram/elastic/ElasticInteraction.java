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
        if(!canvas.isHardwareAccelerated()){surface.draw(canvas);return;}
        Session session=sessions.get(scope.getRootView());
        ElasticTransform motion=session==null?null:session.inputTransform(scope);
        View target=motion==null?null:motion.owner();
        if(target==null){surface.draw(canvas);return;}
        android.graphics.Rect bounds=surface.getBounds();
        motion.getTransformation(target.getDrawingTime(),motion.surfaceTransformation);
        int save=canvas.save();canvas.translate(motion.offsetX(),motion.offsetY());canvas.scale(motion.x.value,motion.y.value,bounds.exactCenterX(),bounds.exactCenterY());surface.draw(canvas);canvas.restoreToCount(save);
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
        Session(View root){this.root=new WeakReference<>(root);slop=ViewConfiguration.get(root.getContext()).getScaledTouchSlop();root.addOnAttachStateChangeListener(this);}
        void observe(MotionEvent event){
            int action=event.getActionMasked();float x=event.getRawX(),y=event.getRawY();
            if(lastTime==event.getEventTime()&&downTime==event.getDownTime()&&lastAction==action&&lastX==x&&lastY==y)return;
            lastTime=event.getEventTime();downTime=event.getDownTime();lastAction=action;lastX=x;lastY=y;
            if(action==MotionEvent.ACTION_DOWN){
                if(transform!=null)transform.release();transform=null;target.clear();
                View owner=root.get();if(owner==null)return;
                blocked=false;View view=find(owner,x,y,0);if(view==null)return;
                Object promoted=view.getTag(org.telegram.messenger.R.id.flexy_elastic_surface);
                if(promoted instanceof View)view=(View)promoted;
                if(view.getAnimation()!=null && !(view.getAnimation() instanceof ElasticTransform))return; // Native transition has priority.
                downX=x;downY=y;dragging=view instanceof SeekBar || (!insideScroll(view)
                        && !(view instanceof EditText) && !Boolean.TRUE.equals(view.getTag(org.telegram.messenger.R.id.flexy_elastic_input_scope)));
                target=new WeakReference<>(view);
                float dp=view.getWidth()/view.getResources().getDisplayMetrics().density;
                float strength=dp>180?.025f:dp>110?.04f:.085f;
                if(view instanceof EditText)strength=.018f;
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
        View find(View view,float x,float y,int depth){
            if(depth>40||view.getVisibility()!=View.VISIBLE||!view.isEnabled()||view.getAlpha()<.05f
                    ||!view.getGlobalVisibleRect(hit)||!hit.contains((int)x,(int)y))return null;
            if(view instanceof app.flexygram.kyant.KyantDockView && ((app.flexygram.kyant.KyantDockView)view).isRendering()){blocked=true;return null;}
            if(view instanceof android.webkit.WebView || view instanceof android.view.SurfaceView || view instanceof android.view.TextureView){blocked=true;return null;}
            if(view instanceof ViewGroup){ViewGroup group=(ViewGroup)view;
                for(int i=group.getChildCount()-1;i>=0;i--){View child=find(group.getChildAt(i),x,y,depth+1);if(child!=null)return child;if(blocked)return null;}}
            String name=view.getClass().getName();
            if(view.getParent() instanceof ViewGroup && isList((View)view.getParent())
                    && !name.contains("Header") && !name.contains("Info") && view.getHeight()<160*view.getResources().getDisplayMetrics().density)return view;
            if(isList(view)||view instanceof android.widget.ScrollView)return null;
            boolean semantic=name.endsWith("ChatMessageCell")||name.endsWith("DialogCell")||name.contains("SeekBar")||name.endsWith("ControlsView");
            return view.isClickable()||view.isLongClickable()||view instanceof EditText||semantic?view:null;
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
        ElasticTransform inputTransform(View scope){
            for(int i=motions.size()-1;i>=0;i--){
                ElasticTransform motion=motions.get(i).get();View view=motion==null?null:motion.owner();
                if(view==null||motion.hasEnded()||view.getAnimation()!=motion||!Boolean.TRUE.equals(view.getTag(org.telegram.messenger.R.id.flexy_elastic_input_scope)))continue;
                View ancestor=view;for(int d=0;d<40&&ancestor!=null&&ancestor!=scope;d++)ancestor=ancestor.getParent() instanceof View?(View)ancestor.getParent():null;
                if(ancestor==scope)return motion;
            }
            return null;
        }
        void cancel(){
            for(WeakReference<ElasticTransform> ref:motions){ElasticTransform motion=ref.get();if(motion!=null)motion.finish();}
            motions.clear();transform=null;target.clear();
        }
        @Override public void onViewAttachedToWindow(View view){}
        @Override public void onViewDetachedFromWindow(View view){cancel();}
    }
}
