"""Check material policy on a JVM with Android rendering replaced by small test doubles."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_glass_scope_fallback_theme_and_bounded_controls(tmp_path):
    if not shutil.which("java"):
        pytest.skip("Java required")
    if "jdk.compiler@" not in subprocess.check_output(["java", "--list-modules"], text=True):
        pytest.skip("Java compiler module required")
    sources = {
        "android/graphics/Color.java": "package android.graphics; public class Color { public static final int WHITE=-1; }",
        "org/telegram/messenger/AndroidUtilities.java": "package org.telegram.messenger; public class AndroidUtilities { public static float dpf2(float v) { return v; } }",
        "org/telegram/ui/ActionBar/Theme.java": '''package org.telegram.ui.ActionBar;
public class Theme {
 public static final int key_windowBackgroundWhite=1;
 public interface ResourcesProvider { boolean isDark(); }
 public static boolean isCurrentThemeDark() { return false; }
 public static int getColor(int key, ResourcesProvider p) { return p!=null && p.isDark() ? 0xFF102030 : -1; }
 public static int multAlpha(int color, float alpha) { return (color & 0xFFFFFF) | (Math.round((color>>>24)*alpha)<<24); }
}''',
        "app/exteraless/appearance/AppearanceConfig.java": '''package app.exteraless.appearance;
public class AppearanceConfig {
 public static class Item { public int value; public Item(int v) {value=v;} public int Int(){return value;} public boolean Bool(){return value!=0;} }
 public static Item universalGlass=new Item(0), universalGlassSurfaces=new Item(63), universalGlassOpacity=new Item(42), universalGlassEdge=new Item(70);
}''',
        "org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundProvider.java": '''package org.telegram.ui.Components.blur3.drawable.color;
public interface BlurredBackgroundProvider { int getBackgroundColor(); }''',
        "org/telegram/ui/Components/blur3/drawable/color/impl/BlurredBackgroundProviderImpl.java": '''package org.telegram.ui.Components.blur3.drawable.color.impl;
import org.telegram.ui.ActionBar.Theme;
public class BlurredBackgroundProviderImpl { public static boolean blur=true;
 public static boolean checkBlurEnabled(Theme.ResourcesProvider p){return blur;} }''',
        "org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundProviderBuilder.java": '''package org.telegram.ui.Components.blur3.drawable.color;
import org.telegram.ui.ActionBar.Theme;
public class BlurredBackgroundProviderBuilder implements BlurredBackgroundProvider {
 public interface ColorProvider { int getColor(Theme.ResourcesProvider p, boolean dark); }
 private Theme.ResourcesProvider provider; private ColorProvider bg;
 public BlurredBackgroundProviderBuilder(Theme.ResourcesProvider p){provider=p;}
 public BlurredBackgroundProviderBuilder setBackgroundColor(ColorProvider p){bg=p;return this;}
 public BlurredBackgroundProviderBuilder setStrokeColorTop(ColorProvider p){return this;}
 public BlurredBackgroundProviderBuilder setStrokeColorBottom(ColorProvider p){return this;}
 public BlurredBackgroundProviderBuilder setStrokeColorFull(ColorProvider p){return this;}
 public BlurredBackgroundProviderBuilder setStrokeColorTop(int a,int b){return this;}
 public BlurredBackgroundProviderBuilder setStrokeColorBottom(int a,int b){return this;}
 public BlurredBackgroundProviderBuilder setStrokeColorFull(int a,int b){return this;}
 public BlurredBackgroundProviderBuilder setStrokeWidth(float a,float b){return this;}
 public BlurredBackgroundProviderBuilder setShadowColor(int a,int b){return this;}
 public BlurredBackgroundProviderBuilder setShadowLayer(float a,float b,float c){return this;}
 public BlurredBackgroundProvider build(){return this;}
 public int getBackgroundColor(){return bg.getColor(provider,provider!=null && provider.isDark());}
}''',
        "GlassTest.java": '''import app.exteraless.appearance.*;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.blur3.drawable.color.*;
import org.telegram.ui.Components.blur3.drawable.color.impl.BlurredBackgroundProviderImpl;
public class GlassTest {
 static void check(boolean value){if(!value)throw new AssertionError();}
 public static void main(String[] args){
  Theme.ResourcesProvider light=()->false, dark=()->true;
  BlurredBackgroundProvider fallback=()->0xFFABCDEF;
  check(UniversalGlass.surface(1,light,fallback)==fallback);
  AppearanceConfig.universalGlass.value=1;
  for(int scope=1;scope<=32;scope*=2)check(UniversalGlass.canRender(scope,light));
  AppearanceConfig.universalGlassSurfaces.value=UniversalGlass.HEADER;
  check(!UniversalGlass.canRender(UniversalGlass.INPUT,light));
  check(UniversalGlass.canRender(UniversalGlass.HEADER,light));
  BlurredBackgroundProviderImpl.blur=false;
  check(UniversalGlass.surface(UniversalGlass.HEADER,light,fallback)==fallback);
  BlurredBackgroundProviderImpl.blur=true;
  AppearanceConfig.universalGlassOpacity.value=-100;
  check((UniversalGlass.backgroundColor(light,1)>>>24)==51);
  AppearanceConfig.universalGlassOpacity.value=1000;
  check((UniversalGlass.backgroundColor(light,1)>>>24)==217);
  int c=UniversalGlass.backgroundColor(dark,1);
  check((c&0xFFFFFF)==0x102030 && (c>>>24)<217);
  AppearanceConfig.universalGlassEdge.value=-10;
  check((UniversalGlass.edgeColor(true)>>>24)==0);
  AppearanceConfig.universalGlassEdge.value=1000;
  check((UniversalGlass.edgeColor(true)>>>24)>(UniversalGlass.edgeColor(false)>>>24));
  check(UniversalGlass.material(light,1).getBackgroundColor()==UniversalGlass.fill(light,1).getBackgroundColor());
 }
}''',
    }
    for name, text in sources.items():
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)
    production = ROOT / "TMessagesProj/src/main/java/app/exteraless/appearance/UniversalGlass.java"
    subprocess.run(["java", "-m", "jdk.compiler/com.sun.tools.javac.Main", "-d", str(tmp_path),
                    str(production), *[str(tmp_path / name) for name in sources]], check=True, capture_output=True)
    subprocess.run(["java", "-cp", str(tmp_path), "GlassTest"], check=True, capture_output=True)
