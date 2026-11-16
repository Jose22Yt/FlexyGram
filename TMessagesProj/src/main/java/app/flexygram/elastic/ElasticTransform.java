package app.flexygram.elastic;

import android.view.View;
import android.view.animation.Animation;
import android.view.animation.Transformation;
import java.lang.ref.WeakReference;

/** Draw-only legacy transformation. View properties, native hit rectangles and callbacks stay intact.
 * It never replaces an existing native Animation; the owner decides eligibility before installation.
 */
final class ElasticTransform extends Animation implements View.OnAttachStateChangeListener {
    private final WeakReference<View> owner;
    final ElasticSpring x = new ElasticSpring(1), y = new ElasticSpring(1);
    private final ElasticSpring dx = new ElasticSpring(0), dy = new ElasticSpring(0);
    private final float strength, density, pressX, maxScaleX, roomX, roomY, width, height;
    private long lastTime, firstTime;
    private final boolean inputPulse;
    final Transformation surfaceTransformation = new Transformation();
    private boolean released, finished;
    ElasticTransform(View view, float strength) {
        owner = new WeakReference<>(view); this.strength = strength;
        density = view.getResources().getDisplayMetrics().density;
        inputPulse = view instanceof android.widget.EditText || Boolean.TRUE.equals(view.getTag(org.telegram.messenger.R.id.flexy_elastic_input_scope));
        view.addOnAttachStateChangeListener(this);
        width=view.getWidth();height=view.getHeight();
        float rx=36*density,ry=36*density;
        if(view.getParent() instanceof android.view.ViewGroup && ((android.view.ViewGroup)view.getParent()).getClipChildren()) {
            android.view.ViewGroup parent=(android.view.ViewGroup)view.getParent();
            rx=Math.max(0,Math.min(view.getLeft(),parent.getWidth()-view.getRight()));
            ry=Math.max(0,Math.min(view.getTop(),parent.getHeight()-view.getBottom()));
        }
        roomX=rx;roomY=ry;
        maxScaleX=1+2*Math.max(0,rx-21f*density)/Math.max(1,width);
        pressX=maxScaleX>1.005f?Math.min(1+strength,maxScaleX):1-strength*.9f;
        setFillAfter(true); setDuration(700);
        x.target = pressX; y.target = 1 - strength * .78f;
    }
    View owner(){return owner.get();}
    void press(){
        if(finished)return;
        released=false;firstTime=0;x.target=pressX;y.target=1-strength*.78f;dx.target=dy.target=0;
        View view=owner.get();if(view!=null)view.invalidate();
    }
    void drag(float px, float py) {
        if (released) return;
        x.target = Math.min(maxScaleX, pressX + Math.min(.15f, Math.abs(px) / (166.667f * density)));
        float maxDx=Math.max(0,roomX+(1-x.target)*width/2)/density;
        float maxDy=Math.max(0,roomY+(1-y.target)*height/2)/density;
        dx.target = Math.max(-maxDx,Math.min(maxDx,21f * (float)Math.tanh(px / (22 * density))));
        dy.target = Math.max(-maxDy,Math.min(maxDy,21f * (float)Math.tanh(py / (22 * density))));
        View view=owner.get(); if(view!=null)view.invalidate();
    }
    void release() {
        released = true; x.target = y.target = 1; dx.target = dy.target = 0;
        View view=owner.get(); if(view!=null)view.invalidate();
    }
    @Override public boolean getTransformation(long now, Transformation out) {
        View view=owner.get();
        if(view==null || !view.isAttachedToWindow() || view.getParent()==null || !ElasticConfig.allowed()) { finish(); return false; }
        if(firstTime==0)firstTime=now;
        if(inputPulse && !released && now-firstTime>120)release();
        boolean wasMoving=!(x.settled()&&y.settled()&&dx.settled()&&dy.settled());
        float dt=lastTime==0?1/60f:Math.min((now-lastTime)/1000f,.064f); lastTime=now;
        x.step(dt);y.step(dt);dx.step(dt);dy.step(dt);
        out.clear();
        out.getMatrix().setScale(x.value,y.value,view.getWidth()/2f,view.getHeight()/2f);
        out.getMatrix().postTranslate(dx.value*density,dy.value*density);
        boolean moving=!(x.settled()&&y.settled()&&dx.settled()&&dy.settled());
        if(wasMoving||moving)ElasticFusionGroup.invalidateFor(view);
        if(released&&!moving){finish();return false;}
        return moving; // A settled held control schedules no more frames (fillAfter retains its pose).
    }
    @Override public boolean getTransformation(long now, Transformation out, float scale) { return getTransformation(now,out); }
    float offsetX(){return dx.value*density;}
    float offsetY(){return dy.value*density;}
    void finish() {
        if(finished)return;finished=true;setFillAfter(false);
        View view=owner.get();
        if(view!=null){view.removeOnAttachStateChangeListener(this);if(view.getAnimation()==this)view.clearAnimation();ElasticFusionGroup.invalidateFor(view);}
    }
    @Override public void onViewAttachedToWindow(View view) {}
    @Override public void onViewDetachedFromWindow(View view) { finish(); }
    @Override public boolean hasStarted(){return lastTime!=0;}
    @Override public boolean hasEnded(){return finished;}
    @Override public boolean willChangeBounds(){return false;}
    @Override public boolean willChangeTransformationMatrix(){return true;}
}
