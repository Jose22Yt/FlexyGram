"""Compile all beta wrappers with explicit doubles; execute old/new real Activity code."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from client_android_doubles import STUBS
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'TMessagesProj/src/betaDevelopment/java/org/telegram/ui/beta'
BASE='40c80878b18cdc50f49d44eb4fb26a31b9b0cf6a'
HARNESS='''package org.telegram.ui.beta;
import org.telegram.ui.ActionBar.*;import org.telegram.ui.Cells.*;import android.view.*;import android.widget.*;import java.util.concurrent.*;
public class ActivityHarness {
 static void require(boolean b,String why){if(!b)throw new AssertionError(why);}
 static ActionBarLayout layout(BetaPreviewActivity a)throws Exception{java.lang.reflect.Field f=BetaPreviewActivity.class.getDeclaredField("navigation");f.setAccessible(true);return (ActionBarLayout)f.get(a);}
 static TextSettingsCell python(ActionBarLayout nav){for(View v:((LinearLayout)nav.getLastFragment().getFragmentView()).children)if(v instanceof TextSettingsCell&&"Local Python".equals(((TextSettingsCell)v).text))return (TextSettingsCell)v;throw new AssertionError("missing Python cell");}
 public static void main(String[]args)throws Exception{
  BetaPreviewActivity a=new BetaPreviewActivity();a.onCreate(null);ActionBarLayout nav=layout(a);
  try{
   ((LinearLayout)nav.getLastFragment().getFragmentView()).children.get(1).performClick();View.frame();nav.busy=false;
   TextSettingsCell previous=python(nav);previous.performClick();
   require(com.chaquo.python.Python.entered.await(5,TimeUnit.SECONDS),"worker not started");
   nav.rebuildAllFragmentViews(true,true);TextSettingsCell current=python(nav);
   require(current!=previous,"fixture failed to recreate Settings");
   require(!current.enabled,"REBUILT_PROBE_LOST_PENDING_STATE");
   com.chaquo.python.Python.release.countDown();
   require(android.app.Activity.posted.await(5,TimeUnit.SECONDS),"UI completion not posted");
   Runnable r;while((r=android.app.Activity.ui.poll())!=null)r.run();
   require(current.enabled&&current.value.contains("initialized"),"REBUILT_PROBE_LOST_RESULT");
   require(nav.getFragmentStack().size()==2,"probe altered navigation");
  }finally{com.chaquo.python.Python.release.countDown();a.onDestroy();}
 }
}'''
class ActivityLifecycle(unittest.TestCase):
 def test_old_probe_loses_recreated_cell_new_activity_updates_current_view(self):
  old=subprocess.check_output(['git','show',BASE+':'+str((SOURCE/'BetaPreviewActivity.java').relative_to(ROOT))],cwd=ROOT,text=True)
  tools=Path(os.environ['JAVA_HOME'])/'bin'
  for original in [True,False]:
   with tempfile.TemporaryDirectory()as d:
    folder=Path(d)
    for name,source in STUBS.items():
     p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(source)
    beta=folder/'org/telegram/ui/beta';beta.mkdir(parents=True)
    for p in SOURCE.glob('*.java'):(beta/p.name).write_bytes(p.read_bytes())
    if original:(beta/'BetaPreviewActivity.java').write_text(old)
    (beta/'ActivityHarness.java').write_text(HARNESS)
    p=subprocess.run([str(tools/'javac'),'-d',str(folder/'classes'),*[str(p)for p in folder.rglob('*.java')]],capture_output=True,text=True,timeout=30)
    self.assertEqual(p.returncode,0,p.stderr)
    p=subprocess.run([str(tools/'java'),'-cp',str(folder/'classes'),'org.telegram.ui.beta.ActivityHarness'],capture_output=True,text=True,timeout=15)
    if original:self.assertNotEqual(p.returncode,0);self.assertIn('REBUILT_PROBE_LOST_PENDING_STATE',p.stderr)
    else:self.assertEqual(p.returncode,0,p.stderr)
