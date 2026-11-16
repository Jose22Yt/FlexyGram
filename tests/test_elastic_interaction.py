"""Spring stability/work budgets. Android dispatch/focus/fusion regressions use the real UI harness."""
from test_render_work_reuse import JAVA,ROOT,probe


def test_spring_converges_and_survives_interruption_at_different_frame_rates(tmp_path):
    probe(tmp_path,{'Probe.java':'''import app.flexygram.elastic.ElasticSpring;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){
 for(float dt:new float[]{1f/60,1f/90,1f/120,.2f}){
  ElasticSpring s=new ElasticSpring(1);s.target=1.085f;
  for(int i=0;i<500;i++){s.step(dt);check(Float.isFinite(s.value)&&s.value>.9f&&s.value<1.15f);}
  check(s.settled()&&s.value==s.target&&s.velocity==0);
  s.target=.93f;for(int i=0;i<4;i++)s.step(dt);s.target=1;
  for(int i=0;i<500;i++)s.step(dt);check(s.settled()&&s.value==1);
 }
}}'''},[JAVA/'app/flexygram/elastic/ElasticSpring.java'])


def test_held_pose_stops_invalidating_and_release_detach_and_off_clear_native_animation(tmp_path):
    probe(tmp_path,{
 'android/graphics/Matrix.java':'package android.graphics;public class Matrix{public void setScale(float a,float b,float c,float d){}public void postTranslate(float x,float y){}}',
 'android/view/animation/Transformation.java':'package android.view.animation;public class Transformation{public void clear(){}public android.graphics.Matrix getMatrix(){return new android.graphics.Matrix();}}',
 'android/view/animation/Animation.java':'''package android.view.animation;public class Animation{public void setFillAfter(boolean b){}public void setDuration(long n){}public boolean getTransformation(long n,Transformation t){return false;}public boolean getTransformation(long n,Transformation t,float scale){return false;}public boolean hasStarted(){return false;}public boolean hasEnded(){return false;}public boolean willChangeBounds(){return false;}public boolean willChangeTransformationMatrix(){return false;}}''',
 'android/view/View.java':'''package android.view;public class View{public boolean attached=true;public View parent;public android.view.animation.Animation animation;public interface OnAttachStateChangeListener{void onViewAttachedToWindow(View v);void onViewDetachedFromWindow(View v);}public void addOnAttachStateChangeListener(OnAttachStateChangeListener x){}public void removeOnAttachStateChangeListener(OnAttachStateChangeListener x){}public boolean isAttachedToWindow(){return attached;}public Object getParent(){return parent;}public int getWidth(){return 100;}public int getHeight(){return 56;}public int getLeft(){return 50;}public int getRight(){return 150;}public int getTop(){return 50;}public int getBottom(){return 106;}public Object getTag(int id){return null;}public void invalidate(){}public void clearAnimation(){animation=null;}public android.view.animation.Animation getAnimation(){return animation;}public Res getResources(){return new Res();}public static class Res{public Metrics getDisplayMetrics(){return new Metrics();}}public static class Metrics{public float density=1;}}''',
 'android/view/ViewGroup.java':'package android.view;public class ViewGroup extends View{public boolean getClipChildren(){return false;}}',
 'android/widget/EditText.java':'package android.widget;public class EditText extends android.view.View{}',
 'org/telegram/messenger/R.java':'package org.telegram.messenger;public class R{public static class id{public static int flexy_elastic_input_scope=1;}}',
 'app/flexygram/elastic/ElasticConfig.java':'package app.flexygram.elastic;public class ElasticConfig{public static boolean on=true;public static boolean allowed(){return on;}}',
 'app/flexygram/elastic/ElasticFusionGroup.java':'package app.flexygram.elastic;public class ElasticFusionGroup{public static int invalidations;public static void invalidateFor(android.view.View view){invalidations++;}}',
 'app/flexygram/elastic/Probe.java':'''package app.flexygram.elastic;import android.view.*;import android.view.animation.*;public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){
 View v=new View();v.parent=new ViewGroup();ElasticTransform a=new ElasticTransform(v,.085f);v.animation=a;Transformation t=new Transformation();
 long time=1000;for(int i=0;i<200;i++){time+=16;a.getTransformation(time,t);}
 check(a.x.settled());int held=ElasticFusionGroup.invalidations;
 for(int i=0;i<10000;i++){time+=16;check(!a.getTransformation(time,t));}
 check(ElasticFusionGroup.invalidations==held); // no hidden redraw loop while holding a settled pose
 a.release();for(int i=0;i<200;i++){time+=16;a.getTransformation(time,t);}check(v.animation==null&&a.hasEnded());
 a=new ElasticTransform(v,.085f);v.animation=a;v.parent=null;a.getTransformation(++time,t);check(v.animation==null);
 v.parent=new ViewGroup();a=new ElasticTransform(v,.085f);v.animation=a;ElasticConfig.on=false;a.getTransformation(++time,t);check(v.animation==null);
 }}''',
 'Probe.java':'public class Probe{public static void main(String[]args){app.flexygram.elastic.Probe.main(args);}}'
    },[JAVA/'app/flexygram/elastic/ElasticSpring.java',JAVA/'app/flexygram/elastic/ElasticTransform.java'])


def test_controls_are_reachable_and_hooks_do_not_consume_or_rewrite_native_input():
    controls=(JAVA/'app/flexygram/settings/signature/SignatureDirectSettingsActivity.java').read_text()
    assert 'include("elastic")' in controls and 'new app.flexygram.elastic.ElasticSettingsActivity()' in controls
    assert 'new app.flexygram.elastic.NativeDockSettingsActivity()' in controls
    config=(JAVA/'app/flexygram/elastic/ElasticConfig.java').read_text()
    assert 'getBoolean("enabled", true)' in config and 'getBoolean("kyant_home_dock", false)' in config
    assert 'lite_mode6' not in config and 'FLAG_LIQUID_GLASS' not in config
    source=(JAVA/'app/flexygram/elastic/ElasticInteraction.java').read_text()
    for bad in ['performClick(','.dispatchTouchEvent(','.setAction(','.setOnTouchListener(','.setScaleX(','.setTranslationX(']:assert bad not in source,bad
    for path in ['BasePermissionsActivity.java','PhotoViewer.java','ArticleViewer.java','ActionBar/AlertDialog.java','ActionBar/BottomSheet.java','ActionBar/ActionBarPopupWindow.java','Stories/StoryViewer.java','Stories/recorder/StoryRecorder.java']:
        assert 'ElasticInteraction.observe(' in (JAVA/'org/telegram/ui'/path).read_text(),path
    compositor=(JAVA/'org/telegram/ui/Components/ChatActivityEnterView.java').read_text()
    assert compositor.index('messageEditText.setTag(R.id.flexy_elastic_surface') > compositor.index('messageEditText = new ChatActivityEditTextCaption')
    assert 'ElasticFusionGroup.bind(textFieldContainer' not in compositor
    assert 'frameLayout.setTag(R.id.flexy_elastic_surface' not in compositor
    assert 'messageEditText.setTag(R.id.flexy_elastic_surface, messageEditText)' in compositor
    assert 'ElasticControlBackground.install(control' in compositor
