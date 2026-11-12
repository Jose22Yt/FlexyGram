"""Fixed 3D cylinder: static geometry, curvature persistence, native interaction and bounded work."""
from test_render_work_reuse import ROOT, JAVA, probe
from test_composer_layout import method
from pathlib import Path
import os
import re
import subprocess
import xml.etree.ElementTree as ET
import pytest

SCROLL = JAVA / 'app/flexygram/scroll'


def config_hosts():
    return {
        'android/content/Context.java': '''package android.content;public class Context{public static final int MODE_PRIVATE=0;
 public SharedPreferences getSharedPreferences(String f,int m){return org.telegram.messenger.ApplicationLoader.prefs;}}''',
        'android/content/SharedPreferences.java': '''package android.content;public interface SharedPreferences{
 int getInt(String k,int d);Editor edit();void registerOnSharedPreferenceChangeListener(OnSharedPreferenceChangeListener l);
 interface OnSharedPreferenceChangeListener{void onSharedPreferenceChanged(SharedPreferences p,String k);}
 interface Editor{Editor putInt(String k,int v);void apply();}}''',
        'org/telegram/messenger/ApplicationLoader.java': '''package org.telegram.messenger;public class ApplicationLoader{
 public static android.content.Context applicationContext=new android.content.Context();public static android.content.SharedPreferences prefs;}''',
    }


PREFS = '''static class Prefs implements android.content.SharedPreferences,android.content.SharedPreferences.Editor{
 java.util.Map<String,Integer> values=new java.util.HashMap<>();OnSharedPreferenceChangeListener listener;int reads,writes;
 public int getInt(String k,int d){reads++;return values.getOrDefault(k,d);}public Editor edit(){writes++;return this;}
 public Editor putInt(String k,int v){values.put(k,v);return this;}public void apply(){listener.onSharedPreferenceChanged(this,null);}
 public void registerOnSharedPreferenceChangeListener(OnSharedPreferenceChangeListener l){listener=l;}}
 static void check(boolean b){if(!b)throw new AssertionError();}
'''


def test_legacy_modes_remain_enabled_as_3d_and_curvature_persists_without_draw_io(tmp_path):
    files = config_hosts()
    files['Probe.java'] = '''import app.flexygram.scroll.*;public class Probe{PREFS
 public static void main(String[]a)throws Exception{Prefs p=new Prefs();p.values.put("chats",2);p.values.put("conversation",3);p.values.put("intensity",2);
 org.telegram.messenger.ApplicationLoader.prefs=p;ScrollEffectsConfig.load();check(p.writes==0);
 check(ScrollEffectsConfig.style(0)==1&&ScrollEffectsConfig.style(1)==1&&ScrollEffectsConfig.curvature()==80);
 int reads=p.reads;for(int i=0;i<10000;i++){ScrollEffectsConfig.style(0);ScrollEffectsConfig.style(1);ScrollEffectsConfig.curvature();}check(reads==p.reads);
 ScrollEffectsConfig.setCurvature(47);ScrollEffectsConfig.setStyle(0,0);check(p.values.get("curvature")==47&&ScrollEffectsConfig.style(0)==0&&ScrollEffectsConfig.style(1)==1);
 java.lang.reflect.Field f=ScrollEffectsConfig.class.getDeclaredField("preferences");f.setAccessible(true);f.set(null,null);ScrollEffectsConfig.load();
 check(ScrollEffectsConfig.curvature()==47&&ScrollEffectsConfig.style(0)==0&&ScrollEffectsConfig.style(1)==1);
 p.values.put("curvature",999);p.values.put("conversation",-1);p.apply();check(ScrollEffectsConfig.curvature()==100&&ScrollEffectsConfig.style(1)==0);
 ScrollEffectsConfig.setCurvature(-5);check(ScrollEffectsConfig.curvature()==0);
 }}'''.replace('PREFS', PREFS)
    probe(tmp_path, files, [SCROLL / 'ScrollEffectsConfig.java'])


def test_curvature_preview_is_live_but_writes_only_when_committed(tmp_path):
    files = config_hosts()
    files['Probe.java'] = '''import app.flexygram.scroll.*;public class Probe{PREFS
 public static void main(String[]a){Prefs p=new Prefs();org.telegram.messenger.ApplicationLoader.prefs=p;ScrollEffectsConfig.load();
 int[]invalidates={0};Runnable callback=()->invalidates[0]++;ScrollEffectsConfig.observe(callback);
 for(int i=1;i<=100;i++)ScrollEffectsConfig.previewCurvature(i);
 check(p.writes==0&&ScrollEffectsConfig.curvature()==100&&invalidates[0]>0);
 int count=invalidates[0];ScrollEffectsConfig.previewCurvature(100);check(invalidates[0]==count);
 ScrollEffectsConfig.setCurvature(100);check(p.writes==1&&p.values.get("curvature")==100);
 }}'''.replace('PREFS', PREFS)
    probe(tmp_path, files, [SCROLL / 'ScrollEffectsConfig.java'])


def controller_hosts():
    return {
        'android/graphics/Matrix.java': '''package android.graphics;public class Matrix{
 public static int allocations,inversions;public static float lastPreY;public double[]m=new double[9];
 public Matrix(){allocations++;identity();}public void identity(){for(int i=0;i<9;i++)m[i]=i%4==0?1:0;}
 public void preScale(float x,float y){m[0]*=x;m[3]*=x;m[6]*=x;m[1]*=y;m[4]*=y;m[7]*=y;}
 public void preTranslate(float x,float y){m[2]+=m[0]*x+m[1]*y;m[5]+=m[3]*x+m[4]*y;m[8]+=m[6]*x+m[7]*y;lastPreY=y;}
 public void postTranslate(float x,float y){m[0]+=x*m[6];m[1]+=x*m[7];m[2]+=x*m[8];m[3]+=y*m[6];m[4]+=y*m[7];m[5]+=y*m[8];}
 public void set(Matrix n){System.arraycopy(n.m,0,m,0,9);}
 public boolean invert(Matrix n){inversions++;double a=m[0],b=m[1],c=m[2],d=m[3],e=m[4],f=m[5],g=m[6],h=m[7],i=m[8];
 double det=a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g);if(Math.abs(det)<1e-12)return false;
 n.m[0]=(e*i-f*h)/det;n.m[1]=(c*h-b*i)/det;n.m[2]=(b*f-c*e)/det;
 n.m[3]=(f*g-d*i)/det;n.m[4]=(a*i-c*g)/det;n.m[5]=(c*d-a*f)/det;
 n.m[6]=(d*h-e*g)/det;n.m[7]=(b*g-a*h)/det;n.m[8]=(a*e-b*d)/det;return true;}
 public void mapPoints(float[]p){double x=p[0],y=p[1],w=m[6]*x+m[7]*y+m[8];p[0]=(float)((m[0]*x+m[1]*y+m[2])/w);p[1]=(float)((m[3]*x+m[4]*y+m[5])/w);}
}''',
        'android/graphics/Camera.java': '''package android.graphics;public class Camera{
 public static int builds,locations;public static float rotationX;private float angle,depth=576;
 public void save(){}public void restore(){angle=0;}public void setLocation(float x,float y,float z){locations++;depth=-z*72;}
 public void rotateX(float x){angle=x;}public void getMatrix(Matrix m){builds++;rotationX=angle;m.identity();double r=Math.toRadians(angle);m.m[4]=Math.cos(r);m.m[7]=-Math.sin(r)/depth;}}
''',
        'android/graphics/Canvas.java': '''package android.graphics;public class Canvas{public int depth,concats;public boolean fail;public Matrix last;
 public int save(){return ++depth;}public void restoreToCount(int s){depth=s-1;}public void concat(Matrix m){concats++;last=m;if(fail)throw new IllegalStateException();}}''',
        'android/view/View.java': 'package android.view;public class View{public static final int VISIBLE=0;}',
        'android/content/Context.java': 'package android.content;public class Context{public static final String ACCESSIBILITY_SERVICE="accessibility";public Object getSystemService(String s){return android.view.accessibility.AccessibilityManager.instance;}}',
        'android/view/accessibility/AccessibilityManager.java': 'package android.view.accessibility;public class AccessibilityManager{public static AccessibilityManager instance=new AccessibilityManager();public boolean exploration;public boolean isTouchExplorationEnabled(){return exploration;}}',
        'androidx/recyclerview/widget/RecyclerView.java': '''package androidx.recyclerview.widget;public class RecyclerView extends android.view.View{
 public int state,frames,invalidates,listeners;public boolean attached=true;public int visibility=0;
 public android.content.Context getContext(){return new android.content.Context();}public void addOnScrollListener(Object l){listeners++;}
 public boolean isAttachedToWindow(){return attached;}public int getWindowVisibility(){return visibility;}public int getScrollState(){return state;}
 public int getWidth(){return 400;}public void invalidate(){invalidates++;}public void postInvalidateOnAnimation(){frames++;}}''',
        'app/flexygram/scroll/ScrollEffectsConfig.java': '''package app.flexygram.scroll;public class ScrollEffectsConfig{
 public static final int NONE=0,WHEEL=1;public static int current=1,curve=60;public static Runnable listener;
 public static void load(){}public static int style(int s){return current;}public static int curvature(){return curve;}public static void observe(Runnable r){listener=r;}}''',
    }


def test_fixed_shape_is_active_without_scroll_and_never_schedules_animation_frames(tmp_path):
    files = controller_hosts()
    files['Probe.java'] = '''import app.flexygram.scroll.*;import android.graphics.*;import androidx.recyclerview.widget.RecyclerView;
 public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){
 RecyclerView list=new RecyclerView();ScrollEffectsController c=new ScrollEffectsController(list,0);Canvas canvas=new Canvas();
 c.beginFrame(100,900);check(c.isActive());c.concat(canvas,120,180);float angle=Camera.rotationX;long hash=c.renderHash();check(Math.abs(angle)>20);
 float[]initial={200,150};canvas.last.mapPoints(initial);
 for(int i=0;i<1000;i++){list.state=i%3;c.beginFrame(100,900);c.concat(canvas,120,180);float[]point={200,150};canvas.last.mapPoints(point);
 check(c.renderHash()==hash&&Camera.rotationX==angle&&point[0]==initial[0]&&point[1]==initial[1]);}
 check(list.frames==0&&list.listeners==0&&list.invalidates==0);
 ScrollEffectsConfig.curve=85;ScrollEffectsConfig.listener.run();check(list.invalidates==1);c.beginFrame(100,900);check(c.renderHash()!=hash);
 }}'''
    probe(tmp_path, files, [SCROLL / 'ScrollEffectsController.java', SCROLL / 'ScrollEffectGeometry.java'])


def test_inverse_touch_maps_the_drawn_cylinder_even_at_rest(tmp_path):
    files = controller_hosts()
    files['Probe.java'] = '''import app.flexygram.scroll.*;import android.graphics.*;import androidx.recyclerview.widget.RecyclerView;
 public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){
 for(int curve:new int[]{10,40,60,100}){ScrollEffectsConfig.curve=curve;RecyclerView list=new RecyclerView();ScrollEffectsController c=new ScrollEffectsController(list,0);Canvas canvas=new Canvas();c.beginFrame(100,900);
 for(float top:new float[]{110,300,650,820}){c.concat(canvas,top,top+60);float[]screen={200,top+30};canvas.last.mapPoints(screen);float[]nativePoint=new float[2];
 check(c.mapTouch(screen[0],screen[1],top,top+60,nativePoint));check(Math.abs(nativePoint[0]-200)<.001&&Math.abs(nativePoint[1]-(top+30))<.001);}
 check(list.frames==0);
 }} }'''
    probe(tmp_path, files, [SCROLL / 'ScrollEffectsController.java', SCROLL / 'ScrollEffectGeometry.java'])


def test_very_tall_cells_do_not_cross_the_camera_plane_at_maximum_curvature(tmp_path):
    files = controller_hosts()
    files['Probe.java'] = '''import app.flexygram.scroll.*;import android.graphics.*;import androidx.recyclerview.widget.RecyclerView;
 public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){
 ScrollEffectsConfig.curve=100;ScrollEffectsController c=new ScrollEffectsController(new RecyclerView(),0);c.beginFrame(100,900);Canvas canvas=new Canvas();
 c.concat(canvas,800,18000);double[]m=canvas.last.m;
 for(float y:new float[]{800,900,18000})check(m[6]*200+m[7]*y+m[8]>.1);
 }}'''
    probe(tmp_path, files, [SCROLL / 'ScrollEffectsController.java', SCROLL / 'ScrollEffectGeometry.java'])


def test_disabled_flat_detached_and_accessibility_paths_are_dormant(tmp_path):
    files = controller_hosts()
    files['Probe.java'] = '''import app.flexygram.scroll.*;import android.graphics.*;import androidx.recyclerview.widget.RecyclerView;
 public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){
 RecyclerView list=new RecyclerView();ScrollEffectsController c=new ScrollEffectsController(list,0);Canvas canvas=new Canvas();
 ScrollEffectsConfig.current=0;c.beginFrame(100,900);check(!c.isActive()&&c.save(canvas,100,180)==-1);
 ScrollEffectsConfig.current=1;ScrollEffectsConfig.curve=0;c.beginFrame(100,900);check(!c.isActive());
 ScrollEffectsConfig.curve=60;list.attached=false;c.beginFrame(100,900);check(!c.isActive());list.attached=true;
 android.view.accessibility.AccessibilityManager.instance.exploration=true;c.beginFrame(100,900);check(!c.isActive());
 android.view.accessibility.AccessibilityManager.instance.exploration=false;c.beginFrame(100,900);check(c.isActive());c.reset();check(!c.isActive());
 c.beginFrame(100,900);check(c.isActive());check(list.frames==0);
 }}'''
    probe(tmp_path, files, [SCROLL / 'ScrollEffectsController.java', SCROLL / 'ScrollEffectGeometry.java'])


def test_projection_cache_is_bounded_and_canvas_save_is_balanced_on_failure(tmp_path):
    files = controller_hosts()
    files['Probe.java'] = '''import app.flexygram.scroll.*;import android.graphics.*;import androidx.recyclerview.widget.RecyclerView;
 public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){
 RecyclerView list=new RecyclerView();ScrollEffectsController c=new ScrollEffectsController(list,0);Canvas canvas=new Canvas();c.beginFrame(100,900);
 int before=Camera.builds;for(int pass=0;pass<6;pass++)for(int row=0;row<30;row++)c.concat(canvas,100+row*25,120+row*25);check(Camera.builds-before==30);
 int allocations=Matrix.allocations;for(int pass=0;pass<100;pass++)for(int row=0;row<30;row++)c.concat(canvas,100+row*25,120+row*25);check(Matrix.allocations==allocations);
 for(int row=0;row<200;row++)c.concat(canvas,100+row*3,102+row*3);check(Matrix.allocations<=66);
 canvas.fail=true;try{c.save(canvas,100,180);throw new AssertionError();}catch(IllegalStateException ok){}check(canvas.depth==0);
 }}'''
    probe(tmp_path, files, [SCROLL / 'ScrollEffectsController.java', SCROLL / 'ScrollEffectGeometry.java'])


def test_curvature_has_flat_zero_monotone_strength_and_coherent_cylinder_spacing(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.scroll.*;public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){ScrollEffectGeometry g=new ScrollEffectGeometry();float previous=0;
 for(int curve=0;curve<=100;curve++){g.calculate(.8f,800,curve);check(Math.abs(g.rotationX)>=previous);previous=Math.abs(g.rotationX);
 if(curve==0)check(g.rotationX==0&&g.translationY==0&&g.scaleX==1);
 for(float p:new float[]{-.8f,-.4f,.1f,.4f,.8f}){
 g.calculate(p-.001f,800,curve);float left=g.translationY;g.calculate(p+.001f,800,curve);float right=g.translationY;g.calculate(p,800,curve);
 double derivative=1+(right-left)/.002/400;check(Math.abs(derivative-Math.cos(Math.toRadians(g.rotationX)))<.002&&g.scaleX>0);
 }} }}'''}, [SCROLL / 'ScrollEffectGeometry.java'])


def test_native_touch_interrupts_fling_and_keeps_curvature_and_scroll_deltas(tmp_path):
    source = (JAVA / 'org/telegram/ui/Components/RecyclerListView.java').read_text()
    actual = '\n'.join(method(source, sig) for sig in ['public boolean dispatchTouchEvent(MotionEvent ev)', 'private MotionEvent scrollEffectsTouchEvent(MotionEvent event)'])
    probe(tmp_path, {'Probe.java': '''class MotionEvent{static final int ACTION_DOWN=0,ACTION_UP=1,ACTION_MOVE=2,ACTION_CANCEL=3;int action;float x,y;boolean recycled;
 MotionEvent(int a,float x,float y){action=a;this.x=x;this.y=y;}int getActionMasked(){return action;}float getX(){return x;}float getY(){return y;}
 static MotionEvent obtain(MotionEvent e){return new MotionEvent(e.action,e.x,e.y);}void offsetLocation(float x,float y){this.x+=x;this.y+=y;}void recycle(){recycled=true;}}
 class RectF{float top=100,bottom=200;}class View{int getVisibility(){return 0;}float getX(){return 0;}float getY(){return 100;}int getWidth(){return 400;}int getHeight(){return 100;}}
 class Effect{boolean isActive(){return true;}boolean mapTouch(float x,float y,float t,float b,float[]p){p[0]=x-20;p[1]=y+12;return true;}}
 public class Probe{final int VISIBLE=0,SCROLL_STATE_SETTLING=2;Effect scrollEffects=new Effect();RectF scrollEffectBounds=new RectF();float[]scrollTouchPoint=new float[2];float scrollTouchOffsetX,scrollTouchOffsetY;
 int state=2,stops,presses,taps;float x,y;boolean fail;MotionEvent forwarded;int getScrollState(){return state;}void stopScroll(){state=0;stops++;}
 int getChildCount(){return 1;}View getChildAt(int i){return new View();}boolean getScrollEffectBounds(View v,RectF b){return true;}
 boolean dispatchNativeListTouchEvent(MotionEvent e){forwarded=e;x=e.x;y=e.y;if(fail)throw new RuntimeException();if(e.action==0&&state==0)presses++;if(e.action==1&&presses>0)taps++;return true;}
 ACTUAL
 static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){Probe p=new Probe();MotionEvent down=new MotionEvent(0,70,130);p.dispatchTouchEvent(down);
 check(p.stops==1&&p.presses==1&&p.x==50&&p.y==142&&down.x==70&&!down.recycled&&p.forwarded.recycled&&p.scrollEffects.isActive());
 p.dispatchTouchEvent(new MotionEvent(2,75,110));check(p.x==55&&p.y==122);p.dispatchTouchEvent(new MotionEvent(1,75,110));check(p.taps==1&&p.scrollTouchOffsetX==0&&p.scrollEffects.isActive());
 p.dispatchTouchEvent(new MotionEvent(0,70,130));p.fail=true;try{p.dispatchTouchEvent(new MotionEvent(3,70,130));throw new AssertionError();}catch(RuntimeException ok){}
 check(p.forwarded.recycled&&p.scrollTouchOffsetX==0&&p.scrollTouchOffsetY==0);
 }}'''.replace('ACTUAL', actual)})


def native_chat_geometry():
    source = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    start = source.index('    private abstract class ChatListRecyclerView ')
    fields = source[source.index('{', start) + 1:source.index('        public ChatListRecyclerView(', start)]
    return fields + method(source[start:], 'private boolean isNativeScrollEffectOverlay(') + method(source[start:], 'protected boolean getScrollEffectBounds(')


CHAT_HOST = '''class RectF{float top,bottom;}
 class R{static class id{static final int parent_tag=1;}}
 class MessageObject{static class GroupedMessages{}}
 class View{static final int VISIBLE=0;float y;int height=24;float getY(){return y;}int getHeight(){return height;}}
 class Video extends View{Object parent,source;Object getParent(){return parent;}Object getTag(int key){return source;}int getVisibility(){return VISIBLE;}}
 class ChatMessageCell extends View{MessageObject.GroupedMessages group;Object photo=new Object();MessageObject.GroupedMessages getCurrentMessagesGroup(){return group;}Object getPhotoImage(){return photo;}}
 class ChatActionCell extends View{}class ChatMessageUnsupportedCell extends View{}
 class Base{View[]children;int reads;int getChildCount(){return children.length;}View getChildAt(int i){reads++;return children[i];}
 protected boolean getScrollEffectBounds(View v,RectF b){b.top=v.y;b.bottom=v.y+v.height;return true;}
 public void beginScrollEffectsFrame(float t,float b){}public void onScrolled(int x,int y){}protected void onLayout(boolean c,int l,int t,int r,int b){}protected void onDetachedFromWindow(){}
 }
 public class Probe extends Base{Object contentView=new Object();View scrimView;Video videoPlayerContainer;
 ACTUAL
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){BODY}
 }'''


def test_albums_share_one_static_anchor_and_clear_bounded_caches_on_geometry_changes(tmp_path):
    body = '''Probe p=new Probe();p.children=new View[30];RectF b=new RectF();MessageObject.GroupedMessages group=null;
 for(int i=0;i<30;i++){if(i%3==0)group=new MessageObject.GroupedMessages();ChatMessageCell c=new ChatMessageCell();c.y=100+i*24;c.group=group;p.children[i]=c;}
 for(int pass=0;pass<6;pass++)for(int i=0;i<30;i++){p.getScrollEffectBounds(p.children[i],b);check(b.top==100+(i/3)*72&&b.bottom==172+(i/3)*72);}
 check(p.reads==300);Object cache=p.scrollEffectGroups;
 for(View v:p.children)v.y+=50;p.onScrolled(0,50);p.getScrollEffectBounds(p.children[0],b);check(b.top==150&&b.bottom==222);
 p.children[0].height=400;p.onLayout(true,0,0,400,900);p.getScrollEffectBounds(p.children[1],b);check(b.top==150&&b.bottom==550);
 p.beginScrollEffectsFrame(100,900);check(p.scrollEffectGroupCount==0&&p.scrollEffectGroups==cache);
 p.children=new View[40];for(int i=0;i<40;i++){ChatMessageCell c=new ChatMessageCell();c.y=i*24;c.group=new MessageObject.GroupedMessages();p.children[i]=c;}
 for(View v:p.children){p.getScrollEffectBounds(v,b);check(b.top==v.y&&b.bottom==v.y+24);}check(p.scrollEffectGroupCount==32);
 p.onDetachedFromWindow();for(Object key:p.scrollEffectGroups)check(key==null);check(p.scrollEffectVideoCell==null&&p.scrollEffectVideoGroup==null);'''
    probe(tmp_path, {'Probe.java': CHAT_HOST.replace('ACTUAL', native_chat_geometry()).replace('BODY', body)})


def test_native_popup_or_video_exempts_only_its_own_group_without_flattening_the_ring(tmp_path):
    body = '''Probe p=new Probe();p.children=new View[6];RectF b=new RectF();MessageObject.GroupedMessages group=null;
 for(int i=0;i<6;i++){if(i%3==0)group=new MessageObject.GroupedMessages();ChatMessageCell c=new ChatMessageCell();c.y=100+i*24;c.group=group;p.children[i]=c;}
 p.scrimView=p.children[0];check(!p.getScrollEffectBounds(p.children[0],b)&&!p.getScrollEffectBounds(p.children[1],b));check(p.getScrollEffectBounds(p.children[3],b));
 p.scrimView=null;p.videoPlayerContainer=new Video();p.videoPlayerContainer.parent=p.contentView;p.videoPlayerContainer.source=((ChatMessageCell)p.children[0]).photo;
 p.beginScrollEffectsFrame(100,900);check(!p.getScrollEffectBounds(p.children[1],b)&&p.getScrollEffectBounds(p.children[3],b));
 p.videoPlayerContainer.parent=null;check(p.getScrollEffectBounds(p.children[1],b));p.onDetachedFromWindow();check(p.scrollEffectVideoSource==null);'''
    probe(tmp_path, {'Probe.java': CHAT_HOST.replace('ACTUAL', native_chat_geometry()).replace('BODY', body)})
    chat = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    draw = method(chat[chat.index('chatListView = new ChatListRecyclerView'):], 'protected void dispatchDraw(Canvas canvas)')
    assert 'resetScrollEffects()' not in draw


def test_slider_uses_live_preview_and_commits_on_release_keyboard_or_detach(tmp_path):
    source = (SCROLL / 'ScrollEffectsSettingsActivity.java').read_text()
    listener = '\n'.join(method(source, signature) for signature in [
        'public void onStartTrackingTouch(SeekBar bar)', 'public void onStopTrackingTouch(SeekBar bar)',
        'public void onProgressChanged(SeekBar bar, int value, boolean user)', 'protected void onDetachedFromWindow()'])
    files = config_hosts()
    files['Probe.java'] = '''import app.flexygram.scroll.*;class Parent{boolean blocked;void requestDisallowInterceptTouchEvent(boolean value){blocked=value;}}
 class SeekBar{int progress;Parent parent=new Parent();int getProgress(){return progress;}Parent getParent(){return parent;}}
 class Base{protected void onDetachedFromWindow(){}}
 public class Probe extends Base{PREFS
 boolean tracking;SeekBar seek=new SeekBar();int label;void label(int v){label=v;}
 ACTUAL
 public static void main(String[]a){Prefs p=new Prefs();org.telegram.messenger.ApplicationLoader.prefs=p;ScrollEffectsConfig.load();Probe ui=new Probe();
 ui.onStartTrackingTouch(ui.seek);for(int i=1;i<=100;i++){ui.seek.progress=i;ui.onProgressChanged(ui.seek,i,true);}
 check(p.writes==0&&ScrollEffectsConfig.curvature()==100&&ui.seek.parent.blocked);
 ui.onStopTrackingTouch(ui.seek);check(p.writes==1&&p.values.get("curvature")==100&&!ui.seek.parent.blocked);
 ui.seek.progress=35;ui.onProgressChanged(ui.seek,35,true);check(p.writes==2&&ScrollEffectsConfig.curvature()==35);
 ui.onProgressChanged(ui.seek,80,false);check(p.writes==2&&ScrollEffectsConfig.curvature()==35);
 ui.onStartTrackingTouch(ui.seek);ui.seek.progress=70;ui.onProgressChanged(ui.seek,70,true);ui.onDetachedFromWindow();check(p.writes==3&&p.values.get("curvature")==70&&!ui.tracking);
 }}'''.replace('PREFS', PREFS).replace('ACTUAL', listener)
    probe(tmp_path, files, [SCROLL / 'ScrollEffectsConfig.java'])


def test_only_fixed_3d_controls_remain_and_no_temporal_engine_is_present():
    assert not (SCROLL / 'ScrollEffectMotion.java').exists()
    renderer = (SCROLL / 'ScrollEffectsController.java').read_text()
    for obsolete in ['SystemClock', 'ValueAnimator', 'SharedConfig', 'Spring', 'postInvalidateOnAnimation', 'onTouchDown', 'OnScrollListener']:
        assert obsolete not in renderer
    settings = (SCROLL / 'ScrollEffectsSettingsActivity.java').read_text()
    assert 'setMax(100)' in settings and 'previewCurvature' in settings and 'setCurvature' in settings
    assert 'createSingleChoiceDialog' not in settings and 'intensityRow' not in settings
    names = []
    for locale in ['values', 'values-es']:
        entries = ET.parse(ROOT / f'TMessagesProj/src/main/res/{locale}/flexy_scroll_effects.xml').getroot()
        names.append({e.attrib['name'] for e in entries})
        assert len(names[-1]) == len(entries)
    assert names[0] == names[1] == {'FlexyScrollEffects', 'FlexyScrollChats', 'FlexyScrollConversation', 'FlexyScrollCurvature', 'FlexyScrollInfo'}
    chat = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    assert method(chat, 'protected void drawChatForegroundElements(Canvas canvas, RectF position)').count('concatScrollEffect(canvas, cell)') == 4
    assert 'chatListView.concatScrollEffect(canvas, cell)' in method(chat, 'private void drawChildElement(')
    native = (JAVA / 'org/telegram/ui/Components/RecyclerListView.java').read_text()
    selector = method(native, 'private void drawSelectors2(')
    assert selector.index('saveScrollEffect') < selector.index('selectorTransformer.accept')
    assert 'finally' in selector and 'restoreScrollEffect' in selector
    home = (JAVA / 'org/telegram/ui/DialogsActivity.java').read_text().split('public class DialogsRecyclerView', 1)[1]
    draw = method(home, 'protected void dispatchDraw(Canvas canvas)')
    assert 'resetScrollEffects' not in draw
    assert draw.index('beginScrollEffectsFrame') < draw.index('animationSupportListView')
    assert draw.count('concatScrollEffect(canvas, y, y + view.getMeasuredHeight())') == 2
    assert 'concatScrollEffect(canvas, view)' in draw
    bounds = method(home, 'protected boolean getScrollEffectBounds(')
    assert 'isMoving' not in bounds and 'child instanceof DialogCell' in bounds


def test_module_typechecks_with_real_android_widgets_without_building_apk(tmp_path):
    jar = os.environ.get('FLEXY_SCROLL_ANDROID_JAR')
    if not jar or not Path(jar).is_file():
        pytest.skip('Set FLEXY_SCROLL_ANDROID_JAR to a real Android android.jar')
    files = {
        'androidx/recyclerview/widget/RecyclerView.java': '''package androidx.recyclerview.widget;public class RecyclerView extends android.view.View{
 public RecyclerView(android.content.Context c){super(c);}public static class ViewHolder{public android.view.View itemView;public ViewHolder(android.view.View v){itemView=v;}}
 public static class LayoutParams extends android.view.ViewGroup.LayoutParams{public LayoutParams(int w,int h){super(w,h);}}}''',
        'org/telegram/messenger/ApplicationLoader.java': 'package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext;}',
        'org/telegram/messenger/LocaleController.java': 'package org.telegram.messenger;public class LocaleController{public static String getString(int id){return "";}}',
        'org/telegram/messenger/AndroidUtilities.java': 'package org.telegram.messenger;public class AndroidUtilities{public static int dp(float n){return (int)n;}}',
        'org/telegram/ui/ActionBar/Theme.java': 'package org.telegram.ui.ActionBar;public class Theme{public static final int key_windowBackgroundWhiteBlackText=1;public interface Colorable{void updateColors();}}',
        'app/flexygram/settings/FlexySignatureSlider.java': 'package app.flexygram.settings;public class FlexySignatureSlider extends android.widget.SeekBar{public FlexySignatureSlider(android.content.Context c){super(c);}public void updateColors(){}}',
        'org/telegram/ui/Cells/TextCheckCell.java': 'package org.telegram.ui.Cells;public class TextCheckCell extends android.view.View{public TextCheckCell(android.content.Context c){super(c);}public void setTextAndCheck(String t,boolean c,boolean d){}}',
        'org/telegram/ui/Cells/TextInfoPrivacyCell.java': 'package org.telegram.ui.Cells;public class TextInfoPrivacyCell extends android.view.View{public TextInfoPrivacyCell(android.content.Context c){super(c);}public void setText(CharSequence t){}}',
        'tw/nekomimi/nekogram/ui/cells/HeaderCell.java': 'package tw.nekomimi.nekogram.ui.cells;public class HeaderCell extends android.view.View{public HeaderCell(android.content.Context c){super(c);}public void setText(String t){}}',
        'org/telegram/ui/Components/RecyclerListView.java': 'package org.telegram.ui.Components;public class RecyclerListView{public static class Holder extends androidx.recyclerview.widget.RecyclerView.ViewHolder{public Holder(android.view.View v){super(v);}}}',
        'app/flexygram/settings/SignatureMatteSettingsActivity.java': '''package app.flexygram.settings;
 import android.content.Context;import android.view.*;import androidx.recyclerview.widget.RecyclerView;
 public abstract class SignatureMatteSettingsActivity{public static final int TYPE_HEADER=4,TYPE_INFO_PRIVACY=7,TYPE_CHECK=3;
 protected BaseListAdapter listAdapter;protected String getActionBarTitle(){return "";}protected void updateRows(){}protected int addRow(String...s){return 0;}protected int getThemedColor(int k){return 0;}
 protected abstract void onItemClick(View v,int p,float x,float y);protected abstract BaseListAdapter createAdapter(Context c);protected int settingsRowPosition(RecyclerView.ViewHolder h){return 0;}
 protected class BaseListAdapter{public void notifyItemChanged(int p){}public int getItemViewType(int p){return 0;}public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup p,int t){return null;}public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){}public boolean isEnabled(RecyclerView.ViewHolder h){return true;}}
 protected class MatteListAdapter extends BaseListAdapter{protected MatteListAdapter(Context c){}}}''',
    }
    labels = sorted(set(re.findall(r'R\.string\.(\w+)', (SCROLL / 'ScrollEffectsSettingsActivity.java').read_text())))
    files['org/telegram/messenger/R.java'] = 'package org.telegram.messenger;public class R{public static class string{' + ''.join(f'public static final int {s}={i};' for i, s in enumerate(labels)) + '}}'
    paths = []
    for name, text in files.items():
        path = tmp_path / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text); paths.append(path)
    result = subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-encoding', 'UTF-8', '-proc:none', '-cp', jar,
                             '-d', str(tmp_path / 'classes'), *map(str, paths), *map(str, SCROLL.glob('*.java'))], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
