"""Native splash resource coverage and execution of the actual frame-coalesced theme policy."""
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import pytest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'TMessagesProj/src/main/java'
RES = ROOT / 'TMessagesProj/src/main/res'
A = '{http://schemas.android.com/apk/res/android}'


def run_java(tmp_path, sources, actual=()):
    if not shutil.which('java'):
        pytest.skip('JDK required')
    files = []
    for name, content in sources.items():
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)
        files.append(file)
    result = subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-d', str(tmp_path),
                             *map(str, files), *map(str, actual)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run(['java', '-cp', str(tmp_path), 'Probe'], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_actual_splash_coalesces_changes_and_never_delays_or_holds_the_content(tmp_path):
    source = (JAVA / 'app/flexygram/performance/StartupSplash.java').read_text()
    names = re.findall(r'case (\w+): return R.style.(\w+);', source)
    sources = {
        'android/os/Build.java': 'package android.os; public class Build {public static class VERSION {public static int SDK_INT=31;}}',
        'android/view/View.java': '''package android.view; import java.util.*;
public class View {
 public static List<Runnable> frame=new ArrayList<>(),main=new ArrayList<>();
 public void postOnAnimation(Runnable r){frame.add(r);} public boolean post(Runnable r){main.add(r);return true;}
 public static void tick(){for(Runnable r:new ArrayList<>(frame)){frame.remove(r);r.run();}for(Runnable r:new ArrayList<>(main)){main.remove(r);r.run();}}
}''',
        'android/app/Activity.java': '''package android.app;
public class Activity {
 public boolean finishing,destroyed; public int calls,theme,reads;
 public boolean isFinishing(){return finishing;}public boolean isDestroyed(){return destroyed;}
 public class Splash {public java.util.function.Consumer<SplashView> exit;
  public void setOnExitAnimationListener(java.util.function.Consumer<SplashView> l){exit=l;}
  public void setSplashScreenTheme(int t){theme=t;calls++;}}
 public static class SplashView {public boolean removed;public void remove(){removed=true;}}
 public class Window {public android.view.View getDecorView(){return new android.view.View();}}
 public final Splash splash=new Splash();public Splash getSplashScreen(){reads++;return splash;}
 public Window getWindow(){return new Window();}
}''',
        'org/telegram/messenger/AndroidUtilities.java': 'package org.telegram.messenger; public class AndroidUtilities {public static void runOnUIThread(Runnable r){r.run();}}',
        'org/telegram/messenger/FileLog.java': 'package org.telegram.messenger; public class FileLog {public static void e(Throwable t){throw new AssertionError(t);}}',
        'org/telegram/messenger/R.java': 'package org.telegram.messenger; public class R {public static class style {' +
             ''.join(f'public static final int {style}={i+1};' for i, (_, style) in enumerate(names)) + '}}',
        'org/telegram/ui/LauncherIconController.java': '''package org.telegram.ui; public class LauncherIconController {
 public enum LauncherIcon {''' + ','.join(n for n, _ in names) + '''}
 public static LauncherIcon selected=LauncherIcon.FLEX_NEON;
 public static LauncherIcon getRememberedIcon(){return selected;}}
''',
        'Probe.java': '''import app.flexygram.performance.StartupSplash;
import org.telegram.ui.LauncherIconController;
import org.telegram.ui.LauncherIconController.LauncherIcon;
import android.app.Activity;import android.view.View;
public class Probe {
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){
  Activity a=new Activity();StartupSplash.install(a);
  check(a.calls==0);check(a.splash.exit!=null);
  Activity.SplashView splash=new Activity.SplashView();a.splash.exit.accept(splash);check(splash.removed);
  StartupSplash.refreshAfterFirstFrame(a);StartupSplash.refreshAfterFirstFrame(a);
  check(a.calls==0&&View.frame.size()==1);
  LauncherIconController.selected=LauncherIcon.FLEX_GLOSSY;
  StartupSplash.iconChanged();check(View.frame.size()==1);
  View.tick();check(a.calls==1&&a.theme==StartupSplash.themeFor(LauncherIcon.FLEX_GLOSSY));
  StartupSplash.refreshAfterFirstFrame(a);View.tick();check(a.calls==1);
  LauncherIconController.selected=LauncherIcon.FLEX_GREEN;StartupSplash.iconChanged();View.tick();check(a.calls==2);
  a.finishing=true;LauncherIconController.selected=LauncherIcon.FLEX_CORAL;
  StartupSplash.iconChanged();View.tick();check(a.calls==2);
  a.finishing=false;StartupSplash.refreshAfterFirstFrame(a);View.tick();check(a.calls==3);
  java.util.Set<Integer> themes=new java.util.HashSet<>();
  for(LauncherIcon i:LauncherIcon.values())check(themes.add(StartupSplash.themeFor(i)));
  android.os.Build.VERSION.SDK_INT=30;Activity old=new Activity();StartupSplash.install(old);
  StartupSplash.refreshAfterFirstFrame(old);StartupSplash.iconChanged();View.tick();check(old.reads==0);
 }
}''',
    }
    run_java(tmp_path, sources, [JAVA / 'app/flexygram/performance/StartupSplash.java'])


def test_every_selectable_icon_has_a_stable_native_theme_and_new_icons_have_circular_art():
    controller = (JAVA / 'org/telegram/ui/LauncherIconController.java').read_text()
    icons = re.findall(r'^        (\w+)\("(\w+)", R\.(?:drawable|mipmap)\.', controller, re.M)
    styles = {s.get('name'): s for s in ET.parse(RES / 'values-v31/flexygram_startup.xml').getroot()}
    aliases = {a.get(A+'name').split('.')[-1]: a for a in
               ET.parse(ROOT / 'TMessagesProj/src/main/AndroidManifest.xml').findall('./application/activity-alias')}
    source = (JAVA / 'app/flexygram/performance/StartupSplash.java').read_text()
    for name, key in icons:
        style = styles['Theme.FlexyGram.Start.'+name]
        assert style.get('parent') == 'Theme.FlexyGram.Start'
        assert f'case {name}: return R.style.Theme_FlexyGram_Start_{name};' in source
        resource = style.find('item').text
        if name.startswith('FLEX_') or name == 'EXTERALESS':
            vector = ET.parse(RES / 'drawable-v24' / (resource.split('/')[-1]+'.xml')).getroot()
            assert vector.get(A+'viewportWidth') == '162'
            assert vector.find('./group/clip-path').get(A+'pathData') == 'M54,0 A54,54 0,1 1,54,108 A54,54 0,1 1,54,0 Z'
            assert vector.find('group').get(A+'translateX') == '27'
        else:
            assert resource == aliases[key].get(A+'roundIcon')
    for qualifier in ['values-v31', 'values-v33']:
        base = ET.parse(RES / qualifier / 'flexygram_startup.xml').find('style')
        items = {item.get('name'): item.text for item in base}
        assert items['android:windowSplashScreenAnimationDuration'] == '0'
        assert items['android:windowSplashScreenBackground'] == '@color/SplashBackground'
    manifest = ET.parse(ROOT / 'TMessagesProj/src/main/AndroidManifest.xml')
    activity = next(a for a in manifest.findall('./application/activity') if a.get(A+'name') == 'org.telegram.ui.LaunchActivity')
    assert activity.get(A+'theme') == '@style/Theme.FlexyGram.Start'
    assert activity.get(A+'launchMode') == 'singleTask'


def test_actual_service_dispatch_keeps_background_entry_immediate_and_ui_work_after_frame(tmp_path):
    source = (JAVA / 'org/telegram/messenger/ApplicationLoader.java').read_text()
    start = source.index('        if (prepareDialogs && android.os.Looper.myLooper() == android.os.Looper.getMainLooper())')
    end = source.index('\n        } finally {', start)
    dispatch = source[start:end]
    run_java(tmp_path, {
        'android/os/Looper.java': '''package android.os; public class Looper {
 static final Looper main=new Looper();public static boolean ui=true;
 public static Looper myLooper(){return ui?main:new Looper();}public static Looper getMainLooper(){return main;}}''',
        'android/view/Choreographer.java': '''package android.view;public class Choreographer {
 public static java.util.function.LongConsumer callback;
 public static Choreographer getInstance(){return new Choreographer();}
 public void postFrameCallback(java.util.function.LongConsumer c){callback=c;}}''',
        'Probe.java': '''class ApplicationLoader {
 static int calls;static class Handler {Runnable pending;void post(Runnable r){pending=r;}}
 static Handler applicationHandler=new Handler();static void initializeAccountServices(){calls++;}
 static void dispatch(boolean prepareDialogs){''' + dispatch + '''}}
public class Probe {public static void main(String[]args){
 ApplicationLoader.dispatch(true);if(ApplicationLoader.calls!=0)throw new AssertionError();
 android.view.Choreographer.callback.accept(1L);if(ApplicationLoader.calls!=0)throw new AssertionError();
 ApplicationLoader.applicationHandler.pending.run();if(ApplicationLoader.calls!=1)throw new AssertionError();
 ApplicationLoader.dispatch(false);if(ApplicationLoader.calls!=2)throw new AssertionError();
 android.os.Looper.ui=false;ApplicationLoader.dispatch(true);if(ApplicationLoader.calls!=3)throw new AssertionError();
 }}''',
    })
