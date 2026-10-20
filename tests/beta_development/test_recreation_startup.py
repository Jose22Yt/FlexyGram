"""Reproduce actual Activity restart failures with explicit doubles, no Android/device."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from client_android_doubles import STUBS
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'TMessagesProj/src/betaDevelopment/java/org/telegram/ui/beta'
HARNESS=r'''package org.telegram.ui.beta;
import android.os.Bundle;import android.view.View;import android.widget.*;import org.telegram.ui.ActionBar.*;
public class RestartHarness {
 static void need(boolean value,String reason){if(!value)throw new AssertionError(reason);}
 static ActionBarLayout layout(BetaPreviewActivity a)throws Exception{java.lang.reflect.Field f=BetaPreviewActivity.class.getDeclaredField("navigation");f.setAccessible(true);return (ActionBarLayout)f.get(a);}
 static void open(BetaPreviewActivity a,int index)throws Exception{ActionBarLayout n=layout(a);((LinearLayout)n.getLastFragment().getFragmentView()).children.get(index).performClick();View.frame();n.busy=false;}
 public static void main(String[]args)throws Exception{
  if(args[0].equals("startup")){
   org.telegram.messenger.ApplicationLoader.fail=true;BetaPreviewActivity a=new BetaPreviewActivity();
   try{a.onCreate(null);}catch(Throwable e){throw new AssertionError("POST_INIT_CRASHED");}
   need(a.content instanceof TextView&&((TextView)a.content).text.contains("POST_INIT_FAILED"),"startup stage missing");
   need(!((TextView)a.content).text.contains("SYNTHETIC_PRIVATE_VALUE"),"exception value leaked");
   need(layout(a)==null,"client views built after failed init");a.onDestroy();return;
  }
  BetaPreviewActivity a=new BetaPreviewActivity();a.onCreate(null);a.onResume();
  if(args[0].equals("foreign")){
   Theme.ThemeInfo other=Theme.getTheme("Dark Blue");Theme.applyTheme(other,false,false);a.onDestroy();
   need(Theme.getCurrentTheme()==other,"DESTROY_OVERWROTE_FOREIGN_THEME");return;
  }
  boolean settings=args[0].equals("settings")||args[0].equals("dark");open(a,settings?1:0);
  if(settings){((LinearLayout)layout(a).getLastFragment().getFragmentView()).children.get(0).performClick();View.frame();}
  Bundle state=new Bundle();a.saveState(state);a.changingConfigurations=true;a.onPause();a.onDestroy();
  BetaPreviewActivity replacement=new BetaPreviewActivity();replacement.onCreate(state);replacement.onResume();
  try{
   ActionBarLayout n=layout(replacement);
   if(args[0].equals("dark")){need(Theme.isCurrentThemeDark(),"CONFIG_RESTART_LOST_DARK_THEME");return;}
   need(n.getFragmentStack().size()==2&&n.getLastFragment().getClass().getSimpleName().equals(settings?"Settings":"Conversation"),"UI_STATE_NOT_RESTORED");
   // Restored UI is idle. No account/session/native runtime claim was copied from the old Activity.
   need(!n.busy,"restoration started a transition");
   Bundle saved=new Bundle();replacement.saveState(saved);
   need(saved.values.keySet().equals(java.util.Set.of("flexygram.beta.ui.version","flexygram.beta.ui.route","flexygram.beta.ui.dark")),"UI_STATE_NOT_PRIMITIVE_ALLOWLIST");
   need(saved.values.values().stream().allMatch(v->v instanceof Integer||v instanceof Boolean),"credential-like UI state");
   replacement.onBackPressed();View.frame();
   need(n.getFragmentStack().size()==1&&!replacement.isFinishing(),"restored route cannot return home");
  }finally{replacement.onDestroy();}
 }
}'''
class RecreationStartupTests(unittest.TestCase):
 def run_scenario(self,name):
  with tempfile.TemporaryDirectory()as d:
   folder=Path(d)
   for path,source in STUBS.items():
    p=folder/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(source)
   beta=folder/'org/telegram/ui/beta';beta.mkdir(parents=True)
   for p in SOURCE.glob('*.java'):(beta/p.name).write_bytes(p.read_bytes())
   (beta/'RestartHarness.java').write_text(HARNESS)
   tools=Path(os.environ['JAVA_HOME'])/'bin'
   p=subprocess.run([str(tools/'javac'),'-d',str(folder/'classes'),*[str(p)for p in folder.rglob('*.java')]],capture_output=True,text=True,timeout=30)
   self.assertEqual(p.returncode,0,p.stderr)
   p=subprocess.run([str(tools/'java'),'-cp',str(folder/'classes'),'org.telegram.ui.beta.RestartHarness',name],capture_output=True,text=True,timeout=15)
   self.assertEqual(p.returncode,0,p.stderr)
 def test_conversation_and_settings_survive_activity_recreation(self):
  for name in ['conversation','settings']:
   with self.subTest(route=name):self.run_scenario(name)
 def test_dark_theme_survives_configuration_and_external_theme_is_preserved(self):
  for name in ['dark','foreign']:
   with self.subTest(scenario=name):self.run_scenario(name)
 def test_failed_post_init_is_reported_without_building_client_views(self):self.run_scenario('startup')
