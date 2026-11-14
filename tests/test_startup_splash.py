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


def test_actual_splash_exits_immediately_without_icon_sync_or_content_gate(tmp_path):
    run_java(tmp_path, {
        'android/os/Build.java': 'package android.os;public class Build{public static class VERSION{public static int SDK_INT=31;}}',
        'android/app/Activity.java': '''package android.app;
public class Activity {
 public int reads;public final Splash splash=new Splash();
 public Splash getSplashScreen(){reads++;return splash;}
 public static class Splash{public java.util.function.Consumer<SplashView> exit;
 public void setOnExitAnimationListener(java.util.function.Consumer<SplashView> listener){exit=listener;}}
 public static class SplashView{public boolean removed;public void remove(){removed=true;}}
}''',
        'Probe.java': '''import app.flexygram.performance.StartupSplash;import android.app.Activity;
public class Probe{public static void main(String[]args){
 for(int api:new int[]{31,33,35}){
  android.os.Build.VERSION.SDK_INT=api;Activity activity=new Activity();StartupSplash.install(activity);
  if(activity.reads!=1||activity.splash.exit==null)throw new AssertionError("missing framework handoff");
  Activity.SplashView view=new Activity.SplashView();activity.splash.exit.accept(view);
  if(!view.removed)throw new AssertionError("content held");
 }
 android.os.Build.VERSION.SDK_INT=30;Activity legacy=new Activity();StartupSplash.install(legacy);
 if(legacy.reads!=0)throw new AssertionError("unsupported API");
}}''',
    }, [JAVA / 'app/flexygram/performance/StartupSplash.java'])


def test_starting_window_is_icon_free_including_persisted_per_icon_themes():
    controller = (JAVA / 'org/telegram/ui/LauncherIconController.java').read_text()
    icons = re.findall(r'^        (\w+)\("\w+", R\.(?:drawable|mipmap)\.', controller, re.M)
    styles = {style.get('name'): style for style in ET.parse(RES / 'values-v31/flexygram_startup.xml').getroot()}
    for icon in icons:
        style = styles['Theme.FlexyGram.Start.' + icon]
        assert style.get('parent') == 'Theme.FlexyGram.Start'
        assert not list(style)  # Persisted theme names inherit the empty icon after an update.
    for qualifier in ['values-v31', 'values-v33']:
        base = ET.parse(RES / qualifier / 'flexygram_startup.xml').find('style')
        items = {item.get('name'): item.text for item in base}
        assert items['android:windowSplashScreenAnimatedIcon'] == '@drawable/flexy_startup_empty'
        assert items['android:windowDisablePreview'] == 'true'
        assert items['android:windowSplashScreenAnimationDuration'] == '0'
        assert items['android:windowSplashScreenIconBackgroundColor'] == '@android:color/transparent'
        assert items['android:windowSplashScreenBackground'] == '@color/SplashBackground'
        if qualifier == 'values-v33':
            assert items['android:windowSplashScreenBehavior'] == 'default'
    blank = ET.parse(RES / 'drawable/flexy_startup_empty.xml').getroot()
    assert blank.find('solid').get(A + 'color') == '@android:color/transparent'
    manifest = ET.parse(ROOT / 'TMessagesProj/src/main/AndroidManifest.xml')
    activity = next(a for a in manifest.findall('./application/activity') if a.get(A + 'name') == 'org.telegram.ui.LaunchActivity')
    assert activity.get(A + 'theme') == '@style/Theme.FlexyGram.Start'
    assert activity.get(A + 'launchMode') == 'singleTask'
    assert 'StartupSplash.iconChanged()' not in controller
    assert 'StartupSplash.refreshAfterFirstFrame' not in (JAVA / 'org/telegram/ui/LaunchActivity.java').read_text()


def test_actual_service_dispatch_keeps_background_entry_immediate_and_ui_work_after_frame(tmp_path):
    source = (JAVA / 'org/telegram/messenger/ApplicationLoader.java').read_text()
    start = source.index('        if (prepareDialogs && android.os.Looper.myLooper() == android.os.Looper.getMainLooper())')
    end = source.index('\n        } finally {', start)
    dispatch = source[start:end]
    run_java(tmp_path, {
        'app/exteraless/glyph/GlyphController.java':'package app.exteraless.glyph;public class GlyphController{public static GlyphController getInstance(){return new GlyphController();}public void init(){}}',
        'android/os/Looper.java': '''package android.os; public class Looper {
 static final Looper main=new Looper();public static boolean ui=true;
 public static Looper myLooper(){return ui?main:new Looper();}public static Looper getMainLooper(){return main;}}''',
        'android/view/Choreographer.java': '''package android.view;public class Choreographer {
 public static java.util.function.LongConsumer callback;
 public static Choreographer getInstance(){return new Choreographer();}
 public void postFrameCallback(java.util.function.LongConsumer c){callback=c;}}''',
        'Probe.java': '''class ApplicationLoader {
 static int calls;static class Handler {Runnable pending;void post(Runnable r){pending=r;}}
 static Handler applicationHandler=new Handler();static void initializeAccountServices(){calls++;}static void initializeAccountServices(boolean incremental){calls++;}
 static void dispatch(boolean prepareDialogs){''' + dispatch + '''}}
public class Probe {public static void main(String[]args){
 ApplicationLoader.dispatch(true);if(ApplicationLoader.calls!=0)throw new AssertionError();
 android.view.Choreographer.callback.accept(1L);if(ApplicationLoader.calls!=0)throw new AssertionError();
 ApplicationLoader.applicationHandler.pending.run();if(ApplicationLoader.calls!=1)throw new AssertionError();
 ApplicationLoader.dispatch(false);if(ApplicationLoader.calls!=2)throw new AssertionError();
 android.os.Looper.ui=false;ApplicationLoader.dispatch(true);if(ApplicationLoader.calls!=3)throw new AssertionError();
 }}''',
    })


def test_account_services_are_spread_across_frames_and_headless_stays_immediate(tmp_path):
    from test_composer_layout import method
    source = (JAVA / 'org/telegram/messenger/ApplicationLoader.java').read_text()
    bodies = '\n'.join(method(source, anchor) for anchor in [
        'private static void initializeAccountServices(boolean incremental)',
        'private static void initializeAccountSlot(int account)',
        'private static void scheduleAccountServices(int start)'])
    run_java(tmp_path, {
        'android/os/Trace.java': 'package android.os;public class Trace{public static void beginSection(String s){}public static void endSection(){}}',
        'android/view/Choreographer.java': '''package android.view;public class Choreographer{public static java.util.ArrayList<java.util.function.LongConsumer> frames=new java.util.ArrayList<>();public static Choreographer getInstance(){return new Choreographer();}public void postFrameCallback(java.util.function.LongConsumer r){frames.add(r);}public static void tick(){var todo=new java.util.ArrayList<>(frames);frames.clear();for(var r:todo)r.accept(1);}}''',
        'Probe.java': '''import java.util.*;public class Probe{
 static List<String> calls=new ArrayList<>();static class Handler{List<Runnable> queue=new ArrayList<>();void post(Runnable r){queue.add(r);}void run(){var copy=new ArrayList<>(queue);queue.clear();for(var r:copy)r.run();}}
 static Handler applicationHandler=new Handler();
 static class UserConfig{static final int MAX_ACCOUNT_COUNT=4;int account;static UserConfig getInstance(int a){var v=new UserConfig();v.account=a;return v;}boolean isClientActivated(){return account==1||account==3;}}
 static void initializeDeferredStartupAccount(int account){} // No deferred core sessions in this legacy service-order fixture.
 static class MediaController{static void getInstance(){calls.add("media");}}
 static class ContactsController{int account;static ContactsController getInstance(int a){var v=new ContactsController();v.account=a;return v;}void checkAppAccount(){calls.add("contacts"+account);}}
 static class DownloadController{static void getInstance(int a){calls.add("downloads"+a);}}
 static class BillingController{static BillingController getInstance(){return new BillingController();}void startConnection(){calls.add("billing");}}
 ''' + bodies + '''
 static void check(boolean v){if(!v)throw new AssertionError(calls.toString());}
 public static void main(String[] args){
  initializeAccountServices(true);check(calls.equals(List.of("media")));
  android.view.Choreographer.tick();check(calls.size()==1);applicationHandler.run();check(calls.equals(List.of("media","contacts0")));
  android.view.Choreographer.tick();applicationHandler.run();check(calls.equals(List.of("media","contacts0","contacts1","downloads1")));
  android.view.Choreographer.tick();applicationHandler.run();check(calls.get(4).equals("contacts3"));
  android.view.Choreographer.tick();applicationHandler.run();check(calls.equals(List.of("media","contacts0","contacts1","downloads1","contacts3","downloads3","billing")));check(android.view.Choreographer.frames.isEmpty());
  var expected=new ArrayList<>(calls);calls.clear();initializeAccountServices(false);check(calls.equals(expected));check(android.view.Choreographer.frames.isEmpty());
 }
}''',
    })
