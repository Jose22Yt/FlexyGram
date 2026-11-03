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
 public static final int key_windowBackgroundWhite=1,key_telegram_color=2;
 public interface ResourcesProvider { boolean isDark(); }
 public static boolean isCurrentThemeDark() { return false; }
 public static int getColor(int key, ResourcesProvider p) { if(key==2)return 0xff34ab56;return p!=null && p.isDark() ? 0xFF102030 : -1; }
 public static int multAlpha(int color, float alpha) { return (color & 0xFFFFFF) | (Math.round((color>>>24)*alpha)<<24); }
}''',
        "app/exteraless/appearance/UniversalGlassConfig.java": '''package app.exteraless.appearance;
public class UniversalGlassConfig {
 public static int look;public static class Item { public int value; public Item(int v) {value=v;} public int Int(){return value;} public boolean Bool(){return value!=0;} }
 public static boolean enabled(){return universalGlass.Bool();}
 public static int surfaces(){return universalGlassSurfaces.Int();}
 public static int opacity(){return universalGlassOpacity.Int();}
 public static int edge(){return universalGlassEdge.Int();}public static app.flexygram.effects.GlassSettings snapshot(){return new app.flexygram.effects.GlassSettings(enabled(),opacity(),40,edge(),8,look,55,0,60,true,5);}
 public static Item universalGlass=new Item(0), universalGlassSurfaces=new Item(63), universalGlassOpacity=new Item(42), universalGlassEdge=new Item(70);
}''',
        "org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundProvider.java": '''package org.telegram.ui.Components.blur3.drawable.color;
public interface BlurredBackgroundProvider { int getBackgroundColor();
 default int getShadowColor(){return 0;}default int getStrokeColorTop(){return 0;}default int getStrokeColorBottom(){return 0;}default int getStrokeColorFull(){return 0;}
 default float getStrokeWidthTop(){return .8f;}default float getStrokeWidthBottom(){return .65f;}default float getShadowRadius(){return 3;}default float getShadowDx(){return 0;}default float getShadowDy(){return 1;}
 }''',
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
  UniversalGlassConfig.universalGlass.value=1;
  for(int scope=1;scope<=32;scope*=2)check(UniversalGlass.canRender(scope,light));
  UniversalGlassConfig.universalGlassSurfaces.value=UniversalGlass.HEADER;
  // Saved per-surface exclusions no longer restrict the automatically applied material.
  for(int scope=1;scope<=32;scope*=2)check(UniversalGlass.canRender(scope,light));
  UniversalGlassConfig.universalGlassSurfaces.value=0;
  for(int scope=1;scope<=32;scope*=2)check(UniversalGlass.canRender(scope,light));
  check(!UniversalGlass.canRender(64,light));
  BlurredBackgroundProviderImpl.blur=false;
  check(UniversalGlass.surface(UniversalGlass.HEADER,light,fallback)==fallback);
  BlurredBackgroundProviderImpl.blur=true;
  UniversalGlassConfig.universalGlassOpacity.value=-100;
  check((UniversalGlass.backgroundColor(light,1)>>>24)==GlassContrastPolicy.MIN_LIGHT_ALPHA);
  check((UniversalGlass.backgroundColor(dark,1)>>>24)==43);
  UniversalGlassConfig.universalGlassOpacity.value=1000;
  check((UniversalGlass.backgroundColor(light,1)>>>24)==217);
  int c=UniversalGlass.backgroundColor(dark,1);
  check((c&0xFFFFFF)==0x102030 && (c>>>24)<217);
  UniversalGlassConfig.universalGlassEdge.value=-10;
  check((UniversalGlass.edgeColor(true)>>>24)==0);
  UniversalGlassConfig.universalGlassEdge.value=100;
  check((UniversalGlass.edgeColor(true)>>>24)>(UniversalGlass.edgeColor(false)>>>24));
  check(UniversalGlass.material(light,1).getBackgroundColor()==UniversalGlass.fill(light,1).getBackgroundColor());
  for(int look=1;look<=3;look++) {
   UniversalGlassConfig.look=look;UniversalGlassConfig.universalGlassEdge.value=70;
   int base=app.flexygram.bubbles.BubbleOutline.palette(-1,0xff34ab56,0,0);
   int expected=app.flexygram.bubbles.BubbleOutline.color(base,false,look==1?3:look==2?1:2,55);
   int actual=UniversalGlass.material(light,1).getStrokeColorTop();
   check((actual&0xffffff)==(expected&0xffffff));check((actual>>>24)==Math.round((expected>>>24)*.7f));
   UniversalGlassConfig.universalGlassEdge.value=200;check((UniversalGlass.material(light,1).getStrokeColorTop()>>>24)<=255);
  }
  UniversalGlassConfig.look=0;UniversalGlassConfig.universalGlassEdge.value=100;int lower=UniversalGlass.edgeColor(false,false)>>>24;
  UniversalGlassConfig.universalGlassEdge.value=200;check((UniversalGlass.edgeColor(false,false)>>>24)>lower);
 }
}''',
    }
    sources['app/exteraless/appearance/FlexyGlassConfig.java'] = 'package app.exteraless.appearance;public class FlexyGlassConfig{public static boolean enabled(){return true;}}'
    for name, text in sources.items():
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)
    production = ROOT / "TMessagesProj/src/main/java/app/exteraless/appearance/UniversalGlass.java"
    subprocess.run(["java", "-m", "jdk.compiler/com.sun.tools.javac.Main", "-d", str(tmp_path),
                    str(production), str(production.with_name("GlassContrastPolicy.java")),
                    str(production.with_name("SimpleGlassProvider.java")),
                    str(ROOT / "TMessagesProj/src/main/java/app/flexygram/effects/GlassSettings.java"),
                    str(ROOT / "TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleOutline.java"),
                    *[str(tmp_path / name) for name in sources]], check=True, capture_output=True)
    subprocess.run(["java", "-cp", str(tmp_path), "GlassTest"], check=True, capture_output=True)
