#!/usr/bin/env python3
"""Run the production popup window, swipe layout and menu-opening methods on Android.

Account data, theme/blur providers and the menu contents factory are explicit
fixtures. Window measurement, animation, drawing and positioning are production.
"""
import importlib.util
from pathlib import Path
import shutil
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('header_menu_pipeline', HERE.parent/'music_visual/run.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


def method(text, marker):
    start = text.index(marker)
    end = text.index('{', start) + 1
    depth = 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


def resources(root, res):
    for name in ('popup_fixed_alert2.9.png', 'popup_fixed_alert4.9.png', 'greydivider.9.png'):
        shutil.copyfile(root/'TMessagesProj/src/main/res/drawable-mdpi'/name, res/name)


def write_stubs(source, root):
    def put(path, text):
        p = source/path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    java = root/'TMessagesProj/src/main/java'
    for annotation in ('Keep','NonNull','Nullable'):
        put('androidx/annotation/'+annotation+'.java', 'package androidx.annotation;public @interface '+annotation+'{}')
    for path in ('org/telegram/ui/ActionBar/ActionBarPopupWindow.java',
                 'org/telegram/ui/Components/PopupSwipeBackLayout.java',
                 'org/telegram/ui/Components/LayoutHelper.java',
                 'app/flexygram/animation/FastMotion.java',
                 'app/flexygram/animation/FastMotionTiming.java'):
        put(path, (java/path).read_text())
    put('app/flexygram/motionbuild/FastMotionVisitor.java',(root/'buildSrc/src/main/java/app/flexygram/motionbuild/FastMotionVisitor.java').read_text())
    put('org/telegram/messenger/ApplicationLoader.java','package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext;}')
    put('androidx/dynamicanimation/animation/DynamicAnimation.java','package androidx.dynamicanimation.animation;public class DynamicAnimation<T>{public void start(){}}')
    put('androidx/dynamicanimation/animation/SpringAnimation.java','package androidx.dynamicanimation.animation;public class SpringAnimation extends DynamicAnimation<SpringAnimation>{public boolean canSkipToEnd(){return false;}public void skipToEnd(){}}')
    put('TransformPopup.java','''import java.nio.file.*;import org.objectweb.asm.*;import app.flexygram.motionbuild.FastMotionVisitor;
public class TransformPopup{static boolean inherits(String owner,String base){try{return Class.forName(base,false,TransformPopup.class.getClassLoader()).isAssignableFrom(Class.forName(owner.replace('/','.'),false,TransformPopup.class.getClassLoader()));}catch(Exception e){return false;}}
public static void main(String[]args)throws Exception{Path root=Path.of(args[0]);try(var stream=Files.walk(root.resolve("org/telegram/ui"))){for(Path p:stream.filter(n->n.toString().endsWith(".class")).toList()){ClassWriter writer=new ClassWriter(0);new ClassReader(Files.readAllBytes(p)).accept(new FastMotionVisitor(writer,TransformPopup::inherits),0);Files.write(p,writer.toByteArray());}}}}
''')
    put('org/telegram/messenger/R.java', '''package org.telegram.messenger;public class R{
 public static class drawable{public static int popup_fixed_alert2,popup_fixed_alert4,greydivider;}
 public static class style{public static int PopupAnimation=0;}
 public static class id{public static int width_tag=0x7f010001,object_tag=0x7f010002,fit_width_tag=0x7f010003;}}''')
    put('org/telegram/messenger/AndroidUtilities.java', '''package org.telegram.messenger;import android.graphics.*;import android.util.DisplayMetrics;public class AndroidUtilities{
 public static float density=1;public static Point displaySize=new Point(400,800);public static DisplayMetrics displayMetrics=new DisplayMetrics();
 static{displayMetrics.density=1;displayMetrics.heightPixels=800;displayMetrics.widthPixels=400;}
 public static final RectF rectTmp=new RectF();public static final Rect rectTmp2=new Rect();
 public static int dp(float n){return (int)Math.ceil(n*density);}public static float dpf2(float n){return n*density;}
 public static float lerp(float a,float b,float p){return a+(b-a)*p;}
 public static void lerp(Rect a,Rect b,float p,Rect out){out.set((int)lerp(a.left,b.left,p),(int)lerp(a.top,b.top,p),(int)lerp(a.right,b.right,p),(int)lerp(a.bottom,b.bottom,p));}
 public static float cascade(float t,int i,int n,int spread){return Math.max(0,Math.min(1,t*(1+spread)-(float)i/Math.max(1,n)*spread));}
 public static void cancelRunOnUIThread(Runnable r){new android.os.Handler(android.os.Looper.getMainLooper()).removeCallbacks(r);}
 }''')
    put('org/telegram/messenger/LocaleController.java', 'package org.telegram.messenger;public class LocaleController{public static boolean isRTL;}')
    put('org/telegram/messenger/UserConfig.java', 'package org.telegram.messenger;public class UserConfig{public static int selectedAccount;}')
    put('org/telegram/messenger/FileLog.java', 'package org.telegram.messenger;public class FileLog{public static void e(Throwable e){throw new AssertionError(e);}}')
    put('org/telegram/messenger/AnimationNotificationsLocker.java', 'package org.telegram.messenger;public class AnimationNotificationsLocker{public void lock(){}public void unlock(){}}')
    put('org/telegram/messenger/utils/ViewOutlineProviderImpl.java', 'package org.telegram.messenger.utils;public class ViewOutlineProviderImpl extends android.view.ViewOutlineProvider{public void getOutline(android.view.View v,android.graphics.Outline o){}}')
    put('app/flexygram/icons/IconPressFeedback.java', 'package app.flexygram.icons;public class IconPressFeedback{public static void observe(android.view.View v,android.view.MotionEvent e){}}')
    put('org/telegram/ui/ActionBar/Theme.java', '''package org.telegram.ui.ActionBar;import android.graphics.drawable.*;public class Theme{
 public interface ResourcesProvider{}public static final int key_actionBarDefaultSubmenuBackground=1,key_actionBarDefaultSubmenuSeparator=2,key_windowBackgroundGrayShadow=3,key_actionBarDefaultSubmenuItem=4;
 public static int getColor(int key,ResourcesProvider p){return key==4?0xff000000:0xffeeeeee;}public static int multAlpha(int c,float a){return c;}
 public static Drawable createRadSelectorDrawable(int c,int t,int b){return new ColorDrawable(c);}public static Drawable getThemedDrawable(android.content.Context c,int id,int color){return c.getResources().getDrawable(id).mutate();}
 }''')
    put('org/telegram/ui/ActionBar/ActionBarMenuSubItem.java', '''package org.telegram.ui.ActionBar;public class ActionBarMenuSubItem extends android.widget.TextView{public ActionBarMenuSubItem(android.content.Context c){super(c);}public void onItemShown(){}public void updateSelectorBackground(boolean a,boolean b){}}''')
    put('org/telegram/ui/ActionBar/ActionBarMenuSlider.java', 'package org.telegram.ui.ActionBar;public class ActionBarMenuSlider extends android.view.View{public ActionBarMenuSlider(android.content.Context c){super(c);}}')
    put('org/telegram/ui/ActionBar/ActionBar.java', 'package org.telegram.ui.ActionBar;public class ActionBar extends android.widget.FrameLayout{public ActionBar(android.content.Context c){super(c);}public boolean isActionModeShowed(){return false;}}')
    put('org/telegram/ui/ActionBar/ActionBarMenu.java', 'package org.telegram.ui.ActionBar;public class ActionBarMenu extends android.widget.LinearLayout{public boolean isActionMode;public ActionBar parentActionBar;public ActionBarMenu(android.content.Context c,ActionBar bar){super(c);parentActionBar=bar;}}')
    put('org/telegram/ui/Components/CubicBezierInterpolator.java', 'package org.telegram.ui.Components;public class CubicBezierInterpolator{public static android.animation.TimeInterpolator DEFAULT=new android.view.animation.LinearInterpolator();}')
    put('org/telegram/ui/Components/Easings.java', 'package org.telegram.ui.Components;public class Easings{public static android.animation.TimeInterpolator easeInOutQuad=new android.view.animation.LinearInterpolator();}')
    put('org/telegram/ui/Components/ItemOptions.java', 'package org.telegram.ui.Components;public class ItemOptions{public static void setGapBackgroundColor(org.telegram.ui.ActionBar.ActionBarPopupWindow.ActionBarPopupWindowLayout v,int color){}}')
    text=(java/'org/telegram/ui/ActionBar/ActionBarMenuItem.java').read_text()
    methods='\n'.join(method(text, marker) for marker in (
        'private void createPopupLayout()', 'public boolean hasSubMenu()',
        'public void toggleSubMenu(View topView, View fromView, boolean fromStickersAlert)',
        'private void updateOrShowPopup(boolean show, boolean update)'))
    put('org/telegram/ui/ActionBar/ActionBarMenuItem.java', '''package org.telegram.ui.ActionBar;
import static org.telegram.messenger.AndroidUtilities.dp;
import android.content.*;import android.graphics.*;import android.graphics.drawable.*;import android.view.*;import android.widget.*;
import androidx.core.content.ContextCompat;import org.telegram.messenger.*;import org.telegram.ui.Components.*;
public class ActionBarMenuItem extends FrameLayout{
 private ActionBarPopupWindow popupWindow;private ActionBarPopupWindow.ActionBarPopupWindowLayout popupLayout;
 private ActionBarMenu parentMenu;private boolean animationEnabled=true,layoutInScreen,measurePopup,processedPopupClick,forceSmoothKeyboard,showOnTop;
 private int subMenuOpenSide,additionalXOffset,additionalYOffset,xOffset,yOffset;private float dimMenu;
 private View anchor,showSubMenuFrom;private Runnable showMenuRunnable;private Rect rect;private int[]location;
 private java.util.ArrayList<Object> lazyList=new java.util.ArrayList<>();
 private Theme.ResourcesProvider resourcesProvider;private Delegate subMenuDelegate;private Factory subMenuFactory;private Object subMenuProvider;
 public static class Delegate{public void onShowSubMenu(){}public void onHideSubMenu(){}}
 public static class Panel extends ColorDrawable{public Panel(){super(0xffeeeeee);}public Panel setColorProvider(Object p){return this;}public Panel setRadius(int r){return this;}public Panel setPadding(int n){return this;}public Panel setHasPadding(boolean b){return this;}}
 public static class Factory{public Panel create(View v,boolean b){return new Panel();}}
 public ActionBarMenuItem(Context c,ActionBarMenu menu){super(c);parentMenu=menu;}
 private void layoutLazyItems(){if(popupLayout!=null)return;createPopupLayout();for(String title:new String[]{"Buscar","Silenciar","Eliminar chat"}){TextView item=new TextView(getContext());item.setText(title);item.setTextColor(Color.BLACK);item.setMinimumWidth(196);popupLayout.addView(item,new LinearLayout.LayoutParams(196,48));}}
 private int getThemedColor(int key){return Theme.getColor(key,resourcesProvider);}protected void onDismiss(){}
 public boolean showing(){return popupWindow!=null&&popupWindow.isShowing();}public View contents(){return popupWindow.getContentView();}public void dismiss(){popupWindow.dismiss(false);}
 public void useBlur(){subMenuFactory=new Factory();}
 METHODS
}'''.replace('METHODS',methods))


if __name__=='__main__':
    instrument = '--instrument-motion' in sys.argv
    if instrument:
        sys.argv.remove('--instrument-motion')
    if '--output-dir' not in sys.argv:
        sys.argv += ['--output-dir', str(HERE.parents[2]/'build/connected-alpha-header-menu')]
    output = Path(sys.argv[sys.argv.index('--output-dir')+1]).resolve()
    sdk = Path(sys.argv[sys.argv.index('--sdk-root')+1]).resolve()
    maven = sys.argv[sys.argv.index('--maven')+1] if '--maven' in sys.argv else 'mvn'
    result = pipeline.main(here=HERE,test_class='HeaderMenuTest',stubs_writer=write_stubs,resource_writer=resources)
    if instrument:
        repository = Path(os.environ.get('MAVEN_REPO_LOCAL', str(Path.home()/'.m2/repository')))
        jars = list((repository/'org/ow2/asm/asm').glob('*/asm-*.jar'))
        if not jars:
            raise SystemExit('ASM dependency not available; instrumentation not skipped.')
        asm = max(jars, key=lambda p: tuple(int(x) for x in p.parent.name.split('.') if x.isdigit()))
        classpath = os.pathsep.join(map(str, (output/'target/test-classes',sdk/'platforms/android-37.0/android.jar',asm)))
        subprocess.run(['java','-cp',classpath,'TransformPopup',str(output/'target/test-classes')],check=True)
        subprocess.run([maven,'-o','-B','-f',str(output/'pom.xml'),'-Dmaven.repo.local='+str(repository),
                        '-Dandroid.sdk.jar='+str(sdk/'platforms/android-37.0/android.jar'),'-Pmusic-compile','surefire:test'],check=True)
    raise SystemExit(result)
