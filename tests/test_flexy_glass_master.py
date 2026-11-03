"""Run the persisted master and saved outline policy; no Android UI claim."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'TMessagesProj/src/main/java'


def test_master_persists_and_restores_saved_outline(tmp_path):
    if not shutil.which('java'):
        pytest.skip('JDK required')
    sources = {
        'tw/nekomimi/nekogram/NekoConfig.java': '''package tw.nekomimi.nekogram;
public class NekoConfig {
 public static final Prefs prefs=new Prefs();
 public static Prefs getPreferences(){return prefs;}
 public static class Prefs {
  public Boolean value;
  public boolean getBoolean(String key,boolean def){return value==null?def:value;}
  public Prefs edit(){return this;}
  public Prefs putBoolean(String key,boolean v){value=v;return this;}
  public void apply(){}
 }
}''',
        'org/telegram/messenger/LiteMode.java': '''package org.telegram.messenger;
public class LiteMode {public static int notifications; public static void onGlassEffectChanged(){notifications++;}}''',
        'app/exteraless/appearance/AppearanceConfig.java': '''package app.exteraless.appearance;
public class AppearanceConfig {public static int saved; public static int glassOutlineStyle(){return saved;}}''',
        'MasterProbe.java': '''import app.exteraless.appearance.*;
import org.telegram.ui.Components.blur3.GlassOutlineStyle;
import org.telegram.messenger.LiteMode;
public class MasterProbe {
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args)throws Exception {
  check(FlexyGlassConfig.enabled());
  for(int style=0;style<3;style++) {
   AppearanceConfig.saved=style;
   FlexyGlassConfig.setEnabled(false);
   check(!FlexyGlassConfig.enabled());
   check(GlassOutlineStyle.current()==GlassOutlineStyle.HIDDEN);
   int notifications=LiteMode.notifications;
   FlexyGlassConfig.setEnabled(false);
   check(LiteMode.notifications==notifications);
   var cache=FlexyGlassConfig.class.getDeclaredField("enabled");cache.setAccessible(true);cache.set(null,null);
   check(!FlexyGlassConfig.enabled());
   FlexyGlassConfig.setEnabled(true);
   check(GlassOutlineStyle.current().ordinal()==style);
   check(AppearanceConfig.saved==style);
   check(LiteMode.notifications==notifications+1);
  }
 }
}''',
    }
    files = []
    for name, content in sources.items():
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)
        files.append(file)
    files += [JAVA / 'app/exteraless/appearance/FlexyGlassConfig.java',
              JAVA / 'org/telegram/ui/Components/blur3/GlassOutlineStyle.java']
    subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-d', str(tmp_path),
                    *map(str, files)], check=True, capture_output=True)
    subprocess.run(['java', '-cp', str(tmp_path), 'MasterProbe'], check=True, capture_output=True)
