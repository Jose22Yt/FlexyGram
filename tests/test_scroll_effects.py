"""Production motion/geometry and lifecycle checks; no APK or physical FPS claims."""
from test_render_work_reuse import ROOT, JAVA, probe
from test_composer_layout import method
import xml.etree.ElementTree as ET
import os
from pathlib import Path
import subprocess
import re
import pytest

SCROLL = JAVA / 'app/flexygram/scroll'


def test_motion_is_time_based_at_60_120_144_hz_and_irregular_frames(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.scroll.*;
public class Probe {
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
 // Compare at the same instant, independently of the number of intervening frames.
 float reference=0;
 for(int hz:new int[]{60,120,144}){
 ScrollEffectMotion m=new ScrollEffectMotion();m.scroll(100,1000,0);
 for(int i=1;i*1_000_000_000d/hz<100_000_000L;i++)m.advance((long)(i*1_000_000_000d/hz));
 m.advance(100_000_000L);if(reference==0)reference=m.amount();else check(Math.abs(m.amount()-reference)<.00001);
 }
 ScrollEffectMotion irregular=new ScrollEffectMotion();irregular.scroll(100,1000,0);
 for(long t:new long[]{7,19,43,97,100})irregular.advance(t*1_000_000L);
 check(Math.abs(irregular.amount()-reference)<.00001);
 // A stalled frame crossing the input-expiry boundary integrates both phases.
 ScrollEffectMotion dropped=new ScrollEffectMotion();dropped.scroll(100,1000,0);dropped.advance(100_000_000L);
 check(Math.abs(dropped.amount()-reference)<.00001);
 check(!dropped.advance(2_000_000_000L)&&dropped.amount()==0);
 for(int i=0;i<1000;i++)check(!dropped.advance(3_000_000_000L+i));
 }
}'''}, [SCROLL / 'ScrollEffectMotion.java'])


def test_reversal_is_continuous_and_reset_removes_all_motion(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.scroll.*;public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){ScrollEffectMotion m=new ScrollEffectMotion();m.scroll(80,1000,0);
 m.advance(60_000_000L);float before=m.direction(),strength=m.amount();check(before>.6&&strength>.5);
 m.scroll(-80,1000,60_000_000L);m.advance(60_000_000L);check(m.direction()==before&&m.amount()==strength);
 m.advance(68_000_000L);check(m.direction()<before&&m.direction()>0&&m.amount()>=strength);
 m.scroll(-80,1000,110_000_000L);m.advance(140_000_000L);check(m.direction()<0);
 m.reset();check(m.direction()==0&&m.amount()==0&&!m.advance(150_000_000L));
 m.scroll(0,1000,160_000_000L);check(!m.advance(170_000_000L));
 }}'''}, [SCROLL / 'ScrollEffectMotion.java'])


def test_three_distinct_marked_effects_have_identical_normalized_intensity(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.scroll.*;public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){ScrollEffectGeometry g=new ScrollEffectGeometry();
 g.calculate(1,1,400,800,1,1,1);check(Math.abs(g.rotationX)>50&&g.scaleX<.95&&g.translationY<0);
 g.calculate(1,0,400,800,1,1,1);check(g.rotationX==0&&g.translationY==0&&g.scaleX==1);
 g.calculate(2,1,400,800,1,1,1);check(g.rotationX==13&&g.rotationY==-7&&g.rotationZ>1);
 g.calculate(3,1,400,800,1,1,1);float x=g.translationX;check(x>65&&g.rotationX==0&&g.rotationZ==0);
 g.calculate(3,-1,400,800,1,1,1);check(g.translationX==-x);
 g.calculate(3,1,400,800,1,-1,1);check(g.translationX==-x);
 // Different densities/viewports, same normalized amplitude on both list types.
 g.calculate(3,1,1200,1800,1,1,1);check(Math.abs(g.translationX/1200-x/400)<.000001);
 for(int style=0;style<=3;style++)for(float p:new float[]{-100,-1,0,.5f,1,100}){
 g.calculate(style,p,400,800,0,1,1.3f);check(g.rotationX==0&&g.rotationY==0&&g.translationX==0&&g.translationY==0&&g.scaleX==1);
 g.calculate(style,p,400,800,1,-1,1.3f);check(Float.isFinite(g.translationY)&&g.scaleX>0);
 }
 g.calculate(3,1,0,0,1,1,1);check(g.translationX==0);
 }}'''}, [SCROLL / 'ScrollEffectGeometry.java'])


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


def test_settings_persist_independent_choices_share_intensity_and_refresh_on_import(tmp_path):
    files = config_hosts()
    files['Probe.java'] = '''import app.flexygram.scroll.*;import android.content.*;public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 static class Prefs implements SharedPreferences,SharedPreferences.Editor{
 java.util.Map<String,Integer> values=new java.util.HashMap<>();OnSharedPreferenceChangeListener listener;int reads,writes;
 public int getInt(String k,int d){reads++;return values.getOrDefault(k,d);}public Editor edit(){writes++;return this;}
 public Editor putInt(String k,int v){values.put(k,v);return this;}public void apply(){listener.onSharedPreferenceChanged(this,null);}
 public void registerOnSharedPreferenceChangeListener(OnSharedPreferenceChangeListener l){listener=l;}}
 public static void main(String[]args)throws Exception{Prefs p=new Prefs();org.telegram.messenger.ApplicationLoader.prefs=p;
 ScrollEffectsConfig.load();check(p.writes==0&&ScrollEffectsConfig.style(0)==0&&ScrollEffectsConfig.style(1)==0&&ScrollEffectsConfig.intensity()==1);
 ScrollEffectsConfig.setStyle(0,1);ScrollEffectsConfig.setStyle(1,3);ScrollEffectsConfig.setIntensity(2);
 check(ScrollEffectsConfig.style(0)==1&&ScrollEffectsConfig.style(1)==3&&ScrollEffectsConfig.intensity()==1.3f);
 int reads=p.reads;for(int i=0;i<10000;i++){ScrollEffectsConfig.style(0);ScrollEffectsConfig.style(1);ScrollEffectsConfig.intensity();}check(p.reads==reads);
 // Process recreation reads the same persisted settings.
 java.lang.reflect.Field f=ScrollEffectsConfig.class.getDeclaredField("preferences");f.setAccessible(true);f.set(null,null);ScrollEffectsConfig.load();
 check(ScrollEffectsConfig.style(0)==1&&ScrollEffectsConfig.style(1)==3&&ScrollEffectsConfig.intensityIndex()==2);
 p.values.put("chats",99);p.values.put("intensity",-9);p.apply();check(ScrollEffectsConfig.style(0)==0&&ScrollEffectsConfig.intensityIndex()==1);
 }}'''
    probe(tmp_path, files, [SCROLL / 'ScrollEffectsConfig.java'])


def controller_hosts():
    return {
        'android/animation/ValueAnimator.java': 'package android.animation;public class ValueAnimator{public static boolean enabled=true;public static boolean areAnimatorsEnabled(){return enabled;}}',
        'android/graphics/Matrix.java': 'package android.graphics;public class Matrix{public static int allocations;public Matrix(){allocations++;}public void preScale(float x,float y){}public void preTranslate(float x,float y){}public void postTranslate(float x,float y){}public void set(Matrix m){}public boolean invert(Matrix m){return true;}public void mapPoints(float[]p){}}',
        'android/graphics/Camera.java': 'package android.graphics;public class Camera{public static int builds;public static float rotationX;public void save(){}public void restore(){}public void setLocation(float x,float y,float z){}public void rotateX(float x){rotationX=x;}public void rotateY(float y){}public void rotateZ(float z){}public void getMatrix(Matrix m){builds++;}}',
        'android/graphics/Canvas.java': 'package android.graphics;public class Canvas{public int saves,concats;public boolean fail;public int save(){return ++saves;}public void concat(Matrix m){concats++;if(fail)throw new RuntimeException();}}',
        'android/os/SystemClock.java': 'package android.os;public class SystemClock{public static long now;public static long elapsedRealtimeNanos(){return now;}}',
        'android/os/Build.java': 'package android.os;public class Build{public static class VERSION{public static int SDK_INT=35;}}',
        'android/provider/Settings.java': 'package android.provider;public class Settings{public static class Global{public static String ANIMATOR_DURATION_SCALE="scale";public static float scale=1;public static float getFloat(Object r,String k,float d){return scale;}}}',
        'android/view/View.java': 'package android.view;public class View{public static final int VISIBLE=0;}',
        'android/content/Context.java': 'package android.content;public class Context{public static final String ACCESSIBILITY_SERVICE="accessibility";public Object getContentResolver(){return null;}public Object getSystemService(String s){return android.view.accessibility.AccessibilityManager.instance;}}',
        'android/view/accessibility/AccessibilityManager.java': 'package android.view.accessibility;public class AccessibilityManager{public static AccessibilityManager instance=new AccessibilityManager();public boolean exploration;public boolean isTouchExplorationEnabled(){return exploration;}}',
        'org/telegram/messenger/SharedConfig.java': 'package org.telegram.messenger;public class SharedConfig{public static boolean enabled=true;public static boolean animationsEnabled(){return enabled;}}',
        'androidx/recyclerview/widget/RecyclerView.java': '''package androidx.recyclerview.widget;public class RecyclerView extends android.view.View{
 public static final int SCROLL_STATE_IDLE=0;public int state=1,frames,invalidates;public boolean attached=true;public int visibility=0;
 public static class OnScrollListener{public void onScrolled(RecyclerView r,int dx,int dy){}}
 public android.content.Context getContext(){return new android.content.Context();}public void addOnScrollListener(OnScrollListener l){}
 public boolean isAttachedToWindow(){return attached;}public int getWindowVisibility(){return visibility;}public int getScrollState(){return state;}
 public int getWidth(){return 400;}public void invalidate(){invalidates++;}public void postInvalidateOnAnimation(){frames++;}}''',
        'app/flexygram/scroll/ScrollEffectsConfig.java': '''package app.flexygram.scroll;public class ScrollEffectsConfig{
 public static int NONE=0,PERSPECTIVE=2,current=1;public static void load(){}public static int style(int s){return current;}public static float intensity(){return 1;}}''',
    }


def test_controller_is_dormant_when_disabled_and_releases_frames_after_scroll_or_detach(tmp_path):
    files = controller_hosts()
    files['Probe.java'] = '''import app.flexygram.scroll.*;import android.os.SystemClock;import android.graphics.Canvas;import androidx.recyclerview.widget.RecyclerView;
 public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){RecyclerView list=new RecyclerView();ScrollEffectsController c=new ScrollEffectsController(list,0);Canvas canvas=new Canvas();
 ScrollEffectsConfig.current=0;c.beginFrame(100,900);c.onScrolled(list,0,80);check(c.save(canvas,100,180)==-1&&list.frames==0);
 ScrollEffectsConfig.current=1;c.beginFrame(100,900);c.onScrolled(list,0,80);SystemClock.now=60_000_000L;c.beginFrame(100,900);
 check(c.save(canvas,100,180)>0&&canvas.concats==1&&list.frames>0);long hash=c.renderHash();check(hash!=0);
 int builds=android.graphics.Camera.builds,allocations=android.graphics.Matrix.allocations;
 for(int i=0;i<1000;i++)c.concat(canvas,100,180);
 check(android.graphics.Camera.builds==builds&&android.graphics.Matrix.allocations==allocations);
 c.concat(canvas,100,10000);check(android.graphics.Camera.rotationX==0); // A very tall bubble covers the viewport center.
 c.onTouchDown();check(c.save(canvas,100,180)>0); // A fling releases without snapping.
 SystemClock.now=90_000_000L;c.beginFrame(100,900);check(c.save(canvas,100,180)>0&&c.renderHash()!=hash);
 SystemClock.now=100_000_000L;c.onScrolled(list,0,100);SystemClock.now=160_000_000L;c.beginFrame(100,900);check(c.save(canvas,100,180)>0);
 list.attached=false;c.beginFrame(100,900);check(c.save(canvas,100,180)==-1&&c.renderHash()==0);int frames=list.frames;
 list.attached=true;SystemClock.now=200_000_000L;c.beginFrame(100,900);check(list.frames==frames);
 c.onScrolled(list,0,80);SystemClock.now=260_000_000L;c.beginFrame(100,900);
 android.view.accessibility.AccessibilityManager.instance.exploration=true;c.beginFrame(100,900);check(c.save(canvas,100,180)==-1);
 android.view.accessibility.AccessibilityManager.instance.exploration=false;c.onScrolled(list,0,80);SystemClock.now=320_000_000L;c.beginFrame(100,900);
 android.animation.ValueAnimator.enabled=false;c.beginFrame(100,900);check(c.save(canvas,100,180)==-1);android.animation.ValueAnimator.enabled=true;
 android.os.Build.VERSION.SDK_INT=24;android.provider.Settings.Global.scale=0;c.onScrolled(list,0,80);c.beginFrame(100,900);check(c.save(canvas,100,180)==-1);
 android.os.Build.VERSION.SDK_INT=35;android.provider.Settings.Global.scale=1;
 c.onScrolled(list,0,80);SystemClock.now=2_000_000_000L;c.beginFrame(100,900);frames=list.frames;
 for(int i=0;i<100;i++){SystemClock.now+=16_000_000L;c.beginFrame(100,900);}check(list.frames==frames);
 list.state=0;c.onScrolled(list,0,500);SystemClock.now+=50_000_000L;c.beginFrame(100,900);check(c.save(canvas,100,180)==-1);
 }}'''
    probe(tmp_path, files, [SCROLL / name for name in ['ScrollEffectMotion.java', 'ScrollEffectGeometry.java', 'ScrollEffectsController.java']])


def test_native_draw_passes_and_settings_share_one_controller_without_owning_view_properties():
    chat = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    foreground = method(chat, 'protected void drawChatForegroundElements(Canvas canvas, RectF position)')
    assert foreground.count('concatScrollEffect(canvas, cell)') == 4
    background = method(chat, 'protected void drawChatBackgroundElements(Canvas canvas, RectF positionF)')
    assert 'finally { restoreScrollEffect(canvas, effectSave); }' in background
    assert 'finally { restoreScrollEffect(canvas, groupEffectSave); }' in background
    assert 'saveScrollEffect(canvas, group.transitionParams.cell)' in background
    parent = method(chat, 'private void drawChildElement(')
    assert 'chatListView.concatScrollEffect(canvas, cell)' in parent
    assert 'finally' in parent and 'restoreToCount' in parent
    list_source = (JAVA / 'org/telegram/ui/Components/RecyclerListView.java').read_text()
    touch = method(list_source, 'public boolean dispatchTouchEvent(MotionEvent ev)')
    assert touch.index('scrollEffectsTouchEvent(ev)') < touch.index('dispatchNativeListTouchEvent(nativeEvent)')
    assert 'resetScrollEffects()' in method(list_source, 'protected void onDetachedFromWindow()')
    assert 'builder.add(scrollEffects.renderHash())' in method(list_source, 'public void captureCalculateHash(')
    controller = (SCROLL / 'ScrollEffectsController.java').read_text()
    for forbidden in ['setTranslation', 'setScale', 'setRotation', 'setPivot', 'saveLayer', 'Bitmap', 'postDelayed', 'new ValueAnimator', 'requestLayout']:
        assert forbidden not in controller
    settings = (SCROLL / 'ScrollEffectsSettingsActivity.java').read_text()
    assert 'ScrollEffectsConfig.setStyle(surface, which)' in settings and 'ScrollEffectsConfig.setIntensity(which)' in settings
    page = (JAVA / 'app/flexygram/settings/signature/SignatureDirectSettingsActivity.java').read_text()
    assert 'new app.flexygram.scroll.ScrollEffectsSettingsActivity()' in page[page.index('case "home":'):page.index('case "universal":')]
    names = []
    for locale in ['values', 'values-es']:
        entries = ET.parse(ROOT / f'TMessagesProj/src/main/res/{locale}/flexy_scroll_effects.xml').getroot()
        names.append({e.attrib['name'] for e in entries})
        assert len(names[-1]) == len(entries)
    assert names[0] == names[1]


def test_interrupted_fling_maps_initial_hit_without_changing_scroll_deltas(tmp_path):
    source = (JAVA / 'org/telegram/ui/Components/RecyclerListView.java').read_text()
    actual = '\n'.join(method(source, signature) for signature in [
        'public boolean dispatchTouchEvent(MotionEvent ev)',
        'private MotionEvent scrollEffectsTouchEvent(MotionEvent event)'])
    # Execute the production touch wrapper. The native host records all forwarded coordinates.
    probe(tmp_path, {'Probe.java': '''class MotionEvent{
 static final int ACTION_DOWN=0,ACTION_UP=1,ACTION_MOVE=2,ACTION_CANCEL=3;int action;float x,y;boolean recycled;
 MotionEvent(int a,float x,float y){action=a;this.x=x;this.y=y;}int getActionMasked(){return action;}float getX(){return x;}float getY(){return y;}
 static MotionEvent obtain(MotionEvent e){return new MotionEvent(e.action,e.x,e.y);}void offsetLocation(float x,float y){this.x+=x;this.y+=y;}void recycle(){recycled=true;}}
class RectF{float top=100,bottom=200;}
class View{int getVisibility(){return 0;}float getX(){return 0;}float getY(){return 100;}int getWidth(){return 400;}int getHeight(){return 100;}}
class Effect{int downs;boolean isActive(){return true;}boolean mapTouch(float x,float y,float t,float b,float[]p){p[0]=x-20;p[1]=y+12;return true;}void onTouchDown(){downs++;}}
public class Probe{
 final int VISIBLE=0;Effect scrollEffects=new Effect();RectF scrollEffectBounds=new RectF();float[]scrollTouchPoint=new float[2];float scrollTouchOffsetX,scrollTouchOffsetY;
 float nativeX,nativeY;boolean fail;MotionEvent forwarded;
 int getChildCount(){return 1;}View getChildAt(int i){return new View();}boolean getScrollEffectBounds(View v,RectF b){return true;}
 boolean dispatchNativeListTouchEvent(MotionEvent e){forwarded=e;nativeX=e.x;nativeY=e.y;if(fail)throw new RuntimeException();return true;}
 METHODS
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();MotionEvent down=new MotionEvent(0,70,130);p.dispatchTouchEvent(down);
 check(p.nativeX==50&&p.nativeY==142&&down.x==70&&!down.recycled&&p.forwarded.recycled&&p.scrollEffects.downs==1);
 p.dispatchTouchEvent(new MotionEvent(2,75,110));check(p.nativeX==55&&p.nativeY==122); // Same 5,-20 delta.
 p.dispatchTouchEvent(new MotionEvent(1,75,110));check(p.scrollTouchOffsetX==0&&p.scrollTouchOffsetY==0);
 p.dispatchTouchEvent(new MotionEvent(0,70,130));p.fail=true;try{p.dispatchTouchEvent(new MotionEvent(3,70,130));throw new AssertionError();}catch(RuntimeException ok){}
 check(p.forwarded.recycled&&p.scrollTouchOffsetX==0&&p.scrollTouchOffsetY==0);
 }}'''.replace('METHODS', actual)})


def test_all_new_classes_typecheck_against_real_android_api_without_building_apk(tmp_path):
    android_jar = os.environ.get('FLEXY_SCROLL_ANDROID_JAR')
    if not android_jar or not Path(android_jar).is_file():
        pytest.skip('Set FLEXY_SCROLL_ANDROID_JAR to a real Android API26+ android.jar')
    files = {
        'androidx/recyclerview/widget/RecyclerView.java': '''package androidx.recyclerview.widget;public class RecyclerView extends android.view.View{
 public RecyclerView(android.content.Context c){super(c);}public static final int SCROLL_STATE_IDLE=0;
 public static class ViewHolder{public android.view.View itemView;}
 public static class OnScrollListener{public void onScrolled(RecyclerView r,int x,int y){}}
 public void addOnScrollListener(OnScrollListener l){}public int getScrollState(){return 0;}}''',
        'org/telegram/messenger/ApplicationLoader.java': 'package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext;}',
        'org/telegram/messenger/SharedConfig.java': 'package org.telegram.messenger;public class SharedConfig{public static boolean animationsEnabled(){return true;}}',
        'org/telegram/messenger/LocaleController.java': 'package org.telegram.messenger;public class LocaleController{public static String getString(int id){return "";}}',
        'org/telegram/ui/Cells/TextSettingsCell.java': 'package org.telegram.ui.Cells;public class TextSettingsCell extends android.view.View{public TextSettingsCell(android.content.Context c){super(c);}public void setTextAndValue(String t,String v,boolean d){}}',
        'org/telegram/ui/Cells/TextInfoPrivacyCell.java': 'package org.telegram.ui.Cells;public class TextInfoPrivacyCell extends android.view.View{public TextInfoPrivacyCell(android.content.Context c){super(c);}public void setText(CharSequence t){}}',
        'tw/nekomimi/nekogram/ui/cells/HeaderCell.java': 'package tw.nekomimi.nekogram.ui.cells;public class HeaderCell extends android.view.View{public HeaderCell(android.content.Context c){super(c);}public void setText(String t){}}',
        'org/telegram/ui/Components/AlertsCreator.java': '''package org.telegram.ui.Components;public class AlertsCreator{
 public static android.app.Dialog createSingleChoiceDialog(android.app.Activity a,String[]o,String t,int s,android.content.DialogInterface.OnClickListener l){return null;}}''',
        'app/flexygram/settings/SignatureMatteSettingsActivity.java': '''package app.flexygram.settings;
 import android.content.Context;import android.view.View;import androidx.recyclerview.widget.RecyclerView;
 public abstract class SignatureMatteSettingsActivity{
 public static final int TYPE_HEADER=4,TYPE_INFO_PRIVACY=7,TYPE_SETTINGS=1;
 protected BaseListAdapter listAdapter;protected String getActionBarTitle(){return "";}protected void updateRows(){}
 protected int addRow(String...s){return 0;}protected android.app.Activity getParentActivity(){return null;}protected void showDialog(android.app.Dialog d){}
 protected abstract void onItemClick(View v,int p,float x,float y);protected abstract BaseListAdapter createAdapter(Context c);
 protected int settingsRowPosition(RecyclerView.ViewHolder h){return 0;}
 protected class BaseListAdapter{public void notifyItemChanged(int p){}public int getItemViewType(int p){return 0;}public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){}public boolean isEnabled(RecyclerView.ViewHolder h){return true;}}
 protected class MatteListAdapter extends BaseListAdapter{protected MatteListAdapter(Context c){}}}''',
    }
    labels = sorted(set(re.findall(r'R\.string\.(\w+)', (SCROLL / 'ScrollEffectsSettingsActivity.java').read_text())))
    files['org/telegram/messenger/R.java'] = 'package org.telegram.messenger;public class R{public static class string{' + ''.join(f'public static final int {name}={i};' for i, name in enumerate(labels)) + '}}'
    paths = []
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        paths.append(path)
    result = subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-encoding', 'UTF-8',
                             '-proc:none', '-cp', android_jar, '-d', str(tmp_path / 'classes'),
                             *map(str, paths), *map(str, SCROLL.glob('*.java'))], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
