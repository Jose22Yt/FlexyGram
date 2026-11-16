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

