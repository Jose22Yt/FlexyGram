"""JVM checks for blur buffer sizing; AST regression check for the removed refractive path."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / "TMessagesProj/src/main/java"


def test_reduced_capture_and_safe_buffer_sizes(tmp_path):
    if not shutil.which("java"):
        pytest.skip("Java required")
    if "jdk.compiler@" not in subprocess.check_output(["java", "--list-modules"], text=True):
        pytest.skip("Java compiler module required")
    test = tmp_path / "PolicyTest.java"
    test.write_text('''import org.telegram.ui.Components.blur3.GlassRenderingPolicy;
public class PolicyTest {
 static void check(boolean ok) { if(!ok) throw new AssertionError(); }
 public static void main(String[] args) {
  check(GlassRenderingPolicy.captureScale(false)==8);
  check(GlassRenderingPolicy.captureScale(true)==1);
  // A 1080x2400 input captures 1/64 of the pixels on the normal path.
  int w=GlassRenderingPolicy.captureDimension(1080,8);
  int h=GlassRenderingPolicy.captureDimension(2400,8);
  check(w==135 && h==300 && (long)w*h*64==1080L*2400);
  for(int dimension : new int[]{0,1,7,8,9,15,16,17,1080,1440,2400,2756}) {
   for(int captureScale : new int[]{1,8}) {
    int capture=GlassRenderingPolicy.captureDimension(dimension,captureScale);
    check(capture>=1);
    for(int blurScale : new int[]{1,8,16}) {
     int down=GlassRenderingPolicy.downsampleDimension(capture,captureScale,blurScale);
     check(down>=1);
     float restore=(float)capture*captureScale/down;
     check(Float.isFinite(restore) && restore>0);
    }
   }
  }
  check(GlassRenderingPolicy.captureDimension(48,0)==48);
  check(GlassRenderingPolicy.downsampleDimension(48,1,0)==48);
 }
}''')
    production = JAVA / "org/telegram/ui/Components/blur3/GlassRenderingPolicy.java"
    subprocess.run(["java", "-m", "jdk.compiler/com.sun.tools.javac.Main", "-d", str(tmp_path),
                    str(production), str(test)], check=True, capture_output=True)
    subprocess.run(["java", "-cp", str(tmp_path), "PolicyTest"], check=True, capture_output=True)


def test_refractive_shader_is_unreachable_from_glass_components():
    # This regression guards the shared rendering boundary, including old direct callers.
    tree_sitter = pytest.importorskip("tree_sitter")
    java = pytest.importorskip("tree_sitter_java")
    parser = tree_sitter.Parser(tree_sitter.Language(java.language()))
    paths = [
        "org/telegram/ui/Components/blur3/BlurredBackgroundDrawableViewFactory.java",
        "org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawableRenderNode.java",
    ]
    for path in paths:
        source = (JAVA / path).read_bytes()
        root = parser.parse(source).root_node
        assert not root.has_error
        pending = [root]
        while pending:
            node = pending.pop()
            if node.type == "object_creation_expression":
                type_node = node.child_by_field_name("type")
                assert source[type_node.start_byte:type_node.end_byte] not in (b"LiquidGlassEffect", b"RuntimeShader")
            if node.type == "method_invocation":
                name = node.child_by_field_name("name")
                assert source[name.start_byte:name.end_byte] != b"createRuntimeShaderEffect"
            pending.extend(node.children)


def test_saved_liquid_flag_cannot_reactivate_rendering(tmp_path):
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
   check(!isEnabled(FLAG_LIQUID_GLASS));
   check(!isEnabledSetting(FLAG_LIQUID_GLASS));
   check(isEnabled(8)==((savedFlags&8)!=0));
   check(isEnabled(FLAG_LIQUID_GLASS|8)==((savedFlags&8)!=0));
   check(isEnabledSetting(FLAG_LIQUID_GLASS|8)==((savedFlags&8)!=0));
   check(saved==savedFlags);
  }
 }
}''')
    subprocess.run(["java", "-m", "jdk.compiler/com.sun.tools.javac.Main", "-d", str(tmp_path), str(harness)],
                   check=True, capture_output=True)
    subprocess.run(["java", "-cp", str(tmp_path), "FlagsTest"], check=True, capture_output=True)


def test_signature_surfaces_do_not_require_the_retired_refractive_flag():
    """Guard the actual render gates which previously disabled the replacement blur."""
    import re
    cases = {
        'org/telegram/ui/MainTabsActivity.java': ['blur3_invalidateBlur'],
        'org/telegram/ui/ActionBar/ActionBar.java': ['prepareSignatureNativeGlass', 'drawSignatureNativeGlass'],
        'org/telegram/ui/Components/ChatActivityEnterView.java': ['flexyNativeGlassIslandsAvailable'],
        'org/telegram/ui/ChatActivity.java': ['getGlassSource'],
    }
    parser_module = pytest.importorskip('tree_sitter')
    language = pytest.importorskip('tree_sitter_java')
    parser = parser_module.Parser(parser_module.Language(language.language()))
    for file, required in cases.items():
        source = (JAVA / file).read_bytes()
        pending = [parser.parse(source).root_node]
        found = {}
        while pending:
            node = pending.pop()
            if node.type == 'method_declaration':
                name = node.child_by_field_name('name').text.decode()
                if name in required:
                    found[name] = node.text.decode()
            pending.extend(node.children)
        assert set(found) == set(required)
        for body in found.values():
            assert 'FLAG_LIQUID_GLASS' not in body
            assert 'FLAG_CHAT_BLUR' in body
