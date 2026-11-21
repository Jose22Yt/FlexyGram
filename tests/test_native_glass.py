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
    probe(tmp_path, {'Probe.java': '''
public class Probe {
    static int value=384, powerSaverLevel, level=-1, reads, changes;
    static boolean loaded=true, systemPowerSaver, lastPowerSaverApplied;
    static int lastBatteryLevelCached=-1;
    static long lastBatteryLevelChecked;
    static final int PRESET_POWER_SAVER=0;
    static class Build {
        static class VERSION { static int SDK_INT=35; }
        static class VERSION_CODES { static final int LOLLIPOP=21; }
    }
    static class SystemClock { static long elapsedRealtime(){return 100;} }
    static class BatteryManager {
        static final String EXTRA_LEVEL="level", EXTRA_SCALE="scale";
    }
    static class PowerManager {
        static final String ACTION_POWER_SAVE_MODE_CHANGED="power";
        boolean saver;
        boolean isPowerSaveMode(){return saver;}
    }
    static class Context {
        static final String POWER_SERVICE="power";
        PowerManager power=new PowerManager();
        Object getSystemService(String name){return power;}
    }
    record Intent(String getAction, int level) {
        public int getIntExtra(String key,int fallback){return key.equals("level") ? level : 100;}
    }
    static abstract class BroadcastReceiver { abstract void onReceive(Context c,Intent i); }
    static void loadPreference(){throw new AssertionError();}
    static void onPowerSaverApplied(boolean enabled){changes++;}
    static int getBatteryLevel(){reads++;return lastBatteryLevelCached;}
    static int getValue(){return getValue(false);}
    POLICY
    THRESHOLD
    RECEIVER
    static void require(boolean valid){if(!valid) throw new AssertionError();}
    public static void main(String[] args){
        Context c=new Context();BatteryReceiver receiver=new BatteryReceiver();
        require(getValue()==384 && reads==0);
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
    }
}
'''.replace('POLICY', policy).replace('THRESHOLD', threshold).replace('RECEIVER', receiver)})


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
