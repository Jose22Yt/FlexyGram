"""Real destination, preference and bounded width policy; Android rendering is not emulated."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'TMessagesProj/src/main/java'


def test_dock_resizes_and_empty_selection_survives_reload(tmp_path):
    if not shutil.which('java'):
        pytest.skip('JDK required')
    sources = {
        'android/content/SharedPreferences.java': '''package android.content;
public class SharedPreferences {
 java.util.Map<String,Object> values=new java.util.HashMap<>();
 public boolean getBoolean(String k,boolean d){return (Boolean)values.getOrDefault(k,d);}
 public int getInt(String k,int d){return (Integer)values.getOrDefault(k,d);}
 public String getString(String k,String d){return (String)values.getOrDefault(k,d);}
 public Editor edit(){return new Editor();}
 public class Editor {
  public Editor putBoolean(String k,boolean v){values.put(k,v);return this;}
  public Editor putInt(String k,int v){values.put(k,v);return this;}
  public Editor putString(String k,String v){values.put(k,v);return this;}
  public Editor remove(String k){values.remove(k);return this;}
  public void apply(){}
 }
}''',
        'android/content/Context.java': '''package android.content;
public class Context {public static final int MODE_PRIVATE=0;
 public final SharedPreferences prefs=new SharedPreferences();
 public SharedPreferences getSharedPreferences(String name,int mode){return prefs;}}
''',
        'org/telegram/messenger/ApplicationLoader.java': '''package org.telegram.messenger;
public class ApplicationLoader {public static android.content.Context applicationContext=new android.content.Context();}''',
        'DockProbe.java': '''import app.flexygram.navigation.*;
import java.util.Arrays;
public class DockProbe {
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args) {
  LiquidNavigationConfig.load();check(LiquidNavigationConfig.order().length==4);
  LiquidNavigationConfig.setOrder(new int[0]);check(!LiquidNavigationConfig.isVisible());
  LiquidNavigationConfig.load();check(LiquidNavigationConfig.order().length==0);
  check(LiquidNavigationConfig.shown(4).length==0);
  LiquidNavigationConfig.setOrder(new int[]{4});check(LiquidNavigationConfig.isVisible());
  check(Arrays.equals(LiquidNavigationConfig.shown(6),new int[]{4}));
  LiquidNavigationConfig.setOrder(LiquidNavigationDestinations.defaults());
  LiquidNavigationConfig.setSeparateSearch(true);
  check(LiquidNavigationConfig.shown(4).length==4);
  for(int count=1;count<=6;count++)check(!LiquidNavigationConfig.hideLabels(count,140));
  LiquidNavigationConfig.setShowTitles(false);check(LiquidNavigationConfig.hideLabels(2,500));
  LiquidNavigationConfig.setShowTitles(true);
  LiquidNavigationConfig.setOrder(new int[]{0,10,4});check(Arrays.equals(LiquidNavigationConfig.shown(4),new int[]{0,4}));
  for(int available:new int[]{240,320,360,412,600,1000})for(float fraction:new float[]{.86f,.93f,1f}) {
   int previous=0;
   for(int count=0;count<=6;count++) {
    int width=LiquidNavigationMath.dockWidth(available,count,4,72,fraction,true);
    check(width>=previous&&width<=available);
    if(count==0)check(width==0);
    if(count>0)check(LiquidNavigationMath.dockWidth(available,count,4,72,fraction,false)==available);
    previous=width;
   }
  }
  check(LiquidNavigationMath.dockWidth(412,3,4,72,.93f,true)<LiquidNavigationMath.dockWidth(412,4,4,72,.93f,true));
  int[] ids=LiquidNavigationDestinations.sanitize(new int[]{4,4,-1,2,99});
  check(Arrays.equals(ids,new int[]{4,2}));check(!LiquidNavigationDestinations.contains(ids,0));
  check(Arrays.equals(LiquidNavigationDestinations.fit(new int[]{4,2,1},2),new int[]{4,9}));
  check(Arrays.equals(LiquidNavigationDestinations.fit(new int[]{4,2},1),new int[]{9}));
 }
}''',
    }
    files = []
    for name, content in sources.items():
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)
        files.append(file)
    files += [JAVA / f'app/flexygram/navigation/{name}.java'
              for name in ['LiquidNavigationConfig', 'LiquidNavigationDestinations', 'LiquidNavigationMath']]
    subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-d', str(tmp_path),
                    *map(str, files)], check=True, capture_output=True)
    subprocess.run(['java', '-cp', str(tmp_path), 'DockProbe'], check=True, capture_output=True)


def test_bottom_search_uses_native_action_and_back_cannot_reopen_keyboard():
    host = (JAVA / 'org/telegram/ui/MainTabsActivity.java').read_text()
    search = host[host.index('public void openChatsSearch()'):host.index('private final Runnable flexyTabConfigListener')]
    assert search.index('viewPager.setPosition(chatsPos)') < search.index('dialogsActivity.searchItem.performClick()')
    assert 'dialogsActivity.search("", true)' not in search
    dialogs = (JAVA / 'org/telegram/ui/DialogsActivity.java').read_text()
    click = dialogs[dialogs.index('searchItem.setOnClickListener(v -> {'):]
    delayed = click[click.index('AndroidUtilities.runOnUIThread'):click.index('}, 100);')]
    assert delayed.index('!animatorSearchVisible.getValue()') < delayed.index('AndroidUtilities.showKeyboard')
    layout = (JAVA / 'org/telegram/ui/MainTabsLayout.java').read_text()
    draw = layout[layout.index('protected void dispatchDraw'):]
    assert 'LiquidNavigationConfig.radiusDp()' not in draw  # Attached background may be square; its selection stays round.
