"""Run native Liquid Glass flag queries against enabled, disabled and mixed preferences."""
from pathlib import Path
import shutil, subprocess
import pytest
ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / "TMessagesProj/src/main/java"


def test_native_liquid_flag_respects_saved_preferences(tmp_path):
    """Run the production flag-query methods against old and mixed saved bitmasks."""
    if not shutil.which("java") or "jdk.compiler@" not in subprocess.check_output(["java", "--list-modules"], text=True):
        pytest.skip("Java compiler module required")
    tree_sitter = pytest.importorskip("tree_sitter")
    java = pytest.importorskip("tree_sitter_java")
    parser = tree_sitter.Parser(tree_sitter.Language(java.language()))
    source = (JAVA / "org/telegram/messenger/LiteMode.java").read_bytes()
    pending = [parser.parse(source).root_node]
    methods = {}
    while pending:
        node = pending.pop()
        if node.type == "method_declaration":
            name = node.child_by_field_name("name")
            name = source[name.start_byte:name.end_byte].decode()
            if name in ("isEnabled", "isEnabledSetting"):
                methods[name] = source[node.start_byte:node.end_byte].decode()
        pending.extend(node.children)
    assert len(methods) == 2
    harness = tmp_path / "FlagsTest.java"
    harness.write_text('''public class FlagsTest {
 static final int FLAG_LIQUID_GLASS=1<<18, FLAG_CHAT_FORUM_TWOCOLUMN=4;
 static int saved;
 static class AndroidUtilities { static boolean isTablet(){return false;} }
 static int getValue(){return saved;}
 static int getValue(boolean settings){return saved;}
 static int preprocessFlag(int flag){return flag;}
''' + "\n".join(methods.values()) + '''
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[] args){
  for(int savedFlags : new int[]{0,FLAG_LIQUID_GLASS,FLAG_LIQUID_GLASS|8,8}) {
   saved=savedFlags;
   check(isEnabled(FLAG_LIQUID_GLASS)==((savedFlags&FLAG_LIQUID_GLASS)!=0));
   check(isEnabledSetting(FLAG_LIQUID_GLASS)==((savedFlags&FLAG_LIQUID_GLASS)!=0));
   check(isEnabled(8)==((savedFlags&8)!=0));
   check(isEnabled(FLAG_LIQUID_GLASS|8)==((savedFlags&(FLAG_LIQUID_GLASS|8))!=0));
   check(isEnabledSetting(FLAG_LIQUID_GLASS|8)==((savedFlags&(FLAG_LIQUID_GLASS|8))!=0));
   check(saved==savedFlags);
  }
 }
}''')
    subprocess.run(["java", "-m", "jdk.compiler/com.sun.tools.javac.Main", "-d", str(tmp_path), str(harness)],
                   check=True, capture_output=True)
    subprocess.run(["java", "-cp", str(tmp_path), "FlagsTest"], check=True, capture_output=True)



def test_system_and_in_app_power_savers_preserve_saved_glass_flags(tmp_path):
    from test_composer_layout import method
    from test_render_work_reuse import probe

    source = (JAVA / "org/telegram/messenger/LiteMode.java").read_text()
    policy = method(source, 'public static int getValue(boolean ignorePowerSaving)')
    threshold = method(source, 'private static boolean isBatteryBelowThreshold(')
    receiver = method(source, 'public static class BatteryReceiver extends BroadcastReceiver')
    thermal = method(source, 'private static class ThermalMonitor')
    effect_mask = next(line for line in source.splitlines() if 'int THERMAL_EFFECTS =' in line)
    probe(tmp_path, {'Probe.java': '''
public class Probe {
    static int value=384, powerSaverLevel, level=-1, reads, changes;
    static boolean loaded=true, systemPowerSaver, lastPowerSaverApplied, thermalPressureHigh;
    static int thermalUpdates;
    static class BuildConfig { static final boolean FLEXY_SYSTEM_TRACE=false; }
    static class FileLog { static void e(RuntimeException error){throw new AssertionError(error);} }
    static int lastBatteryLevelCached=-1;
    static long lastBatteryLevelChecked;
    static final int PRESET_POWER_SAVER=0;
    static final int FLAG_CHAT_BLUR=256, FLAG_LIQUID_GLASS=1<<18, FLAG_PARTICLES=1<<17, FLAG_CHAT_THANOS=1<<16;
    EFFECT_MASK_DECLARATION
    static class Build {
        static class VERSION { static int SDK_INT=35; }
        static class VERSION_CODES { static final int LOLLIPOP=21, Q=29; }
    }
    static class SystemClock { static long elapsedRealtime(){return 100;} }
    static class BatteryManager {
        static final String EXTRA_LEVEL="level", EXTRA_SCALE="scale";
    }
    static class PowerManager {
        static final String ACTION_POWER_SAVE_MODE_CHANGED="power";
        static final int THERMAL_STATUS_LIGHT=1, THERMAL_STATUS_SEVERE=3;
        boolean saver;
        int thermalStatus, registrations;
        java.util.function.IntConsumer listener;
        boolean isPowerSaveMode(){return saver;}
        void addThermalStatusListener(java.util.concurrent.Executor executor, java.util.function.IntConsumer callback){
            registrations++;
            listener=status -> executor.execute(() -> callback.accept(status));
            listener.accept(thermalStatus);
        }
    }
    static class Context {
        static final String POWER_SERVICE="power";
        PowerManager power=new PowerManager();
        Object getSystemService(String name){return power;}
        java.util.concurrent.Executor getMainExecutor(){return Runnable::run;}
    }
    record Intent(String getAction, int level) {
        public int getIntExtra(String key,int fallback){return key.equals("level") ? level : 100;}
    }
    static abstract class BroadcastReceiver { abstract void onReceive(Context c,Intent i); }
    static void loadPreference(){throw new AssertionError();}
    static void onPowerSaverApplied(boolean enabled){changes++;}
    static void dispatchPowerPolicyListeners(boolean battery){require(!battery);thermalUpdates++;}
    static int getBatteryLevel(){reads++;return lastBatteryLevelCached;}
    static int getValue(){return getValue(false);}
    POLICY
    THRESHOLD
    RECEIVER
    THERMAL
    static void require(boolean valid){if(!valid) throw new AssertionError();}
    public static void main(String[] args){
        Context c=new Context();BatteryReceiver receiver=new BatteryReceiver();
        require(getValue()==384 && reads==0);
        Build.VERSION.SDK_INT=28;
        receiver.onReceive(c,new Intent("battery",75));
        require(c.power.registrations==0);
        Build.VERSION.SDK_INT=35;
        receiver=new BatteryReceiver();
        c.power.saver=true;receiver.onReceive(c,new Intent("battery",75));
        require(getValue()==0 && getValue(true)==384 && changes==1 && reads==0);
        c.power.saver=false;receiver.onReceive(c,new Intent("power",-1));
        require(getValue()==384 && changes==2 && reads==0);
        powerSaverLevel=20;
        receiver.onReceive(c,new Intent("battery",10));
        require(getValue()==0 && getValue(true)==384 && changes==3);
        c.power.saver=true;receiver.onReceive(c,new Intent("power",-1));
        receiver.onReceive(c,new Intent("battery",80));
        require(getValue()==0 && changes==3);
        c.power.saver=false;receiver.onReceive(c,new Intent("power",-1));
        require(getValue()==384 && changes==4);
        lastBatteryLevelCached=-1;
        require(getValue()==384 && changes==4);
        require(c.power.registrations==1);
        c.power.listener.accept(2);
        require(getValue()==384 && thermalUpdates==0);
        c.power.listener.accept(3);
        c.power.listener.accept(4);
        c.power.listener.accept(2);
        require(getValue()==128 && getValue(true)==384 && thermalUpdates==1 && !lastPowerSaverApplied);
        value=128 | FLAG_CHAT_BLUR | FLAG_LIQUID_GLASS | FLAG_PARTICLES | FLAG_CHAT_THANOS;
        require(getValue()==128 && getValue(true)==value);
        value=384;
        c.power.saver=true;receiver.onReceive(c,new Intent("power",-1));
        c.power.listener.accept(1);
        require(getValue()==0 && changes==5 && thermalUpdates==1);
        c.power.listener.accept(3);
        c.power.saver=false;receiver.onReceive(c,new Intent("power",-1));
        require(getValue()==128 && changes==6 && thermalUpdates==1);
        c.power.listener.accept(1);
        require(getValue()==384 && thermalUpdates==2);
        new BatteryReceiver().onReceive(c,new Intent("battery",90));
        require(c.power.registrations==1);
    }
}
'''.replace('POLICY', policy).replace('THRESHOLD', threshold).replace('RECEIVER', receiver)
        .replace('THERMAL\n', thermal + '\n').replace('EFFECT_MASK_DECLARATION', effect_mask),
        'android/os/Trace.java': '''package android.os;
public class Trace { public static void setCounter(String name, long value) { throw new AssertionError(); } }
''',
    })


def test_disabled_chat_blur_keeps_clipping_without_queuing_captures(tmp_path):
    from test_composer_layout import method
    from test_render_work_reuse import probe

    source = (JAVA / "org/telegram/ui/ChatActivity.java").read_text()
    queue = method(source, 'private void invalidateMergedVisibleBlurredPositionsAndSources(int flags)')
    draw = method(source, 'private void invalidateMergedVisibleBlurredPositionsAndSourcesImpl(int flags)')
    probe(tmp_path, {'Probe.java': '''
public class Probe {
    static final int BLUR_INVALIDATE_FLAG_SCROLL=1, BLUR_INVALIDATE_FLAG_POSITIONS=2, BLUR_INVALIDATE_FLAG_CLIP=4;
    static class Build {
        static class VERSION { static int SDK_INT=35; }
        static class VERSION_CODES { static final int S=31; }
    }
    static class BitwiseUtils { static boolean hasFlag(int mask,int flag){return (mask&flag)!=0;} }
    static class Suppressor {
        int records,setup;
        boolean invalidateResultRenderNodes(Object capture,int w,int h){records++;return true;}
        void setupRenderNodes(Object positions,int count){setup++;}
    }
    static class View {
        int flags;
        void invalidate(int flags){this.flags|=flags;}
        void invalidate(){}
        int getWidth(){return 500;}
        int getHeight(){return 800;}
    }
    static class Source {void invalidateDisplayListForDrawables(){}}
    boolean signatureNativeGlassAllowed;
    int clips,glassDrawablesPositionsCount;
    Probe parentChatActivity;
    Suppressor scrollableViewNoiseSuppressor=new Suppressor();
    View invalidateBlurredSourcesView=new View(),contentView=new View(),chatListView=new View(),actionBar=new View();
    Source glassBackgroundSourceRenderNode=new Source(),glassBackgroundSourceFrostedRenderNode=new Source();
    Object chatBlurCapture,glassDrawablesPositionsMerged;
    Runnable glassSourceInvalidationCallback;
    void invalidateClipRectForBackgroundAndChatList(){clips++;}
    void invalidateAllGlassAttachedViews(){}
    int getMergedVisibleBlurredPositions(Object positions){return 2;}
    QUEUE
    DRAW
    static void require(boolean valid){if(!valid) throw new AssertionError();}
    public static void main(String[] args){
        Probe p=new Probe();
        for(int i=0;i<100;i++)p.invalidateMergedVisibleBlurredPositionsAndSources(3);
        require(p.invalidateBlurredSourcesView.flags==0);
        p.invalidateMergedVisibleBlurredPositionsAndSources(7);
        require(p.invalidateBlurredSourcesView.flags==4);
        p.invalidateMergedVisibleBlurredPositionsAndSourcesImpl(7);
        require(p.clips==1 && p.scrollableViewNoiseSuppressor.records==0 && p.scrollableViewNoiseSuppressor.setup==0);
        p.signatureNativeGlassAllowed=true;
        p.invalidateMergedVisibleBlurredPositionsAndSources(3);
        require(p.invalidateBlurredSourcesView.flags==7);
        p.invalidateMergedVisibleBlurredPositionsAndSourcesImpl(3);
        require(p.scrollableViewNoiseSuppressor.records==1 && p.scrollableViewNoiseSuppressor.setup==1);
    }
}
'''.replace('QUEUE', queue).replace('DRAW', draw)})
