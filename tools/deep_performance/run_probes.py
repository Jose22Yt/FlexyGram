#!/usr/bin/env python3
"""Execute baseline/candidate production methods with explicit host doubles; no device timing."""
from pathlib import Path
import json
import subprocess
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = 'cd2af16c8271e52738f0c4e726cf59862c637087'
JAVA = 'TMessagesProj/src/main/java/'


def source(path, before=False):
    return subprocess.check_output(['git', 'show', BASE + ':' + JAVA + path], cwd=ROOT, text=True) if before else (ROOT / JAVA / path).read_text()


def method(text, token):
    start = text.index(token)
    brace = text.index('{', start)
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == '{': depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0: return text[start:i + 1]
    raise ValueError(token)


NAV_SUPPORT = r'''
import java.util.*;
import android.view.*;
import org.telegram.ui.*;
import org.telegram.ui.ActionBar.BaseFragment;
import app.flexygram.navigation.*;
class NAME {
 boolean attached=true,main=true,isSheet,isLayersLayout,transitionAnimationInProgress=true;
 boolean inPreviewMode,transitionAnimationPreviewMode,previewOpenAnimationInProgress;
 boolean startedTracking,animationInProgress,predictiveBackInProgress,inActionMode,story;
 Object previewMenu,sheetFragment,onCloseAnimationEndRunnable=new Object(),onOpenAnimationEndRunnable;
 ArrayList<BaseFragment> fragmentsStack=new ArrayList<>();
 View containerView=new View(),containerViewBack=new View();
 static class Insets {int bottom;} Insets systemAndDisplayInsets=new Insets();
 int cleanups,keyboardQueries,keyboardHeight;
 NAME(){fragmentsStack.add(new DialogsActivity());fragmentsStack.add(new ChatActivity());}
 int measureKeyboardHeight(){keyboardQueries++;return keyboardHeight;}
 boolean storyViewerAttached(){return story;}
 int getHeight(){return 1000;} int getBottomTabsHeight(boolean b){return 60;} int dp(int n){return n;}
 void onAnimationEndCheck(boolean b){cleanups++;}
 void exercise(MotionEvent event){nativeInstantTouchDown(event);}
 METHOD
}
'''

TAB_SUPPORT = r'''
import android.graphics.*;
class NAME {
 boolean hasGestureSelectedOverride,mainTabMaterial3,needUpdateBackupViewColor;
 float gestureSelectedOverride; int colorDefault,colorSelected,colorSelectedText,invalidations;
 PorterDuffColorFilter tabColorFilter; int tabFilterColor;
 static class Animator {float value;float getFloatValue(){return value;}} Animator isSelectedAnimator=new Animator();
 static class Image {PorterDuffColorFilter filter;int calls,invalidations;void setColorFilter(PorterDuffColorFilter f){filter=f;calls++;}void invalidate(){invalidations++;}}
 static class Text {int color,calls;void setTextColor(int c){color=c;calls++;}}
 Image imageView=new Image(),backupImageView;Text textView=new Text();
 void invalidate(){invalidations++;}
 void colors(){updateColors();}
 METHODS
}
'''

STUBS = {
'android/view/View.java': '''package android.view;public class View {public boolean isKeyboardVisible,shown=true;public float alpha=1;public boolean isShown(){return shown;}public float getAlpha(){return alpha;}}''',
'android/view/MotionEvent.java': '''package android.view;public class MotionEvent {public static final int ACTION_DOWN=0;public int action,pointers=1;public float y=100;public int getActionMasked(){return action;}public int getPointerCount(){return pointers;}public float getRawX(){return 100;}public float getRawY(){return y;}public float getY(){return y;}}''',
'org/telegram/ui/ActionBar/BaseFragment.java': '''package org.telegram.ui.ActionBar;public class BaseFragment {public android.view.View fragmentView=new android.view.View();}''',
'org/telegram/ui/DialogsActivity.java': '''package org.telegram.ui;public class DialogsActivity extends org.telegram.ui.ActionBar.BaseFragment {}''',
'org/telegram/ui/ChatActivity.java': '''package org.telegram.ui;public class ChatActivity extends org.telegram.ui.ActionBar.BaseFragment {}''',
'org/telegram/ui/MainTabsActivity.java': '''package org.telegram.ui;public class MainTabsActivity extends org.telegram.ui.ActionBar.BaseFragment {public org.telegram.ui.ActionBar.BaseFragment visible=new DialogsActivity();public org.telegram.ui.ActionBar.BaseFragment getCurrentVisibleFragment(){return visible;}}''',
'app/flexygram/navigation/NativeInstantTouchTarget.java': '''package app.flexygram.navigation;public class NativeInstantTouchTarget {public static int rows,covers;public static boolean row=true,covered;public static boolean isVisibleDialogRow(android.view.View v,float x,float y){rows++;return v!=null&&row;}public static boolean containsVisiblePoint(android.view.View v,float x,float y){covers++;return covered;}}''',
'android/graphics/PorterDuff.java': '''package android.graphics;public class PorterDuff {public enum Mode {SRC_IN}}''',
'android/graphics/ColorFilter.java': '''package android.graphics;public class ColorFilter {}''',
'android/graphics/PorterDuffColorFilter.java': '''package android.graphics;public class PorterDuffColorFilter extends ColorFilter {public static int created;public final int color;public PorterDuffColorFilter(int c,PorterDuff.Mode m){color=c;created++;}}''',
'android/graphics/PixelFormat.java': '''package android.graphics;public class PixelFormat {public static final int TRANSLUCENT=-3;}''',
'android/graphics/Rect.java': '''package android.graphics;public class Rect {public int left=0,right=100,top=0,bottom=20;public int width(){return right-left;}public float exactCenterY(){return (top+bottom)*.5f;}}''',
'android/graphics/Paint.java': '''package android.graphics;public class Paint {public static final int ANTI_ALIAS_FLAG=1;int color,alpha=255;public Paint(int f){}public void setColor(int c){color=c;alpha=c>>>24;}public void setAlpha(int a){alpha=a;}public void setColorFilter(ColorFilter f){}}''',
'android/graphics/Canvas.java': '''package android.graphics;public class Canvas {public StringBuilder draws=new StringBuilder();public void drawRoundRect(float l,float t,float r,float b,float rx,float ry,Paint p){draws.append(l+","+t+","+r+","+b+","+rx+","+ry+","+p.color+","+p.alpha+";");}}''',
'android/graphics/drawable/Drawable.java': '''package android.graphics.drawable;public abstract class Drawable {public int invalidations;private android.graphics.Rect bounds=new android.graphics.Rect();public android.graphics.Rect getBounds(){return bounds;}public void invalidateSelf(){invalidations++;}public abstract void draw(android.graphics.Canvas c);public abstract void setAlpha(int a);public abstract void setColorFilter(android.graphics.ColorFilter f);public abstract int getOpacity();}''',
'org/telegram/messenger/AndroidUtilities.java': '''package org.telegram.messenger;public class AndroidUtilities {public static float density=1;public static int dp(float n){return (int)Math.ceil(n*density);}}''',
'ColorUtils.java': '''class ColorUtils {static int blendARGB(int a,int b,float f){int c=0;for(int s=0;s<=24;s+=8)c|=((int)(((a>>>s)&255)*(1-f)+((b>>>s)&255)*f))<<s;return c;}}''',
}

HARNESS = r'''
import android.view.*;
import android.graphics.*;
import org.telegram.ui.*;
import org.telegram.ui.ActionBar.BaseFragment;
import app.flexygram.navigation.NativeInstantTouchTarget;
public class Probe {
 static int checks;static void check(boolean b){checks++;if(!b)throw new AssertionError("check "+checks);}
 static boolean bit(int mask,int n){return (mask&(1<<n))!=0;}
 public static void main(String[] ignored){
 BeforeNav before=new BeforeNav();AfterNav after=new AfterNav();MotionEvent ev=new MotionEvent();
 int cases=0,oldRows=0,newRows=0,oldKeyboards=0,newKeyboards=0;
 // Every combination of 20 independent admission guards. Actual helper body, not a rewritten decision.
 for(int mask=0;mask<(1<<20);mask++){
 before.attached=after.attached=bit(mask,0);before.main=after.main=bit(mask,1);
 before.isSheet=after.isSheet=bit(mask,2);before.isLayersLayout=after.isLayersLayout=bit(mask,3);
 before.inPreviewMode=after.inPreviewMode=bit(mask,4);before.transitionAnimationPreviewMode=after.transitionAnimationPreviewMode=bit(mask,5);
 before.previewOpenAnimationInProgress=after.previewOpenAnimationInProgress=bit(mask,6);
 before.previewMenu=after.previewMenu=bit(mask,7)?ev:null;before.sheetFragment=after.sheetFragment=bit(mask,8)?ev:null;
 before.containerView.isKeyboardVisible=after.containerView.isKeyboardVisible=bit(mask,9);
 before.containerViewBack.isKeyboardVisible=after.containerViewBack.isKeyboardVisible=bit(mask,10);
 before.startedTracking=after.startedTracking=bit(mask,11);before.animationInProgress=after.animationInProgress=bit(mask,12);
 before.predictiveBackInProgress=after.predictiveBackInProgress=bit(mask,13);before.inActionMode=after.inActionMode=bit(mask,14);
 before.story=after.story=bit(mask,15);before.keyboardHeight=after.keyboardHeight=bit(mask,16)?100:0;
 NativeInstantTouchTarget.row=bit(mask,17);NativeInstantTouchTarget.covered=bit(mask,18);ev.y=bit(mask,19)?100:980;
 before.cleanups=after.cleanups=0;before.keyboardQueries=after.keyboardQueries=0;
 NativeInstantTouchTarget.rows=0;before.exercise(ev);oldRows+=NativeInstantTouchTarget.rows;oldKeyboards+=before.keyboardQueries;
 NativeInstantTouchTarget.rows=0;after.exercise(ev);newRows+=NativeInstantTouchTarget.rows;newKeyboards+=after.keyboardQueries;
 check(before.cleanups==after.cleanups);cases++;
 }
 // All initial exits plus valid Dialogs/MainTabs, wrong fragment, hidden outgoing surface, and boundaries.
 before=new BeforeNav();after=new AfterNav();NativeInstantTouchTarget.row=true;NativeInstantTouchTarget.covered=false;
 for(int variant=0;variant<7;variant++)for(int action=0;action<4;action++)for(int pointers=0;pointers<3;pointers++)for(float y:new float[]{-1,0,939,940,1001,Float.NaN}){
 BaseFragment prev=variant==0?new DialogsActivity():new MainTabsActivity();
 if(variant==1)((MainTabsActivity)prev).visible=new BaseFragment();
 if(variant==2)((MainTabsActivity)prev).visible=null;
 if(variant==3)prev.fragmentView=null;
 before.fragmentsStack.set(0,prev);after.fragmentsStack.set(0,prev);
 BaseFragment out=variant==4?new BaseFragment():new ChatActivity();before.fragmentsStack.set(1,out);after.fragmentsStack.set(1,out);
 before.transitionAnimationInProgress=after.transitionAnimationInProgress=variant!=5;
 before.onOpenAnimationEndRunnable=after.onOpenAnimationEndRunnable=variant==6?ev:null;
 ev.action=action;ev.pointers=pointers;ev.y=y;before.cleanups=after.cleanups=0;
 before.exercise(ev);after.exercise(ev);check(before.cleanups==after.cleanups);cases++;
 }
 ev.action=0;ev.pointers=1;ev.y=100;after=new AfterNav();after.exercise(ev);check(after.cleanups==1);
 BeforeTabs bt=new BeforeTabs();AfterTabs at=new AfterTabs();
 // Repeated palette applications still reach images/text, including new avatar targets and theme transitions.
 PorterDuffColorFilter.created=0;for(int i=0;i<1000;i++)bt.colors();int oldFilters=PorterDuffColorFilter.created;
 PorterDuffColorFilter.created=0;for(int i=0;i<1000;i++)at.colors();int newFilters=PorterDuffColorFilter.created;check(oldFilters==1000&&newFilters==1);
 for(int i=0;i<10000;i++){
 int a=i*1300721,b=~a,c=a^0x5a123456;float f=(i%257)/256f;
 bt.colorDefault=at.colorDefault=a;bt.colorSelected=at.colorSelected=b;bt.colorSelectedText=at.colorSelectedText=c;
 bt.isSelectedAnimator.value=at.isSelectedAnimator.value=f;
 bt.needUpdateBackupViewColor=at.needUpdateBackupViewColor=i%3==0;
 bt.backupImageView=i%5==0?null:new BeforeTabs.Image();at.backupImageView=i%5==0?null:new AfterTabs.Image();
 bt.colors();at.colors();check(bt.imageView.filter.color==at.imageView.filter.color);check(bt.textView.color==at.textView.color);
 if(bt.backupImageView!=null){check(bt.backupImageView.calls==at.backupImageView.calls);check(bt.backupImageView.invalidations==at.backupImageView.invalidations);if(bt.backupImageView.filter!=null)check(bt.backupImageView.filter.color==at.backupImageView.filter.color);}
 }
 bt=new BeforeTabs();at=new AfterTabs();for(int i=0;i<1000;i++){bt.setGestureSelectedOverride(i/1000f,false);at.setGestureSelectedOverride(i/1000f,false);}int oldInvalidations=bt.invalidations,newInvalidations=at.invalidations;check(oldInvalidations==1000&&newInvalidations==0);
 for(int i=0;i<10000;i++){
 bt.mainTabMaterial3=at.mainTabMaterial3=i%3==0;float value=(i%17)/16f;boolean allow=i%4!=0;
 boolean was=at.hasGestureSelectedOverride;float previous=at.gestureSelectedOverride;int n=at.invalidations;
 bt.setGestureSelectedOverride(value,allow);at.setGestureSelectedOverride(value,allow);
 check(bt.hasGestureSelectedOverride==at.hasGestureSelectedOverride&&bt.gestureSelectedOverride==at.gestureSelectedOverride);
 if(was!=at.hasGestureSelectedOverride||was&&previous!=value)check(at.invalidations==n+1);
 }
 app.flexygram.composer.BeforeComposerSliderTrack bs=new app.flexygram.composer.BeforeComposerSliderTrack();
 app.flexygram.composer.ComposerSliderTrack as=new app.flexygram.composer.ComposerSliderTrack();
 bs.setFraction(50,100);as.setFraction(50,100);bs.invalidations=as.invalidations=0;
 for(int i=0;i<1000;i++){bs.setFraction(50,100);as.setFraction(50,100);}int oldTrack=bs.invalidations,newTrack=as.invalidations;check(oldTrack==1000&&newTrack==0);
 for(float density:new float[]{.75f,1,1.25f,2.75f,4}){
 org.telegram.messenger.AndroidUtilities.density=density;
 for(int i=-10;i<130;i++)for(int max:new int[]{0,1,100,200}){
 bs.configure(i*1300721,~i);as.configure(i*1300721,~i);bs.setFraction(i,max);as.setFraction(i,max);
 Canvas x=new Canvas(),y=new Canvas();bs.draw(x);as.draw(y);check(x.draws.toString().equals(y.draws.toString()));
 }
 }
 System.out.println("{\"evidence\":\"ISOLATED_OPERATION_COUNTS_NOT_DEVICE_TIMING\",\"navigation_combinations\":"+cases+",\"assertions\":"+checks+",\"navigation_row_checks\":{\"before\":"+oldRows+",\"after\":"+newRows+"},\"navigation_keyboard_queries\":{\"before\":"+oldKeyboards+",\"after\":"+newKeyboards+"},\"filters_1000_same_color\":{\"before\":"+oldFilters+",\"after\":"+newFilters+"},\"tab_invalidations_1000_inactive_overrides\":{\"before\":"+oldInvalidations+",\"after\":"+newInvalidations+"},\"track_invalidations_1000_same_fraction\":{\"before\":"+oldTrack+",\"after\":"+newTrack+"},\"device_fps\":null}");
 }
}
'''


def run():
    files = dict(STUBS)
    nav = 'org/telegram/ui/ActionBar/ActionBarLayout.java'
    tab = 'org/telegram/ui/Components/glass/GlassTabView.java'
    for prefix, before in [('Before', True), ('After', False)]:
        files[prefix+'Nav.java'] = NAV_SUPPORT.replace('NAME', prefix+'Nav').replace('METHOD', method(source(nav, before), 'private void nativeInstantTouchDown('))
        methods = '\n'.join(method(source(tab, before), m) for m in ['public void setGestureSelectedOverride(', 'private void updateColors()'])
        files[prefix+'Tabs.java'] = TAB_SUPPORT.replace('NAME', prefix+'Tabs').replace('METHODS', methods)
    track = 'app/flexygram/composer/ComposerSliderTrack.java'
    files[track] = source(track)
    files[track.replace('ComposerSliderTrack', 'BeforeComposerSliderTrack')] = source(track, True).replace('ComposerSliderTrack', 'BeforeComposerSliderTrack')
    policy = 'app/flexygram/navigation/NativeInstantTouchPolicy.java'
    files[policy] = source(policy)
    files['Probe.java'] = HARNESS
    with tempfile.TemporaryDirectory(prefix='flexy-deep-performance-') as tmp:
        temp = Path(tmp)
        written = []
        for path, content in files.items():
            out = temp/path; out.parent.mkdir(parents=True, exist_ok=True); out.write_text(content); written.append(str(out))
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',str(temp/'classes'),*written],check=True)
        result = subprocess.check_output(['java','-cp',str(temp/'classes'),'Probe'],text=True)
    report = json.loads(result)
    report['baseline_sha'] = BASE
    report['limitations'] = ['Host doubles for Android, view hierarchy, keyboard, image targets and drawing commands.', 'No full-app input dispatch, pixel/GPU comparison, APK, JNI, network or physical performance measurement.']
    out = ROOT/'build/deep-performance/probe-results.json'; out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__': run()
