"""Pending host regressions: real beta Activity/bridge with explicit Android doubles.
No APK, device, network, signing or account operations. Requires JDK21; never skips.
"""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from client_android_doubles import STUBS

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'TMessagesProj/src/betaDevelopment/java/org/telegram/ui/beta'
BASE = '78151d9e8083290dca2617279cab3afb53540de6'
HARNESS = r'''package org.telegram.ui.beta;
import android.os.Build;
import android.view.View;
import android.widget.LinearLayout;
import org.telegram.ui.ActionBar.ActionBarLayout;
public class PlatformBackHarness {
 static void need(boolean value,String message){if(!value)throw new AssertionError(message);}
 static ActionBarLayout layout(BetaPreviewActivity owner)throws Exception{
  java.lang.reflect.Field field=BetaPreviewActivity.class.getDeclaredField("navigation");
  field.setAccessible(true);return (ActionBarLayout)field.get(owner);
 }
 public static void main(String[]args)throws Exception{
  Build.VERSION.SDK_INT=Integer.parseInt(args[1]);
  if(args[0].equals("lifecycle")){
   android.app.Activity owner=new android.app.Activity();int[] calls={0};
   BetaSystemBack bridge=new BetaSystemBack(owner,()->calls[0]++);
   bridge.register();bridge.register();
   need(owner.dispatcher.registrations==1,"duplicate callback registration");
   android.window.OnBackInvokedCallback stale=owner.dispatcher.callbacks.get(0);
   owner.dispatcher.dispatch();need(calls[0]==1,"callback did not delegate");
   bridge.close();bridge.close();stale.onBackInvoked();bridge.register();
   need(calls[0]==1&&owner.dispatcher.callbacks.isEmpty()
       &&owner.dispatcher.unregistrations==1&&owner.dispatcher.registrations==1,
       "destroyed bridge retained dispatch or re-registered");return;
  }
  BetaPreviewActivity owner=new BetaPreviewActivity();owner.onCreate(null);owner.onResume();
  try{
   boolean modern=Build.VERSION.SDK_INT>=33;
   need(owner.dispatcher.registrations==(modern?1:0),"MISSING_MODERN_BACK_BRIDGE");
   ActionBarLayout nav=layout(owner);
   ((LinearLayout)nav.getLastFragment().getFragmentView()).children.get(0).performClick();
   View.frame();need(nav.getFragmentStack().size()==2&&nav.busy,"fixture did not open chat");
   if(modern)owner.dispatcher.dispatch();else owner.onBackPressed();
   View.frame();
   need(!owner.isFinishing()&&nav.getFragmentStack().size()==2,
       "Back bypassed the existing busy-transition queue");
   nav.busy=false;View.frame();
   need(!owner.isFinishing()&&nav.getFragmentStack().size()==1,
       "queued Back did not return to synthetic home");
  }finally{owner.onPause();owner.onDestroy();}
  need(owner.dispatcher.callbacks.isEmpty(),"Activity destruction retained platform callback");
 }
}'''

class PlatformBackTests(unittest.TestCase):
    def run_cases(self, cases, original=False):
        tools = Path(os.environ['JAVA_HOME']) / 'bin'
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name, content in STUBS.items():
                target = folder / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
            target = folder / 'org/telegram/ui/beta'
            target.mkdir(parents=True)
            for source in SOURCE.glob('*.java'):
                (target / source.name).write_bytes(source.read_bytes())
            if original:
                old = subprocess.check_output(['git', 'show', BASE + ':' +
                    str((SOURCE / 'BetaPreviewActivity.java').relative_to(ROOT))], cwd=ROOT, text=True)
                (target / 'BetaPreviewActivity.java').write_text(old)
            (target / 'PlatformBackHarness.java').write_text(HARNESS)
            compiled = subprocess.run([str(tools / 'javac'), '-d', str(folder / 'classes'),
                *map(str, folder.rglob('*.java'))], capture_output=True, text=True, timeout=30)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            for mode, sdk in cases:
                completed = subprocess.run([str(tools / 'java'), '-cp', str(folder / 'classes'),
                    'org.telegram.ui.beta.PlatformBackHarness', mode, str(sdk)],
                    capture_output=True, text=True, timeout=15)
                if original:
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertIn('MISSING_MODERN_BACK_BRIDGE', completed.stderr)
                else:
                    self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_api33_36_37_original_lacks_bridge_new_activity_preserves_queue(self):
        self.run_cases([('back', 36)], original=True)
        self.run_cases([('back', 33), ('back', 36), ('back', 37)])

    def test_api24_32_keep_legacy_back_without_platform_registration(self):
        self.run_cases([('back', 24), ('back', 32)])

    def test_platform_registration_and_destruction_are_idempotent(self):
        self.run_cases([('lifecycle', 36)])


if __name__ == '__main__':
    unittest.main()
